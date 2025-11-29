#!/usr/bin/env python3
import os, json, hashlib, time, subprocess, zipfile, random, re
from typing import List, Dict

# Optional (script runs without them using synthetic items)
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
STATE_PATH = os.path.join(ROOT, ".infinity_os_stream_state.json")

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

# Stream colors
STREAM = {
    "token":  "\033[96m",  # cyan
    "master": "\033[91m",  # red
    "value":  "\033[92m",  # green
    "title":  "\033[97m",  # bright white
    "body":   "\033[97m",  # bright white base
    "reset":  "\033[0m"
}

# Stopwords to leave uncolored (extend as needed)
STOPWORDS = set("""
a an the and or but if in on at to of for from with without within by over under as is are was were be been being
this that these those it its into onto about above below between among through during before after because since
so than then when while where how what which who whom whose not nor yes no up down out off only just even ever
""".strip().split())

# Semantic families for color coding (clusters, not single words)
FAMILIES = {
    "engineer": [
        r"\bengineer(?:ing)?\b", r"\bdesign(?:er|s|ing)?\b", r"\bconstruct(?:ion|s|ed|ing)?\b",
        r"\bsystem(?:s|ic)?\b", r"\btool(?:s)?\b", r"\bAI\b", r"\bcomputer(?:s)?\b",
        r"\bsoftware\b", r"\bhardware\b", r"\barchitecture\b", r"\bframework\b",
        r"\balgorithm(?:s)?\b", r"\bmodel(?:s|ing)?\b", r"\bplatform(?:s)?\b", r"\binterface(?:s)?\b"
    ],
    "research": [
        r"\bresearch(?:er|ers)?\b", r"\bstudy(?:ies)?\b", r"\bdata\b", r"\banalysis\b", r"\bexperiment(?:s|al)?\b",
        r"\btrial(?:s)?\b", r"\bmetric(?:s)?\b", r"\bstatistic(?:s|al)?\b", r"\bdataset(?:s)?\b",
        r"\bMcDonald'?s\b", r"\bhamburger(?:s)?\b", r"\bbeef\b", r"\bfranchise(?:s|es)?\b", r"\bmarket(?:s|ing)?\b",
        r"\bmeasurement(?:s)?\b", r"\bobservation(?:s)?\b", r"\bcorpus\b"
    ],
    "assimilate": [
        r"\bintegrate(?:d|s|ion)?\b", r"\bcombine(?:d|s|ing)?\b", r"\bmerge(?:d|s|ing)?\b", r"\bassimilate(?:d|s|ion)?\b",
        r"\bfuse(?:d|s|ing)?\b", r"\bhybrid(?:s|ize|ized|ization)?\b", r"\baggregate(?:d|s|ing)?\b"
    ],
    "import": [
        r"\bimport(?:s|ed|ing)?\b", r"\binput(?:s)?\b", r"\bfeed(?:s|ing)?\b", r"\bingest(?:s|ed|ion)?\b",
        r"\bsource(?:s|d)?\b", r"\bfetch(?:es|ed|ing)?\b", r"\bharvest(?:s|ed|ing)?\b"
    ],
    "routes": [
        r"\broute(?:s|d|ing)?\b", r"\bpath(?:s|way|ways)?\b", r"\bchange(?:s|d|ing)?\b",
        r"\bvariant(?:s)?\b", r"\bmutation(?:s)?\b", r"\btrajectory(?:ies)?\b", r"\breroute(?:s|d|ing)?\b"
    ],
    "investigate": [
        r"\binvestigate(?:s|d|ing)?\b", r"\bprobe(?:s|d|ing)?\b", r"\baudit(?:s|ed|ing)?\b",
        r"\binspect(?:s|ed|ion|ing)?\b", r"\bdiagnos(?:e|es|ed|is)\b", r"\bexplore(?:s|d|ing)?\b",
        r"\bverify(?:ies|ied|ing)?\b", r"\bvalidate(?:s|d|ion|ing)?\b"
    ],
    "ceo": [
        r"\bCEO\b", r"\blead(?:er|ers|ership|s)?\b", r"\bmanage(?:r|rs|ment|s)?\b",
        r"\bgovern(?:ance|ing|ed)?\b", r"\bexecutive(?:s)?\b", r"\bdirector(?:s)?\b"
    ]
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

HEADERS = {"User-Agent": "InfinityHarvester/3.0 (+Termux)"}

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

def crossref_query(term, rows=12) -> List[Dict]:
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

def pubmed_query(term, retmax=12) -> List[Dict]:
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

def synthetic_items(term, n=14) -> List[Dict]:
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
        f"Transition metal centers modulating {term}.",
        f"Heterogeneous catalysis and {term} in industrial processes.",
        f"Materials defects and {term} reliability."
    ]
    return [{"title": t, "abstract": t, "link": ""} for t in templ[:n]]

