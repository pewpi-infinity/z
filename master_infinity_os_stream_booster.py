#!/usr/bin/env python3
import os, json, hashlib, time, zipfile, random, re

# ===== directories =====
ROOT = os.path.expanduser("~/z")
ZIP_DIR = os.path.join(ROOT, "zipcoins_booster")
BATCH_DIR = os.path.join(ROOT, "batches_booster")
STATE_PATH = os.path.join(ROOT, ".booster_state.json")

# ===== token families / colors (same style, same logic) =====
COLOR = {
    "engineer":   "\033[92m",
    "ceo":        "\033[33m",
    "assimilate": "\033[95m",
    "import":     "\033[94m",
    "research":   "\033[93m",
    "routes":     "\033[91m",
    "investigate":"\033[95m",
    "reset":      "\033[0m"
}

STREAM = {
    "token":  "\033[96m",
    "master": "\033[91m",
    "value":  "\033[92m",
    "title":  "\033[97m",
    "body":   "\033[97m",
    "reset":  "\033[0m"
}

STOPWORDS = set("a an the and or but if in on at to of from with this that is was be been being".split())

# --- UPDATED FAMILIES ---
FAMILIES = {
    # Assimilate now includes linking/process/program concepts (Purple)
    "assimilate": [r"integrate", r"merge", r"combine", r"link", r"process", r"program", r"asset"],
    
    # Engineer is broadened to capture more action/science words (Green priority)
    "engineer": [r"engineer", r"design", r"system", r"framework", r"create", r"develop", r"build", r"flow", r"execute"],
    
    # Remaining categories
    "research": [r"research", r"study", r"data", r"analysis"],
    "import": [r"import", r"input", r"feed"],
    "routes": [r"route", r"path", r"change"],
    "investigate": [r"investigate", r"probe", r"audit"],
    "ceo": [r"CEO", r"leader", r"manage"]
}

# --- CLASSIFY PRIORITY ORDER ---
# Sets the order in which FAMILIES are checked, enforcing the purple and green priority.
CLASSIFY_ORDER = ["assimilate", "engineer", "ceo", "import", "routes", "investigate", "research"]


TERMS = [
    "hydrogen lattice", "quantum defects", "lanthanide fields",
    "electron clouds", "atomic resonance", "solid state kinetics"
]

def ensure():
    os.makedirs(ZIP_DIR, exist_ok=True)
    os.makedirs(BATCH_DIR, exist_ok=True)

def sha(s): 
    return hashlib.sha256(s.encode()).hexdigest()

def tokenize(t):
    return re.findall(r"\w+|\s+|[^\w\s]", t)

# --- UPDATED CLASSIFY FUNCTION ---
def classify(w):
    lw = w.lower()
    if lw in STOPWORDS: return "reset"
    
    # Check families in the defined priority order
    for fam in CLASSIFY_ORDER:
        pats = FAMILIES[fam]
        for p in pats:
            if re.search(p, w, re.I):
                return fam
    
    # Fallback to research if no match is found
    return "research"

def colorize(text):
    out = []
    for t in tokenize(text):
        if re.match(r"^\w+$", t):
            fam = classify(t)
            if fam == "reset":
                out.append(t)
            else:
                out.append(COLOR[fam] + t + COLOR["reset"])
        else:
            out.append(t)
    return "".join(out)

def synthetic(term):
    arr = []
    # Note: I've updated the synthetic data slightly to include more engineer/assimilate trigger words
    # to better test the new color logic.
    for i in range(8):
        x = f"Study {i+1}: Engineer the framework to integrate {term} across bands and defects."
        arr.append({"title": x, "abstract": x})
    return arr

def build_article(term, sources):
    title = f"Booster Infinity Research on {term}"
    body = "- " + "\n- ".join([s["title"] for s in sources])
    return title, colorize(title), colorize(body), body

def richness(body, n):
    w = re.findall(r"\w+", body)
    c = [x for x in w if x.lower() not in STOPWORDS]
    return max(50, int(len(c) * 0.3 + n * 1.5))

def make_zip(idx):
    folder = f"boost_coin_{idx:05d}"
    p = os.path.join(ZIP_DIR, folder)
    os.makedirs(p, exist_ok=True)
    return folder, p

def stream(idx, folder, h, val, t, art):
    print(f"{STREAM['token']}[BOOST {idx}] {folder}{STREAM['reset']}")
    print(f"{STREAM['master']}MASTER {h}{STREAM['reset']}")
    print(f"{STREAM['value']}VALUE ${val}{STREAM['reset']}")
    print(f"{STREAM['title']}TITLE {t}{STREAM['reset']}")
    print(f"{STREAM['body']}{art}{STREAM['reset']}\n")

def main():
    ensure()
    if os.path.isfile(STATE_PATH):
        state = json.load(open(STATE_PATH))
    else:
        state = {"next": 0}

    print("[BOOSTER] Infinity OS Token Booster Online.")

    # === Slower so it doesn't conflict ===
    # ~4 tokens per second
    DELAY = 0.23

    while True:
        try:
            term = random.choice(TERMS)
            sources = synthetic(term)
            title, title_c, art, plain = build_article(term, sources)

            val = richness(plain, len(sources))
            folder, path = make_zip(state["next"])

            meta = {
                "topic": term,
                "title": title,
                "value": val,
                "research": art
            }
            json.dump(meta, open(os.path.join(path, "meta.json"), "w"), indent=4)

            h = sha(term + plain)
            idx = state["next"]

            stream(idx, folder, h, val, title, art)

            state["next"] += 1
            json.dump(state, open(STATE_PATH, "w"))

            time.sleep(DELAY)

        except KeyboardInterrupt:
            print("\n[BOOSTER] Stopped.")
            break

