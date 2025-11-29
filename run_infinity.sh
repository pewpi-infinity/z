#!/bin/bash
set -euo pipefail

# =========[ COLORS ]=========
RED="\033[31m"
GREEN="\033[32m"
YELLOW="\033[33m"
BLUE="\033[34m"
MAGENTA="\033[35m"
CYAN="\033[36m"
BOLD="\033[1m"
NC="\033[0m"

# =========[ PATHS ]=========
ROOT="$HOME/z"
URL_FILE="$ROOT/urls.txt"
VALID_FILE="$ROOT/valid_urls.txt"
RAW_DIR="$ROOT/raw_sources"
ZIP_DIR="$ROOT/zipcoins"
TOKENS_DIR="$ROOT/master_hash_tokens"

echo -e "--------------------------------------------------"
echo -e " ${BOLD}${CYAN}[RESET] Fresh Infinity chain...${NC}"
echo -e "--------------------------------------------------"

rm -rf "$RAW_DIR" "$ZIP_DIR" "$VALID_FILE"
mkdir -p "$RAW_DIR" "$ZIP_DIR" "$TOKENS_DIR"

echo -e "${GREEN}RESET COMPLETE.${NC}"

# =========[ STEP 1: URL CLEAN + VALIDATE ]=========
echo -e "--------------------------------------------------"
echo -e " ${BOLD}${BLUE}[STEP 1] Cleaning + validating URLs...${NC}"
echo -e "--------------------------------------------------"

if [[ ! -f "$URL_FILE" ]]; then
  echo -e "${RED}[ERROR] urls.txt not found at $URL_FILE${NC}"
  exit 1
fi

rm -f "$VALID_FILE"
touch "$VALID_FILE"

while IFS= read -r url; do
  [[ -z "$url" ]] && continue

  case "$url" in
    *"journals.plos.org"*"?id=10.1371/journal.pone.0300002"*)
      fixed="https://arxiv.org/abs/2401.00002"
      echo -e "${YELLOW}[FIXED]${NC} $url -> $fixed"
      echo "$fixed" >> "$VALID_FILE"
      ;;
    *"zenodo.org/records/11540345"*)
      fixed="https://arxiv.org/abs/2401.00002"
      echo -e "${YELLOW}[FIXED]${NC} $url -> $fixed"
      echo "$fixed" >> "$VALID_FILE"
      ;;
    *"zenodo.org/records/11540404"*)
      fixed="https://journals.plos.org/plosone/article?id=10.1371/journal.pone.0300001"
      echo -e "${YELLOW}[FIXED]${NC} $url -> $fixed"
      echo "$fixed" >> "$VALID_FILE"
      ;;
    *"zenodo.org/records/11536830"*)
      fixed="https://arxiv.org/abs/2401.00001"
      echo -e "${YELLOW}[FIXED]${NC} $url -> $fixed"
      echo "$fixed" >> "$VALID_FILE"
      ;;
    *)
      echo -e "${GREEN}[OK]${NC} $url"
      echo "$url" >> "$VALID_FILE"
      ;;
  esac
done < "$URL_FILE"

echo -e "${GREEN}[URL CLEAN] Complete → $VALID_FILE${NC}"

# =========[ STEP 2: SCRAPE FULL RESEARCH PAGES ]=========
echo -e "--------------------------------------------------"
echo -e " ${BOLD}${BLUE}[STEP 2] Scraping research pages...${NC}"
echo -e "--------------------------------------------------"

i=1
while IFS= read -r u; do
  [[ -z "$u" ]] && continue
  fname=$(printf "raw_%05d.txt" "$i")
  out="$RAW_DIR/$fname"

  echo -e "${CYAN}[SCRAPER] Fetching:${NC} $u"
  curl -L -s "$u" -o "$out" || {
    echo -e "${RED}[SCRAPER ERROR] Failed:${NC} $u"
    rm -f "$out"
    continue
  }

  if [[ ! -s "$out" ]]; then
    echo -e "${RED}[SCRAPER ERROR] Empty response:${NC} $u"
    rm -f "$out"
  else
    echo -e "${GREEN}[SCRAPER] Saved${NC} $(basename "$out")"
    ((i++))
  fi
done < "$VALID_FILE"

echo -e "${GREEN}[SCRAPER] DONE – raw sources in $RAW_DIR${NC}"

# =========[ STEP 3: BUILD ZIPCOINS (TEXT + HTML + META) ]=========
echo -e "--------------------------------------------------"
echo -e " ${BOLD}${BLUE}[STEP 3] Building zipcoins...${NC}"
echo -e "--------------------------------------------------"

count=1
for f in "$RAW_DIR"/raw_*.txt; do
  [[ ! -f "$f" ]] && continue

  coin=$(printf "zip_coin_%05d" "$count")
  out="$ZIP_DIR/$coin"
  mkdir -p "$out"

  raw="$(cat "$f")"
  comp="$(echo "$raw" | tr '\n' ' ' | sed 's/  */ /g' | cut -c1-4000)"

  echo "$raw"  > "$out/original.txt"
  echo "$comp" > "$out/compiled.txt"

  # Simple colored research view in HTML (whole block styled)
  cat > "$out/compiled.html" <<HTML
