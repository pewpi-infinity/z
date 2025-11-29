#!/data/data/com.termux/files/usr/bin/python3
import os
import json

ZIP_DIR = "pewpi-infinity/z/zipcoins"

def load_zipcoins():
    """Load all zipcoin folders + metadata."""
    coins = []
    if not os.path.isdir(ZIP_DIR):
        print(f"[CROSSLINK ERROR] ZIP_DIR missing: {ZIP_DIR}")
        return coins

    for name in sorted(os.listdir(ZIP_DIR)):
        path = os.path.join(ZIP_DIR, name)
        if not os.path.isdir(path):
            continue

        meta_file = os.path.join(path, "meta.json")
        if not os.path.isfile(meta_file):
            print(f"[CROSSLINK WARNING] Missing meta.json in {name}")
            continue

        try:
            with open(meta_file, "r", encoding="utf-8") as f:
                meta = json.load(f)

            # FIX: your meta uses "coin_id" not "id"
            coins.append({
                "id": meta["coin_id"],     # <‑‑ use your field
                "folder": path,
                "index": int(meta["coin_id"].split("_")[-1]),
            })

        except Exception as e:
            print(f"[CROSSLINK ERROR] Bad meta.json in {name}: {e}")

    return coins


def build_html_for(coin, all_ids):
    """Build HTML navigation + compiled text."""
    compiled_file = os.path.join(coin["folder"], "compiled.txt")
    try:
        with open(compiled_file, "r", encoding="utf-8") as f:
            body = f.read()
    except:
        body = "[NO COMPILED TEXT]"

    nav = "<h3>Zipcoin Navigation</h3><ul>"
    for cid in all_ids:
        nav += f"<li><a href='../{cid}/compiled.html'>{cid}</a></li>"
    nav += "</ul><hr>"

    html = (
        "<html><head><meta charset='utf-8'>"
        f"<title>{coin['id']}</title></head><body>"
        f"{nav}<pre>{body}</pre></body></html>"
    )

    return html


def main():
    print("[CROSSLINK] Loading zipcoins...")
    coins = load_zipcoins()
    if not coins:
        print("[CROSSLINK] No zipcoins found.")
        return

    all_ids = [c["id"] for c in coins]

    print("[CROSSLINK] Building cross‑linked compiled.html...")

    for coin in coins:
        html = build_html_for(coin, all_ids)
        out = os.path.join(coin["folder"], "compiled.html")
        with open(out, "w", encoding="utf-8", errors="ignore") as f:
            f.write(html)

        print(f"[CROSSLINK] Added navigation + compiled HTML to {coin['id']}")

    print("[CROSSLINK] All zipcoins updated successfully.")


if __name__ == "__main__":
    main()

