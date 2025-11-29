#!/data/data/com.termux/files/usr/bin/bash

echo "--------------------------------------------------"
echo "[CHAIN] Starting FULL Infinity Chain..."
echo "--------------------------------------------------"

# STEP 1 — Validate URLs
echo "[CHAIN] Validating URLs..."
python3 arxiv_resolver.py

# STEP 2 — Scrape fresh raw_sources
echo "[CHAIN] Scraping research papers..."
python3 scraper_raw_sources.py

# STEP 3 — Build zipcoins
echo "[CHAIN] Building zipcoins..."
python3 zipcoin_builder.py

# STEP 4 — Build crosslinks + HTML
echo "[CHAIN] Building cross‑links..."
python3 crosslink_builder.py

# STEP 5 — Master hash
TOKEN_DIR="pewpi-infinity/z/master_hash_tokens"
mkdir -p "$TOKEN_DIR"

NEXT=$(printf "token_%05d" $(($(ls "$TOKEN_DIR" | wc -l) + 1)))
TARGET="$TOKEN_DIR/$NEXT"

mkdir -p "$TARGET"

echo "[CHAIN] Packaging master hash token at $TARGET"
cp -r pewpi-infinity/z/zipcoins/* "$TARGET"/

# Generate master hash
(
    cd "$TARGET"
    echo "[CHAIN] Creating master hash..."
    sha256sum * > master_hash.txt
)

# STEP 6 — Commit + push to GitHub
echo "[CHAIN] Committing to GitHub..."
git add .
git commit -m "Auto: Added new token $NEXT"
git push origin master

echo "--------------------------------------------------"
echo "[CHAIN] Full chain completed and pushed to GitHub."
echo "--------------------------------------------------"