<!doctype html>
<html>
<head>
  <meta charset="utf-8" />
  <title>$coin – Infinity Research</title>
  <style>
    body { font-family: system-ui, sans-serif; background:#050816; color:#f8f9fa; padding:24px; }
    h1 { color:#74c0fc; }
    .hash { color:#ffd43b; font-family: monospace; }
    pre { white-space: pre-wrap; word-wrap: break-word; background:#111827; padding:16px; border-radius:8px; }
    .badge { display:inline-block; padding:4px 8px; border-radius:999px; background:#1e293b; font-size:12px; margin-right:8px;}
  </style>
</head>
<body>
  <h1>$coin</h1>
  <div>
    <span class="badge">Infinity Research Zipcoin</span>
  </div>
  <h2>Compiled Research Snippet</h2>
  <pre>$comp</pre>
</body>
</html>
HTML

  # Meta for crosslink/cross‑tools
  cat > "$out/meta.json" <<META
{
  "coin_id": "$coin",
  "raw_file": "$(basename "$f")",
  "raw_path": "$f"
}
META

  echo -e "${MAGENTA}[ZIPCOIN] Built${NC} $coin"
  ((count++))
done

echo -e "${GREEN}[ZIPCOIN] DONE – coins in $ZIP_DIR${NC}"

# =========[ STEP 4: CROSSLINK HTML (Prev/Next) ]=========
echo -e "--------------------------------------------------"
echo -e " ${BOLD}${BLUE}[STEP 4] Adding cross‑links...${NC}"
echo -e "--------------------------------------------------"

mapfile -t coins < <(printf "%s\n" "$ZIP_DIR"/zip_coin_* | sort)
total=${#coins[@]}

if (( total > 0 )); then
  for ((idx=0; idx<total; idx++)); do
    coin_dir="${coins[$idx]}"
    coin_name=$(basename "$coin_dir")
    prev_idx=$(( (idx - 1 + total) % total ))
    next_idx=$(( (idx + 1) % total ))
    prev_name=$(basename "${coins[$prev_idx]}")
    next_name=$(basename "${coins[$next_idx]}")

    nav="<div style='margin-top:16px'>
  <a href='../$prev_name/compiled.html' style='color:#74c0fc'>⟵ Prev ($prev_name)</a> |
  <a href='../$next_name/compiled.html' style='color:#74c0fc'>Next ($next_name) ⟶</a>
</div></body>"

    sed -i "s#</body>#$nav#g" "$coin_dir/compiled.html"

    echo -e "${CYAN}[CROSSLINK]${NC} $coin_name ←→ prev:$prev_name next:$next_name"
  done
else
  echo -e "${YELLOW}[CROSSLINK] No zipcoins found, skipping.${NC}"
fi

echo -e "${GREEN}[CROSSLINK] DONE.${NC}"

# =========[ STEP 5: MASTER HASH TOKEN ]=========
echo -e "--------------------------------------------------"
echo -e " ${BOLD}${BLUE}[STEP 5] Building master hash token...${NC}"
echo -e "--------------------------------------------------"

existing_count=$(ls -1 "$TOKENS_DIR" 2>/dev/null | grep -E '^token_' | wc -l || true)
next_num=$((existing_count + 1))
token_name=$(printf "token_%05d" "$next_num")
token_dir="$TOKENS_DIR/$token_name"
mkdir -p "$token_dir"

hash_file="$token_dir/master_hash.txt"

if comp_files=$(find "$ZIP_DIR" -maxdepth 2 -type f -name "compiled.txt" | sort); then
  if [[ -n "$comp_files" ]]; then
    echo "$comp_files" | xargs sha256sum > "$hash_file"
    echo -e "${GREEN}[MASTER] Hash file created →${NC} $hash_file"
  else
    echo -e "${YELLOW}[MASTER] No compiled.txt files to hash.${NC}"
  fi
else
  echo -e "${YELLOW}[MASTER] No zipcoins to hash.${NC}"
fi

echo -e " ${BOLD}${MAGENTA}Master Token:${NC} $token_name"

# =========[ STEP 6: GIT PUSH ]=========
echo -e "--------------------------------------------------"
echo -e " ${BOLD}${BLUE}[STEP 6] Git commit + push...${NC}"
echo -e "--------------------------------------------------"

if git -C "$ROOT" rev-parse --is-inside-work-tree >/dev/null 2>&1; then
  cd "$ROOT"
  git add .
  TS=$(date +"%Y-%m-%d %H:%M:%S")
  git commit -m "Auto Infinity Chain – $TS" >/dev/null 2>&1 || echo -e "${YELLOW}[GIT] Nothing to commit.${NC}"
  git push || echo -e "${YELLOW}[GIT] Push failed (check remote).${NC}"
  echo -e "${GREEN}[GIT] Step finished.${NC}"
else
  echo -e "${YELLOW}[GIT] Not in a git repo, skipping push.${NC}"
fi

echo -e "--------------------------------------------------"
echo -e " ${BOLD}${GREEN}[DONE] Infinity chain complete.${NC}"
echo -e "--------------------------------------------------"
