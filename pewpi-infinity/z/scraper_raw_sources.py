#!/data/data/com.termux/files/usr/bin/python3
import os
import requests

URL_FILE = "urls.txt"
RAW_DIR = "pewpi-infinity/z/raw_sources"

os.makedirs(RAW_DIR, exist_ok=True)

def load_urls():
    urls = []
    if not os.path.exists(URL_FILE):
        print(f"[SCRAPER ERROR] {URL_FILE} missing")
        return urls
    with open(URL_FILE, "r") as f:
        for line in f:
            u = line.strip()
            if u:
                urls.append(u)
    return urls

def fetch(url):
    try:
        r = requests.get(url, timeout=20)
        r.raise_for_status()
        return r.text
    except Exception as e:
        print(f"[SCRAPER ERROR] {url}: {e}")
        return None

def main():
    print("[SCRAPER] Loading URL list...")
    urls = load_urls()
    print(f"[SCRAPER] Loaded {len(urls)} URLs...")

    for i, url in enumerate(urls, start=1):
        print(f"[SCRAPER] Fetching: {url}")
        text = fetch(url)
        if text is None:
            continue
        out = os.path.join(RAW_DIR, f"raw_{i:05d}.txt")
        with open(out, "w", encoding="utf-8", errors="ignore") as f:
            f.write(text)
        print(f"[SCRAPER] Saved {os.path.basename(out)}")

    print("[SCRAPER] DONE – All raw_sources saved.")

if __name__ == "__main__":
    main()

