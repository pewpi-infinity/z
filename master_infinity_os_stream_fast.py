#!/usr/bin/env python3
import os, json, hashlib, time, subprocess, zipfile, random, re
from typing import List, Dict

# Same color engine and anchors
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

STOPWORDS = set("""
a an the and or but if in on at to of for from with without within by over under as is are was were be been being
this that these those it its into onto about above below between among through during before after because since
so than then when while where how what which who whom whose not nor yes no up down out off only just even ever
""".strip().split())

FAMILIES = {
    "engineer": [
        r"\bengineer(?:ing)?\b", r"\bdesign(?:er|s|ing)?\b", r"\bconstruct(?:ion|s|ed|ing)?\b",
        r"\bsystem(?:s|ic)?\b", r"\btool(?:s)?\b", r"\bAI\b", r"\bcomputer(?:s)?\b",
        r"\bsoftware\b", r"\bhardware\b", r"\barchitecture\b", r"\bframework\b",
        r"\balgorithm(?:s)?\b", r"\bmodel(?:s|ing)?\b", r"\bplatform(?:s)?\b"
    ],
    "research": [
        r"\bresearch(?:er|ers)?\b", r"\bstudy(?:ies)?\b", r"\bdata\b", r"\banalysis\b",
        r"\bexperiment(?:s|al)?\b", r"\bmetric(?:s)?\b", r"\bstatistic(?:s|al)?\b"
    ],
    "assimilate": [
        r"\bintegrate(?:d|s|ion)?\b", r"\bcombine(?:d|s|ing)?\b", r"\bmerge(?:d|s|ing)?\b"
    ],
    "import": [
        r"\bimport(?:s|ed|ing)?\b", r"\binput(?:s)?\b", r"\bfeed(?:s|ing)?\b",
    ],
    "routes": [
        r"\broute(?:s|d|ing)?\b", r"\bpath(?:s)?\b", r"\bchange(?:s|d|ing)?\b"
    ],
    "investigate": [
        r"\binvestigate(?:s|d|ing)?\b", r"\bprobe(?:s|d|ing)?\b"
    ],
    "ceo": [
        r"\bCEO\b", r"\blead(?:er|ership)?\b", r"\bmanage(?:r|ment)?\b"
    ]
}

ROOT = os.path.expanduser("~/z")
ZIP_DIR = os.path.join(ROOT, "zipcoins")
BATCH_DIR = os.path.join(ROOT, "batches")
REPO = os.path.join(ROOT, "pewpi-infinity/z")
STATE_PATH = os.path.join(ROOT, ".infinity_os_stream_state.json")

SEED_TERMS = [
    "atomic radius trends", "ionization energy", "solid-state defects",
    "electronegativity patterns", "crystal field theory", "semiconductor doping",
    "redox kinetics", "surface adsorption", "lanthanide contraction"
]

def ensure_dirs():
    os.makedirs(ZIP_DIR, exist_ok=True)
    os.makedirs(BATCH_DIR, exist_ok=True)
    os.makedirs(REPO, exist_ok=True)

def sha(x):  # faster hashing helper
    return hashlib.sha256(x.encode()).hexdigest()

def tokenize(text):
    return re.findall(r"\w+|\s+|[^\w\s]", text)

def classify(w):
    lw = w.lower()
    if lw in STOPWORDS:
        return "reset"
    for k, patterns in FAMILIES.items():
        for p in patterns:
            if re.search(p, w, re.I):
                return k
    if re.match(r"^\d+(\.\d+)?$", lw):
        return "research"
    return "research"

def colorize(text):
    out = []
    for t in tokenize(text):
        if re.match(r"^\w+$", t):
            cat = classify(t)
            if cat == "reset":
                out.append(t)
            else:
                out.append(COLOR[cat] + t + COLOR["reset"])
        else:
            out.append(t)
    return "".join(out)

def synthetic_sources(term):
    out = []
    for i in range(25):
        t = f"Study {i+1} on {term} correlations in multi-block materials."
        out.append({"title": t, "abstract": t})
    return out

def build_article(term, sources):
    title = f"Infinity Research on {term}"
    bullets = [f"- {s['title']}" for s in sources]
    body = "\n".join(bullets)
    article = colorize(body)
    title_c = colorize(title)
    return title, title_c, article

def richness(text, n):
    w = re.findall(r"\w+", text)
    c = [x for x in w if x.lower() not in STOPWORDS]
    base = len(c)
    return max(90, int(base * 0.4 + n * 2))

def make_zip(index):
    folder = f"zip_coin_{index:05d}"
    path = os.path.join(ZIP_DIR, folder)
    os.makedirs(path, exist_ok=True)
    return folder, path

def stream(idx, folder, mhash, val, title, art):
    print(f"{STREAM['token']}[TOKEN {idx}/1000] {folder}{STREAM['reset']}")
    print(f"{STREAM['master']}[MASTER] {mhash}{STREAM['reset']}")
    print(f"{STREAM['value']}[VALUE] ${val}{STREAM['reset']}")
    print(f"{STREAM['title']}[TITLE]{STREAM['reset']} {title}")
    print(f"{STREAM['body']}[INFINITY RESEARCH]{STREAM['reset']} {art}\n")

def finalize(state):
    if len(state["current"]) < 1000:
        return
    b = state["batch"] + 1
    hashes = state["current"][:1000]
    major = sha("".join(hashes))

    batch_path = os.path.join(BATCH_DIR, f"batch_{b:04d}")
    os.makedirs(batch_path, exist_ok=True)

    with open(os.path.join(batch_path, "batch_ledger.json"), "w") as f:
        json.dump({"batch": b, "count": 1000, "major": major, "hashes": hashes}, f, indent=4)

    with open(os.path.join(batch_path, "summary.json"), "w") as f:
        json.dump({"batch": b, "major": major}, f, indent=4)

    state["current"] = state["current"][1000:]
    state["batch"] = b

    print(f"{STREAM['master']}[ROLL-UP] Batch {b:04d} → MAJOR {major}{STREAM['reset']}")
    return True

def main():
    ensure_dirs()
    state = {"next": 0, "batch": 0, "current": []}
    if os.path.isfile(STATE_PATH):
        state = json.load(open(STATE_PATH))

    print("[FAST STREAM] Infinity OS hyper-accelerated research online.")
    while True:
        try:
            term = random.choice(SEED_TERMS)
            sources = synthetic_sources(term)

            title, title_c, article = build_article(term, sources)
            plain = re.sub(r"\x1b\[[0-9;]*m", "", article)
            val = richness(plain, len(sources))

            folder, path = make_zip(state["next"])
            meta = {"topic": term, "value_usd": val, "title": title, "research": article}
            json.dump(meta, open(os.path.join(path, "meta.json"), "w"), indent=4)

            master_hash = sha(term + plain)

            idx = (len(state["current"]) % 1000) + 1
            stream(idx, folder, master_hash, val, title, article)

            state["current"].append(master_hash)
            state["next"] += 1

            json.dump(state, open(STATE_PATH, "w"))

            if finalize(state):
                json.dump(state, open(STATE_PATH, "w"))
            time.sleep(0.03)

        except KeyboardInterrupt:
            print("\n[FAST STREAM] Stopped.")
            break

