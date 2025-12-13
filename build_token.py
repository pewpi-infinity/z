#!/usr/bin/env python3
"""
Build Your Own Token System - Token creation with content analysis and valuation
Part of the Pewpi Login / Infinity Research Portal
"""

import os
import json
import hashlib
import datetime
import math
import base64
import re
from datetime import timezone

# ------------------------------ CONFIG ------------------------------
Z_ROOT = os.path.abspath(os.path.dirname(__file__))
TOKENS_DIR = os.path.join(Z_ROOT, "tokens")
SESSION_BUFFER = os.path.join(Z_ROOT, "session_buffer.json")

os.makedirs(TOKENS_DIR, exist_ok=True)

# ------------------------------ SCORING KEYWORDS ----------------------
# Keywords that boost content value based on research importance
BOOST_KEYWORDS = {
    # Tier 1: Critical Research ($500+ per occurrence)
    "quantum": 500,
    "hydrogen": 500,
    "fusion": 500,
    "einstein": 500,
    "relativity": 500,
    "infinity": 500,
    "neural": 450,
    "photon": 450,
    "plasma": 450,
    "electron": 450,
    # Tier 2: High Value ($300+ per occurrence)
    "vector": 300,
    "tensor": 300,
    "gravity": 300,
    "reactor": 300,
    "lattice": 300,
    "thermodynamics": 300,
    "entropy": 300,
    # Tier 3: Significant ($150+ per occurrence)
    "ai": 150,
    "algorithm": 150,
    "compute": 150,
    "research": 150,
    "discovery": 150,
    "patent": 150,
    "proprietary": 150,
    # Tier 4: Notable ($75+ per occurrence)
    "data": 75,
    "analysis": 75,
    "model": 75,
    "theory": 75,
    "experiment": 75,
    # Special Keywords (Mega Value)
    "kris": 10000,
    "pewpi": 10000,
    "hydra": 8000,
    "osprey": 8000,
    "classified": 15000,
    "secret": 12000,
}

# Value range constants
MIN_VALUE = 90
MAX_VALUE = 964_590_650_869_860_860.97


def get_timestamp():
    """Get current UTC timestamp."""
    return datetime.datetime.now(timezone.utc).isoformat().replace('+00:00', 'Z')


def infinity_hash(text):
    """Generate SHA-256 hash for content."""
    return hashlib.sha256(text.encode()).hexdigest()


def vector_position(seed):
    """Return a stable (x,y,z) vector coordinate for the token."""
    h = int(seed[:12], 16)
    return {
        "x": round((h % 997) / 997, 6),
        "y": round((h % 613) / 613, 6),
        "z": round((h % 409) / 409, 6)
    }


def score_content(text):
    """
    Score content based on:
    - Length/depth of content
    - Keyword matches (research importance)
    - File type bonuses
    - Uniqueness factor
    """
    score = 0
    analysis = {
        "word_count": 0,
        "char_count": 0,
        "keyword_matches": {},
        "depth_bonus": 0,
        "complexity_bonus": 0
    }

    # Cache computed values to avoid redundant calculations
    text_lower = text.lower()
    words = text_lower.split()
    char_count = len(text)
    word_count = len(words)

    # Base scores
    analysis["char_count"] = char_count
    analysis["word_count"] = word_count

    # Character count base score
    score += char_count * 0.5

    # Word count score
    score += word_count * 2

    # Keyword matching with tier bonuses - use regex for better performance
    for keyword, bonus in BOOST_KEYWORDS.items():
        # Use word boundary matching for more accurate counts
        count = len(re.findall(r'\b' + re.escape(keyword) + r'\b', text_lower))
        if count > 0:
            keyword_score = count * bonus
            score += keyword_score
            analysis["keyword_matches"][keyword] = {
                "count": count,
                "bonus": keyword_score
            }

    # Depth bonus - exponential scaling for long content
    if char_count > 100:
        depth = int(math.log(char_count, 2) * 100)
        score += depth
        analysis["depth_bonus"] = depth

    # Complexity bonus - based on unique words ratio
    if word_count > 0:
        unique_ratio = len(set(words)) / word_count
        complexity = int(unique_ratio * 1000)
        score += complexity
        analysis["complexity_bonus"] = complexity

    # Line count bonus (structured content)
    lines = text.split('\n')
    line_count = len(lines)
    if line_count > 5:
        score += line_count * 10

    return score, analysis


