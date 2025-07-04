import os
import subprocess
import requests
import logging
from bs4 import BeautifulSoup
from multiprocessing import Pool, cpu_count
from urllib.parse import urljoin
import pandas as pd
import logging
from datetime import datetime
import sys
from shared_utils import get_logger, download_file

timestamp = datetime.now().strftime("%M%H_%d%m%Y")  # MH_DMY
script_name = os.path.splitext(os.path.basename(sys.argv[0]))[0]
logger, log_path = get_logger(timestamp,script_name)

# Constants
BATCH_DATE='temp/20250515'
LANG='ar'
CATOGREY='financial'
SUB_CATOGREY= 'reports'
FORMAT='pdf'

BASE_URL = "https://www.saudiexchange.sa"
MAIN_PAGE = f'{BASE_URL}/endpoint'


def fetch_links_n_metadata():
    '''
    Get html eliments and get downloadable links and any available metadata
    '''
    return [], []


def main():
    #Step 1: Get downloadble_links (custom)

    start_time = datetime.now()
    downloadble_links, titles = fetch_links_n_metadata() # Change function implimntation to match its html structure
    
    
    logger.info(f"Found {len(downloadble_links)} PDF links.")
    logger.info(f'Found {len(downloadble_links)} links to download ')
    
    #Step 2: Prapare argus for download_file, required for catogrization (custom)
    url_args = [ (hrefs,BATCH_DATE,LANG,CATOGREY,SUB_CATOGREY,FORMAT,filenaem) for hrefs, filenaem in zip(downloadble_links,titles) ]
    
    #Step 3: Multi-process to download the data 
    with Pool(cpu_count()) as pool:
        store_path, download_time = pool.starmap(download_file, url_args)
    
    end_time = datetime.now() - start_time
    
    #Step 4: Log metadata
    df = pd.DataFrame({
        'source_url': MAIN_PAGE,
        'downloadble_link': downloadble_links,
        'store_path': store_path,
        'download_time': download_time
    })

    output_csv = f'{BATCH_DATE}_{script_name}_{LANG}_{timestamp}.csv'
    df.to_csv(output_csv, index=False)

    logger.info(f"Done scraping in {end_time} Saved results to {output_csv}")
    logger.info("downloads completed.")

if __name__ == "__main__":
    logging.info(f"INIT_CONFIG | SCRIPT_NAME={script_name} | TIMESTAMP={timestamp} | LANG={LANG} || MAIN_PAGE={MAIN_PAGE} | DATA_SOURCE={BATCH_DATE}| LOG_PATH={log_path}")
    main()
