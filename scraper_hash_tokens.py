import os
import math
import time
import hashlib
from pathlib import Path
import requests
from bs4 import BeautifulSoup

URLS_FILE = "urls.txt"
OUTPUT_ROOT = Path("pewpi-infinity/z") / "master_hash_tokens"
TOKENS_PER_ZIP = 1000
ZIP_COINS_PER_MASTER = 1000
REQUEST_TIMEOUT = 15
SLEEP_BETWEEN_REQUESTS = 1

def fetch_html(url):
    headers = {"User-Agent": "ResearchHashScraper/2.0"}
    resp = requests.get(url, headers=headers, timeout=REQUEST_TIMEOUT)
    resp.raise_for_status()
    return resp.text

def extract_text(html):
    soup = BeautifulSoup(html, "html.parser")
    for tag in soup(["script", "style", "noscript"]): 
        tag.extract()
    text = soup.get_text(" ")
    return " ".join(t.strip() for t in text.split())

def rewrite_research_tokens(text):
    words = text.split()
    return [w.lower() for w in words]

def chunk(tokens, size):
    for i in range(0, len(tokens), size):
        yield tokens[i:i+size]

def write_zip_coin(folder, index, tokens):
    (folder / f"zip_coin_{index:05d}.txt").write_text(" ".join(tokens))

def write_master_hash_token(master_index, zip_groups):
    master_folder = OUTPUT_ROOT / f"token_{master_index:05d}"
    master_folder.mkdir(parents=True, exist_ok=True)

    sha = hashlib.sha256()
    for i, zip_tokens in enumerate(zip_groups, 1):
        write_zip_coin(master_folder, i, zip_tokens)
        sha.update(" ".join(zip_tokens).encode())

    (master_folder / "hash.txt").write_text(sha.hexdigest())

def load_urls():
    if not os.path.exists(URLS_FILE):
        raise FileNotFoundError(f"{URLS_FILE} missing.")
    return [u.strip() for u in open(URLS_FILE) if u.strip()]

def main():
    urls = load_urls()
    all_tokens = []

    for idx, url in enumerate(urls, 1):
        try:
            html = fetch_html(url)
            text = extract_text(html)
            tokens = rewrite_research_tokens(text)
            all_tokens.extend(tokens)
            time.sleep(SLEEP_BETWEEN_REQUESTS)
        except Exception as e:
            print("ERROR:", e)

    zip_coins = list(chunk(all_tokens, TOKENS_PER_ZIP))
    master_count = math.ceil(len(zip_coins) / ZIP_COINS_PER_MASTER)

    for i in range(master_count):
        group = zip_coins[i*ZIP_COINS_PER_MASTER:(i+1)*ZIP_COINS_PER_MASTER]
        write_master_hash_token(i+1, group)

    print("Done — master hash tokens saved to pewpi-infinity/z/master_hash_tokens/")
    
if __name__ == "__main__":
    main()
