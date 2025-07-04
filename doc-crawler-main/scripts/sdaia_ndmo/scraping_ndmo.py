import os
import sys
from bs4 import BeautifulSoup
from urllib.parse import urljoin
from datetime import datetime
import requests
import pdb 

from doc_crawler.utils.shared_utils import get_logger, sanitize_filename
from doc_crawler import Crawller

LANG='ar' # ar
main_url = f"https://sdaia.gov.sa/{LANG}/SDAIA/about/Pages/RegulationsAndPolicies.aspx"
base_url = "https://sdaia.gov.sa"

def fetch_sdaia_documents(main_url,base_url):
    try:
        response = requests.get(main_url, headers={ "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)" })
        response.raise_for_status()
    except Exception as e:
        print(f"[ERROR] Failed to fetch page: {e}")
        return [], []

    soup = BeautifulSoup(response.content, "html.parser")
    pdf_links = []
    titles = []

    for a_tag in soup.find_all("a", href=True):
        href = a_tag["href"]
        if href.lower().endswith(".pdf"):
            full_url = urljoin(base_url, href)
            text = sanitize_filename(os.path.basename(href))
            pdf_links.append(full_url)
            titles.append(text)
    
    return pdf_links, titles

if __name__ == "__main__":
    timestamp = datetime.now().strftime("%M%H_%d%m%Y")
    script_name = os.path.splitext(os.path.basename(sys.argv[0]))[0]
    logger, log_path = get_logger(timestamp, script_name)

    # Crawl Setup
    crawl = Crawller(
        main_page=main_url,
        batch_date="20250518",
        lang=LANG,
        category="government",
        sub_category="regulations",
        file_format="pdf",
        logger=logger,
        script_name=script_name,
        log_path=log_path,
    )

    links, titles = fetch_sdaia_documents(main_url,base_url)
    crawl.run(links, titles)
    
