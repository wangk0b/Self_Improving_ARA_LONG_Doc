import os
import re
import subprocess
import requests
import logging
from bs4 import BeautifulSoup
from multiprocessing import Pool, cpu_count
from urllib.parse import urljoin
import pandas as pd
import os
import logging
from datetime import datetime
import sys

#TODO Move logging to utils folder

# Create logs directory
day = datetime.now().strftime("%d%m%Y")
LOG_DIR = f"logs/{day}"
os.makedirs(LOG_DIR, exist_ok=True)

# Prepare timestamp and script name
timestamp = datetime.now().strftime("%M%H_%d%m%Y")  # min_hr_day_month_year
script_name = os.path.splitext(os.path.basename(sys.argv[0]))[0]
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

####


_dict = {
    'ar': {
        'page_url': 'https://www.saudiexchange.sa/wps/portal/saudiexchange/newsandreports/reports-publications/annual-reports?locale=ar',
    },
    'en': {
        'page_url': 'https://www.saudiexchange.sa/wps/portal/saudiexchange/newsandreports/reports-publications/annual-reports?locale=en',
    }
}

# Constants
BASE_URL = "https://www.saudiexchange.sa"
USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
HEADERS = {"User-Agent": USER_AGENT}
DOWNLOAD_DIR = "downloads/saudiexchange/ar/reports-publication/annual-reports"
LANG = 'ar'
PAGE_URL = _dict[LANG]['page_url']

os.makedirs(DOWNLOAD_DIR, exist_ok=True)

def sanitize_filename(url):
    base = os.path.basename(url.split("?")[0])
    return re.sub(r"[^\w\-_\. ]", "_", base).replace(" ", "_")

def fetch_pdf_links():
    try:
        response = requests.get(PAGE_URL, headers=HEADERS)
        response.raise_for_status()
    except requests.RequestException as e:
        logging.error(f"Failed to fetch page {PAGE_URL}: {e}")
        return [], [], []

    soup = BeautifulSoup(response.text, "html.parser")
    trading_list = soup.find(class_="tradingList")
    if not trading_list:
        logging.warning(".tradingList not found in page.")
        return [], [], []

    links = []
    headings = [h2.get_text(strip=True) for h2 in trading_list.find_all("h2")]
    lastupdates = [date.get_text(strip=True).replace('\n', ' ').strip()
                   for date in trading_list.find_all(class_='lastUpdate')]

    for a in trading_list.find_all("a", href=True):
        text = a.get_text(strip=True)
        href = a["href"]
        if "تحميل" in text or "Download" in text:
            full_url = urljoin(BASE_URL, href)
            links.append(full_url)

    return links, headings, lastupdates

def download_with_wget(link):
    url, title = link
    filename = sanitize_filename(title)
    output_path = os.path.join(DOWNLOAD_DIR, title + '.pdf')
    if os.path.exists(output_path):
        logging.info(f"Already exists: {title}.pdf saved with {title.replace('.pdf','_2.pdf')}")
        output_path = output_path.replace('.pdf','_2.pdf')

    command = [
        "wget",
        "--user-agent=" + USER_AGENT,
        "-O", output_path,
        url
    ]

    try:
        subprocess.run(command, check=True)
        logging.info(f"Downloaded: {filename}")
        return output_path
    except subprocess.CalledProcessError as e:
        logging.error(f"Failed to download {filename}: {e}")
        return None

def main():

    start_time = datetime.now()
    links, headings, lastupdates = fetch_pdf_links()
    logging.info(f"Found {len(links)} PDF links.")
    logging.info(f'Found {len(links)} links to download ')
    with Pool(processes=max(int(cpu_count() / 2), 1)) as pool:
        output_paths = pool.map(download_with_wget, zip(links, headings))
    
    end_time = datetime.now() - start_time
    
    df = pd.DataFrame({
        'src_url': PAGE_URL,
        'links': links,
        'title': headings,
        'lastupdate': lastupdates,
        'store_path': output_paths
    })

    output_csv = f'saudiexchange_annual_reports_{LANG}_{timestamp}.csv'
    df.to_csv(output_csv, index=False)

    logging.info(f"Done scraoing in {end_time} seconds Saved results to {output_csv}")
    logging.info("downloads completed.")

if __name__ == "__main__":
    logging.info(f"INIT_CONFIG | SCRIPT_NAME={script_name} | TIMESTAMP={timestamp} | LANG={LANG} | PAGE_URL={PAGE_URL} | BASE_URL={BASE_URL} | USER_AGENT={USER_AGENT} | DOWNLOAD_DIR={DOWNLOAD_DIR} | LOG_PATH={log_path}")
    main()
