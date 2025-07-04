#!/bin/bash

ROOT_DIR="/mnt/azureml/cr/j/33f053f07b6742588ce31b1e9323cf15/exe/wd/outputs/outputs/raw-docs/"
metadata_path="./www_sama_gov_sa.tsv"
download_logs="/mnt/azureml/cr/j/33f053f07b6742588ce31b1e9323cf15/cap/data-capability/wd/raw_docs_metadat_out/20250617/runs/www.sama.gov.sa_2600_27052025_scraping_sama_recursive.csv"

cd /mnt/azureml/cr/j/33f053f07b6742588ce31b1e9323cf15/exe/wd/outputs/doc-crawler/doc_utils
echo $(pwd) 

# python3 metadata_collector.py $ROOT_DIR \
#     --output $metadata_path \
#     --download_logs $download_logs

# validation without parent folder (website name folder)
python3 validator.py $ROOT_DIR -m $metadata_path
