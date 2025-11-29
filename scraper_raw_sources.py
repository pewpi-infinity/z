#!/data/data/com.termux/files/usr/bin/python3
import os
import requests
from bs4 import BeautifulSoup

# Input URL list
URL_FILE = "valid_urls.txt"
VALID_URLS_FILE = "valid_urls.txt"

# Output directory for raw scraped text
RAW_DIR = "pewpi-infinity/z/raw_sources"

# Ensure output folder exists
os.makedirs(RAW_DIR, exist_ok=True)

# Browser-like headers so sites don’t block scraping
HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (X11; Linux x86_64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0 Safari/537.36"
    )
}

def load_urls():
    if not os.path.exists(URL_FILE):
        raise FileNotFoundError(f"{URL_FILE} missing.")

    with open(URL_FILE, "r") as f:
        urls = [u.strip() for u in f.readlines() if u.strip()]

    return urls


def fetch(url):
    """Download content with browser headers and extract readable text."""
    try:
        print(f"[SCRAPER] Fetching: {url}")
        r = requests.get(url, headers=HEADERS, timeout=15)
        r.raise_for_status()

        ctype = r.headers.get("content-type", "").lower()

        # Handle PDFs differently
        if "pdf" in ctype:
            try:
                return r.content.decode("latin1", errors="ignore")
            except Exception:
                return r.text

        # Extract readable text from HTML
        soup = BeautifulSoup(r.text, "html.parser")

        # Remove scripts/styles
        for tag in soup(["script", "style"]):
            tag.decompose()

        text = soup.get_text(separator="\n", strip=True)

        # Filter out empty/garbage text
        if not text or len(text) < 50:
            print(f"[SCRAPER ERROR] Content too short -> {url}")
            return None

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

    print("[SCRAPER] DONE – All raw_sources saved.")


if __name__ == "__main__":
    main()

