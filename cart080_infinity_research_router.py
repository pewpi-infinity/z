#!/usr/bin/env python3
import os, hashlib, json, datetime, pathlib

REPO_DIR = os.path.expanduser("~/z")
TOKENS_DIR = os.path.join(REPO_DIR, "tokens")

os.makedirs(TOKENS_DIR, exist_ok=True)

SESSION_BUFFER = os.path.join(REPO_DIR, "session_buffer.json")

def load_buffer():
    if os.path.exists(SESSION_BUFFER):
        with open(SESSION_BUFFER, 'r') as f:
            return json.load(f)
    return {"pending": []}

def save_buffer(buf):
    with open(SESSION_BUFFER, 'w') as f:
        json.dump(buf, f, indent=4)

def create_token(text):
    h = hashlib.sha256(text.encode()).hexdigest()
    ts = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    token_obj = {
        "hash": h,
        "timestamp": ts,
        "raw_text": text
    }

    # Store raw token data for Cart 081 + 082
    filepath = os.path.join(TOKENS_DIR, f"{h}.json")
    with open(filepath, 'w') as f:
        json.dump(token_obj, f, indent=4)

    return token_obj

def main():
    print("∞ Infinity Research Router Online (Cart 080)")
    print("Paste content below. End input with a blank line:\n")

    lines=[]
    while True:
        try:
            l=input()
            if not l.strip():
                break
            lines.append(l)
        except EOFError:
            break

    text="\n".join(lines).strip()
    if not text:
        print("No input provided. Exiting.")
        return

    token_obj = create_token(text)

    buf = load_buffer()
    buf["pending"].append(token_obj["hash"])
    save_buffer(buf)

    print("\n[∞] Token created:", token_obj["hash"])
    print("[∞] Added to session buffer for valuation (Cart 081 + 082).")
    print("[∞] Raw token JSON saved to repo.\n")

if __name__ == "__main__":
    main()
