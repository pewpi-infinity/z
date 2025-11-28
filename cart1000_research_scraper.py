#!/usr/bin/env python3
import os, hashlib, zipfile, random, time, json

try:
    import requests
    from bs4 import BeautifulSoup
except:
    print("Run: pip install requests beautifulsoup4")
    raise SystemExit(1)

SAVE_DIR = "zipcoins"
MAX_PAGES = 1000
TIMEOUT = 10

# Wikipedia blocks default Python requests
USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
    "Mozilla/5.0 (Linux; Android 10)",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)",
    "Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:109.0)"
]

HEADERS = lambda: {
    "User-Agent": random.choice(USER_AGENTS),
    "Accept": "text/html",
}

SEED_SOURCES = [
    "https://www.gnu.org/philosophy/free-sw.html",
    "https://www.linuxfoundation.org/",
    "https://www.python.org/doc/essays/",
    "https://www.ibm.com/think/topics/artificial-intelligence",
    "https://www.microsoft.com/en-us/research/articles/",
    "https://www.sciencedaily.com/news/computers_math/artificial_intelligence/",
]

def ensure_dirs():
    os.makedirs(SAVE_DIR, exist_ok=True)

def fetch(url):
    try:
        print(f"[FETCH] {url}")
        r = requests.get(url, headers=HEADERS(), timeout=TIMEOUT)
        if r.status_code != 200:
            print(f"[STATUS {r.status_code}] retrying with new User-Agent")
            r = requests.get(url, headers=HEADERS(), timeout=TIMEOUT)
        if r.status_code == 200:
            return r.text
        print(f"[ERR] {url} -> status {r.status_code}")
        return None
    except Exception as e:
        print(f"[ERR] {url} -> {e}")
        return None

def get_links(html):
    soup = BeautifulSoup(html, "html.parser")
    links = []
    for a in soup.find_all("a", href=True):
        href = a["href"]
        if href.startswith("http"):
            links.append(href)
    random.shuffle(links)
    return links[:15]

def scrape():
    pages = []
    seen = set()
    queue = list(SEED_SOURCES)

    while len(pages) < MAX_PAGES and queue:
        url = queue.pop(0)
        if url in seen: 
            continue
        seen.add(url)

        html = fetch(url)
        if not html:
            continue

        pages.append((url, html))
        print(f"[OK] {len(pages)}/{MAX_PAGES}")

        for l in get_links(html):
            if l not in seen:
                queue.append(l)

    return pages

def build_zip(pages):
    joined = "".join([html for (_, html) in pages])
    sha = hashlib.sha256(joined.encode("utf-8")).hexdigest()
    token_id = sha

    zip_path = os.path.join(SAVE_DIR, f"{token_id}.zip")

    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
        for i, (url, html) in enumerate(pages, start=1):
            zf.writestr(f"page_{i:04d}.html", html)

        manifest = {
            "token_id": token_id,
            "created_at": int(time.time()),
            "count": len(pages)
        }
        zf.writestr("manifest.json", json.dumps(manifest, indent=2))

    return token_id, zip_path

def main():
    ensure_dirs()
    print("∞ Infinity 403-Bypass Scraper Online ∞")

    pages = scrape()
    if not pages:
        print("[!] No pages scraped. Aborting.")
        return

    token, path = build_zip(pages)

    print("\n=== TOKEN READY ===")
    print("Token:", token)
    print("Saved:", path)
    print("====================")

if __name__ == "__main__":
    main()
