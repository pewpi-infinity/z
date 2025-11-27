#!/usr/bin/env python3
"""
Pewpi Login System - User authentication and token counting for Infinity Research Portal
"""

import os
import json
import hashlib
import datetime
import secrets
import math
from datetime import timezone

# ------------------------------ CONFIG ------------------------------
Z_ROOT = os.path.abspath(os.path.dirname(__file__))
USERS_FILE = os.path.join(Z_ROOT, "users.json")
TOKENS_DIR = os.path.join(Z_ROOT, "tokens")

# Ensure tokens directory exists
os.makedirs(TOKENS_DIR, exist_ok=True)

# ------------------------------ STORAGE ------------------------------
def load_users():
    """Load users data from JSON file."""
    if os.path.exists(USERS_FILE):
        with open(USERS_FILE, "r") as f:
            return json.load(f)
    return {"users": {}, "sessions": {}}


def save_users(data):
    """Save users data to JSON file."""
    with open(USERS_FILE, "w") as f:
        json.dump(data, f, indent=4)


# ------------------------------ HELPERS ------------------------------
def hash_password(password):
    """Create secure hash of password."""
    return hashlib.sha256(password.encode()).hexdigest()


def generate_session_token():
    """Generate a secure session token."""
    return secrets.token_hex(32)


def get_timestamp():
    """Get current UTC timestamp."""
    return datetime.datetime.now(timezone.utc).isoformat().replace('+00:00', 'Z')


# ------------------------------ USER MANAGEMENT -----------------------
def register_user(username, password):
    """Register a new user."""
    data = load_users()

    if username in data["users"]:
        return {"success": False, "error": "Username already exists"}

    data["users"][username] = {
        "password_hash": hash_password(password),
        "token_count": 0,
        "tokens_created": [],
        "mega_hashes": [],
        "created_at": get_timestamp(),
        "last_login": None
    }

    save_users(data)
    return {"success": True, "message": f"User '{username}' registered successfully"}


def sign_in(username, password):
    """Sign in a user and create a session."""
    data = load_users()

    if username not in data["users"]:
        return {"success": False, "error": "User not found"}

    user = data["users"][username]
    if user["password_hash"] != hash_password(password):
        return {"success": False, "error": "Invalid password"}

    # Create session
    session_token = generate_session_token()
    data["sessions"][session_token] = {
        "username": username,
        "created_at": get_timestamp()
    }

    # Update last login
    data["users"][username]["last_login"] = get_timestamp()
    save_users(data)

    return {
        "success": True,
        "session_token": session_token,
        "username": username,
        "token_count": user["token_count"],
        "message": f"Welcome back, {username}! Token count: {user['token_count']}"
    }


def logout(session_token):
    """Log out a user by invalidating their session."""
    data = load_users()

    if session_token in data["sessions"]:
        username = data["sessions"][session_token]["username"]
        del data["sessions"][session_token]
        save_users(data)
        return {"success": True, "message": f"User '{username}' logged out successfully"}

    return {"success": False, "error": "Invalid session token"}


def get_user_info(session_token):
    """Get user information from session token."""
    data = load_users()

    if session_token not in data["sessions"]:
        return {"success": False, "error": "Invalid session"}

    username = data["sessions"][session_token]["username"]
    user = data["users"].get(username)

    if not user:
        return {"success": False, "error": "User not found"}

    return {
        "success": True,
        "username": username,
        "token_count": user["token_count"],
        "tokens_created": user["tokens_created"],
        "mega_hashes": user["mega_hashes"],
        "created_at": user["created_at"],
        "last_login": user["last_login"]
    }


def update_token_count(session_token, increment=1):
    """Update user's token count."""
    data = load_users()

    if session_token not in data["sessions"]:
        return {"success": False, "error": "Invalid session"}

    username = data["sessions"][session_token]["username"]
    data["users"][username]["token_count"] += increment
    save_users(data)

    return {
        "success": True,
        "new_count": data["users"][username]["token_count"]
    }


def add_user_token(session_token, token_hash):
    """Add a created token to user's record."""
    data = load_users()

    if session_token not in data["sessions"]:
        return {"success": False, "error": "Invalid session"}

    username = data["sessions"][session_token]["username"]
    data["users"][username]["tokens_created"].append({
        "hash": token_hash,
        "created_at": get_timestamp()
    })
    data["users"][username]["token_count"] += 1
    save_users(data)

    return {
        "success": True,
        "token_count": data["users"][username]["token_count"]
    }


def add_mega_hash(session_token, mega_hash, value):
    """Add a mega hash to user's record."""
    data = load_users()

    if session_token not in data["sessions"]:
        return {"success": False, "error": "Invalid session"}

    username = data["sessions"][session_token]["username"]
    data["users"][username]["mega_hashes"].append({
        "hash": mega_hash,
        "value": value,
        "created_at": get_timestamp()
    })
    save_users(data)

    return {"success": True}


# ------------------------------ MAIN (CLI) ----------------------------
def main():
    """Interactive CLI for pewpi_login system."""
    print("∞ Pewpi Login System ∞")
    print("Commands: register, login, logout, info, quit")

    session = None

    while True:
        cmd = input("\n> ").strip().lower()

        if cmd == "register":
            username = input("Username: ").strip()
            password = input("Password: ").strip()
            result = register_user(username, password)
            print(result.get("message") or result.get("error"))

        elif cmd == "login":
            username = input("Username: ").strip()
            password = input("Password: ").strip()
            result = sign_in(username, password)
            if result["success"]:
                session = result["session_token"]
                print(result["message"])
            else:
                print(result["error"])

        elif cmd == "logout":
            if session:
                result = logout(session)
                print(result.get("message") or result.get("error"))
                session = None
            else:
                print("Not logged in")

        elif cmd == "info":
            if session:
                result = get_user_info(session)
                if result["success"]:
                    print(f"Username: {result['username']}")
                    print(f"Token Count: {result['token_count']}")
                    print(f"Tokens Created: {len(result['tokens_created'])}")
                    print(f"Mega Hashes: {len(result['mega_hashes'])}")
                else:
                    print(result["error"])
            else:
                print("Not logged in")

        elif cmd == "quit":
            break

        else:
            print("Unknown command")


if __name__ == "__main__":
    main()
