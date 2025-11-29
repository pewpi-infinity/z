import os
import random
from pathlib import Path

ZIPCOIN_DIR = Path("pewpi-infinity/z/zipcoins")

def load_zipcoins():
    folders = sorted([d for d in ZIPCOIN_DIR.iterdir() if d.is_dir()])
    return folders

def build_links(index, total, folders):
    current = index
    prev_link = folders[current - 1].name if current > 0 else None
    next_link = folders[current + 1].name if current < total - 1 else None
    random_link = random.choice(folders).name

    return prev_link, next_link, random_link

def generate_html(original, research, chain, name, prev_link, next_link, random_link):
    nav_html = "<div style='margin-bottom:20px;'>"

    if prev_link:
        nav_html += f"<a href='../{prev_link}/compiled.html' style='margin-right:15px;color:#2980b9;'>← Previous</a>"
    if next_link:
        nav_html += f"<a href='../{next_link}/compiled.html' style='margin-right:15px;color:#27ae60;'>Next →</a>"

    nav_html += f"<a href='../{random_link}/compiled.html' style='color:#e67e22;'>Random 🔗</a>"
    nav_html += "</div>"

    return f"""
<html><body style="font-family: sans-serif; line-height:1.6;">
<h2 style="color:#9b59b6;">{name}</h2>
{nav_html}

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

{nav_html}

</body></html>
"""

def process_links():
    folders = load_zipcoins()
    total = len(folders)

    if total == 0:
        print("[CROSSLINK] No zip coins found.")
        return

    for index, folder in enumerate(folders):
        original = (folder / "original.txt").read_text()
        research = (folder / "research.txt").read_text()
        chain = (folder / "chain.txt").read_text()

        prev_link, next_link, random_link = build_links(index, total, folders)

        html = generate_html(
            original,
            research,
            chain,
            folder.name,
            prev_link,
            next_link,
            random_link
        )

        (folder / "compiled.html").write_text(html)

        print(f"[CROSSLINK] Added navigation + compiled HTML to {folder.name}")

    print("[CROSSLINK] All zip coins updated with cross‑links.")

if __name__ == "__main__":
    process_links()
