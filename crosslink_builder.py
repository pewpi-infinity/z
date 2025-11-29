import os
import json

ROOT = os.path.expanduser("~/z")
ZIP_DIR = os.path.join(ROOT, "zipcoins")

print("[CROSSLINK] Loading zipcoins...")

coins = []
for folder in sorted(os.listdir(ZIP_DIR)):
    path = os.path.join(ZIP_DIR, folder)
    if not os.path.isdir(path):
        continue

    meta_path = os.path.join(path, "meta.json")
    if not os.path.isfile(meta_path):
        print(f"[CROSSLINK ERROR] Missing meta.json in {folder}")
        continue

    try:
        with open(meta_path, "r") as f:
            meta = json.load(f)
        meta["folder"] = folder
        coins.append(meta)
    except Exception as e:
        print(f"[CROSSLINK ERROR] Bad meta.json in {folder}: {e}")

if not coins:
    print("[CROSSLINK] No zipcoins found.")
    exit()

# chain them
for i, coin in enumerate(coins):
    links = {}
    if i > 0:
        links["prev"] = coins[i - 1]["folder"]
    if i < len(coins) - 1:
        links["next"] = coins[i + 1]["folder"]

    coin_dir = os.path.join(ZIP_DIR, coin["folder"])
    link_path = os.path.join(coin_dir, "links.json")
    with open(link_path, "w") as f:
        json.dump(links, f, indent=4)

print("[CROSSLINK] Links added successfully.")
