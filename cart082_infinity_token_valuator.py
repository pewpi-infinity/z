#!/usr/bin/env python3
import os, json, hashlib, datetime, math, re

REPO_DIR = os.path.expanduser("~/z")
TOKENS_DIR = os.path.join(REPO_DIR, "tokens")
BUFFER = os.path.join(REPO_DIR, "session_buffer.json")

BOOST_KEYWORDS = [
    "hydrogen","quantum","plasma","electron","vector","tensor",
    "relativity","einstein","gravity","photon","ai","neural",
    "fusion","reactor","lattice","kris","infinity","hydra","osprey"
]

def score_text(text):
    # Cache length and lowercase conversion to avoid redundant operations
    text_len = len(text)
    text_lower = text.lower()
    base = text_len

    # keyword bonuses - compute text_lower once
    boost = 0
    for k in BOOST_KEYWORDS:
        boost += text_lower.count(k) * 50

    # exponential tail for long depth - use cached length
    depth = int(math.log(max(1, text_len), 3) * 40)

    return base + boost + depth

def scale_value(score):
    if score < 200:
        return f"${80 + score // 4}"
    if score < 800:
        return f"${400 + score}"
    if score < 3000:
        return f"${1200 + score*3}"
    return f"${50000 + score*12}"

def valuate_token(tpath):
    # Use context manager to properly close file handles
    with open(tpath, 'r') as f:
        obj = json.load(f)
    text = obj["raw_text"]

    s = score_text(text)
    v = scale_value(s)

    obj["value"] = v
    obj["score"] = s

    with open(tpath, 'w') as f:
        json.dump(obj, f, indent=4)

    return obj["hash"], v

def main():
    if not os.path.exists(BUFFER):
        print("[!] No buffer found.")
        return

    with open(BUFFER, 'r') as f:
        buf = json.load(f)
    pending = buf.get("pending", [])

    if not pending:
        print("[!] No tokens waiting.")
        return

    print("∞ Valuating pending Infinity tokens...\n")

    for h in pending:
        path = os.path.join(TOKENS_DIR, f"{h}.json")
        if not os.path.exists(path):
            continue
        thash, val = valuate_token(path)
        print(f"[∞] {thash} → {val}")

    # clear buffer
    buf["pending"]=[]
    with open(BUFFER, 'w') as f:
        json.dump(buf, f, indent=4)

    print("\n[∞] Valuation complete. All tokens updated in repo.")

if __name__ == "__main__":
    main()
