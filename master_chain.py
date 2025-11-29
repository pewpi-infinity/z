import os
import json
import hashlib
import subprocess
import time

ROOT = os.path.expanduser("~/z")
ZIP_DIR = os.path.join(ROOT, "zipcoins")
REPO = os.path.join(ROOT, "pewpi-infinity/z")

# ANSI escape codes mapped to your 7 colors
COLOR_HTML = {
    "green": "\033[92m",   # engineer
    "orange": "\033[33m",  # ceo (approx orange)
    "purple": "\033[95m",  # assimilate
    "blue": "\033[94m",    # import
    "yellow": "\033[93m",  # research
    "red": "\033[91m",     # routes
    "pink": "\033[95m",    # investigate (reuse magenta)
    "reset": "\033[0m"
}

def sha256(data: str) -> str:
    return hashlib.sha256(data.encode("utf-8")).hexdigest()

print("[CHAIN] Streaming research pages...")

coins = []
for folder in sorted(os.listdir(ZIP_DIR)):
    path = os.path.join(ZIP_DIR, folder)
    if not os.path.isdir(path):
        continue

    meta_path = os.path.join(path, "meta.json")
    if not os.path.isfile(meta_path):
        continue

    with open(meta_path, "r") as f:
        meta = json.load(f)

    # Hashes
    orig_hash = sha256(meta.get("link", ""))
    research_hash = sha256(meta.get("research", ""))
    combo_hash = sha256(orig_hash + research_hash)
    master_hash = sha256(combo_hash)
    audit_hash = sha256(master_hash + folder)

    # Save provenance
    chain_path = os.path.join(path, "chain.json")
    with open(chain_path, "w") as f:
        json.dump({
            "engineer_green": orig_hash,
            "research_yellow": research_hash,
            "assimilate_purple": combo_hash,
            "routes_red": master_hash,
            "investigate_pink": audit_hash,
            "ceo_orange": folder,
            "import_blue": meta.get("input", "")
        }, f, indent=4)

    # STREAM the research page with color coding
    print(f"{COLOR_HTML['orange']}=== ZIPCOIN {folder} ==={COLOR_HTML['reset']}")
    print(f"{COLOR_HTML['green']}Engineer (orig link): {meta.get('link','')}{COLOR_HTML['reset']}")
    print(f"{COLOR_HTML['yellow']}Research: {meta.get('research','')}{COLOR_HTML['reset']}")
    print(f"{COLOR_HTML['purple']}Assimilate (combo logic applied){COLOR_HTML['reset']}")
    print(f"{COLOR_HTML['red']}Routes (master hash stored){COLOR_HTML['reset']}")
    print(f"{COLOR_HTML['pink']}Investigate (audit trail){COLOR_HTML['reset']}")
    print(f"{COLOR_HTML['blue']}Import (input): {meta.get('input','')}{COLOR_HTML['reset']}")
    print()

    # Slow down so it "flies" page by page
    time.sleep(0.5)

    coins.append(master_hash)

if not coins:
    print("[CHAIN] No zipcoins found.")
    exit()

# Roll up 1000 master hashes
batch = coins[:1000]
major_master = sha256("".join(batch))

major_path = os.path.join(ROOT, "major_master.json")
with open(major_path, "w") as f:
    json.dump({"major_master_hash": major_master}, f, indent=4)

print(f"{COLOR_HTML['red']}[CHAIN] Major master hash created{COLOR_HTML['reset']}")

# Push to repo
subprocess.run(["git", "-C", REPO, "add", "."], check=False)
subprocess.run(["git", "-C", REPO, "commit", "-m", "Add major master hash"], check=False)
subprocess.run(["git", "-C", REPO, "push"], check=False)

