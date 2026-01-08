#!/usr/bin/env python3
import os, json

REPO_DIR = os.path.expanduser("~/z")
TOKENS_DIR = os.path.join(REPO_DIR, "tokens")
BUFFER = os.path.join(REPO_DIR, "session_buffer.json")

def main():
    print("∞ Infinity Ingest Buffer (Cart 081) Online")

    if not os.path.exists(BUFFER):
        print("[!] No buffer found. Nothing to ingest.")
        return

    buf = json.load(open(BUFFER))
    pending = buf.get("pending", [])

    if not pending:
        print("[!] Buffer empty. Nothing waiting for valuation.")
        return

    print(f"[∞] Tokens waiting for valuation: {len(pending)}")
    for p in pending:
        print("   →", p)

    print("\nRun Cart 082 to process valuations.")

if __name__ == "__main__":
    main()
