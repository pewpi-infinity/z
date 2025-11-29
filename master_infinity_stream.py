#!/usr/bin/env python3
import os, json, hashlib, time, subprocess, zipfile, random, re
from typing import List, Dict

# Optional imports for scraping (script will still run without them)
try:
    import requests
    from bs4 import BeautifulSoup
except Exception:
    requests = None
    BeautifulSoup = None

ROOT = os.path.expanduser("~/z")
ZIP_DIR = os.path.join(ROOT, "zipcoins")
REPO = os.path.join(ROOT, "pewpi-infinity/z")
BATCH_DIR = os.path.join(ROOT, "batches")
STATE_PATH = os.path.join(ROOT, ".infinity_stream_state.json")

# Proprietary seven-color anchors (ANSI)
COLOR = {
    "engineer":   "\033[92m",  # green
    "ceo":        "\033[33m",  # orange (approx)
    "assimilate": "\033[95m",  # purple/magenta
    "import":     "\033[94m",  # blue
    "research":   "\033[93m",  # yellow
    "routes":     "\033[91m",  # red
    "investigate":"\033[95m",  # pink/magenta
    "reset":      "\033[0m"
}

# Stream colors: token, master, research body
STREAM = {
    "token":  "\033[96m",  # cyan
    "master": "\033[91m",  # red
    "body":   "\033[97m",  # bright white (base text)
    "reset":  "\033[0m"
}

SEED_TERMS = [
    "periodic table trends", "transition metal catalysis", "lanthanide contraction",
    "alkali metals reactivity", "halogen oxidation states", "noble gas applications",
    "electronegativity and bonding", "ionization energy", "atomic radius",
    "d-block coordination chemistry", "p-block chemistry", "f-block spectroscopy",
    "crystal field theory", "organometallic catalysis", "solid-state band structure",
    "semiconductor doping", "surface adsorption", "materials defects",
    "heterogeneous catalysis", "redox chemistry"
]

HEADERS = {"User-Agent": "InfinityHarvester/2.0 (+Termux)"}

def ensure_dirs():
    os.makedirs(ZIP_DIR, exist_ok=True)
    os.makedirs(REPO, exist_ok=True)
    os.makedirs(BATCH_DIR, exist_ok=True)

def sha256(s: str) -> str:
    return hashlib.sha256(s.encode("utf-8")).hexdigest()

def save_json(path, obj):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w") as f:
        json.dump(obj, f, indent=4)

def load_json(path, default):
    try:
        if os.path.isfile(path):
            with open(path, "r") as f:
                return json.load(f)
    except Exception:
        pass
    return default

# -----------------------------
# Harvesters (10–30 items total)
# -----------------------------

def crossref_query(term, rows=10) -> List[Dict]:
    if requests is None:
        return []
    try:
        url = "https://api.crossref.org/works"
        params = {"query": term, "rows": rows, "filter": "type:journal-article"}
        r = requests.get(url, params=params, headers=HEADERS, timeout=15)
        r.raise_for_status()
        data = r.json()
        items = []
        for it in data.get("message", {}).get("items", []):
            title = " ".join(it.get("title", [])).strip() or term
            abstract_html = it.get("abstract", "") or ""
            abstract = ""
            if abstract_html and BeautifulSoup:
                abstract = BeautifulSoup(abstract_html, "html.parser").get_text(" ", strip=True)
            elif it.get("subject"):
                abstract = f"{title} — {', '.join(it.get('subject', [])[:6])}"
            link = it.get("URL") or ""
            items.append({"title": title, "abstract": abstract, "link": link})
        return items
    except Exception:
        return []

def pubmed_query(term, retmax=10) -> List[Dict]:
    if requests is None:
        return []
    base = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils"
    try:
        s = requests.get(f"{base}/esearch.fcgi", params={
            "db": "pubmed", "term": term, "retmode": "json", "retmax": retmax
        }, headers=HEADERS, timeout=15)
        s.raise_for_status()
        ids = s.json().get("esearchresult", {}).get("idlist", [])
        if not ids:
            return []
        f = requests.get(f"{base}/esummary.fcgi", params={
            "db": "pubmed", "id": ",".join(ids), "retmode": "json"
        }, headers=HEADERS, timeout=15)
        f.raise_for_status()
        summ = f.json().get("result", {})
        items = []
        for pid in ids:
            rec = summ.get(pid, {})
            title = rec.get("title", "").strip()
            link = f"https://pubmed.ncbi.nlm.nih.gov/{pid}/"
            abstract = ""
            # Best-effort abstract scrape
            try:
                page = requests.get(link, headers=HEADERS, timeout=10)
                if page.ok and BeautifulSoup:
                    soup = BeautifulSoup(page.text, "html.parser")
                    abst = soup.select_one(".abstract-content")
                    if abst:
                        abstract = abst.get_text(" ", strip=True)
            except Exception:
                pass
            items.append({"title": title, "abstract": abstract, "link": link})
        return items
    except Exception:
        return []

