#!/usr/bin/env python3
"""
Authentication Server - GitHub OAuth Integration for Infinity Research Portal
Handles OAuth flow, session management, and user tracking
"""

import os
import json
import hashlib
import secrets
import datetime
from datetime import timezone
from functools import wraps

from flask import Flask, request, redirect, jsonify, session, url_for, send_from_directory
from flask_cors import CORS
import requests
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Initialize Flask app
app = Flask(__name__, static_folder='static', static_url_path='/static')
app.secret_key = os.getenv('SESSION_SECRET', secrets.token_hex(32))
CORS(app, supports_credentials=True)

# Configuration
GITHUB_CLIENT_ID = os.getenv('GITHUB_CLIENT_ID')
GITHUB_CLIENT_SECRET = os.getenv('GITHUB_CLIENT_SECRET')
GITHUB_REDIRECT_URI = os.getenv('GITHUB_REDIRECT_URI', 'http://localhost:5000/auth/callback')

# File paths
Z_ROOT = os.path.abspath(os.path.dirname(__file__))
USERS_FILE = os.path.join(Z_ROOT, "users.json")
LOGIN_COMMITS_FILE = os.path.join(Z_ROOT, "login_commits.json")

# Rate limiting storage (simple in-memory for now)
rate_limit_store = {}

# ------------------------------ UTILITIES ------------------------------

def get_timestamp():
    """Get current UTC timestamp."""
    return datetime.datetime.now(timezone.utc).isoformat().replace('+00:00', 'Z')


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


def load_login_commits():
    """Load login commits from JSON file."""
    if os.path.exists(LOGIN_COMMITS_FILE):
        with open(LOGIN_COMMITS_FILE, "r") as f:
            return json.load(f)
    return {"commits": [], "metadata": {"created_at": get_timestamp()}}


def save_login_commits(data):
    """Save login commits to JSON file."""
    with open(LOGIN_COMMITS_FILE, "w") as f:
        json.dump(data, f, indent=4)


def add_login_commit(username, action, ip_address=None):
    """Track a login commit."""
    commits = load_login_commits()
    
    commit = {
        "username": username,
        "timestamp": get_timestamp(),
        "action": action,
        "ip": ip_address or request.remote_addr,
        "session_id": session.get('session_token', 'unknown')
    }
    
    commits["commits"].append(commit)
    save_login_commits(commits)
    return commit


def generate_session_token():
    """Generate a secure session token."""
    return secrets.token_hex(32)


def check_rate_limit(identifier, limit_per_minute=10):
    """Simple rate limiting check."""
    now = datetime.datetime.now()
    minute_key = now.strftime('%Y-%m-%d %H:%M')
    key = f"{identifier}:{minute_key}"
    
    count = rate_limit_store.get(key, 0)
    if count >= limit_per_minute:
        return False
    
    rate_limit_store[key] = count + 1
    
    # Clean old entries (simple approach)
    if len(rate_limit_store) > 1000:
        rate_limit_store.clear()
    
    return True


# ------------------------------ DECORATORS ------------------------------

