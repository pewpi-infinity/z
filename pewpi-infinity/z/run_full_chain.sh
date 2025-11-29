#!/usr/bin/env bash

set -e

echo "--------------------------------------------------"
echo "[CHAIN] Starting FULL Infinity Chain (Cart V2)..."
echo "--------------------------------------------------"

# enforce working directory
cd "$(dirname "$0")"

###############################################
# 1. CLEAN OLD OUTPUTS
###############################################
echo "[CHAIN] Cleaning old outputs..."

rm -rf pewpi-infinity/z/raw_sources/*
rm -rf pewpi-infinity/z/zipcoins/*
rm -rf pewpi-infinity/z/master_hash_tokens/*

mkdir -p pewpi-infinity/z/raw_sources
mkdir -p pewpi-infinity/z/zipcoins
mkdir -p pewpi-infinity/z/master_hash_tokens

echo "[CHAIN] Clean complete."

###############################################
# 2. VALIDATE URLS
###############################################
echo "[CHAIN] Validating URLs..."
python3 url_clean_v2.py
echo "[CHAIN] URL validation complete."

###############################################
# 3. SCRAPE RESEARCH PAPERS
###############################################
echo "[CHAIN] Scraping raw_sources..."
python3 scraper_raw_sources_v2.py
echo "[CHAIN] Scraping done."

###############################################
# 4. BUILD ZIPCOINS
###############################################
echo "[CHAIN] Building zipcoins..."
python3 zipcoin_builder_v2.py
echo "[CHAIN] Zipcoins built."

###############################################
# 5. BUILD CROSS‑LINKS
###############################################
echo "[CHAIN] Building crosslinks..."
python3 crosslink_builder_v2.py
echo "[CHAIN] Crosslinks complete."

###############################################
# 6. BUILD MASTER HASH TOKEN (1000-cap structure)
###############################################
echo "[CHAIN] Building master hash token..."
python3 master_hash_builder_v2.py
echo "[CHAIN] Master hash built."

###############################################
# 7. GIT PUSH
###############################################
echo "[CHAIN] Pushing to GitHub…"

git add .
git commit -m "Auto: Full Chain V2"
git push origin master

echo "--------------------------------------------------"
echo "[CHAIN] FULL CHAIN COMPLETED AND PUSHED"
echo "--------------------------------------------------"

