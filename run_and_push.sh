#!/usr/bin/env bash

SCRAPER="scraper_hash_tokens.py"
TARGET_DIR="pewpi-infinity/z/master_hash_tokens"

echo "[RUN] Working directory: $(pwd)"
echo "[RUN] Looking for: $SCRAPER"
ls

if [ ! -f "$SCRAPER" ]; then
  echo "[ERROR] Can't find $SCRAPER in $(pwd)"
  exit 1
fi

echo "[RUN] Starting research hash scraper..."
python "$SCRAPER"

STATUS=$?
if [ $STATUS -ne 0 ]; then
  echo "[ERROR] Python exited with status $STATUS"
  exit $STATUS
fi

echo "[RUN] Scraper complete. Checking master hash count in: $TARGET_DIR"

if [ ! -d "$TARGET_DIR" ]; then
  echo "[ERROR] Target dir $TARGET_DIR does not exist."
  exit 1
fi

COUNT=$(ls -1 "$TARGET_DIR" | grep '^token_' | wc -l)

echo "[RUN] Found $COUNT master hash token folders."

if [ "$COUNT" -ge 1000 ]; then
  echo "[RUN] 1000+ master hash tokens detected. Triggering Git push..."

  git add pewpi-infinity/z
  git commit -m "Added batch of 1000 master hash tokens"
  git push origin main

  echo "[RUN] Push complete."
else
  echo "[RUN] Only $COUNT master tokens found. Skipping Git push for now."
fi