def require_auth(f):
    """Decorator to require authentication for endpoints."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        session_token = session.get('session_token')
        
        if not session_token:
            return jsonify({"success": False, "error": "Not authenticated"}), 401
        
        # Verify session exists
        users_data = load_users()
        if session_token not in users_data.get("sessions", {}):
            session.clear()
            return jsonify({"success": False, "error": "Invalid session"}), 401
        
        return f(*args, **kwargs)
    
    return decorated_function


# ------------------------------ OAUTH ENDPOINTS ------------------------------

@app.route('/auth/github', methods=['GET'])
def github_oauth_initiate():
    """Initiate GitHub OAuth flow."""
    if not GITHUB_CLIENT_ID:
        return jsonify({
            "success": False,
            "error": "GitHub OAuth not configured. Please set GITHUB_CLIENT_ID in .env"
        }), 500
    
    # Check rate limit
    if not check_rate_limit(request.remote_addr):
        return jsonify({
            "success": False,
            "error": "Rate limit exceeded. Please try again later."
        }), 429
    
    # Generate state token for CSRF protection
    state_token = secrets.token_hex(16)
    session['oauth_state'] = state_token
    
    # GitHub OAuth authorization URL
    github_auth_url = (
        f"https://github.com/login/oauth/authorize"
        f"?client_id={GITHUB_CLIENT_ID}"
        f"&redirect_uri={GITHUB_REDIRECT_URI}"
        f"&scope=read:user user:email"
        f"&state={state_token}"
    )
    
    return redirect(github_auth_url)


@app.route('/auth/callback', methods=['GET'])
def github_oauth_callback():
    """Handle GitHub OAuth callback."""
    # Verify state token (CSRF protection)
    state = request.args.get('state')
    if state != session.get('oauth_state'):
        return jsonify({
            "success": False,
            "error": "Invalid state token. Possible CSRF attack."
        }), 400
    
    # Get authorization code
    code = request.args.get('code')
    if not code:
        error = request.args.get('error', 'Unknown error')
        return jsonify({
            "success": False,
            "error": f"OAuth error: {error}"
        }), 400
    
    # Exchange code for access token
    try:
        token_response = requests.post(
            'https://github.com/login/oauth/access_token',
            data={
                'client_id': GITHUB_CLIENT_ID,
                'client_secret': GITHUB_CLIENT_SECRET,
                'code': code,
                'redirect_uri': GITHUB_REDIRECT_URI
            },
            headers={'Accept': 'application/json'},
            timeout=10
        )
        token_data = token_response.json()
        
        if 'error' in token_data:
            return jsonify({
                "success": False,
                "error": f"Token exchange failed: {token_data.get('error_description', 'Unknown error')}"
            }), 400
        
        access_token = token_data.get('access_token')
        
        # Get user information from GitHub
        user_response = requests.get(
            'https://api.github.com/user',
            headers={
                'Authorization': f'Bearer {access_token}',
                'Accept': 'application/json'
            },
            timeout=10
        )
        user_data = user_response.json()
        
        github_username = user_data.get('login')
        github_id = user_data.get('id')
        
        if not github_username:
            return jsonify({
                "success": False,
                "error": "Failed to retrieve user information from GitHub"
            }), 400
        
        # Create or update user in our system
        users_data = load_users()
        
        if github_username not in users_data["users"]:
            # New user - create account
            users_data["users"][github_username] = {
                "github_id": github_id,
                "github_username": github_username,
                "token_count": 0,
                "tokens_created": [],
                "mega_hashes": [],
                "created_at": get_timestamp(),
                "last_login": None,
                "oauth_provider": "github"
            }
        
        # Create session
        session_token = generate_session_token()
        users_data["sessions"][session_token] = {
            "username": github_username,
            "created_at": get_timestamp(),
            "github_access_token": access_token  # Store for API calls
        }
        
        # Update last login
        users_data["users"][github_username]["last_login"] = get_timestamp()
        save_users(users_data)
        
        # Store session token in Flask session
        session['session_token'] = session_token
        session['username'] = github_username
        
        # Track login commit
        add_login_commit(github_username, "github_oauth_login")
        
        # Redirect to index page
        return redirect('/')
        
    except requests.exceptions.RequestException as e:
        return jsonify({
            "success": False,
            "error": f"Network error during OAuth: {str(e)}"
        }), 500


@app.route('/auth/status', methods=['GET'])
def auth_status():
    """Get current authentication status."""
    session_token = session.get('session_token')
    
    if not session_token:
        return jsonify({
            "success": False,
            "authenticated": False,
            "error": "Not authenticated"
        }), 401
    
    users_data = load_users()
    
    if session_token not in users_data.get("sessions", {}):
        session.clear()
        return jsonify({
            "success": False,
            "authenticated": False,
            "error": "Invalid session"
        }), 401
    
    username = users_data["sessions"][session_token]["username"]
    user = users_data["users"].get(username)
    
    if not user:
        return jsonify({
            "success": False,
            "authenticated": False,
            "error": "User not found"
        }), 404
    
    return jsonify({
        "success": True,
        "authenticated": True,
        "username": username,
        "token_count": user.get("token_count", 0),
        "tokens_created": len(user.get("tokens_created", [])),
        "mega_hashes": len(user.get("mega_hashes", [])),
        "last_login": user.get("last_login"),
        "created_at": user.get("created_at")
    })


@app.route('/auth/logout', methods=['POST', 'GET'])
def logout():
    """Log out the current user."""
    session_token = session.get('session_token')
    username = session.get('username')
    
    if session_token:
        users_data = load_users()
        
        if session_token in users_data.get("sessions", {}):
            del users_data["sessions"][session_token]
            save_users(users_data)
        
        # Track logout commit
        if username:
            add_login_commit(username, "logout")
    
    session.clear()
    
    return jsonify({
        "success": True,
        "message": "Logged out successfully"
    })


# ------------------------------ USER ENDPOINTS ------------------------------

@app.route('/api/user/commits', methods=['GET'])
@require_auth
def get_user_commits():
    """Get user's login commit history."""
    username = session.get('username')
    commits_data = load_login_commits()
    
    user_commits = [
        c for c in commits_data.get("commits", [])
        if c.get("username") == username
    ]
    
    # Sort by timestamp, most recent first
    user_commits.sort(key=lambda c: c.get("timestamp", ""), reverse=True)
    
    return jsonify({
        "success": True,
        "commits": user_commits[:50]  # Return last 50 commits
    })


