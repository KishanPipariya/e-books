import os
import logging
import time
from typing import List
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup
from tqdm import tqdm
from selenium import webdriver
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

BASE_URL = "https://standardebooks.org"
EBOOKS_URL = f"{BASE_URL}/ebooks"
DOWNLOAD_DIR = os.path.abspath('ebooks')
LINKS_FILE = "links.txt"

def setup_driver(download_dir: str) -> webdriver.Firefox:
    options = Options()
    options.add_argument("--headless")
    options.set_preference('browser.download.folderList', 2)
    options.set_preference('browser.download.manager.showWhenStarting', False)
    options.set_preference('browser.download.dir', download_dir)
    options.set_preference('browser.helperApps.neverAsk.saveToDisk', 'application/octet-stream,application/epub+zip')
    
    return webdriver.Firefox(options=options)

def get_total_pages(session: requests.Session) -> int:
    try:
        response = session.get(f"{EBOOKS_URL}?page=1&per-page=48")
        response.raise_for_status()
        soup = BeautifulSoup(response.content, features='xml')
        
        # Find the navigation element that contains page numbers
        navs = soup.find_all('nav')
        if len(navs) < 2:
            logger.warning("Could not find pagination navigation. Defaulting to 1 page.")
            return 1
            
        pagination_nav = navs[1]
        page_items = pagination_nav.find_all('li')
        return len(page_items)
    except Exception as e:
        logger.error(f"Error fetching total pages: {e}")
        return 1

def scrape_book_links(session: requests.Session, page: int) -> List[str]:
    """Scrapes book links from a single page."""
    links = []
    url = f"{EBOOKS_URL}?page={page}&per-page=48"
    try:
        response = session.get(url)
        response.raise_for_status()
        soup = BeautifulSoup(response.content, 'lxml')
        
        ol = soup.find('ol')
        if not ol:
            return []
            
        anchors = ol.find_all('a')
        valid_anchors = [a for a in anchors if 'https' not in a.get('href', '')]

        for i in range(0, len(valid_anchors), 2):
            href = valid_anchors[i].get('href')
            if href:
                full_url = urljoin(BASE_URL, href)
                links.append(full_url)
                
    except Exception as e:
        logger.error(f"Error scraping links from page {page}: {e}")
        
    return links

def get_all_book_links() -> List[str]:
    """Orchestrates the scraping of all book links."""
    os.makedirs(DOWNLOAD_DIR, exist_ok=True)
    
    session = requests.Session()
    session.headers.update({'User-Agent': 'Mozilla/5.0 (compatible; EbookScraper/1.0)'})
    
    logger.info("Fetching total pages...")
    total_pages = get_total_pages(session)
    logger.info(f"Total pages to scrape: {total_pages}")
    
    all_links = []
    for i in tqdm(range(1, total_pages + 1), desc="Scraping Pages"):
        links = scrape_book_links(session, i)
        all_links.extend(links)
        
    # Save links to file
    with open(LINKS_FILE, "w") as f:
        for link in all_links:
            f.write(f"{link}\n")
            
    logger.info(f"Saved {len(all_links)} links to {LINKS_FILE}")
    return all_links

def download_ebook(driver: webdriver.Firefox, url: str):
    """Downloads the kepub file for a given book URL."""
    try:
        driver.get(url)
        
        wait = WebDriverWait(driver, 10)
        link_elem = wait.until(EC.element_to_be_clickable((By.LINK_TEXT, "kepub")))
        link_elem.click()
        
       
        time.sleep(2) 
        
    except TimeoutException:
        logger.warning(f"Timeout waiting for download link at {url}")
    except Exception as e:
        logger.error(f"Error downloading from {url}: {e}")

def download_all_ebooks():
    """Reads links from file and downloads them."""
    if not os.path.exists(LINKS_FILE):
        logger.error(f"{LINKS_FILE} not found. Run scraping first.")
        return

    with open(LINKS_FILE, 'r') as f:
        links = [line.strip() for line in f.readlines() if line.strip()]
        
    logger.info(f"Found {len(links)} books to download.")
    
    driver = setup_driver(DOWNLOAD_DIR)
    try:
        for link in tqdm(links, desc="Downloading Books"):
            download_ebook(driver, link)
    finally:
        driver.quit()

def main():
    if not os.path.exists(LINKS_FILE) or os.path.getsize(LINKS_FILE) == 0:
        get_all_book_links()
    else:
        logger.info(f"Using existing {LINKS_FILE}. Delete it to re-scrape.")
        
    download_all_ebooks()

if __name__ == "__main__":
    main()

        