def synthetic_items(term, n=12) -> List[Dict]:
    # Fallback when APIs unavailable; creates structured notes
    templ = [
        f"Survey on {term} across d-, p-, and f-block elements.",
        f"Correlations between electronegativity and bond strength for {term}.",
        f"Lanthanide contraction effects on coordination complexes related to {term}.",
        f"Halogen oxidation anomalies and catalytic implications for {term}.",
        f"Surface adsorption mechanisms in materials chemistry concerning {term}.",
        f"Solid-state band structure variations and {term} performance.",
        f"Semiconductor doping strategies influenced by {term}.",
        f"Redox behavior patterns and {term}-dependent kinetics.",
        f"Atomic radius trends and their role in {term}.",
        f"Crystal field theory applications informing {term}.",
        f"Organometallic pathways expanding {term} catalysis.",
        f"Transition metal centers modulating {term}."
    ]
    items = [{"title": t, "abstract": t, "link": ""} for t in templ[:n]]
    return items

def harvest_sources(term) -> List[Dict]:
    # Collect 10–30 items
    items = []
    items += crossref_query(term, rows=12)
    items += pubmed_query(term, retmax=12)
    if len(items) < 10:
        items += synthetic_items(term, n=12)
    random.shuffle(items)
    return items[:random.randint(10, 30)]

# -----------------------------------
# Infinity rewrite + color decoration
# -----------------------------------

ANCHOR_TERMS = {
    "engineer":   [r"\bdesign\b", r"\bengineer\b", r"\bbuild\b", r"\bconstruct\b"],
    "ceo":        [r"\bCEO\b", r"\blead\b", r"\bmanage\b", r"\bgovern\b"],
    "assimilate": [r"\bintegrate\b", r"\bcombine\b", r"\bmerge\b", r"\bassimilate\b"],
    "import":     [r"\bimport\b", r"\binput\b", r"\bfeed\b", r"\bingest\b"],
    "research":   [r"\bresearch\b", r"\bstudy\b", r"\bdata\b", r"\banalysis\b"],
    "routes":     [r"\broute\b", r"\bpathway\b", r"\bchange\b", r"\bvariant\b"],
    "investigate":[r"\binvestigate\b", r"\bprobe\b", r"\baudit\b", r"\binspect\b"]
}

def colorize(text: str) -> str:
    # Apply proprietary color anchors to matching terms within the text
    out = text
    for anchor, patterns in ANCHOR_TERMS.items():
        color = COLOR[anchor]
        for pat in patterns:
            out = re.sub(pat, lambda m: f"{color}{m.group(0)}{COLOR['reset']}", out, flags=re.IGNORECASE)
    return out

def rewrite_infinity(term: str, sources: List[Dict]) -> str:
    # Synthesize 10–30 abstracts into one Infinity Research page
    bullets = []
    for it in sources:
        title = (it.get("title") or "").strip()
        abstract = (it.get("abstract") or "").strip()
        if abstract and title:
            bullets.append(f"{title}: {abstract}")
        elif abstract:
            bullets.append(abstract)
        elif title:
            bullets.append(title)
    # Expand into sections with your anchors as headings
    sections = [
        f"{COLOR['engineer']}Engineer:{COLOR['reset']} Core constructs around {term} across d/p/f blocks.",
        f"{COLOR['research']}Research:{COLOR['reset']} Aggregated findings from {len(sources)} sources.",
        f"{COLOR['assimilate']}Assimilate:{COLOR['reset']} Integrated signals: electronegativity, ionization, radius, redox.",
        f"{COLOR['routes']}Routes:{COLOR['reset']} Catalytic pathways and anomalies suggesting novel mechanisms.",
        f"{COLOR['investigate']}Investigate:{COLOR['reset']} Consistency checks and outlier audits.",
        f"{COLOR['import']}Import:{COLOR['reset']} Inputs synthesized from multi-source harvesting.",
        f"{COLOR['ceo']}CEO:{COLOR['reset']} Token anchored in Infinity ledger."
    ]
    body = "\n- " + "\n- ".join(bullets[:60])  # cap to keep it readable
    page = "\n".join(sections) + "\n\n" + body
    return colorize(page)

