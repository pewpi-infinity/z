#!/usr/bin/env python3
import subprocess, os, time, sys

# Your REAL repo path
REPO_PATH = "/data/data/com.termux/files/home/z"

def run(cmd):
    print(f"[RUN] {cmd}")
    return subprocess.run(cmd, shell=True)

def main():
    print("∞ Infinity GitHub Push Cart Online ∞")
    print("Using repo path:", REPO_PATH)

    if not os.path.isdir(REPO_PATH):
        print("❌ ERROR: Repo path does not exist.")
        sys.exit(1)

    os.chdir(REPO_PATH)

    print("\n→ Checking git status…")
    run("git status")

    print("\n→ Adding all files…")
    run("git add -A")

    ts = time.strftime("%Y-%m-%d %H:%M:%S")
    commit_msg = f"AUTO-PUSH: {ts}"

    print("\n→ Committing…")
    run(f"git commit -m '{commit_msg}'")

    print("\n→ Pushing to GitHub (origin/main)…")
    run("git push origin main")

    print("\n∞ COMPLETE — Everything synced to GitHub ∞")

if __name__ == '__main__':
    main()
