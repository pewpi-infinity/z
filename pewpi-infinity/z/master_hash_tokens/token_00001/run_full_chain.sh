#!/usr/bin/env bash

RAW_SCRAPER="scraper_raw_sources.py"
ZIP_BUILDER="zipcoin_builder.py"
CROSSLINK="crosslink_builder.py"

ZIPCOIN_DIR="pewpi-infinity/z/zipcoins"
MASTER_DIR="pewpi-infinity/z/master_hash_tokens"

echo "[CHAIN] Starting full research chain..."
echo "--------------------------------------------------"

# 1. SCRAPE RAW SOURCES
echo "[CHAIN] Running RAW scraper..."
python $RAW_SCRAPER
if [ $? -ne 0 ]; then
    echo "[ERROR] Raw scraper failed."
    exit 1
fi

# 2. BUILD ZIP COINS (HASH1, HASH2, HASH3)
echo "[CHAIN] Building zip_coins..."
python $ZIP_BUILDER
if [ $? -ne 0 ]; then
    echo "[ERROR] Zipcoin builder failed."
    exit 1
fi

# 3. BUILD CROSS‑LINK PAGES
echo "[CHAIN] Adding crosslinks + compiled articles..."
python $CROSSLINK
if [ $? -ne 0 ]; then
    echo "[ERROR] Crosslink builder failed."
    exit 1
fi

# 4. PACKAGE INTO MASTER HASH TOKEN
echo "[CHAIN] Packaging master hash token..."

mkdir -p "$MASTER_DIR"

COUNT=$(ls -1 $ZIPCOIN_DIR | wc -l)
MASTER_INDEX=$(ls -1 $MASTER_DIR | wc -l)
MASTER_INDEX=$((MASTER_INDEX + 1))

MASTER_FOLDER="$MASTER_DIR/token_$(printf "%05d" $MASTER_INDEX)"
mkdir -p "$MASTER_FOLDER"

echo "[CHAIN] Moving $COUNT zip_coins into $MASTER_FOLDER"

for folder in "$ZIPCOIN_DIR"/*; do
    mv "$folder" "$MASTER_FOLDER"/
done

# 5. CREATE MASTER HASH FILE
echo "[CHAIN] Creating master hash..."

HASH_FILE="$MASTER_FOLDER/master_hash.txt"
touch "$HASH_FILE"

for coin in "$MASTER_FOLDER"/*; do
    if [ -d "$coin" ]; then
        sha256sum "$coin"/compiled.txt >> "$HASH_FILE"
    fi
done

echo "[CHAIN] Master hash created: $HASH_FILE"

# 6. GIT COMMIT + PUSH
echo "[CHAIN] Committing to GitHub..."

git add pewpi-infinity/z
git commit -m "Auto: Added $COUNT zipcoins -> $MASTER_FOLDER"
git push origin main

echo "--------------------------------------------------"
echo "[CHAIN] Full chain completed and pushed to GitHub."
echo "--------------------------------------------------"