@app.route('/api/user/update-tokens', methods=['POST'])
@require_auth
def update_user_tokens():
    """Update user's token count (called after token creation)."""
    username = session.get('username')
    data = request.get_json() or {}
    
    token_hash = data.get('token_hash')
    token_value = data.get('token_value', 0)
    action = data.get('action', 'token_build')
    
    if not token_hash:
        return jsonify({
            "success": False,
            "error": "token_hash is required"
        }), 400
    
    users_data = load_users()
    
    if username not in users_data["users"]:
        return jsonify({
            "success": False,
            "error": "User not found"
        }), 404
    
    # Add token to user's record
    users_data["users"][username]["tokens_created"].append({
        "hash": token_hash,
        "value": token_value,
        "created_at": get_timestamp()
    })
    
    # Increment token count
    users_data["users"][username]["token_count"] += 1
    
    save_users(users_data)
    
    # Track action commit
    add_login_commit(username, action)
    
    return jsonify({
        "success": True,
        "token_count": users_data["users"][username]["token_count"],
        "message": "Token count updated successfully"
    })


# ------------------------------ TOKEN BUILDING ENDPOINTS ------------------------------

@app.route('/api/token/build', methods=['POST'])
@require_auth
def build_token_api():
    """
    Build a token with authentication.
    Requires user to be logged in.
    """
    username = session.get('username')
    data = request.get_json() or {}
    
    text = data.get('text', '')
    source_type = data.get('source_type', 'text')
    filename = data.get('filename')
    
    if not text or not text.strip():
        return jsonify({
            "success": False,
            "error": "Text content is required"
        }), 400
    
    # Sanitize inputs
    text = str(text)[:1_000_000]  # Limit to 1MB
    if filename:
        filename = os.path.basename(str(filename))
    
    try:
        # Import and use build_token function
        from build_token import build_token
        
        token = build_token(
            text=text,
            source_type=source_type,
            filename=filename,
            username=username
        )
        
        # Update user's token count
        users_data = load_users()
        if username in users_data["users"]:
            users_data["users"][username]["tokens_created"].append({
                "hash": token["hash"],
                "value": token.get("value", 0),
                "created_at": get_timestamp()
            })
            users_data["users"][username]["token_count"] += 1
            save_users(users_data)
        
        # Track token build commit
        add_login_commit(username, "token_build")
        
        return jsonify({
            "success": True,
            "token": {
                "hash": token["hash"],
                "value": token.get("value", 0),
                "value_formatted": token.get("value_formatted", ""),
                "score": token.get("score", 0),
                "timestamp": token.get("timestamp", "")
            },
            "token_count": users_data["users"][username]["token_count"],
            "message": "Token created successfully"
        })
    
    except Exception as e:
        return jsonify({
            "success": False,
            "error": f"Token creation failed: {str(e)}"
        }), 500


# ------------------------------ HEALTH CHECK ------------------------------

@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint."""
    return jsonify({
        "status": "healthy",
        "service": "Infinity Research Portal Auth Server",
        "timestamp": get_timestamp(),
        "oauth_configured": bool(GITHUB_CLIENT_ID and GITHUB_CLIENT_SECRET)
    })


@app.route('/', methods=['GET'])
def index_page():
    """Serve the main index page."""
    return send_from_directory('.', 'index.html')


@app.route('/research_index.json', methods=['GET'])
def research_index():
    """Serve the research index JSON."""
    return send_from_directory('.', 'research_index.json')


# ------------------------------ MONGOOSE OS INTEGRATION ------------------------------

# Import and set up Mongoose OS routes
try:
    from mongoose_connector import create_mongoose_routes
    create_mongoose_routes(app)
except ImportError:
    print("⚠️  Warning: mongoose_connector not available")


# ------------------------------ MAIN ------------------------------

if __name__ == '__main__':
    print("∞ Infinity Research Portal - Authentication Server ∞")
    print(f"OAuth configured: {bool(GITHUB_CLIENT_ID and GITHUB_CLIENT_SECRET)}")
    
    if not GITHUB_CLIENT_ID or not GITHUB_CLIENT_SECRET:
        print("\n⚠️  WARNING: GitHub OAuth not configured!")
        print("   Please set GITHUB_CLIENT_ID and GITHUB_CLIENT_SECRET in .env file")
        print("   See .env.example for template\n")
    
    host = os.getenv('FLASK_HOST', '0.0.0.0')
    port = int(os.getenv('FLASK_PORT', 5000))
    debug = os.getenv('FLASK_DEBUG', 'False').lower() == 'true'
    
    app.run(host=host, port=port, debug=debug)