def calculate_value(score):
    """
    Calculate token value from score.
    Range: $90 - $964,590,650,869,860,860.97
    """
    if score < 100:
        return MIN_VALUE + (score * 0.5)

    if score < 500:
        return 100 + (score * 2)

    if score < 2000:
        return 1000 + (score * 10)

    if score < 10000:
        return 20000 + (score * 100)

    if score < 100000:
        return 1000000 + (score * 5000)

    if score < 1000000:
        return 500000000 + (score * 100000)

    # Exponential scaling for extremely high scores
    base = 100_000_000_000
    multiplier = math.log(score, 10) * 100_000_000_000

    value = min(base + multiplier * (score / 1000000), MAX_VALUE)
    return value


def format_value(value):
    """Format value as currency string."""
    if value >= 1_000_000_000_000:
        return f"${value:,.2f}"
    elif value >= 1_000_000_000:
        return f"${value/1_000_000_000:.2f}B"
    elif value >= 1_000_000:
        return f"${value/1_000_000:.2f}M"
    elif value >= 1000:
        return f"${value/1000:.2f}K"
    else:
        return f"${value:.2f}"


def build_token(text, source_type="text", filename=None):
    """
    Build a token from user input.

    Args:
        text: The content to tokenize
        source_type: "text", "file", or "paste"
        filename: Original filename if from file upload

    Returns:
        Token object with hash, value, and metadata
    """
    # Generate hash
    token_hash = infinity_hash(text + str(datetime.datetime.now(timezone.utc)))

    # Score content
    score, analysis = score_content(text)

    # Calculate value
    value = calculate_value(score)

    # Build token object
    token = {
        "hash": token_hash,
        "timestamp": get_timestamp(),
        "source_type": source_type,
        "filename": filename,
        "raw_text": text,
        "score": score,
        "value": value,
        "value_formatted": format_value(value),
        "vector": vector_position(token_hash),
        "analysis": analysis
    }

    # Save token to file
    token_path = os.path.join(TOKENS_DIR, f"{token_hash}.json")
    with open(token_path, "w") as f:
        json.dump(token, f, indent=4)

    # Add to session buffer for valuation pipeline
    add_to_buffer(token_hash)

    return token


def add_to_buffer(token_hash):
    """Add token hash to session buffer for processing."""
    buffer = {"pending": []}
    if os.path.exists(SESSION_BUFFER):
        with open(SESSION_BUFFER, "r") as f:
            buffer = json.load(f)

    if token_hash not in buffer.get("pending", []):
        buffer.setdefault("pending", []).append(token_hash)

    with open(SESSION_BUFFER, "w") as f:
        json.dump(buffer, f, indent=4)


def process_file_upload(file_content, filename):
    """
    Process uploaded file content.

    Args:
        file_content: Base64 encoded file content or raw text
        filename: Name of the uploaded file

    Returns:
        Token object
    """
    try:
        # Try to decode base64
        decoded = base64.b64decode(file_content).decode('utf-8')
    except (TypeError, ValueError):
        # If not base64, use as-is
        decoded = file_content

    return build_token(decoded, source_type="file", filename=filename)


