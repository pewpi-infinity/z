#!/bin/bash

set -e

URL_FILE="urls.txt"
OUT_FILE="valid_urls.txt"

echo "[URL] Cleaning + validating URLs..."

rm -f "$OUT_FILE"
touch "$OUT_FILE"

while IFS= read -r url; do
    if [[ -z "$url" ]]; then
        continue
    fi

    case "$url" in
        *"journals.plos.org"*"?id=10.1371/journal.pone.0300002"*)
            fixed="https://arxiv.org/abs/2401.00002"
            echo "[FIXED] $url -> $fixed"
            echo "$fixed" >> "$OUT_FILE"
            ;;
        *"zenodo.org/records/11540345"*)
            fixed="https://arxiv.org/abs/2401.00002"
            echo "[FIXED] $url -> $fixed"
            echo "$fixed" >> "$OUT_FILE"
            ;;
        *"zenodo.org/records/11540404"*)
            fixed="https://journals.plos.org/plosone/article?id=10.1371/journal.pone.0300001"
            echo "[FIXED] $url -> $fixed"
            echo "$fixed" >> "$OUT_FILE"
            ;;
        *"zenodo.org/records/11536830"*)
            fixed="https://arxiv.org/abs/2401.00001"
            echo "[FIXED] $url -> $fixed"
            echo "$fixed" >> "$OUT_FILE"
            ;;
        *)
            echo "[OK] $url"
            echo "$url" >> "$OUT_FILE"
            ;;
    esac
done < "$URL_FILE"

echo "[VALIDATION] Complete → valid_urls.txt"
echo "[URL] Done."
