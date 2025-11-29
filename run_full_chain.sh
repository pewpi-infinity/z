#!/data/data/com.termux/files/usr/bin/bash

echo "--------------------------------------------------"
echo "[CHAIN] Starting FULL Infinity Chain..."
echo "--------------------------------------------------"

############################################
# STEP 1 — Validate URLs
############################################
echo "[CHAIN] Validating URLs..."
python3 arxiv_resolver.py
if [ $? -ne 0 ]; then
    echo "[ERROR] URL resolver failed."
    exit 1
fi

############################################
# STEP 2 — Scrape raw_sources
############################################
echo "[CHAIN] Scraping research papers..."
python3 scraper_raw_sources.py
if [ $? -ne 0 ]; then
    echo "[ERROR] Raw-source scraper failed."
    exit 1
fi

############################################
# STEP 3 — Build zipcoins
############################################
echo "[CHAIN] Building zipcoins..."
python3 zipcoin_builder.py
if [ $? -ne 0 ]; then
    echo "[ERROR] Zipcoin builder failed."
    exit 1
fi

############################################
# STEP 4 — Build crosslinks + HTML
############################################
echo "[CHAIN] Building cross‑links..."
python3 crosslink_builder.py
if [ $? -ne 0 ]; then
    echo "[ERROR] Crosslink builder failed."
    exit 1
fi

############################################
# STEP 5 — Build master hash token
############################################
TOKEN_DIR="pewpi-infinity/z/master_hash_tokens"
ZIP_DIR="pewpi-infinity/z/zipcoins"

mkdir -p "$TOKEN_DIR"

# Next master token number
NEXT=$(printf "token_%05d" $(( $(ls -1 "$TOKEN_DIR" | wc -l) + 1 )))
TARGET="$TOKEN_DIR/$NEXT"

echo "[CHAIN] Packaging master hash token at $TARGET"
mkdir -p "$TARGET"

# Copy zipcoin folders into master token
cp -r "$ZIP_DIR"/* "$TARGET"/

############################################
# Create master_hash.txt inside token folder
############################################
echo "[CHAIN] Creating master hash..."

(
    cd "$TARGET"
    # Hash every compiled.txt file properly
    for file in */compiled.txt; do
        sha256sum "$file" >> master_hash.txt
    done
)

echo "[CHAIN] Master hash created."

############################################
# STEP 6 — Commit + push to GitHub
############################################
echo "[CHAIN] Committing to GitHub..."

git add .
git commit -m "Auto: Added new token $NEXT"
git push origin master

echo "--------------------------------------------------"
echo "[CHAIN] Full chain completed and pushed to GitHub."
echo "--------------------------------------------------"

