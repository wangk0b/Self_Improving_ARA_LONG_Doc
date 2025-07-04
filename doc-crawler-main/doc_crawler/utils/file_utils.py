import os
import argparse
from pathlib import Path
import csv
from datetime import datetime
from PyPDF2 import PdfReader
from tqdm import tqdm

def get_file_info(file_path, root_date):
    try:
        stat = file_path.stat()
        size = stat.st_size
    except OSError:
        return None  # skip unreadable files

    parts = file_path.parts
    if len(parts) < 6:
        return None

    orientation = None
    number_of_pages = None
    if file_path.suffix.lower() == '.pdf':
        try:
            reader = PdfReader(str(file_path))
            orientation = get_pdf_orientation(reader)
            number_of_pages = len(reader.pages)
            del reader
        except Exception:
            orientation = "unknown"
            number_of_pages = None

    return {
        "date": root_date,
        "language": parts[-6],
        "category": parts[-5],
        "sub_category": parts[-4],
        "format": parts[-3],
        "file_name": file_path.name,
        "file_size": size,
        "orientation": orientation,
        "number_of_pages": number_of_pages,
        "store_path": os.path.join(*parts[-6:])  # Used to join with download logs
    }

def get_pdf_orientation(reader):
    try:
        first_page = reader.pages[1]  # Skip cover
    except IndexError:
        first_page = reader.pages[0]

    try:
        media_box = first_page.mediabox
        width = float(media_box.upper_right[0]) - float(media_box.lower_left[0])
        height = float(media_box.upper_right[1]) - float(media_box.lower_left[1])
        return "landscape" if width > height else "portrait"
    except Exception:
        return "unknown"

def extract_file_metadata(root_folder):
    root_folder = Path(root_folder)
    root_date = root_folder.name
    rows = []

    for file_path in tqdm(root_folder.rglob("*")):
        if file_path.is_file():
            info = get_file_info(file_path, root_date)
            if info:
                rows.append(info)

    return rows

def load_download_logs(csv_paths):
    log_map = {}
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
    return log_map

def merge_with_logs(rows, log_map):
    for row in rows:
        match = log_map.get(row["store_path"], {})
        row["source_url"] = match.get("source_url")
        row["downloadable_link"] = match.get("downloadable_link")
        row["download_time"] = match.get("download_time")
    return rows

def save_to_tsv(rows, output_path):

    fieldnames = [
        "date", "language", "category", "sub_category", "format",
        "file_name", "file_size", "orientation", "number_of_pages",
        "source_url", "downloadable_link", "download_time", "store_path"
    ]
    with open(output_path, mode="w", newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, delimiter='\t', fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

def main():
    parser = argparse.ArgumentParser(description="Get per-file metadata and merge with download logs.")
    parser.add_argument("root_folder", help="Path to the root folder (e.g. /path/to/raw-doc/20250515)")
    parser.add_argument("--output", default="file_metadata.tsv", help="Output TSV filename")
    parser.add_argument("--download_logs", nargs="*", help="One or more download log CSVs with source_url, downloadable_link, store_path, download_time")
    args = parser.parse_args()

    rows = extract_file_metadata(args.root_folder)

    if args.download_logs:
        log_map = load_download_logs(args.download_logs)
        rows = merge_with_logs(rows, log_map)

    save_to_tsv(rows, args.output)
    print(f"Metadata TSV saved to: {args.output}")

if __name__ == "__main__":
    main()
