import argparse
import csv
import json

from pathlib import Path
from tqdm import tqdm

from format_utils import validate_and_extract_metadata
from dataframe_utils import save_to_tsv, summarize_metadata
from validation_schema import ValidationError
import pdb  # For debugging purposes

def extract_file_metadata(root_folder,invalid_doc_log):
    root_folder = Path(root_folder)
    root_date = root_folder.name
    rows = []
    invalid_rows = []
    
    for file_path in tqdm(root_folder.rglob("*")):
        try:
            if file_path.is_file():
                info = validate_and_extract_metadata(file_path)
                if type(info) is ValidationError:
                    invalid_rows.append({
                            'path':str(file_path),
                            'validationerror':info.error_type.value})
                else:
                    # Log invalid files
                    rows.append(info)
        except Exception as e:
            invalid_rows.append({
                'path':str(file_path),
                'validationerror':str(e)})
            
    
    if len(invalid_rows) != 0:

        f = open(invalid_doc_log,'w')
        for item in invalid_rows:
            f.write(json.dumps(item, ensure_ascii=False) + '\n')

        print(f'{len(invalid_rows)} invalid/unreadable doc found. paths saved at {invalid_doc_log}')
    return rows

def load_download_logs(paths):
    log_map = {}
    
    csv_paths = [Path(p) for p in paths if Path(p).is_file() and p.endswith('.csv')]
    json_paths = [Path(p) for p in paths if Path(p).is_file() and p.endswith('.json')]
    
    # Handle CSV files (each row is a dict with store_path, source_url, downloadable_link, download_time)
    for csv_path in csv_paths:
        with open(csv_path, newline='', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                key = row.get("store_path")

                if key:
                    log_map[key] = {
                        "source_url": row.get("source_url"),
                        "downloadable_link": row.get("downloadable_link"),
                        "download_time": row.get("download_time"),
                    }
    
    # Handle JSON files (entire file is a list of dicts)
    for json_path in json_paths:
        
        with open(json_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            for item in data['file_details']:
                if item.get("status") == "success":
                    try:
                        key = item.get("filename")
                        if key:
                            log_map[key] = {
                                "source_url": item.get("parent_url", "").split("?")[0],
                                "downloadable_link": item.get("url"),
                                "download_time": item.get("timestamp"),
                            }
                    except (json.JSONDecodeError, TypeError):
                        continue  # Skip bad files

    return log_map

def merge_with_logs(rows, log_map):
    for row in rows:
        match = log_map.get(row["store_path"], {})
        row["source_url"] = match.get("source_url")
        row["downloadable_link"] = match.get("downloadable_link")
        row["download_time"] = match.get("download_time")
    return rows

def main():
    parser = argparse.ArgumentParser(description="Check document validity and get per-file metadata.")
    parser.add_argument("root_folder", help="Path to the root folder (e.g. /path/to/raw-doc/www_site_com)")
    parser.add_argument("--output", default="file_metadata.tsv", help="Output TSV filename")
    parser.add_argument("--download_logs", nargs="*", help="One or more download log CSVs with source_url, downloadable_link, store_path, download_time")
    parser.add_argument("--invalid_doc", nargs="*", default="./invalid_doc.txt", help="Paths of unreadable or invalid documents. ")
    
    args = parser.parse_args()

    print(f"Extracting metadata of : {args.root_folder}")
    rows = extract_file_metadata(args.root_folder,args.invalid_doc)
    
    if args.download_logs:
        print(f"Loading download logs from: {args.download_logs}")
        log_map = load_download_logs(args.download_logs)
        rows = merge_with_logs(rows, log_map)

    df = save_to_tsv(rows, args.output)
    print(f"Metadata TSV saved to: {args.output}")
    summarize_metadata(df)
    

if __name__ == "__main__":
    main()
