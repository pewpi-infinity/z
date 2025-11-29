#!/data/data/com.termux/files/usr/bin/python3
import os
import requests
from bs4 import BeautifulSoup

URLS_FILE = "urls.txt"
VALID_URLS_FILE = "valid_urls.txt"
RAW_DIR = "pewpi-infinity/z/raw_sources"

# Ensure raw_sources directory exists
os.makedirs(RAW_DIR, exist_ok=True)

HEADERS = {
    "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
                  "(KHTML, like Gecko) Chrome/120.0 Safari/537.36"
}

def load_urls():
    if not os.path.exists(URLS_FILE):
        raise FileNotFoundError(f"{URLS_FILE} missing.")
    with open(URLS_FILE, "r") as f:
        urls = [u.strip() for u in f.readlines() if u.strip()]
    return urls

def fetch(url):
    """Download the content with browser headers and fallback HTML parsing."""
    try:
        r = requests.get(url, headers=HEADERS, timeout=25)
        r.raise_for_status()

        # If PDF, save raw text of bytes
        if "pdf" in r.headers.get("content-type", ""):
            return r.content.decode("latin1", errors="ignore")

        # HTML: extract readable text
        soup = BeautifulSoup(r.text, "html.parser")
        text = soup.get_text(separator="\n")
        return text

    except Exception as e:
        print(f"[SCRAPER ERROR] Could not fetch {url} -> {e}")
        return None

def save_raw(index, text):
    fname = os.path.join(RAW_DIR, f"raw_{index:05d}.txt")
    with open(fname, "w", encoding="utf-8", errors="ignore") as f:
        f.write(text)
    print(f"[SCRAPER] Saved raw_{index:05d}.txt")

def main():
    print("[SCRAPER] Loading URL list...")
    urls = load_urls()

    print(f"[SCRAPER] Loaded {len(urls)} URLs...")

    clean = []
    for url in urls:
        if " " in url or not url.startswith("http"):
            print(f"[BAD] {url} -> removing")
            continue
        clean.append(url)

    # Save validated list
    with open(VALID_URLS_FILE, "w") as f:
        for u in clean:
            f.write(u + "\n")

    print("[SCRAPER] Validation complete.")
    print("[SCRAPER] Starting scrape of validated URLs...")

    for i, url in enumerate(clean, start=1):
        text = fetch(url)
        if text:
            save_raw(i, text)

    print("[SCRAPER] DONE — All raw_sources saved.")

if __name__ == "__main__":
    main()
