#!/usr/bin/env python3
import os
import json

ROOT = os.path.dirname(os.path.abspath(__file__))

TOKEN_DIR = os.path.join(ROOT, "infinity_tokens")
TOKENS_DIR = os.path.join(ROOT, "tokens")  # Add regular tokens dir
RAD_DIR = os.path.join(ROOT, "radionics_reader")
OUTFILE = os.path.join(ROOT, "research_index.json")

records = []

color_to_role = {
    "green": "engineering",
    "orange": "ceo",
    "blue": "import",
    "pink": "investigate",
    "red": "routes",
    "yellow": "data",
    "purple": "assimilation",
}

# Index infinity_tokens/*.json
if os.path.isdir(TOKEN_DIR):
    for fname in os.listdir(TOKEN_DIR):
        if not fname.endswith(".json"):
            continue
        full = os.path.join(TOKEN_DIR, fname)
        try:
            with open(full, "r", encoding="utf-8") as f:
                data = json.load(f)
        except Exception:
            data = {}

        hash_from_name = os.path.splitext(fname)[0]
        token_hash = data.get("hash") or hash_from_name

        color = (data.get("color")
                 or data.get("channel_color")
                 or data.get("lane_color")
                 or "").lower()

        role = data.get("role") or color_to_role.get(color, "data")

        title = (data.get("title")
                 or data.get("label")
                 or data.get("name")
                 or f"Token {token_hash[:8]}…")

        src = data.get("source_url") or data.get("url") or ""
        ts = data.get("timestamp") or data.get("ts") or ""
        notes = data.get("notes") or ""
        value = data.get("value", 0)

        records.append({
            "hash": token_hash,
            "role": role,
            "title": title,
            "url": f"infinity_tokens/{fname}",
            "source_url": src,
            "timestamp": ts,
            "notes": notes,
            "value": value
        })

# Index tokens/*.json (regular token directory)
if os.path.isdir(TOKENS_DIR):
    for fname in os.listdir(TOKENS_DIR):
        if not fname.endswith(".json"):
            continue
        full = os.path.join(TOKENS_DIR, fname)
        try:
            with open(full, "r", encoding="utf-8") as f:
                data = json.load(f)
        except Exception:
            data = {}

        hash_from_name = os.path.splitext(fname)[0]
        if hash_from_name.startswith("MEGA_"):
            hash_from_name = hash_from_name[5:]  # Remove MEGA_ prefix
            
        token_hash = data.get("hash") or data.get("mega_hash") or hash_from_name

        # Determine role based on content or default
        role = data.get("role", "data")

        # Try to extract title from raw_text or research field
        raw_text = data.get("raw_text", "")
        research = data.get("research", "")
        
        title = data.get("title", "")
        if not title:
            # Try to extract first line or first few words
            content = raw_text or research
            if content:
                first_line = content.split('\n')[0][:60]
                title = first_line if first_line else f"Token {token_hash[:8]}…"
            else:
                title = f"Token {token_hash[:8]}…"

        src = data.get("source_url") or ""
        ts = data.get("timestamp") or ""
        notes = data.get("notes") or ""
        value = data.get("value", 0)

        records.append({
            "hash": token_hash,
            "role": role,
            "title": title,
            "url": f"tokens/{fname}",
            "source_url": src,
            "timestamp": ts,
            "notes": notes,
            "value": value
        })

# Index radionics_reader/*.txt as Data role
if os.path.isdir(RAD_DIR):
    for fname in os.listdir(RAD_DIR):
        if not (fname.endswith(".txt") or fname.endswith(".md")):
            continue

        hash_from_name = os.path.splitext(fname)[0]

        records.append({
            "hash": hash_from_name,
            "role": "data",
            "title": f"Radionics capture {hash_from_name[:8]}…",
            "url": f"radionics_reader/{fname}",
            "source_url": "",
            "timestamp": "",
            "notes": "",
            "value": 0
        })

# Optional: sort by timestamp if present, else by hash
def sort_key(r):
    ts = r.get("timestamp") or ""
    return (ts, r.get("hash") or "")

records.sort(key=sort_key, reverse=True)  # Most recent first

with open(OUTFILE, "w", encoding="utf-8") as f:
    json.dump(records, f, indent=2)

print(f"Wrote {len(records)} records to research_index.json")
