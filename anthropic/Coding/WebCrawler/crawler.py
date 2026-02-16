import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin
import os
import tempfile

HEADERS = {
    'User-Agent': 'CoolBot/0.0 (https://example.org/coolbot/; coolbot@example.org) generic-library/0.0'
}

def get_links():
    countries_list = 'https://en.wikipedia.org/wiki/List_of_countries_by_population_(United_Nations)'
    all_links = []
    
    response = requests.get(countries_list, headers=HEADERS)
    soup = BeautifulSoup(response.text, "lxml")
    countries_el = soup.select('td .flagicon+ a')
    for link_el in countries_el:
        link = link_el.get("href")
        link = urljoin(countries_list, link)
        all_links.append(link)
    return all_links

def save_links_to_temp(link):
    # Use the system temp directory
    temp_dir = os.path.join(tempfile.gettempdir(), 'crawled_pages')
    os.makedirs(temp_dir, exist_ok=True)
    
    try:
        # Generate filename from URL
        filename = link.split("/")[-1] + ".html"
        filepath = os.path.join(temp_dir, filename)
        
        print(f"Downloading {link}...")
        response = requests.get(link, headers=HEADERS)
        
        with open(filepath, "wb") as f:
            f.write(response.content)
    except Exception as e:
        print(f"Error processing {link}: {e}")

import time
from concurrent.futures import ThreadPoolExecutor

if __name__ == "__main__":
    links = get_links()
    
    # Print location once
    temp_dir = os.path.join(tempfile.gettempdir(), 'crawled_pages')
    print(f"Saving pages to: {temp_dir}")
    
    start_time = time.time()
    
    # Use ThreadPoolExecutor to download pages in parallel
    with ThreadPoolExecutor(max_workers=10) as executor:
        executor.map(save_links_to_temp, links[:200])
        
    duration = time.time() - start_time
    print(f"Downloaded {len(links[:200])} links in {duration} seconds")