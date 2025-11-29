#!/data/data/com.termux/files/usr/bin/python3
import os
import json

ZIP_DIR = "pewpi-infinity/z/zipcoins"

def load_zipcoins():
    coins = []
    for folder in sorted(os.listdir(ZIP_DIR)):
        if folder.startswith("zip_coin_"):
            path = os.path.join(ZIP_DIR, folder, "meta.json")
            if os.path.exists(path):
                with open(path, "r") as f:
                    data = json.load(f)
                coins.append({
                    "id": data["id"],
                    "color": data["color"],
                    "hash": data["hash"],
                    "folder": os.path.join(ZIP_DIR, folder)
                })
    return coins

def build_html(coin, all_coins):
    nav_links = ""
    for c in all_coins:
        if c["id"] != coin["id"]:
            nav_links += (
                f"<div style='padding:4px;'>"
                f"<a href='../{c['id']}/compiled.html' "
                f"style='color: #{c['color']}; font-weight: bold;'>"
                f"{c['id']} (#{c['color']})"
                f"</a></div>\n"
            )

    original_path = os.path.join(coin["folder"], "original.txt")
    with open(original_path, "r", encoding="utf-8", errors="ignore") as f:
        body = f.read().replace("\n", "<br>")

    html = f"""
<html>
<head>
<title>{coin['id']}</title>
<style>
body {{
    font-family: Arial;
    padding: 20px;
}}
.nav {{
    border: 1px solid #ccc;
    padding: 10px;
    margin-bottom: 20px;
}}
</style>
</head>
<body>
<h1>{coin['id']}</h1>
<h3>Color Key: <span style="color: #{coin['color']};">#{coin['color']}</span></h3>
<div class="nav">
<h3>Cross‑Links</h3>
{nav_links}
</div>
<div>
<h3>Article</h3>
<p>{body}</p>
</div>
</body>
</html>
"""
    return html

def main():
    print("[CROSSLINK] Loading zipcoins...")
    coins = load_zipcoins()

    for coin in coins:
        html = build_html(coin, coins)
        outpath = os.path.join(coin["folder"], "compiled.html")
        with open(outpath, "w", encoding="utf-8", errors="ignore") as f:
            f.write(html)

        print(f"[CROSSLINK] Added navigation + compiled HTML to {coin['id']}")

    print("[CROSSLINK] All zipcoins updated successfully.")

if __name__ == "__main__":
    main()