def harvest_sources(term) -> List[Dict]:
    items = []
    items += crossref_query(term, rows=14)
    items += pubmed_query(term, retmax=14)
    if len(items) < 10:
        items += synthetic_items(term, n=14)
    random.shuffle(items)
    return items[:random.randint(10, 30)]

# -----------------------------------
# Infinity rewrite + color decoration
# -----------------------------------

def tokenize_preserve(text: str) -> List[str]:
    # Split words but keep punctuation/spaces for reassembly
    # This simple tokenizer keeps non-word separators intact
    tokens = re.findall(r"\w+|\s+|[^\w\s]", text, flags=re.UNICODE)
    return tokens

def classify_word(word: str) -> str:
    lw = word.lower()
    if lw in STOPWORDS:
        return "reset"
    # Match semantic families
    for anchor, pats in FAMILIES.items():
        for pat in pats:
            if re.search(pat, word, flags=re.IGNORECASE):
                return anchor
    # Default heuristic: numbers → research; hyphenated tech → engineer
    if re.match(r"^\d+(\.\d+)?$", lw):
        return "research"
    if re.search(r"[A-Za-z]+-[A-Za-z]+", lw):
        return "engineer"
    return "research"  # default bias to research visibility

def colorize_words(text: str) -> str:
    tokens = tokenize_preserve(text)
    out = []
    for t in tokens:
        if re.match(r"^\w+$", t):  # word
            cat = classify_word(t)
            color = COLOR.get(cat, COLOR["research"])
            if cat == "reset":
                out.append(t)  # stopwords uncolored
            else:
                out.append(f"{color}{t}{COLOR['reset']}")
        else:
            out.append(t)  # punctuation/space intact
    return "".join(out)

def write_infinity_article(term: str, sources: List[Dict]) -> Dict[str, str]:
    # Title and sections
    title = f"Infinity Research on {term.capitalize()}: Multi‑source Synthesis and Semantic Routes"
    bullets = []
    for it in sources:
        title_i = (it.get("title") or "").strip()
        abstract_i = (it.get("abstract") or "").strip()
        if abstract_i and title_i:
            bullets.append(f"{title_i}: {abstract_i}")
        elif abstract_i:
            bullets.append(abstract_i)
        elif title_i:
            bullets.append(title_i)
    bullets = bullets[:80]

    sections = [
        f"{COLOR['engineer']}Engineer:{COLOR['reset']} Core constructs across d/p/f blocks and systems design.",
        f"{COLOR['research']}Research:{COLOR['reset']} Aggregated findings from {len(sources)} sources with quantitative signals.",
        f"{COLOR['assimilate']}Assimilate:{COLOR['reset']} Integrated correlations: electronegativity, ionization, radius, redox.",
        f"{COLOR['routes']}Routes:{COLOR['reset']} Emerging pathways, anomalies, and catalytic variants.",
        f"{COLOR['investigate']}Investigate:{COLOR['reset']} Audits, validations, and discrepancy probes.",
        f"{COLOR['import']}Import:{COLOR['reset']} Inputs synthesized from harvested links (kept in hashes).",
        f"{COLOR['ceo']}CEO:{COLOR['reset']} Anchoring token in Infinity ledger for governance."
    ]
    body_plain = "\n- " + "\n- ".join(bullets)
    # Apply word-level coloring to the entire composed body
    body_colored = colorize_words(body_plain)
    header_colored = "\n".join(sections)
    # Colorize the title (word-level, excluding stopwords)
    title_colored = colorize_words(title)
    article = f"{title_colored}\n\n{header_colored}\n\n{body_colored}"
    return {"title": title, "article": article}

