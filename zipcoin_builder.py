#!/data/data/com.termux/files/usr/bin/python3
import os
import json

# Where the raw scraped text lives
RAW_DIR = "pewpi-infinity/z/raw_sources"

# Where we write zipcoins
ZIP_DIR = "pewpi-infinity/z/zipcoins"

os.makedirs(ZIP_DIR, exist_ok=True)


def load_raw_files():
    """Return list of (path, text) for all raw_XXXXX.txt files."""
    files = []
    if not os.path.isdir(RAW_DIR):
        print(f"[ZIPCOIN ERROR] RAW_DIR missing: {RAW_DIR}")
        return files

    for name in sorted(os.listdir(RAW_DIR)):
        if not name.startswith("raw_") or not name.endswith(".txt"):
            continue
        path = os.path.join(RAW_DIR, name)
        try:
            with open(path, "r", encoding="utf-8", errors="ignore") as f:
                text = f.read().strip()
        except Exception as e:
            print(f"[ZIPCOIN ERROR] Could not read {path}: {e}")
            continue

        if not text:
            print(f"[ZIPCOIN WARNING] Empty raw file: {path}")
            continue

        files.append((path, text))
    return files


def simple_compile(text: str) -> str:
    """
    Very simple 'compiled' version of the text.
    For now we just normalize whitespace and truncate to a sane length.
    You can replace this with something fancier later.
    """
    text = " ".join(text.split())
    # keep first ~4000 chars so files don't explode
    return text[:4000]


def build_zipcoin(index: int, raw_path: str, text: str):
    """Build a single zipcoin folder with original + compiled text + meta."""
    coin_name = f"zip_coin_{index:05d}"
    out_dir = os.path.join(ZIP_DIR, coin_name)
    os.makedirs(out_dir, exist_ok=True)

    compiled_text = simple_compile(text)

    # Very basic HTML wrapper
    html = (
        "<html><head><meta charset='utf-8'>"
        f"<title>{coin_name}</title></head><body><pre>"
        f"{compiled_text}"
        "</pre></body></html>"
    )

    # Save original text
    with open(os.path.join(out_dir, "original.txt"), "w",
              encoding="utf-8", errors="ignore") as f:
        f.write(text)

    # Save compiled text
    with open(os.path.join(out_dir, "compiled.txt"), "w",
              encoding="utf-8", errors="ignore") as f:
        f.write(compiled_text)

    # Save compiled HTML
    with open(os.path.join(out_dir, "compiled.html"), "w",
              encoding="utf-8", errors="ignore") as f:
        f.write(html)

    # Save meta
    meta = {
        "coin_id": coin_name,
        "raw_file": os.path.basename(raw_path),
        "raw_path": raw_path,
    }
    with open(os.path.join(out_dir, "meta.json"), "w",
              encoding="utf-8", errors="ignore") as f:
        json.dump(meta, f, indent=2)

    print(f"[ZIPCOIN] Built {coin_name}")


def main():
    print("[ZIPCOIN] Building zipcoins...")
    raw_files = load_raw_files()

    if not raw_files:
        print("[ZIPCOIN] No raw sources found. Nothing to do.")
        return

    for idx, (path, text) in enumerate(raw_files, start=1):
        build_zipcoin(idx, path, text)

    print(f"[ZIPCOIN] All zipcoins built → {ZIP_DIR}")


if __name__ == "__main__":
    main()

