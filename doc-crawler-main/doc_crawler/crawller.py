import sys
import requests
import logging
import os

from datetime import datetime
from multiprocessing import Pool, cpu_count
from urllib.parse import urlsplit
from tqdm import tqdm  
import pandas as pd

PARENT_OUTPU_FOLDER = '/mnt/azureml/cr/j/cdcd10f324984c70adb01fe3dcc62893/exe/wd/outputs/raw-docs'
METADATA_OUTPU_FOLDER = f'{PARENT_OUTPU_FOLDER}-metadata'

class Crawller:
    def __init__(
        self,
        main_page,
        batch_date,
        lang='ar',
        category='Financial',
        sub_category='reports',
        file_format='pdf',
        script_name=None,
        logger=None,
        log_path=None,
    ):
        self.main_page = main_page
        self.batch_date = batch_date
        os.makedirs(f'{PARENT_OUTPU_FOLDER}/{batch_date}', exist_ok=True)
        # Setting up Data cat
        self.lang = lang
        self.category = category
        self.sub_category = sub_category
        self.format = file_format

        # Setting up the logger 
        self.timestamp = datetime.now().strftime("%M%H_%d%m%Y")
        self.script_name = script_name or os.path.splitext(os.path.basename(sys.argv[0]))[0]
        self.logger = logger
        self.log_path = log_path

    def set_metadata(self, data_length, lang=None, category=None, sub_category=None, format=None):
        """
        Set default metadata values for crawler attributes as lists.
        
        Args:
            data_length (int): Length of data for list initialization
            lang: Default language(s)
            category: Default category(ies)
            sub_category: Default subcategory(ies)
            format: Default format(s)
            
        Returns:
            self: Returns self for method chaining
        """
        # Define a helper function to handle each attribute
        def process_attribute(attr_value, attr_name):
            if attr_value is None:
                # Get the current default value to replicate
                current_value = getattr(self, attr_name)
                return [current_value] * data_length
            elif not isinstance(attr_value, list):
                # Convert single value to list
                return [attr_value] * data_length
            else:
                # Already a list, use as is
                return attr_value
        
        # Process each attribute
        self.lang = process_attribute(lang, "lang")
        self.category = process_attribute(category, "category")
        self.sub_category = process_attribute(sub_category, "sub_category")
        self.format = process_attribute(format, "format")    
    
    @staticmethod
    def download_file(
        url,
        base_download_folder,
        lang=None,
        category=None,
        sub_category=None,
        file_format="pdf",
        filename=None,
        logger=None
    ):
        """
        Downloads a file to a dynamically constructed folder path.
        
        Args:
            url (str): The URL of the file.
            base_download_folder (str): Base path for saving the files.
            lang (str, optional): Language code (e.g., 'en', 'ar').
            category (str, optional): Main category.
            sub_category (str, optional): Sub-category.
            file_format (str, optional): File format. Default is 'pdf'.
            filename (str, optional): Optional filename. If not provided, it's inferred from the URL.
        
        Returns:
            str: Full path of the saved PDF. None returned if not downloaded.
        """
        # Build the path dynamically
        parts = [base_download_folder, lang, category, sub_category, file_format]
        folder_path = os.path.join(*[p for p in parts if p])  # Skip None values
        os.makedirs(f'{PARENT_OUTPU_FOLDER}/{folder_path}', exist_ok=True)

        # Infer filename from url if not provided
        if not filename:
            filename = os.path.basename(urlsplit(url).path)

        if not filename.lower().endswith(f".{file_format}"):
                filename += f".{file_format}"

        save_path = f'{PARENT_OUTPU_FOLDER}/{folder_path}/{filename}'
        
        # Download the file
        try:
            with requests.get(url, headers={ "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"} ,stream=True, timeout=20) as r:
                r.raise_for_status()
                with open(save_path, 'wb') as f:
                    for chunk in r.iter_content(chunk_size=8192):
                        f.write(chunk)
                    logging.info(f"Downloaded: {url}")

            return save_path, datetime.now()
        except Exception as e:
            if logger :
                logger.error(f"[{datetime.now()}] Failed to download: {url} -> {e}")
            print(f"[{datetime.now()}] Failed to download: {url} -> {e}")
        return None, None


    def run(self, downloadble_links, titiles):
        self.logger.info(f"INIT_CONFIG | SCRIPT_NAME={self.script_name} | TIMESTAMP={self.timestamp} "
                         f"| MAIN_PAGE={self.main_page} | DATA_SOURCE={self.batch_date} | LOG_PATH={self.log_path}")

        start_time = datetime.now()
                
        if titiles is None or len(titiles) == 0:
            titiles = [None]*len(downloadble_links)

        self.logger.info(f"Found {len(downloadble_links)} links to download")

        self.set_metadata(len(downloadble_links))

        url_args = [
            (url, self.batch_date, lang, cat, sub_cat, fmt, title)
            for (url, lang, cat, sub_cat, fmt, title) in zip( downloadble_links, self.lang, self.category, self.sub_category, self.format, titiles )
        ]

        
        with Pool(cpu_count()) as pool:
            results = pool.starmap(self.download_file, url_args)

        elapsed = datetime.now() - start_time

        store_paths, download_times = zip(*results)

        df = pd.DataFrame({
        'source_url': self.main_page,
        'downloadble_link': downloadble_links,
        'store_path': store_paths,
        'download_time': download_times
        })
        
        set_lang = '_'.join(list(set(self.lang)))
        output_csv = f"{self.timestamp}_{self.script_name}_{set_lang}.csv"
        
        os.makedirs(f'{METADATA_OUTPU_FOLDER}/{self.batch_date}', exist_ok=True)
        df.to_csv(f'{METADATA_OUTPU_FOLDER}/{self.batch_date}/{output_csv}', index=False)

        
        self.logger.info(f"Done scraping in {elapsed}. Saved results to {output_csv}")
        self.logger.info("Downloads completed.")