# -------------------------
# Hashing & provenance chain
# -------------------------

def compute_master(links: List[str], research_text: str) -> str:
    orig_hash = sha256("\n".join(links))
    research_hash = sha256(research_text)
    combo_hash = orig_hash + research_hash
    master = sha256(combo_hash)
    return master

def make_zipcoin_folder(index: int):
    folder = f"zip_coin_{index:05d}"
    path = os.path.join(ZIP_DIR, folder)
    os.makedirs(path, exist_ok=True)
    return folder, path

# ---------------
# Stream and batch
# ---------------

def stream_coin(token_idx: int, folder: str, master_hash: str, research_text: str):
    print(f"{STREAM['token']}[TOKEN {token_idx}/1000] {folder}{STREAM['reset']}")
    print(f"{STREAM['master']}[MASTER] {master_hash}{STREAM['reset']}")
    print(f"{STREAM['body']}[INFINITY RESEARCH]{STREAM['reset']} {research_text}\n")

def finalize_batch_if_ready(state):
    if len(state["current_batch_hashes"]) < 1000:
        return False
    batch_index = state["batch_index"] + 1
    batch_hashes = state["current_batch_hashes"][:1000]
    major_master = sha256("".join(batch_hashes))

    batch_folder = os.path.join(BATCH_DIR, f"batch_{batch_index:04d}")
    os.makedirs(batch_folder, exist_ok=True)

    ledger_path = os.path.join(batch_folder, "batch_ledger.json")
    save_json(ledger_path, {
        "batch_index": batch_index,
        "count": 1000,
        "major_master_hash": major_master,
        "master_hashes": batch_hashes
    })

    summary_path = os.path.join(batch_folder, "summary.json")
    save_json(summary_path, {"batch_index": batch_index, "major_master_hash": major_master})

    zip_name = os.path.join(BATCH_DIR, f"major_master_{batch_index:04d}.zip")
    with zipfile.ZipFile(zip_name, "w", compression=zipfile.ZIP_DEFLATED) as z:
        z.write(ledger_path, arcname="batch_ledger.json")
        z.write(summary_path, arcname="summary.json")

    marker_path = os.path.join(REPO, f"major_master_{batch_index:04d}.json")
    save_json(marker_path, {"major_master_hash": major_master, "batch_index": batch_index})

    state["current_batch_hashes"] = state["current_batch_hashes"][1000:]
    state["batch_index"] = batch_index

    print(f"{STREAM['master']}[ROLL-UP] Batch {batch_index:04d} → MAJOR {major_master}{STREAM['reset']}")
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
        "next_index": 0,
        "batch_index": 0,
        "current_batch_hashes": []
    })

    print("[INFINITY] Streaming multi-source Infinity research. Ctrl+C to stop.")
    while True:
        try:
            term = random.choice(SEED_TERMS)
            sources = harvest_sources(term)
            links = [s.get("link","") for s in sources if s.get("link")]
            research_text = rewrite_infinity(term, sources)

            folder, path = make_zipcoin_folder(state["next_index"])
            meta = {
                "topic": term,
                "links_count": len(links),
                "research": research_text
            }
            save_json(os.path.join(path, "meta.json"), meta)

            # Compute master hash with hidden provenance links
            master_hash = compute_master(links, research_text)

            token_idx = (len(state["current_batch_hashes"]) % 1000) + 1
            stream_coin(token_idx, folder, master_hash, research_text)

            # Append and persist
            state["current_batch_hashes"].append(master_hash)
            state["next_index"] += 1
            save_json(STATE_PATH, state)

            time.sleep(0.2)

            if finalize_batch_if_ready(state):
                save_json(STATE_PATH, state)
                git_push()

            time.sleep(0.6)
        except KeyboardInterrupt:
            print("\n[INFINITY] Stopped.")
            break
        except Exception as e:
            print(f"[INFINITY ERROR] {e}")
            time.sleep(1.0)

if __name__ == "__main__":
    main()
