import os
import requests
import time
from pathlib import Path
from bs4 import BeautifulSoup

# -------- CONFIG --------
URLS_FILE = "urls.txt"
RAW_DIR = Path("pewpi-infinity/z/raw_sources")
REQUEST_TIMEOUT = 15
SLEEP_BETWEEN_REQUESTS = 1
# ------------------------

def ensure_dirs():
    RAW_DIR.mkdir(parents=True, exist_ok=True)

def load_urls():
    if not os.path.exists(URLS_FILE):
        raise FileNotFoundError(f"{URLS_FILE} missing.")
    with open(URLS_FILE, "r") as f:
        return [u.strip() for u in f if u.strip()]

def fetch_html(url):
    headers = {
        "User-Agent": "InfinityResearchScraper/3.0"
    }
    r = requests.get(url, headers=headers, timeout=REQUEST_TIMEOUT)
    r.raise_for_status()
    return r.text

def extract_visible_text(html):
    soup = BeautifulSoup(html, "html.parser")
    for tag in soup(["script", "style", "noscript"]):
        tag.extract()
    text = soup.get_text(" ")
    return " ".join(t.strip() for t in text.split())

def write_raw_source(url, text, index):
    filename = RAW_DIR / f"raw_{index:05d}.txt"
    with open(filename, "w", encoding="utf-8") as f:
        f.write(f"URL: {url}\n\n")
        f.write(text)

def main():
    ensure_dirs()
    urls = load_urls()

    print(f"[SCRAPER] Loaded {len(urls)} URLs.")
    for idx, url in enumerate(urls, start=1):
        try:
            print(f"[SCRAPER] Fetching: {url}")
            html = fetch_html(url)
            text = extract_visible_text(html)
            write_raw_source(url, text, idx)
            print(f"[SCRAPER] Saved raw source #{idx}")
            time.sleep(SLEEP_BETWEEN_REQUESTS)
        except Exception as e:
            print(f"[SCRAPER] ERROR: {e}")

    print("[SCRAPER] Done. Raw sources saved to pewpi-infinity/z/raw_sources/")
    
if __name__ == "__main__":
    main()
