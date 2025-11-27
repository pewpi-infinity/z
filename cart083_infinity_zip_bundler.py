#!/usr/bin/env python3
import os, zipfile, time, datetime, shutil

RAW_DIR = "/data/data/com.termux/files/home/infinity_raw"
BUNDLE_DIR = "/data/data/com.termux/files/home/z/data"
LOGFILE = "/data/data/com.termux/files/home/z/data/bundler_log.txt"

os.makedirs(RAW_DIR, exist_ok=True)
os.makedirs(BUNDLE_DIR, exist_ok=True)

def log(msg):
    with open(LOGFILE, "a") as f:
        f.write(f"[{datetime.datetime.now()}] {msg}\n")
    print(msg)

def make_bundle(files, batch_number):
    bundle_path = f"{BUNDLE_DIR}/token_batch_{batch_number:05d}.zip"
    log(f"Creating bundle: {bundle_path}")

    with zipfile.ZipFile(bundle_path, "w", zipfile.ZIP_DEFLATED) as z:
        for fpath in files:
            arcname = os.path.basename(fpath)
            try:
                z.write(fpath, arcname)
            except:
                pass

    log(f"Bundle saved: {bundle_path}")
    return bundle_path

def scan_and_bundle():
    batch = 0

    while True:
        all_files = []
        for root, dirs, files in os.walk(RAW_DIR):
            for f in files:
                if f.endswith(".json") or f.endswith(".gz") or f.endswith(".hash"):
                    all_files.append(os.path.join(root, f))

        if len(all_files) >= 5000:
            batch += 1
            selected = all_files[:5000]
            bundle = make_bundle(selected, batch)

            # OPTIONAL: Delete raw after bundle
            # for f in selected: os.remove(f)

            log(f"Batch {batch} complete. {len(selected)} files bundled.")

        time.sleep(3)

if __name__ == "__main__":
    log("∞ Infinity Zip Bundler Online ∞")
    scan_and_bundle()
