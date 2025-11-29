#!/data/data/com.termux/files/usr/bin/bash
echo "[URL] Cleaning + validating URLs..."
python3 arxiv_resolver.py
echo "[URL] Done. Output → valid_urls.txt"
