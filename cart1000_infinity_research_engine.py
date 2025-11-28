#!/usr/bin/env python3
import os
import json
import time
import uuid
import re
import zipfile
import subprocess
from datetime import datetime, timezone

import requests
from bs4 import BeautifulSoup
from colorama import init, Fore, Style

# ====================================================
# CONFIG
# ====================================================
BASE_DIR = os.path.expanduser("~/z")   # YOUR GITHUB REPO ROOT

TOKENS_DIR = os.path.join(BASE_DIR, "infinity_tokens")
ZIPS_DIR = os.path.join(BASE_DIR, "infinity_zips")
COUNTER_FILE = os.path.join(BASE_DIR, "infinity_token_counter.json")
SOURCES_FILE = os.path.join(BASE_DIR, "research_sources.txt")

MAX_SENTENCES = 14
TOKENS_PER_BATCH = 1000
VALUE_MULTIPLIER = 2.5

DEFAULT_SOURCES = [
    "https://en.wikipedia.org/wiki/Biosphere",
    "https://en.wikipedia.org/wiki/Ecosystem",
    "https://en.wikipedia.org/wiki/Aluminium_oxide",
    "https://en.wikipedia.org/wiki/Thermoelectric_effect"
]

COLOR_CYCLE = [
    Fore.YELLOW, Fore.CYAN, Fore.MAGENTA, Fore.GREEN, Fore.WHITE
]

TIERS = [
    ("STANDARD", 0),
    ("PREMIER", 1000),
    ("ELITE", 5000),
    ("MYTHIC", 20000)
]

init(autoreset=True)

# ====================================================
# UTILITIES
# ====================================================
def ensure_dirs():
    os.makedirs(TOKENS_DIR, exist_ok=True)
    os.makedirs(ZIPS_DIR, exist_ok=True)

def load_counter():
    if not os.path.exists(COUNTER_FILE):
        return {"total_tokens":0,"total_capsules":0,"batch_index":0}
    try:
        with open(COUNTER_FILE,"r") as f:
            return json.load(f)
    except:
        return {"total_tokens":0,"total_capsules":0,"batch_index":0}

def save_counter(c):
    with open(COUNTER_FILE,"w") as f:
        json.dump(c,f,indent=2)

# ====================================================
# AUTO GIT PUSH
# ====================================================
def git_push():
    """Automatically commit + push everything to GitHub."""
    try:
        subprocess.run(["git","add","."], cwd=BASE_DIR)
        subprocess.run([
            "git","commit","-m",f"∞ Scroll update {datetime.now().isoformat()}"
        ], cwd=BASE_DIR, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        subprocess.run(["git","push","origin","main"], cwd=BASE_DIR)
        print(Fore.GREEN + "[GIT] Repo synced successfully.")
    except Exception as e:
        print(Fore.RED + f"[GIT] FAILED: {e}")

# ====================================================
# SCRAPER FUNCTIONS
# ====================================================
def iter_sources():
    if os.path.exists(SOURCES_FILE):
        with open(SOURCES_FILE,"r") as f:
            for line in f:
                u = line.strip()
                if u: yield u
    else:
        for u in DEFAULT_SOURCES:
            yield u

def fetch(u):
    try:
        r = requests.get(u,headers={"User-Agent":"Infinity/1.0"},timeout=20)
        r.raise_for_status()
        return r.text
    except:
        return None

def extract(html):
    if not html:
        return ""
    soup = BeautifulSoup(html,"html.parser")
    paras = soup.find_all("p")
    return " ".join([p.get_text(" ",strip=True) for p in paras])

def split_sentences(text):
    text = re.sub(r"\s+"," ",text)
    return re.split(r"(?<=[.!?])\s+", text)

def token_est(s):
    return max(1,int(len(s.split())*1.3))

def tier_for(v):
    t = TIERS[0][0]
    for name,req in TIERS:
        if v >= req:
            t = name
    return t

def flush_batch(batch, idx):
    if not batch:
        return
    name = f"infinity_batch_{idx:05d}.zip"
    path = os.path.join(ZIPS_DIR,name)
    with zipfile.ZipFile(path,"w",zipfile.ZIP_DEFLATED) as z:
        for c in batch:
            z.writestr(f"{c['hash']}.json",json.dumps(c,indent=2))
    print(Fore.GREEN + f"[SCROLL SEALED] {name}")
    git_push()

def pretty(c, counter, nxt):
    print(Fore.CYAN + "-"*72)
    print(Fore.CYAN + f"INF HASH : {c['hash']}")
    print(Fore.YELLOW + f"VALUE    : ${c['value']}")
    print(Fore.MAGENTA + f"TIER     : {c['tier']}")
    print(Fore.GREEN + f"SOURCE   : {c['source']}")
    print(Fore.WHITE + f"TIME     : {c['timestamp']}")
    print(Fore.CYAN + "-"*72)

    for i,s in enumerate(c["sentences"]):
        print(COLOR_CYCLE[i % len(COLOR_CYCLE)] + "  " + s)

    if c.get("notes"):
        print(Fore.LIGHTMAGENTA_EX + "\n  [YOUR NOTES]")
        print(Fore.LIGHTMAGENTA_EX + "  " + c["notes"])

    print(Fore.CYAN + "-"*72)
    print(Fore.YELLOW + f"TOTAL TOKENS: {counter['total_tokens']} (next zip at {nxt})")
    print(Fore.CYAN + "-"*72 + "\n")

# ====================================================
# MAIN ENGINE
# ====================================================
def main():
    ensure_dirs()
    counter = load_counter()
    batch = []

    print(Fore.GREEN + "\n∞ Infinity Research Engine — ONLINE ∞\n")

    for url in iter_sources():
        html = fetch(url)
        text = extract(html)
        sents = split_sentences(text)

        if not sents:
            sents = ["No extractable text was found at fetch time."]

        sents = sents[:MAX_SENTENCES]

        h = uuid.uuid4().hex
        ts = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")

        toks = sum(token_est(s) for s in sents)
        val = int(toks * VALUE_MULTIPLIER)
        tier = tier_for(val)

        title = url.rsplit("/",1)[-1].replace("_"," ").upper()

        capsule = {
            "hash":h,
            "source":url,
            "timestamp":ts,
            "title":f"{title} – RESEARCH PAGE",
            "sentences":sents,
            "approx_tokens":toks,
            "value":val,
            "tier":tier
        }

        try:
            print(Fore.BLUE + f"\nAdd Infinity notes for {title} (Enter to skip):")
            notes = input("> ").strip()
            if notes:
                capsule["notes"] = notes
        except:
            pass

        counter["total_capsules"] += 1
        counter["total_tokens"] += toks

        next_cutoff = ((counter["total_tokens"] // TOKENS_PER_BATCH)+1)*TOKENS_PER_BATCH

        # write token json
        path = os.path.join(TOKENS_DIR,f"{h}.json")
        with open(path,"w") as f:
            json.dump(capsule,f,indent=2)

        batch.append(capsule)
        pretty(capsule,counter,next_cutoff)

        # seal scroll
        if counter["total_tokens"] >= next_cutoff:
            flush_batch(batch,counter["batch_index"])
            batch = []
            counter["batch_index"] += 1

        save_counter(counter)
        git_push()
        time.sleep(1)

    # flush remaining
    if batch:
        flush_batch(batch,counter["batch_index"])
        counter["batch_index"] += 1

    save_counter(counter)
    print(Fore.GREEN + "\n∞ Infinity Research Engine — COMPLETE ∞\n")


if __name__ == "__main__":
    main()
