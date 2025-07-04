import os
import sys 
import time
import pdb

import logging
import requests
from datetime import datetime
from urllib.parse import urljoin, urlparse, urlsplit
from multiprocessing import Pool, cpu_count
import pandas as pd

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC


# Setup Logger 
def get_logger(script_name):
    
    day = datetime.now().strftime("%Y%m%d")
    LOG_DIR = f"logs/{day}"
    os.makedirs(LOG_DIR, exist_ok=True)
    
    # Prepare timestamp and script name
    timestamp = datetime.now().strftime("%Y%m%d_%H%M")  # year_month_day_hr_min 
    log_filename = f"{timestamp}_{script_name}.log"
    log_path = os.path.join(LOG_DIR, log_filename)
    
    # Setup logging
    logging.basicConfig(
        filename=log_path,
        filemode="a",
        format="%(asctime)s - %(levelname)s - %(message)s",
        level=logging.INFO
    )
    
    # Also log to console
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    formatter = logging.Formatter('%(levelname)s - %(message)s')
    console_handler.setFormatter(formatter)
    logging.getLogger().addHandler(console_handler)
    
    return logging.getLogger(script_name), timestamp, log_path


script_name = os.path.splitext(os.path.basename(sys.argv[0]))[0]
logger, timestamp, log_path = get_logger(script_name)


HEADERS = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
BASE_URL = "https://www.saudiexchange.sa"

BATCH_DATE='raw-doc/20250515'
LANG='ar'
CATOGREY='finantial'
#Sub_catogry => dynamic
FORMAT='pdf' 

# MAIN_PAGE = f"{BASE_URL}/wps/portal/saudiexchange/ourmarkets/main-market-watch?locale={LANG}"
MAIN_PAGE = f"{BASE_URL}/wps/portal/saudiexchange/ourmarkets/nomuc-market-watch?locale={LANG}"

TARGET_SECTIONS = { 'ar':
    ["القوائم المالية والتقارير"],
    'en':
    ["FINANCIAL STATEMENTS AND REPORTS"]
}

SUB_CATOGREY_MAP = {
    'ar':{
         'القوائم المالية': 'statements',
         'تقرير مجلس الإدارة': 'reports'
    },
    'en': {
        'Financial Statements': 'statements',
        'Board Report': 'reports'
    }
}

SUB_CATOGREY_LIST = {
    'ar':['القوائم المالية','تقرير مجلس الإدارة'],
    'en':['Financial Statements','Board Report']
}

def fetch_links_with_selenium():
    """Use Selenium to fetch the company links from the Saudi Exchange website"""
    logging.info("Starting to fetch company links with Selenium...")
    
    # Set up headless Chrome browser
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument(f"user-agent={HEADERS['User-Agent']}")
    
    try:
        driver = webdriver.Chrome(options=chrome_options)
        logging.info(f"Loading page: {MAIN_PAGE}")
        driver.get(MAIN_PAGE)
        
        # Wait for the table to load (adjust timeout as needed)
        wait = WebDriverWait(driver, 15)
        table = wait.until(EC.presence_of_element_located((By.ID, "marketWatchTable1")))
        
        # Create empty list for company links
        links = []
        
        # Find all rows in the table
        rows = table.find_elements(By.TAG_NAME, "tr")
        logging.info(f"Found {len(rows)} rows in the table")
        
        # Extract links from each row
        for row in rows:
            try:
                # Look for links in the company name column (typically the first or second column)
                links_elements = row.find_elements(By.TAG_NAME, "a")
                
                for link in links_elements:
                    href = link.get_attribute("href")
                    if href and ("company-profile-main" in href or "company-profile-nomu-parallel"  in href):  # Filter for company profile links
                        company_name = link.text.strip()
                        full_url = href
                        if company_name:  # Only add if there's a company name
                            links.append((company_name, full_url))
                            logging.info(f"Found company: {company_name} - {full_url}")
            except Exception as e:
                logging.error(f"Error processing row: {e}")
                continue

        time.sleep(60)
        driver.quit()
        
        logging.info(f"Successfully extracted {len(links)} company links")
        return links
    
    except Exception as e:
        logging.error(f"Error in fetch_links_with_selenium: {e}")
        if 'driver' in locals():
            driver.quit()
        return []