# -------------------------
# Hashing, value, provenance
# -------------------------

def compute_master(links: List[str], research_text: str) -> str:
    orig_hash = sha256("\n".join(links))
    research_hash = sha256(research_text)
    combo_hash = orig_hash + research_hash
    return sha256(combo_hash)

def richness_value(article_plain: str, sources_count: int) -> int:
    # Heuristic value: density of colored words + cross-anchor diversity + sources_count
    # 1) Count non-stopword tokens
    words = re.findall(r"\w+", article_plain)
    content_words = [w for w in words if w.lower() not in STOPWORDS]
    base = len(content_words)

    # 2) Anchor hits
    anchor_hits = 0
    anchor_diversity = 0
    for anchor, pats in FAMILIES.items():
        hits = 0
        for pat in pats:
            hits += len(re.findall(pat, article_plain, flags=re.IGNORECASE))
        if hits > 0:
            anchor_diversity += 1
            anchor_hits += hits

    # 3) Sources multiplier
    src_factor = 1 + min(sources_count, 30) / 30.0

    # 4) Coherence bonus: diversity of anchors
    coherence = 1 + anchor_diversity / len(FAMILIES)

    # Raw score mapped to dollars (floor at 90)
    score = (base * 0.2 + anchor_hits * 0.5) * src_factor * coherence
    dollars = max(90, int(score))
    return dollars

def make_zipcoin_folder(index: int):
    folder = f"zip_coin_{index:05d}"
    path = os.path.join(ZIP_DIR, folder)
    os.makedirs(path, exist_ok=True)
    return folder, path

# ---------------
# Stream and batch
# ---------------

def stream_coin(token_idx: int, folder: str, master_hash: str, value_usd: int, title: str, article_colored: str):
    print(f"{STREAM['token']}[TOKEN {token_idx}/1000] {folder}{STREAM['reset']}")
    print(f"{STREAM['master']}[MASTER] {master_hash}{STREAM['reset']}")
    print(f"{STREAM['value']}[VALUE] ${value_usd}{STREAM['reset']}")
    print(f"{STREAM['title']}[TITLE]{STREAM['reset']} {title}")
    print(f"{STREAM['body']}[INFINITY RESEARCH]{STREAM['reset']} {article_colored}\n")

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

# -----------------
# Main stream loop
# -----------------

def main():
    os.makedirs(ZIP_DIR, exist_ok=True)
    os.makedirs(REPO, exist_ok=True)
    os.makedirs(BATCH_DIR, exist_ok=True)

    state = load_json(STATE_PATH, {
        "next_index": 0,
        "batch_index": 0,
        "current_batch_hashes": []
    })

    print("[INFINITY OS] Streaming multi-source, color-coded Infinity research. Ctrl+C to stop.")
    while True:
        try:
            term = random.choice(SEED_TERMS)
            sources = harvest_sources(term)
            links = [s.get("link","") for s in sources if s.get("link")]
            article = write_infinity_article(term, sources)
            title = article["title"]
            article_colored = article["article"]

            # Compute value based on plain text (remove ANSI to count accurately)
            plain_no_ansi = re.sub(r"\x1b\[[0-9;]*m", "", article_colored)
            value_usd = richness_value(plain_no_ansi, len(sources))

            folder, path = make_zipcoin_folder(state["next_index"])
            meta = {
                "topic": term,
                "links_count": len(links),
                "title": title,
                "value_usd": value_usd,
                "research": article_colored  # store colored for terminal experience
            }
            save_json(os.path.join(path, "meta.json"), meta)

            master_hash = compute_master(links, plain_no_ansi)

            token_idx = (len(state["current_batch_hashes"]) % 1000) + 1
            stream_coin(token_idx, folder, master_hash, value_usd, title, article_colored)

            state["current_batch_hashes"].append(master_hash)
            state["next_index"] += 1
            save_json(STATE_PATH, state)

            time.sleep(0.25)

            if finalize_batch_if_ready(state):
                save_json(STATE_PATH, state)
                git_push()

            time.sleep(0.6)
        except KeyboardInterrupt:
            print("\n[INFINITY OS] Stopped.")
            break
        except Exception as e:
            print(f"[INFINITY OS ERROR] {e}")
            time.sleep(1.0)

if __name__ == "__main__":
    main()
