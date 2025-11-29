#!/usr/bin/env python3
import os, json, hashlib, time, subprocess, zipfile

ROOT = os.path.expanduser("~/z")
ZIP_DIR = os.path.join(ROOT, "zipcoins")
REPO = os.path.join(ROOT, "pewpi-infinity/z")
STATE_PATH = os.path.join(ROOT, ".slim_state.json")
PROCESSED_PATH = os.path.join(ROOT, ".slim_processed.json")
BATCH_DIR = os.path.join(ROOT, "batches")

# Minimal ANSI colors for research visibility (yellow) and master hash (red)
C = {
    "research": "\033[93m",  # yellow
    "master":   "\033[91m",  # red
    "token":    "\033[94m",  # blue
    "reset":    "\033[0m"
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
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w") as f:
        json.dump(obj, f, indent=4)

def ensure_dirs():
    os.makedirs(ZIP_DIR, exist_ok=True)
    os.makedirs(REPO, exist_ok=True)
    os.makedirs(BATCH_DIR, exist_ok=True)

def compute_master(meta):
    # master hash = sha256( sha256(link) + sha256(research) )
    orig = sha256(meta.get("link",""))
    research = sha256(meta.get("research",""))
    combo = orig + research
    master = sha256(combo)
    return master

def stream_coin(folder, idx_in_batch, meta, master_hash):
    # Show ONLY: token (1/1000), master hash, research text
    print(f"{C['token']}[TOKEN {idx_in_batch}/1000] {folder}{C['reset']}")
    print(f"{C['master']}[MASTER] {master_hash}{C['reset']}")
    print(f"{C['research']}[RESEARCH]{C['reset']} {meta.get('research','')}\n")

def process_zipcoin(folder, state):
    meta_path = os.path.join(ZIP_DIR, folder, "meta.json")
    if not os.path.isfile(meta_path):
        return None

    try:
        with open(meta_path, "r") as f:
            meta = json.load(f)
    except Exception:
        return None

    master_hash = compute_master(meta)

    # Determine current index in the active batch (1..1000)
    idx_in_batch = (len(state["current_batch_hashes"]) % 1000) + 1

    # Stream the page (slim)
    stream_coin(folder, idx_in_batch, meta, master_hash)

    # Append to current batch ledger (hashes only)
    state["current_batch_hashes"].append(master_hash)
    state["processed"].append(folder)
    return master_hash

def finalize_batch(state):
    # When we reach 1000 masters, roll up into a major master, zip, and push
    if len(state["current_batch_hashes"]) < 1000:
        return False

    batch_index = state["batch_index"] + 1
    batch_hashes = state["current_batch_hashes"][:1000]
    major_master = sha256("".join(batch_hashes))

    # Write batch ledger and summary
    batch_folder = os.path.join(BATCH_DIR, f"batch_{batch_index:04d}")
    os.makedirs(batch_folder, exist_ok=True)

    ledger_path = os.path.join(batch_folder, "batch_ledger.json")
    save_json(ledger_path, {
        "batch_index": batch_index,
        "count": 1000,
        "major_master_hash": major_master,
        "master_hashes": batch_hashes
    })

    # Create ZIP containing ledger and a minimal summary
    zip_name = os.path.join(BATCH_DIR, f"major_master_{batch_index:04d}.zip")
    summary_path = os.path.join(batch_folder, "summary.json")
    save_json(summary_path, {
        "batch_index": batch_index,
        "major_master_hash": major_master
    })

    with zipfile.ZipFile(zip_name, "w", compression=zipfile.ZIP_DEFLATED) as z:
        z.write(ledger_path, arcname="batch_ledger.json")
        z.write(summary_path, arcname="summary.json")

    # Also write a plain JSON marker at repo root for easy diff
    marker_path = os.path.join(REPO, f"major_master_{batch_index:04d}.json")
    save_json(marker_path, {"major_master_hash": major_master, "batch_index": batch_index})

    # Reset current batch and increment index
    state["current_batch_hashes"] = state["current_batch_hashes"][1000:]
    state["batch_index"] = batch_index

    print(f"{C['master']}[ROLL-UP] Batch {batch_index:04d} → MAJOR {major_master}{C['reset']}")
    return True

def git_push():
    try:
        subprocess.run(["git", "-C", REPO, "add", "."], check=False)
        subprocess.run(["git", "-C", REPO, "commit", "-m", "Infinity: major master batch update"], check=False)
        subprocess.run(["git", "-C", REPO, "push"], check=False)
        print("[PUSH] Repo push attempted")
    except Exception as e:
        print(f"[PUSH WARN] {e}")

def main():
    ensure_dirs()
    state = load_json(STATE_PATH, {
        "batch_index": 0,
        "current_batch_hashes": [],
        "processed": []
    })
    processed_set = set(state["processed"])

    print("[SLIM] Streaming. Press Ctrl+C to stop.")
    while True:
        try:
            folders = [f for f in sorted(os.listdir(ZIP_DIR)) if os.path.isdir(os.path.join(ZIP_DIR, f))]
            new = [f for f in folders if f not in processed_set]

            for folder in new:
                mh = process_zipcoin(folder, state)
                if mh is not None:
                    processed_set.add(folder)
                    state["processed"] = sorted(list(processed_set))
                    save_json(STATE_PATH, state)
                    time.sleep(0.15)

                if finalize_batch(state):
                    save_json(STATE_PATH, state)
                    git_push()

            # Idle animation: lightly re-show last token to keep “flying”
            if not new and state["processed"]:
                last = state["processed"][-1]
                meta_path = os.path.join(ZIP_DIR, last, "meta.json")
                if os.path.isfile(meta_path):
                    try:
                        with open(meta_path, "r") as f:
                            meta = json.load(f)
                        idx = (len(state["current_batch_hashes"]) % 1000) or 1000
                        mh = compute_master(meta)
                        stream_coin(last, idx, meta, mh)
                    except Exception:
                        pass
                time.sleep(1.0)
            else:
                time.sleep(0.5)
        except KeyboardInterrupt:
            print("\n[SLIM] Stopped.")
            break
        except Exception as e:
            print(f"[SLIM ERROR] {e}")
            time.sleep(1.0)

if __name__ == "__main__":
    main()