def fetch_pdf_links(company_data):
    """Fetch file links specifically from specfic sections based on lang and section"""
    company_name, company_url = company_data
    try:
        logging.info(f"Fetching PDFs for: {company_name} ({company_url})")
        
        # Use Selenium to handle JavaScript-rendered content
        chrome_options = Options()
        chrome_options.add_argument("--headless")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument(f"user-agent={HEADERS['User-Agent']}")
        
        driver = webdriver.Chrome(options=chrome_options)
        driver.get(company_url)
        
        # Wait for the page to load
        time.sleep(3)
        
        pdf_links = []
        target_sections = TARGET_SECTIONS[LANG]
        
        try:
            # Find tabs or sections on the page
            for section_name in target_sections:
                logging.info(f"Looking for section: {section_name}")
                
                # Try to find and click on the tab/section
                try:
                    # Look for elements containing the section name
                    elements = driver.find_elements(By.XPATH, f"//*[contains(text(), '{section_name}')]")
                    
                    if elements:
                        # Click the first matching element
                        for element in elements:
                            try:
                                driver.execute_script("arguments[0].scrollIntoView();", element)
                                element.click()
                                logging.info(f"Clicked on section: {section_name}")
                                # Wait for content to load
                                time.sleep(2)
                                break
                            except Exception as e:
                                continue
                    
                    # After clicking (or trying to), look for PDF links
                    all_trs = driver.find_elements(By.TAG_NAME, "tr")
                    sub_category = 'others'

                    for i, thead in enumerate(all_trs):
                        header_row = thead.find_elements(By.TAG_NAME, "th")
                        
                        if (len(header_row) == 1) and (header_row[0].text in SUB_CATOGREY_LIST[LANG]):
                            sub_category = SUB_CATOGREY_MAP[LANG][header_row[0].text]
                            continue
                        else:
                            links = thead.find_elements(By.TAG_NAME, "a")
                            for link in links:
                                try:
                                    href = link.get_attribute("href")
                                    if href and href.endswith(".pdf"):
                                        pdf_links.append((href,sub_category,company_name))
                                        logging.info(f"Found PDF in '{section_name}': {href}")
                                except Exception as e:
                                    continue
                        
                except Exception as e:
                    logging.error(f"Error processing section '{section_name}': {e}")
        
        except Exception as e:
            logging.error(f"Error navigating company page: {e}")
        
        driver.quit()
        
        # Remove duplicates
        pdf_links = list(set(pdf_links))
        logging.info(f"Found {len(pdf_links)} unique PDFs for {company_name}")
        
        return pdf_links
    except Exception as e:
        logging.error(f"Failed to fetch PDF links from {company_url} - {e}")
        return []

def download_pdf(
    url,
    base_download_folder,
    lang=None,
    category=None,
    sub_category=None,
    file_format="pdf",
    filename=None,
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
    os.makedirs(folder_path, exist_ok=True)

    # Infer filename from url if not provided
    if not filename:
        filename = os.path.basename(urlsplit(url).path)

    if not filename.lower().endswith(f".{file_format}"):
            filename += f".{file_format}"

    save_path = f'{folder_path}/{filename}'
    
    # Download the file
    try:
        with requests.get(url, headers=HEADERS, stream=True, timeout=20) as r:
            r.raise_for_status()
            with open(save_path, 'wb') as f:
                for chunk in r.iter_content(chunk_size=8192):
                    f.write(chunk)
                logging.info(f"Downloaded: {url}")

        return save_path

    except Exception as e:
        print(f"[{datetime.now()}] Failed to download: {url} -> {e}")
        return None

def main():

    start_time = datetime.now()
    # Get company pages
    company_pages = fetch_links_with_selenium()
    logging.info(f"Fetched {len(company_pages)} company pages")

    # Get files of each company
    with Pool(cpu_count()) as pool:
        pdfs = pool.map(fetch_pdf_links, company_pages)

    all_pdf_links = []
    for pdf in pdfs:
        all_pdf_links.extend(pdf)

    # Downliad the file
    url_args = [ (hrefs,BATCH_DATE,LANG,CATOGREY,sub_categories,FORMAT,f'{company_name.replace(" ","_")}_{os.path.basename(urlsplit(hrefs).path).replace(" ","_")}') for hrefs, sub_categories, company_name in all_pdf_links ]
    
    with Pool(cpu_count()) as pool:
        store_path = pool.starmap(download_pdf, url_args)
    
    end_time = datetime.now() - start_time

    # Save source metadata
    downloadble_links, _, company_names = zip(*all_pdf_links)
    company_dict = dict(company_pages)
    company_list = [ company_dict[name] for name in company_names]

    df = pd.DataFrame({
        'source_url': company_list,
        'downloadble_link': downloadble_links,
        'store_path': store_path,
        'time_stamp': [timestamp]*len(downloadble_links)
    })

    output_csv = f'{BATCH_DATE}_{script_name}_{LANG}_{timestamp}.csv'
    df.to_csv(output_csv, index=False)

    logging.info(f"Done scraping in {end_time} Saved results metadata at {output_csv}")

if __name__ == "__main__":
    logging.info(f"INIT_CONFIG | SCRIPT_NAME={script_name} | TIMESTAMP={timestamp} | LANG={LANG} || MAIN_PAGE={MAIN_PAGE} | DATA_SOURCE={BATCH_DATE}| LOG_PATH={log_path}")
    main()