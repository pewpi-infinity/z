#!/usr/bin/env python3
import os, json, hashlib, time, subprocess, zipfile, random
import requests
from bs4 import BeautifulSoup

ROOT = os.path.expanduser("~/z")
ZIP_DIR = os.path.join(ROOT, "zipcoins")
REPO = os.path.join(ROOT, "pewpi-infinity/z")
BATCH_DIR = os.path.join(ROOT, "batches")
STATE_PATH = os.path.join(ROOT, ".harvest_stream_state.json")

# Minimal colors for visibility
C = {
    "research": "\033[93m",  # yellow for research text
    "master":   "\033[91m",  # red for master hash
    "token":    "\033[94m",  # blue for token counter
    "reset":    "\033[0m"
}

# Seed topics: periodic table + core science concepts
SEED_TERMS = [
    "periodic table trends", "transition metals catalysis", "lanthanides spectroscopy",
    "alkali metals reactivity", "halogens oxidation states", "noble gases applications",
    "electronegativity and bonding", "ionization energy correlations", "atomic radius trends",
    "d-block chemistry", "p-block chemistry", "f-block chemistry", "coordination complexes",
    "crystal field theory", "organometallic chemistry", "solid state chemistry",
    "materials science band structure", "semiconductor doping", "surface chemistry adsorption"
]

HEADERS = {"User-Agent": "InfinityHarvester/1.0 (+Termux)"}

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

def crossref_query(term, rows=5):
    url = "https://api.crossref.org/works"
    params = {"query": term, "rows": rows, "filter": "type:journal-article"}
    try:
        r = requests.get(url, params=params, headers=HEADERS, timeout=15)
        r.raise_for_status()
        data = r.json()
        items = []
        for it in data.get("message", {}).get("items", []):
            title = " ".join(it.get("title", [])).strip() or term
            abstract_html = it.get("abstract", "") or ""
            abstract = BeautifulSoup(abstract_html, "html.parser").get_text().strip() if abstract_html else ""
            link = (it.get("URL") or "")
            if not abstract:
                # Try short description from container-title or subject
                subj = ", ".join(it.get("subject", [])[:4])
                abstract = f"{title} — {subj}".strip()
            if title or abstract or link:
                items.append({"title": title, "abstract": abstract, "link": link})
        return items
    except Exception:
        return []

def pubmed_query(term, retmax=5):
    # Fetch PubMed IDs then details
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
            abstract = rec.get("sortpubdate", "")
            # Attempt to fetch abstract page text (best effort)
            try:
                page = requests.get(link, headers=HEADERS, timeout=10)
                if page.ok:
                    soup = BeautifulSoup(page.text, "html.parser")
                    abst = soup.select_one(".abstract-content")
                    if abst:
                        abstract = abst.get_text(" ", strip=True)
            except Exception:
                pass
            if title or abstract:
                items.append({"title": title, "abstract": abstract, "link": link})
        return items
    except Exception:
        return []

def harvest_one():
    term = random.choice(SEED_TERMS)
    items = crossref_query(term, rows=5)
    if not items:
        items = pubmed_query(term, retmax=5)
    # If still empty, fallback to a synthetic research entry using the term
    if not items:
        items = [{"title": term, "abstract": f"Exploratory notes on {term}.",
                  "link": ""}]
    return term, items

def make_zipcoin_folder(index):
    folder = f"zip_coin_{index:05d}"
    path = os.path.join(ZIP_DIR, folder)
    os.makedirs(path, exist_ok=True)
    return folder, path

def build_research_text(item):
    # Compose a single research text blob
    parts = []
    if item.get("title"):
        parts.append(item["title"])
    if item.get("abstract"):
        parts.append(item["abstract"])
    if item.get("link"):
        parts.append(f"Source: {item['link']}")
    return "\n\n".join(parts).strip()

def compute_master_from_meta(meta):
    # master = sha256( sha256(link) + sha256(research) )
    h_link = sha256(meta.get("link", ""))
    h_res = sha256(meta.get("research", ""))
    return sha256(h_link + h_res)

def stream_coin(token_idx, folder, master_hash, research_text):
    print(f"{C['token']}[TOKEN {token_idx}/1000] {folder}{C['reset']}")
    print(f"{C['master']}[MASTER] {master_hash}{C['reset']}")
    print(f"{C['research']}[RESEARCH]{C['reset']} {research_text}\n")

def finalize_batch_if_ready(state):
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

    summary_path = os.path.join(batch_folder, "summary.json")
    save_json(summary_path, {
        "batch_index": batch_index,
        "major_master_hash": major_master
    })

    # Zip it
    zip_name = os.path.join(BATCH_DIR, f"major_master_{batch_index:04d}.zip")
    with zipfile.ZipFile(zip_name, "w", compression=zipfile.ZIP_DEFLATED) as z:
        z.write(ledger_path, arcname="batch_ledger.json")
        z.write(summary_path, arcname="summary.json")

    # Marker in repo for fast diff
    marker_path = os.path.join(REPO, f"major_master_{batch_index:04d}.json")
    save_json(marker_path, {"major_master_hash": major_master, "batch_index": batch_index})

    # Reset batch window
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
        "next_index": 0,
        "batch_index": 0,
        "current_batch_hashes": []
    })

    print("[HARVEST] Streaming research. Press Ctrl+C to stop.")
    while True:
        try:
            # Harvest a small set of items per iteration
            term, items = harvest_one()
            for item in items:
                folder, path = make_zipcoin_folder(state["next_index"])
                research_text = build_research_text(item)
                meta = {
                    "topic": term,
                    "link": item.get("link", ""),
                    "research": research_text
                }
                save_json(os.path.join(path, "meta.json"), meta)

                # Compute master hash
                master_hash = compute_master_from_meta(meta)

                # Token number in current batch (1..1000)
                token_idx = (len(state["current_batch_hashes"]) % 1000) + 1

                # Stream ONLY: token, master hash, full research
                stream_coin(token_idx, folder, master_hash, research_text)

                # Append to batch
                state["current_batch_hashes"].append(master_hash)
                state["next_index"] += 1
                save_json(STATE_PATH, state)

                time.sleep(0.15)

                # Finalize every 1000
                if finalize_batch_if_ready(state):
                    save_json(STATE_PATH, state)
                    git_push()

            # Idle pace
            time.sleep(0.8)
        except KeyboardInterrupt:
            print("\n[HARVEST] Stopped.")
            break
        except Exception as e:
            print(f"[HARVEST ERROR] {e}")
            time.sleep(1.0)

if __name__ == "__main__":
    main()
