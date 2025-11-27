#!/usr/bin/env python3
import os, json, subprocess

ROOT = os.getcwd()
TOKENS = os.path.join(ROOT, "tokens")

ROLES = {
    "engineer": "Engineer (Green)",
    "ceo": "CEO (Orange)",
    "import": "Import (Blue)",
    "investigate": "Investigate (Pink)",
    "routes": "Routes (Red)",
    "data": "Data (Yellow)",
    "assim": "Assimilation (Purple)"
}

def ensure_folders():
    if not os.path.exists(TOKENS):
        os.makedirs(TOKENS)
    for role in ROLES:
        path = os.path.join(TOKENS, role)
        if not os.path.exists(path):
            os.makedirs(path)

def build_role_page(role):
    folder = os.path.join(TOKENS, role)
    files = os.listdir(folder)
    entries = []

    for f in files:
        if f.endswith(".json"):
            entries.append(f"<li><a href='../tokens/{role}/{f}' target='_blank'>{f}</a></li>")

    list_html = "\n".join(entries) if entries else "<p>No pages yet.</p>"

    html = f"""
<!DOCTYPE html>
<html>
<head>
<meta charset='UTF-8'/>
<title>{ROLES[role]}</title>
<style>
body {{
  background:#0a1222;
  color:#d0d8ff;
  font-family:Arial;
  padding:20px;
}}
a {{
  color:#9cc4ff;
}}
</style>
</head>
<body>
<h1>{ROLES[role]}</h1>
<p>Role Token Folder: <b>{role}</b></p>
<ul>
{list_html}
</ul>
<p><a href='../index.html'>⬅ Back to Portal</a></p>
</body>
</html>
"""

    with open(f"{role}.html", "w") as f:
        f.write(html)


def build_all():
    ensure_folders()
    for role in ROLES:
        build_role_page(role)

def git_push():
    subprocess.run(["git", "add", "."])
    subprocess.run(["git", "commit", "-m", "Infinity frontend routing fix"])
    subprocess.run(["git", "push"])

if __name__ == "__main__":
    build_all()
    git_push()
