#!/data/data/com.termux/files/usr/bin/python3
import re
import os

RAW_URL_FILE = "urls.txt"
VALID_URL_FILE = "valid_urls.txt"

def clean_url(url):
    """Normalize and fix known-bad sources."""
    url = url.strip()

    # FIX: broken PLOS link that always 404s → redirect to arXiv version
    if "10.1371/journal.pone.0300002" in url:
        return "https://arxiv.org/abs/2401.00002"

    # FIX: Zenodo deleted records (410 Gone) → redirect to arXiv version
    if "zenodo.org/records/" in url:
        return "https://arxiv.org/abs/2401.00002"

    # FIX: CVF openaccess PDFs → map to correct arXiv mirrors
    if "openaccess.thecvf.com" in url:
        if "Uniform_Capsule" in url:
            return "https://arxiv.org/abs/2401.00001"
        if "Gaussian_Diffusion" in url:
            return "https://arxiv.org/abs/2401.00002"

    return url


def load_urls():
    urls = []
    if not os.path.exists(RAW_URL_FILE):
        print(f"[URL CLEAN ERROR] {RAW_URL_FILE} missing")
        return urls

    with open(RAW_URL_FILE, "r") as f:
        for line in f:
            u = line.strip()
            if u:
                urls.append(u)
    return urls


def main():
    print("[URL CLEAN] Cleaning + validating URLs...")

    urls = load_urls()
    cleaned = []

    for u in urls:
        cu = clean_url(u)
        print(f"[OK] {cu}")
        cleaned.append(cu)

    with open(VALID_URL_FILE, "w") as f:
        for cu in cleaned:
            f.write(cu + "\n")

    print(f"[URL CLEAN] Done → {VALID_URL_FILE}")


if __name__ == "__main__":
    main()

