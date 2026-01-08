#!/usr/bin/env python3
import os, re, json, hashlib, time, datetime, random, gzip, requests, subprocess

# ------------------------------ CONFIG ------------------------------
Z_ROOT = os.path.abspath(os.path.dirname(__file__))
TOKENS_DIR = os.path.join(Z_ROOT, "tokens")
RAW_DIR    = os.path.join(Z_ROOT, "raw")
ZIPCOIN_DIR = os.path.join(Z_ROOT, "zipcoins")

for d in [TOKENS_DIR, RAW_DIR, ZIPCOIN_DIR]:
    os.makedirs(d, exist_ok=True)

SCRAPE_SOURCES = [
    "https://arxiv.org/list/cs.AI/recent",
    "https://arxiv.org/list/physics.atom-ph/recent",
    "https://arxiv.org/list/quant-ph/recent",
    "https://en.wikipedia.org/wiki/Quantum_computing",
    "https://en.wikipedia.org/wiki/Hydrogen_production",
    "https://en.wikipedia.org/wiki/Helium",
    "https://en.wikipedia.org/wiki/Thermodynamics",
    "https://en.wikipedia.org/wiki/Carbon_capture",
]

HEADERS = {"User-Agent": "InfinityResearchBot/77.0"}

# ------------------------------ HELPERS ------------------------------
def infinity_hash(text):
    return hashlib.sha256(text.encode()).hexdigest()

def vector_position(seed):
    """Return a stable (x,y,z) vector coordinate for the token."""
    h = int(seed[:12], 16)
    return {
        "x": round((h % 997) / 997, 6),
        "y": round((h % 613) / 613, 6),
        "z": round((h % 409) / 409, 6)
    }

def valuation(text):
    length = len(text)
    science_bonus = 0
    if any(word in text.lower() for word in ["quantum","hydrogen","vector","thermo","ai","physics"]):
        science_bonus = random.randint(500,900_000)

    base = max(80, min(900 + length//150, 5000))
    return base + science_bonus

def git_push():
    try:
        subprocess.run(["git","add","."], cwd=Z_ROOT)
        subprocess.run(["git","commit","-m","Infinity research update"], cwd=Z_ROOT)
        subprocess.run(["git","push"], cwd=Z_ROOT)
    except:
        pass

# ------------------------------ SCRAPER ------------------------------
def scrape():
    url = random.choice(SCRAPE_SOURCES)
    try:
        r = requests.get(url, headers=HEADERS, timeout=10)
        if r.status_code != 200:
            return None
        text = r.text
        clean = re.sub(r"<[^>]+>","",text)
        return clean[:4000]  # throttle
    except:
        return None

# --------------------------- INFINITY REWRITE -------------------------
def infinity_rewrite(raw):
    lines = raw.split("\n")
    chosen = "\n".join(lines[:12])
    return f"[∞ Research Extract]\n{chosen}\n"

# ------------------------ TOKEN GENERATION ----------------------------
def generate_token(block):
    seed = infinity_hash(block + str(time.time()))
    vec  = vector_position(seed)
    val  = valuation(block)

    token = {
        "hash": seed,
        "timestamp": datetime.datetime.utcnow().isoformat()+"Z",
        "value": val,
        "vector": vec,
        "research": block[:1800]
    }

    path = os.path.join(TOKENS_DIR, f"{seed}.json")
    with open(path,"w") as f: json.dump(token,f,indent=4)
    return seed, path

# ------------------------ ZIPCOIN PACKAGER ----------------------------
def package_zipcoin():
    files = sorted(os.listdir(TOKENS_DIR))
    if len(files) < 3: return

    group = files[:3]
    combo_text = ""

    for f in group:
        with open(os.path.join(TOKENS_DIR,f)) as fp:
            combo_text += fp.read() + "\n---\n"

    zip_hash = infinity_hash(combo_text)
    zip_path = os.path.join(ZIPCOIN_DIR, f"{zip_hash}.zipcoin.gz")

    with gzip.open(zip_path, "wb") as z:
        z.write(combo_text.encode())

    for f in group:
        os.remove(os.path.join(TOKENS_DIR,f))

# --------------------------- MAIN LOOP --------------------------------
def main():
    print("∞ CART 077 — Infinity Research Scraper — TURBO MODE ∞")
    print("Streaming live research → tokens → repo...")

    while True:
        raw = scrape()
        if not raw:
            print("[x] scrape failed… retry")
            time.sleep(3)
            continue

        block = infinity_rewrite(raw)
        seed, path = generate_token(block)

        print(f"\n[∞] TOKEN GENERATED {seed[:12]}… val={seed[-6:]}")
        print(f"[∞] Stored: {path}")
        print(f"[∞] Vector: {vector_position(seed)}")

        package_zipcoin()
        git_push()

        time.sleep(4)  # turbo pace but safe

if __name__ == "__main__":
    main()

