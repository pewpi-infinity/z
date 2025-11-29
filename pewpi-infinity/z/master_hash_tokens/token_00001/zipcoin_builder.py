import os
import hashlib
from pathlib import Path

RAW_DIR = Path("pewpi-infinity/z/raw_sources")
OUTPUT_DIR = Path("pewpi-infinity/z/zipcoins")

def ensure_dirs():
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

def rewrite_research(text):
    # Simple placeholder rewrite. Replace with your algo later.
    return " ".join(word.lower() for word in text.split())

def build_chain_metadata(index, total):
    return f"zip_coin_index: {index}\ntotal_zipcoins: {total}\nhash_label: HASH-3\n"

def make_compiled_html(original, research, chain, index):
    return f"""
<html><body style="font-family: sans-serif; line-height:1.6;">
<h2 style="color:#9b59b6;">ZIP COIN #{index}</h2>

<div style="border-left:4px solid #3498db; padding:10px; margin-bottom:20px;">
<h3 style="color:#3498db;">Original Extract (HASH 1)</h3>
<pre>{original}</pre>
</div>

<div style="border-left:4px solid #2ecc71; padding:10px; margin-bottom:20px;">
<h3 style="color:#2ecc71;">Rewritten Research (HASH 2)</h3>
<pre>{research}</pre>
</div>

<div style="border-left:4px solid #e67e22; padding:10px; margin-bottom:20px;">
<h3 style="color:#e67e22;">Chain Metadata (HASH 3)</h3>
<pre>{chain}</pre>
</div>

</body></html>
"""

def process_raw_sources():
    ensure_dirs()
    raw_files = sorted(list(RAW_DIR.glob("raw_*.txt")))
    total = len(raw_files)

    for idx, raw_path in enumerate(raw_files, start=1):
        text = raw_path.read_text()

        original = text
        research = rewrite_research(text)
        chain = build_chain_metadata(idx, total)

        folder = OUTPUT_DIR / f"zip_coin_{idx:05d}"
        folder.mkdir(parents=True, exist_ok=True)

        (folder / "original.txt").write_text(original)
        (folder / "research.txt").write_text(research)
        (folder / "chain.txt").write_text(chain)
        (folder / "compiled.txt").write_text(
            f"=== ORIGINAL (HASH1) ===\n{original}\n\n"
            f"=== RESEARCH (HASH2) ===\n{research}\n\n"
            f"=== CHAIN (HASH3) ===\n{chain}\n"
        )
        (folder / "compiled.html").write_text(
            make_compiled_html(original, research, chain, idx)
        )

        print(f"[ZIPCOIN] Built zip_coin_{idx:05d}")

    print("[ZIPCOIN] All zip coins built and saved to pewpi-infinity/z/zipcoins/")

if __name__ == "__main__":
    process_raw_sources()
