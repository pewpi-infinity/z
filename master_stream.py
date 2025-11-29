#!/usr/bin/env python3
import os, json, hashlib, time, subprocess

ROOT = os.path.expanduser("~/z")
ZIP_DIR = os.path.join(ROOT, "zipcoins")
REPO = os.path.join(ROOT, "pewpi-infinity/z")
STATE_PATH = os.path.join(ROOT, ".stream_state.json")
PROCESSED_PATH = os.path.join(ROOT, ".processed_zipcoins.json")

# ANSI colors mapped to your logic
COLOR = {
    "green":  "\033[92m",  # engineer
    "orange": "\033[33m",  # ceo (approx orange)
    "purple": "\033[95m",  # assimilate
    "blue":   "\033[94m",  # import
    "yellow": "\033[93m",  # research
    "red":    "\033[91m",  # routes
    "pink":   "\033[95m",  # investigate (magenta)
    "reset":  "\033[0m"
}

def sha256(s: str) -> str:
    return hashlib.sha256(s.encode("utf-8")).hexdigest()

def load_json(path, default):
    try:
        if os.path.isfile(path):
            with open(path, "r") as f:
                return json.load(f)
    except Exception:
        pass
    return default

def save_json(path, obj):
    try:
        with open(path, "w") as f:
            json.dump(obj, f, indent=4)
        return True
    except Exception as e:
        print(f"[STREAM ERROR] Failed to write {path}: {e}")
        return False

def ensure_dirs():
    os.makedirs(ZIP_DIR, exist_ok=True)
    os.makedirs(REPO, exist_ok=True)  # if it doesn't exist, we still create the folder

def stream_page(folder, meta):
    # Full-color streaming of the research page in your 7-anchor logic
    print(f"{COLOR['orange']}====== ZIPCOIN {folder} ======{COLOR['reset']}")
    print(f"{COLOR['green']}Engineer (orig link):{COLOR['reset']} {meta.get('link','')}")
    print(f"{COLOR['yellow']}Research (read/data):{COLOR['reset']} {meta.get('research','')}")
    print(f"{COLOR['purple']}Assimilate (integration):{COLOR['reset']} {meta.get('assimilation','') or '[auto] link+research combined'}")
    print(f"{COLOR['blue']}Import (needs input):{COLOR['reset']} {meta.get('input','')}")
    print(f"{COLOR['red']}Routes (changes/weird possible):{COLOR['reset']} [master stored]")
    print(f"{COLOR['pink']}Investigate (probe/audit):{COLOR['reset']} [audit stored]")
    print(f"{COLOR['orange']}CEO (ownership anchor):{COLOR['reset']} {folder}")
    print()

def process_zipcoin(folder, state):
    path = os.path.join(ZIP_DIR, folder)
    meta_path = os.path.join(path, "meta.json")
    if not os.path.isfile(meta_path):
        print(f"[STREAM WARN] Missing meta.json in {folder}")
        return None

    try:
        with open(meta_path, "r") as f:
            meta = json.load(f)
    except Exception as e:
        print(f"[STREAM ERROR] Bad meta.json in {folder}: {e}")
        return None

    # Hash chain
    orig_hash = sha256(meta.get("link", ""))
    research_hash = sha256(meta.get("research", ""))
    combo_hash = sha256(orig_hash + research_hash)  # assimilate
    master_hash = sha256(combo_hash)                # routes/master
    audit_hash = sha256(master_hash + folder)       # investigate

    # Persist provenance per coin
    chain_path = os.path.join(path, "chain.json")
    save_json(chain_path, {
        "engineer_green": orig_hash,
        "research_yellow": research_hash,
        "assimilate_purple": combo_hash,
        "routes_red": master_hash,
        "investigate_pink": audit_hash,
        "ceo_orange": folder,
        "import_blue": meta.get("input", "")
    })

    # Stream full “page” with colors
    stream_page(folder, meta)

    # Update rolling state
    state["master_hashes"].append(master_hash)
    return master_hash

def roll_batches(state):
    # Every 1000 master hashes → one major master
    count = len(state["master_hashes"])
    next_idx = count // 1000  # how many full batches exist
    if next_idx <= state["major_batches"]:
        return False

    # Compute new batch hash
    batch_hashes = state["master_hashes"][state["major_batches"]*1000 : next_idx*1000]
    major_master = sha256("".join(batch_hashes))
    idx = state["major_batches"] + 1

    major_obj = {
        "batch_index": idx,
        "count_in_batch": 1000,
        "major_master_hash": major_master,
        "timestamp": int(time.time())
    }

    # Write a file per batch
    major_file = os.path.join(ROOT, f"major_master_{idx:04d}.json")
    save_json(major_file, major_obj)

    # Also write/update a ledger
    ledger_path = os.path.join(ROOT, "major_master_ledger.json")
    ledger = load_json(ledger_path, [])
    ledger.append(major_obj)
    save_json(ledger_path, ledger)

    print(f"{COLOR['red']}[STREAM] Major master {idx} created ({len(batch_hashes)} hashes){COLOR['reset']}")
    state["major_batches"] = idx
    return True

def git_push():
    # Best-effort git push; non-fatal if it fails
    try:
        subprocess.run(["git", "-C", REPO, "add", "."], check=False)
        subprocess.run(["git", "-C", REPO, "commit", "-m", "Infinity: update major master batches"], check=False)
        subprocess.run(["git", "-C", REPO, "push"], check=False)
        print("[STREAM] Repo push attempted.")
    except Exception as e:
        print(f"[STREAM WARN] Git push failed: {e}")

def main():
    ensure_dirs()

    # Load state
    state = load_json(STATE_PATH, {"major_batches": 0, "master_hashes": []})
    processed = set(load_json(PROCESSED_PATH, []))

    print("[STREAM] Watching zipcoins. Press Ctrl+C to stop.")
    while True:
        try:
            folders = [f for f in sorted(os.listdir(ZIP_DIR)) if os.path.isdir(os.path.join(ZIP_DIR, f))]
            new_folders = [f for f in folders if f not in processed]

            # Process new coins first
            for folder in new_folders:
                mh = process_zipcoin(folder, state)
                if mh is not None:
                    processed.add(folder)
                    save_json(PROCESSED_PATH, sorted(list(processed)))
                    save_json(STATE_PATH, state)
                    time.sleep(0.25)  # make it feel like it's flying

                # Batch roll & push whenever we hit a multiple of 1000
                if roll_batches(state):
                    save_json(STATE_PATH, state)
                    git_push()

            # Re-stream already processed coins if you want continuous pages flying
            if not new_folders:
                # Optional: lightly re-show last few pages to keep the terminal alive
                replay = list(processed)[-5:]
                for folder in replay:
                    meta_path = os.path.join(ZIP_DIR, folder, "meta.json")
                    if os.path.isfile(meta_path):
                        try:
                            with open(meta_path, "r") as f:
                                meta = json.load(f)
                            stream_page(folder, meta)
                        except Exception:
                            pass
                        time.sleep(0.15)

            time.sleep(1.5)  # main watch interval
        except KeyboardInterrupt:
            print("\n[STREAM] Stopped by user.")
            break
        except Exception as e:
            print(f"[STREAM ERROR] Loop error: {e}")
            time.sleep(1.5)

if __name__ == "__main__":
    main()
