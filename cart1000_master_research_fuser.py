#!/usr/bin/env python3
import os, hashlib, zipfile, requests, time, random

# ---- CONFIG ----
MASTER_DIR = "zipcoins"
MICRO_DIR = "zipcoins/micro"
MICRO_COUNT = 1000
TIMEOUT = 8

# REAL RESEARCH SOURCES ONLY
SOURCES = [
    "https://research.ibm.com/blog",
    "https://www.cs.princeton.edu/research",
    "https://www.cs.stanford.edu/research",
    "https://www.eecs.mit.edu/research/",
    "https://www.seas.harvard.edu/research",
    "https://www.nature.com/search?q=computing",
    "https://arxiv.org/list/cs.AI/recent",
    "https://www.sciencedaily.com/news/computers_math/artificial_intelligence/",
    "https://www.nist.gov/topics/artificial-intelligence",
    "https://www.nasa.gov/stem-content/",
]
# ---------------

def ensure_dirs():
    os.makedirs(MASTER_DIR, exist_ok=True)
    os.makedirs(MICRO_DIR, exist_ok=True)

def fetch(url):
    try:
        ua = random.choice([
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)",
            "Mozilla/5.0 (Linux; Android 10)",
        ])
        r = requests.get(url, timeout=TIMEOUT, headers={"User-Agent": ua})
        if r.status_code == 200:
            return r.text
        return None
    except:
        return None

def make_micro_zip(i, url, html):
    path = os.path.join(MICRO_DIR, f"micro_{i:04d}.zip")
    with zipfile.ZipFile(path, "w", zipfile.ZIP_DEFLATED) as zf:
        zf.writestr("source.txt", url)
        zf.writestr("page.html", html)
    return path

def main():
    ensure_dirs()
    micro_paths = []
    print("∞ Building micro-research packets… ∞")

    for i in range(1, MICRO_COUNT + 1):
        url = random.choice(SOURCES)
        html = fetch(url)

        if not html:
            print(f"[{i}/{MICRO_COUNT}] FAIL {url}")
            continue

        z = make_micro_zip(i, url, html)
        micro_paths.append(z)
        print(f"[{i}/{MICRO_COUNT}] OK  {url}")

    print("\n∞ Fusing 1000 micro-zips into master token… ∞")

    combined = "".join(open(p, "rb").read().hex() for p in micro_paths)
    sha = hashlib.sha256(combined.encode()).hexdigest()
    master_path = os.path.join(MASTER_DIR, f"{sha}.zip")

    with zipfile.ZipFile(master_path, "w", zipfile.ZIP_DEFLATED) as zf:
        for p in micro_paths:
            zf.write(p, arcname=os.path.basename(p))

    print("\n=== TOKEN READY ===")
    print("Master Hash:", sha)
    print("File:", master_path)
    print("===================")

if __name__ == "__main__":
    main()
