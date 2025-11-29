#!/data/data/com.termux/files/usr/bin/python3
import os
import json

ZIP_DIR = "pewpi-infinity/z/zipcoins"

def load_zipcoins():
    """Load all zipcoins and return a list of dicts containing their data."""
    coins = []
    if not os.path.isdir(ZIP_DIR):
        print(f"[CROSSLINK ERROR] Missing zipcoins directory: {ZIP_DIR}")
        return coins

    for folder in sorted(os.listdir(ZIP_DIR)):
        path = os.path.join(ZIP_DIR, folder)
        if not os.path.isdir(path):
            continue

        meta_path = os.path.join(path, "meta.json")
        if not os.path.isfile(meta_path):
            print(f"[CROSSLINK ERROR] Missing meta.json in {folder}")
            continue

        try:
            with open(meta_path, "r", encoding="utf-8", errors="ignore") as f:
                meta = json.load(f)
        except Exception as e:
            print(f"[CROSSLINK ERROR] Cannot read meta.json in {folder}: {e}")
            continue

        # REQUIRED field for Cart v2 system
        if "id" not in meta:
            print(f"[CROSSLINK ERROR] meta.json missing 'id' → {folder}")
            continue

        coins.append({
            "id": meta["id"],
            "folder": folder,
            "path": path
        })

    return coins


def add_crosslinks(coins):
    """Add next/previous navigation to each compiled.html in every zipcoin."""
    total = len(coins)
    if total == 0:
        print("[CROSSLINK] No zipcoins found.")
        return

    for i, coin in enumerate(coins):
        current = coin["folder"]

        prev_coin = coins[i - 1]["folder"] if i > 0 else None
        next_coin = coins[i + 1]["folder"] if i < total - 1 else None

        compiled_path = os.path.join(coin["path"], "compiled.html")
        if not os.path.isfile(compiled_path):
            print(f"[CROSSLINK ERROR] Missing compiled.html in {current}")
            continue

        try:
            with open(compiled_path, "r", encoding="utf-8", errors="ignore") as f:
                html = f.read()
        except Exception as e:
            print(f"[CROSSLINK ERROR] Cannot read compiled.html in {current}: {e}")
            continue

        nav = "<hr>"
        if prev_coin:
            nav += f"<a href='../{prev_coin}/compiled.html'>← Previous</a> | "
        else:
            nav += "← Previous | "

        if next_coin:
            nav += f"<a href='../{next_coin}/compiled.html'>Next →</a>"
        else:
            nav += "Next →"

        html = html.replace("</body>", f"{nav}</body>")

        try:
            with open(compiled_path, "w", encoding="utf-8", errors="ignore") as f:
                f.write(html)
        except Exception as e:
            print(f"[CROSSLINK ERROR] Cannot write compiled.html in {current}: {e}")
            continue

        print(f"[CROSSLINK] Added navigation to {current}")


def main():
    print("[CROSSLINK] Loading zipcoins...")
    coins = load_zipcoins()
    add_crosslinks(coins)
    print("[CROSSLINK] All zipcoins updated.")

if __name__ == "__main__":
    main()

