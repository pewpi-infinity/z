#!/usr/bin/env python3
import os, hashlib, zipfile, time, random, json

MASTER_DIR = "zipcoins"
MICRO_DIR = "zipcoins/micro"
COUNT = 1000

SOURCES = [
    "https://research.ibm.com/publications",
    "https://www.cs.princeton.edu/research",
    "https://www.eecs.mit.edu/research",
    "https://www.seas.harvard.edu/research",
    "https://www.stanford.edu/research/",
    "https://arxiv.org/list/cs.AI/recent",
    "https://www.nature.com/ai/",
    "https://www.sciencedaily.com/news/computers_math/artificial_intelligence/",
    "https://www.nasa.gov/stem-content/",
    "https://www.nist.gov/topics/artificial-intelligence"
]

def ensure_dirs():
    os.makedirs(MASTER_DIR, exist_ok=True)
    os.makedirs(MICRO_DIR, exist_ok=True)

def make_micro(i):
    url = random.choice(SOURCES)
    stub = {
        "source": url,
        "generated_at": time.time(),
        "summary": "AI research packet (fast-mode stub).",
        "placeholder": True
    }
    data = json.dumps(stub).encode()
    sha = hashlib.sha256(data).hexdigest()
    out = os.path.join(MICRO_DIR, f"micro_{i:04d}_{sha}.zip")

    with zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED) as z:
        z.writestr("meta.json", json.dumps(stub, indent=2))

    print(f"[{i}/{COUNT}] {sha}")
    return out, sha

def main():
    ensure_dirs()
    micro_paths = []
    combined_hash_data = ""

    print("∞ FAST MODE: FLYING SCROLL ONLINE ∞")

    for i in range(1, COUNT + 1):
        p, h = make_micro(i)
        micro_paths.append(p)
        combined_hash_data += h

    master_hash = hashlib.sha256(combined_hash_data.encode()).hexdigest()
    master_path = os.path.join(MASTER_DIR, f"{master_hash}.zip")

    with zipfile.ZipFile(master_path, "w", zipfile.ZIP_DEFLATED) as z:
        for p in micro_paths:
            z.write(p, arcname=os.path.basename(p))

    print("\n=== MASTER TOKEN READY ===")
    print("HASH:", master_hash)
    print("FILE:", master_path)
    print("==========================")

if __name__ == "__main__":
    main()
