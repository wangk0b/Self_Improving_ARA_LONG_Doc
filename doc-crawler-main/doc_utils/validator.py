import os
import re
import shutil
import argparse
import hashlib
import multiprocessing
from tqdm import tqdm
from functools import partial

import pandas as pd
import numpy as np
import fitz  # PyMuPDF
from datetime import datetime, timedelta

import pdb
tqdm.pandas()

from format_utils import convert_to_images
from redis_cache import get_redis_connection
from modules.language_detector import YoloLangDetector, TextLangDetector
from modules.layout_segmentation import LayoutSegmentor

def process_row(row_dict, lang_detector=None):
    fname = row_dict['full_path']
    try:
        images = convert_to_images(fname)

        if isinstance(lang_detector, TextLangDetector):
            doc = fitz.open(fname)
            pages_text = [page.get_text() for page in doc]
            cls_lang = lang_detector.get_lang(pages_text)
        else:
            cls_lang = lang_detector.get_lang(images)

        return ('ok', fname, cls_lang)
    
    except Exception as e:
        return ('error', fname, str(e))
    

def run_parallel_lang_detection(df, lang_detector, num_workers=10):
    # Convert DataFrame to list of dicts for safety
    records = df.to_dict(orient='records')
    func_process_row = partial(process_row, lang_detector=lang_detector)
    
    results = []
    if num_workers == 1: #For debugging 
        for rec in tqdm(records):
            _tuple = func_process_row(rec)
            results.append(_tuple)
    else:     
        max_workers = multiprocessing.cpu_count() - 5
        with multiprocessing.Pool(processes=num_workers or max_workers) as pool:
            results = list(tqdm(pool.imap(func_process_row, records), total=len(records)))

    lang_results = []
    dup_flags = []
    error_logs = []

    for res in results:
        if res[0] == 'ok':
            _, fname, cls_lang = res
            lang_results.append((fname, cls_lang))
            dup_flags.append(False)
            error_logs.append((fname, None))
        else:
            _, fname, err = res
            lang_results.append((fname, 'unknown'))
            dup_flags.append(False)
            error_logs.append((fname, err))

    return lang_results, dup_flags, error_logs

    
def get_canonical_content_hash(images,hash_algo="sha256"):
    '''
    Computes the canonical content hash of images
    
    Args:
        pdf (bytes): The contents of the PDF file.
        hash_algo (str, optional): The hash algorithm to use. Defaults to "sha256".
    '''
    h = hashlib.new(hash_algo)
    for image in images:
        h.update(np.array(image).tobytes(order="C"))
        
    return h.hexdigest()

def file_foramt_validation(file_path):
    """
    Validate the file format based on its extension.
    """
    valid_extensions = {'.pdf', '.txt', '.docx', '.xlsx', '.csv'}
    is_valid_ext = file_path.suffix.lower() in valid_extensions
    if not is_valid_ext:
        print(f"Invalid file extension for: {file_path}")
        return False
    is_vliad_folder = file_path.parts[-3] == file_path.suffix.lower()

    return (is_valid_ext and is_vliad_folder)

def is_file_exist(df,root_folder):
    """
    Check if the file exists in the filesystem.
    """
    is_exist = df['store_path'].apply(lambda x: os.path.exists((os.path.join(root_folder, x))))
    return is_exist


def detect_duplicate_filenames(df):
    """
    Detect duplicate files based on cleaned filenames (ignores trailing _1, _2, etc.).
    Returns a boolean Series indicating duplicate rows.
    """
    def normalize_name(path):
        filename = os.path.basename(path)
        name_no_ext = os.path.splitext(filename)[0]
        return re.sub(r'_\d+$', '', name_no_ext)

    clean_names = df['store_path'].apply(normalize_name)
    return clean_names.duplicated(keep=False)

if __name__ == "__main__":
        
    parser = argparse.ArgumentParser(description="Validate file formats and check existence in the filesystem.")
    parser.add_argument("root_folder", help="Path to the root folder (e.g. /path/to/raw-doc/www_example_com)")
    parser.add_argument("-m","--metadata_path", help="metadata file in TSV or CSV format", default="file_metadata.tsv")
    parser.add_argument("-pt","--model_path", help="model path in pt", default="/mnt/azureml/cr/j/33f053f07b6742588ce31b1e9323cf15/exe/wd/outputs/doc-crawler/models/img_lang_cls_yolov11n_1.pt")

    args = parser.parse_args()
    
    root_folder = args.root_folder
    metadata_path = args.metadata_path
    
    if metadata_path.endswith('.tsv'):
        df = pd.read_csv(metadata_path,sep='\t', encoding='utf-8')
        ext = '.tsv'
    else:
        df = pd.read_csv(metadata_path, encoding='utf-8')
        ext = '.csv'
    
    # Step1: Check if the file is actually exist in the filesystem
    print('Checking if files exists in the filesystem')
    is_exist = is_file_exist(df, root_folder)
    
    if not is_exist.all():
        #TODO: dump the missing files to a separate file
        missing_files = df.loc[~is_exist]
        print(f"{len(missing_files)} files do not exist in the filesystem:")
        df['is_exist'] = is_exist
        df = df[df['is_exist']==True]
    
    #Step2: Check File duplicates based on content
    df['full_path'] = df['store_path'].apply(lambda x: os.path.join(root_folder, x))
    r = get_redis_connection()
    
    if args.model_path is None:
        lang_detector = TextLangDetector(
            labels={0: "ar", 1: "en"}
        )
    else:
        lang_detector = YoloLangDetector(
            labels={0: "ar", 1: "en",2:"ar-en"},
            model_path=args.model_path,
            layout_segmenter= LayoutSegmentor(
            model_path='/mnt/azureml/cr/j/33f053f07b6742588ce31b1e9323cf15/exe/wd/outputs/doc-crawler/models/yolov12l-doclaynet.pt')
        )
    
    start = datetime.now().isoformat()
    print("start",start)   
    lang, dup, errors = run_parallel_lang_detection(df, lang_detector)
    import pdb; pdb.set_trace()
    
    df['errors'] = [err if err else None for _, err in errors]
    df['new_lang'] = [lang[1] for lang in lang]
    df['is_duplicate_content'] = dup
    df = df[df['is_duplicate_content']== False]
    df = df[df['new_lang'] != 'unknown']
    
    import pdb; pdb.set_trace()
    
    df['new_file_path'] = [
    path.replace(f'/{lang}/',f'/{new_lang}/') if lang != new_lang else None 
    for path, lang, new_lang in zip(df['full_path'], df['language'], df['new_lang'])
    ]

    for _, row in tqdm(df[df['new_file_path'].notna()].iterrows()):
        src = row['full_path']
        dst = row['new_file_path']
        
        os.makedirs(os.path.dirname(dst), exist_ok=True)
        shutil.move(src, dst)

    end = datetime.now().isoformat()
    print("end",end)
    import pdb; pdb.set_trace()
    
    #Step2: Check File duplicates based on file_name
    # df['is_duplicate_name'] = detect_duplicate_filenames(df)
    # duplicates_df = df[df['is_duplicate_name']]

    # #Dump duplicate files to a separate file to be checked manually
    # output_path = metadata_path.replace(ext,f'duplicates{ext}') 
    # duplicates_df.to_csv(output_path, sep='\t' if ext == '.tsv' else ',', index=False, encoding='utf-8')
    
    #Step3: Validate docoment lang
    
