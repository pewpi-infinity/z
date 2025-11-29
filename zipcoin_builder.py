#!/data/data/com.termux/files/usr/bin/python3
import os
import json
import hashlib

RAW_DIR = "pewpi-infinity/z/raw_sources"
ZIP_DIR = "pewpi-infinity/z/zipcoins"

os.makedirs(ZIP_DIR, exist_ok=True)

def sha(text):
    return hashlib.sha256(text.encode("utf-8", errors="ignore")).hexdigest()

def build_zipcoin(index, text):
    """Creates a structured zipcoin with:
       - id
       - color hash
       - metadata
       - article body
    """

    coin_id = f"zip_coin_{index:05d}"
    folder = os.path.join(ZIP_DIR, coin_id)
    os.makedirs(folder, exist_ok=True)

    # Color key based on deterministic hash of content
    color_code = sha(text)[:6]

    metadata = {
        "id": coin_id,
        "color": color_code,
        "source_length": len(text),
        "hash": sha(text)
    }

    # Save metadata
    with open(os.path.join(folder, "meta.json"), "w") as f:
        json.dump(metadata, f, indent=4)

    # Save raw original
    with open(os.path.join(folder, "original.txt"), "w", encoding="utf-8", errors="ignore") as f:
        f.write(text)

    # Build compiled article
    compiled = f"""
# ZIP COIN {index}

Color: #{color_code}

---

{text}
"""

    with open(os.path.join(folder, "compiled.txt"), "w", encoding="utf-8", errors="ignore") as f:
        f.write(compiled)

    print(f"[ZIPCOIN] Built {coin_id}")

def load_raw_sources():
    files = sorted(os.listdir(RAW_DIR))
    txts = []
    for fname in files:
        if fname.endswith(".txt"):
            path = os.path.join(RAW_DIR, fname)
            with open(path, "r", encoding="utf-8", errors="ignore") as f:
                txts.append(f.read())
    return txts

def main():
    print("[ZIPCOIN] Building zipcoins...")
    raw = load_raw_sources()

    for i, text in enumerate(raw, start=1):
        build_zipcoin(i, text)

    print("[ZIPCOIN] All zipcoins built → pewpi-infinity/z/zipcoins")

if __name__ == "__main__":
    main()