# ------------------------------ MEGA HASH -----------------------------
def generate_mega_hash(token_hashes, description=""):
    """
    Generate a Mega Hash by combining multiple token hashes.
    Mega hashes indicate important content aggregations with
    dynamically calculated high-value outcomes ($963B+).

    Args:
        token_hashes: List of token hashes to combine
        description: Optional description of the mega hash

    Returns:
        Mega hash object with combined value
    """
    if len(token_hashes) < 2:
        return {"error": "Need at least 2 tokens to create a mega hash"}

    # Load and combine token data
    combined_text = ""
    total_score = 0
    token_data = []

    for th in token_hashes:
        token_path = os.path.join(TOKENS_DIR, f"{th}.json")
        if os.path.exists(token_path):
            with open(token_path, "r") as f:
                data = json.load(f)
                combined_text += data.get("raw_text", "") + "\n---\n"
                total_score += data.get("score", 0)
                token_data.append(data)

    # Generate mega hash
    mega_hash = infinity_hash(combined_text + str(datetime.datetime.now(timezone.utc)) + "MEGA")

    # Mega hash scoring - exponential combination bonus
    combination_bonus = len(token_hashes) * 1_000_000
    synergy_bonus = math.pow(len(token_hashes), 3) * 10_000_000

    mega_score = total_score + combination_bonus + synergy_bonus

    # Calculate mega value - minimum $963B for valid mega hashes
    base_mega_value = 963_000_000_000  # $963 billion base
    scale_factor = mega_score / 1000
    mega_value = base_mega_value + (scale_factor * 1_000_000_000)

    # Cap at max value
    mega_value = min(mega_value, MAX_VALUE)

    mega_token = {
        "mega_hash": mega_hash,
        "component_hashes": token_hashes,
        "component_count": len(token_hashes),
        "description": description,
        "timestamp": get_timestamp(),
        "combined_score": mega_score,
        "value": mega_value,
        "value_formatted": format_value(mega_value),
        "vector": vector_position(mega_hash),
        "type": "MEGA_HASH"
    }

    # Save mega token
    mega_path = os.path.join(TOKENS_DIR, f"MEGA_{mega_hash}.json")
    with open(mega_path, "w") as f:
        json.dump(mega_token, f, indent=4)

    return mega_token


# ------------------------------ CLI INTERFACE -------------------------
def main():
    """Interactive CLI for Build Your Own Token."""
    print("∞ Build Your Own Token - Infinity Research Portal ∞")
    print("=" * 50)
    print("Commands:")
    print("  build   - Create a token from text input")
    print("  mega    - Create a mega hash from existing tokens")
    print("  list    - List existing tokens")
    print("  quit    - Exit")
    print("=" * 50)

    while True:
        cmd = input("\n> ").strip().lower()

        if cmd == "build":
            print("\nEnter/paste your content. End with a blank line:")
            lines = []
            while True:
                try:
                    line = input()
                    if not line.strip():
                        break
                    lines.append(line)
                except EOFError:
                    break

            text = "\n".join(lines).strip()
            if not text:
                print("[!] No content provided.")
                continue

            token = build_token(text, source_type="text")
            print(f"\n[∞] TOKEN CREATED")
            print(f"    Hash: {token['hash']}")
            print(f"    Score: {token['score']}")
            print(f"    Value: {token['value_formatted']}")
            print(f"    Vector: {token['vector']}")

        elif cmd == "mega":
            print("\nEnter token hashes to combine (one per line, blank to finish):")
            hashes = []
            while True:
                h = input("  Hash: ").strip()
                if not h:
                    break
                hashes.append(h)

            if len(hashes) < 2:
                print("[!] Need at least 2 tokens for mega hash.")
                continue

            desc = input("Description (optional): ").strip()
            mega = generate_mega_hash(hashes, desc)

            if "error" in mega:
                print(f"[!] {mega['error']}")
            else:
                print(f"\n[∞] MEGA HASH CREATED")
                print(f"    Mega Hash: {mega['mega_hash']}")
                print(f"    Components: {mega['component_count']}")
                print(f"    Value: {mega['value_formatted']}")

        elif cmd == "list":
            tokens = os.listdir(TOKENS_DIR)
            print(f"\n[∞] {len(tokens)} tokens in repository:")
            for t in tokens[:10]:
                print(f"    {t}")
            if len(tokens) > 10:
                print(f"    ... and {len(tokens) - 10} more")

        elif cmd == "quit":
            print("Goodbye!")
            break

        else:
            print("Unknown command. Use: build, mega, list, quit")


if __name__ == "__main__":
    main()
