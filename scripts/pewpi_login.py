#!/usr/bin/env python3
"""
pewpi_login.py — A login tool for managing user credentials with IP verification.

This script provides:
1. CLI to add users and manage credentials
2. HTTP server mode to accept login requests and verify client IP

SECURITY WARNING:
=================
The --embed option writes credentials into this source file. This is INSECURE
and should only be used in isolated/testing environments. The recommended
approach is to use the external credentials.json file (default behavior).

Usage:
  Add user:    python pewpi_login.py add-user <username> <password> --ips <comma-separated-ips> [--embed]
  Run server:  python pewpi_login.py run --host 0.0.0.0 --port 8080
"""

import argparse
import datetime
import hashlib
import json
import logging
import os
import re
import sys
from http.server import HTTPServer, BaseHTTPRequestHandler

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Try to import bcrypt, fall back to hashlib.sha256 if not available
try:
    import bcrypt
    BCRYPT_AVAILABLE = True
    logger.info("Using bcrypt for password hashing (recommended)")
except ImportError:
    BCRYPT_AVAILABLE = False
    logger.warning("bcrypt not available, falling back to SHA256 (less secure)")

# Paths
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
CREDENTIALS_FILE = os.path.join(SCRIPT_DIR, "credentials.json")

# =============================================================================
# EMBEDDED CREDENTIALS PLACEHOLDER
# =============================================================================
# WARNING: Embedding credentials in source code is INSECURE!
# Only use this feature in isolated/testing environments.
# The script prioritizes embedded credentials over credentials.json when present.
# To embed credentials, use: python pewpi_login.py add-user <user> <pass> --ips <ips> --embed
# =============================================================================
EMBEDDED_CREDENTIALS = {}
# =============================================================================


def hash_password(password: str) -> str:
    """Hash a password using bcrypt if available, otherwise SHA256."""
    if BCRYPT_AVAILABLE:
        salt = bcrypt.gensalt()
        hashed = bcrypt.hashpw(password.encode('utf-8'), salt)
        return hashed.decode('utf-8')
    else:
        # Fallback to SHA256 (less secure, but functional)
        return "sha256:" + hashlib.sha256(password.encode('utf-8')).hexdigest()


def verify_password(password: str, hashed: str) -> bool:
    """Verify a password against a hash."""
    if hashed.startswith("sha256:"):
        # SHA256 fallback
        expected = "sha256:" + hashlib.sha256(password.encode('utf-8')).hexdigest()
        return expected == hashed
    else:
        # bcrypt
        if not BCRYPT_AVAILABLE:
            logger.error("Cannot verify bcrypt hash without bcrypt installed")
            return False
        try:
            return bcrypt.checkpw(password.encode('utf-8'), hashed.encode('utf-8'))
        except Exception as e:
            logger.error(f"Password verification failed: {e}")
            return False


def load_credentials() -> dict:
    """
    Load credentials, prioritizing embedded credentials if present.
    Falls back to credentials.json if embedded credentials are empty.
    """
    # Prioritize embedded credentials if they exist
    if EMBEDDED_CREDENTIALS:
        logger.info("Using embedded credentials")
        return EMBEDDED_CREDENTIALS.copy()
    
    # Fall back to credentials.json
    if os.path.exists(CREDENTIALS_FILE):
        try:
            with open(CREDENTIALS_FILE, 'r', encoding='utf-8') as f:
                creds = json.load(f)
                logger.info(f"Loaded credentials from {CREDENTIALS_FILE}")
                return creds
        except (json.JSONDecodeError, IOError) as e:
            logger.error(f"Failed to load credentials from {CREDENTIALS_FILE}: {e}")
            return {}
    
    logger.info("No credentials found")
    return {}


def save_credentials_to_file(credentials: dict) -> bool:
    """Save credentials to the JSON file."""
    try:
        with open(CREDENTIALS_FILE, 'w', encoding='utf-8') as f:
            json.dump(credentials, f, indent=2)
        logger.info(f"Credentials saved to {CREDENTIALS_FILE}")
        return True
    except IOError as e:
        logger.error(f"Failed to save credentials: {e}")
        return False


def embed_credentials_in_script(credentials: dict) -> bool:
    """
    Embed credentials directly into this script file.
    
    WARNING: This is INSECURE and should only be used in isolated/testing environments.
    """
    script_path = os.path.abspath(__file__)
    
    try:
        with open(script_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Format the credentials dictionary for embedding
        creds_str = json.dumps(credentials, indent=4)
        
        # Use a more robust approach: find the section between markers
        # Match from EMBEDDED_CREDENTIALS = to the closing # === line
        pattern = r'(# =+\nEMBEDDED_CREDENTIALS = )\{[^#]*\}(\n# =+)'
        replacement = r'\1' + creds_str + r'\2'
        
        new_content, count = re.subn(pattern, replacement, content, count=1, flags=re.DOTALL)
        
        if count == 0:
            # Fallback: try simpler pattern for empty dict
            pattern = r'EMBEDDED_CREDENTIALS = \{\}'
            replacement = f'EMBEDDED_CREDENTIALS = {creds_str}'
            new_content, count = re.subn(pattern, replacement, content, count=1)
        
        if count == 0:
            logger.error("Could not find EMBEDDED_CREDENTIALS placeholder in script")
            return False
        
        with open(script_path, 'w', encoding='utf-8') as f:
            f.write(new_content)
        
        logger.warning("=" * 60)
        logger.warning("SECURITY WARNING: Credentials embedded in source code!")
        logger.warning("This is INSECURE. Use only in isolated/testing environments.")
        logger.warning("=" * 60)
        logger.info(f"Credentials embedded in {script_path}")
        return True
        
    except IOError as e:
        logger.error(f"Failed to embed credentials: {e}")
        return False


def add_user(username: str, password: str, ips: list, embed: bool = False) -> bool:
    """Add a new user with the given credentials and allowed IPs."""
    if not username or not password:
        logger.error("Username and password are required")
        return False
    
    if not ips:
        logger.error("At least one IP address is required")
        return False
    
    # Load existing credentials from file (not embedded, for adding)
    credentials = {}
    if os.path.exists(CREDENTIALS_FILE):
        try:
            with open(CREDENTIALS_FILE, 'r', encoding='utf-8') as f:
                credentials = json.load(f)
        except (json.JSONDecodeError, IOError):
            credentials = {}
    
    # Hash the password
    password_hash = hash_password(password)
    
    # Create user record
    user_record = {
        "password_hash": password_hash,
        "allowed_ips": ips,
        "created_at": datetime.datetime.now(datetime.timezone.utc).isoformat()
    }
    
    credentials[username] = user_record
    
    # Save to JSON file (always)
    if not save_credentials_to_file(credentials):
        return False
    
    logger.info(f"User '{username}' added with allowed IPs: {ips}")
    
    # Optionally embed in script
    if embed:
        if not embed_credentials_in_script(credentials):
            logger.warning("Failed to embed credentials, but they were saved to JSON file")
    
    return True


def get_client_ip(headers: dict, remote_addr: str) -> str:
    """
    Get the client IP address from request headers.
    Prioritizes X-Forwarded-For header, falls back to remote address.
    
    SECURITY NOTE: The X-Forwarded-For header can be spoofed by clients.
    This implementation trusts the header when present, which is appropriate
    when the server is behind a trusted reverse proxy that sets this header.
    If exposed directly to the internet without a trusted proxy, consider
    using only the remote_addr to prevent IP spoofing.
    """
    x_forwarded_for = headers.get('X-Forwarded-For', '')
    if x_forwarded_for:
        # X-Forwarded-For can contain multiple IPs (client, proxy1, proxy2, ...)
        # Take the first IP which is typically the original client
        # Note: This trusts the X-Forwarded-For header; use behind a trusted proxy
        client_ip = x_forwarded_for.split(',')[0].strip()
        logger.debug(f"Client IP from X-Forwarded-For: {client_ip}")
        return client_ip
    
    logger.debug(f"Client IP from remote address: {remote_addr}")
    return remote_addr


class LoginHandler(BaseHTTPRequestHandler):
    """HTTP request handler for the login server."""
    
    credentials = {}
    
    def log_message(self, format, *args):
        """Override to use our logger."""
        logger.info("%s - %s", self.address_string(), format % args)
    
    def send_json_response(self, status_code: int, data: dict):
        """Send a JSON response."""
        self.send_response(status_code)
        self.send_header('Content-Type', 'application/json')
        self.end_headers()
        self.wfile.write(json.dumps(data).encode('utf-8'))
    
    def do_POST(self):
        """Handle POST requests."""
        if self.path == '/login':
            self.handle_login()
        else:
            self.send_json_response(404, {"ok": False, "message": "not found"})
    
    def do_GET(self):
        """Handle GET requests (health check)."""
        if self.path == '/health':
            self.send_json_response(200, {"ok": True, "message": "healthy"})
        else:
            self.send_json_response(404, {"ok": False, "message": "not found"})
    
    def handle_login(self):
        """Handle login POST request."""
        try:
            # Read request body
            try:
                content_length = int(self.headers.get('Content-Length', 0))
            except (ValueError, TypeError):
                self.send_json_response(400, {"ok": False, "message": "invalid Content-Length header"})
                return
            
            if content_length == 0:
                self.send_json_response(400, {"ok": False, "message": "empty request body"})
                return
            
            body = self.rfile.read(content_length)
            
            try:
                data = json.loads(body.decode('utf-8'))
            except json.JSONDecodeError:
                self.send_json_response(400, {"ok": False, "message": "invalid JSON"})
                return
            
            username = data.get('username', '')
            password = data.get('password', '')
            
            if not username or not password:
                logger.warning("Login attempt with missing credentials")
                self.send_json_response(403, {"ok": False, "message": "authentication failed"})
                return
            
            # Get client IP
            headers_dict = {k: v for k, v in self.headers.items()}
            client_ip = get_client_ip(headers_dict, self.client_address[0])
            
            logger.info(f"Login attempt for user '{username}' from IP {client_ip}")
            
            # Check credentials
            if username not in self.credentials:
                logger.warning(f"User '{username}' not found")
                self.send_json_response(403, {"ok": False, "message": "authentication failed"})
                return
            
            user_record = self.credentials[username]
            
            # Verify password
            if not verify_password(password, user_record.get('password_hash', '')):
                logger.warning(f"Invalid password for user '{username}'")
                self.send_json_response(403, {"ok": False, "message": "authentication failed"})
                return
            
            # Verify IP
            allowed_ips = user_record.get('allowed_ips', [])
            if client_ip not in allowed_ips:
                logger.warning(f"IP {client_ip} not allowed for user '{username}'. Allowed: {allowed_ips}")
                self.send_json_response(403, {"ok": False, "message": "authentication failed"})
                return
            
            # Success!
            logger.info(f"User '{username}' authenticated successfully from {client_ip}")
            self.send_json_response(200, {"ok": True, "message": "authenticated"})
            
        except Exception as e:
            logger.error(f"Error handling login: {e}")
            self.send_json_response(500, {"ok": False, "message": "internal server error"})


def run_server(host: str, port: int):
    """Run the HTTP login server."""
    # Load credentials
    credentials = load_credentials()
    
    if not credentials:
        logger.warning("No credentials loaded. Add users with 'add-user' command first.")
    else:
        logger.info(f"Loaded {len(credentials)} user(s)")
    
    # Set credentials on handler class
    LoginHandler.credentials = credentials
    
    server_address = (host, port)
    httpd = HTTPServer(server_address, LoginHandler)
    
    logger.info(f"Starting login server on {host}:{port}")
    logger.info("Endpoints:")
    logger.info(f"  POST /login - Authenticate user (JSON: username, password)")
    logger.info(f"  GET /health - Health check")
    logger.info("Press Ctrl+C to stop")
    
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        logger.info("Server stopped")
        httpd.server_close()


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description='pewpi_login - User authentication with IP verification',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  Add a user:
    python pewpi_login.py add-user admin secretpass --ips 192.168.1.1,10.0.0.1
  
  Add a user with embedded credentials (INSECURE):
    python pewpi_login.py add-user admin secretpass --ips 192.168.1.1 --embed
  
  Run the server:
    python pewpi_login.py run --host 0.0.0.0 --port 8080

SECURITY WARNING:
  The --embed option writes credentials into the source file.
  This is INSECURE and should only be used in isolated/testing environments.
  Default behavior uses credentials.json which is safer.
"""
    )
    
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    # add-user command
    add_parser = subparsers.add_parser('add-user', help='Add a new user')
    add_parser.add_argument('username', help='Username')
    add_parser.add_argument('password', help='Password')
    add_parser.add_argument('--ips', required=True, 
                           help='Comma-separated list of allowed IP addresses')
    add_parser.add_argument('--embed', action='store_true',
                           help='Embed credentials in script (INSECURE - use only for testing)')
    
    # run command
    run_parser = subparsers.add_parser('run', help='Run the login server')
    run_parser.add_argument('--host', default='0.0.0.0', help='Host to bind to (default: 0.0.0.0)')
    run_parser.add_argument('--port', type=int, default=8080, help='Port to listen on (default: 8080)')
    
    args = parser.parse_args()
    
    if args.command == 'add-user':
        ips = [ip.strip() for ip in args.ips.split(',') if ip.strip()]
        success = add_user(args.username, args.password, ips, args.embed)
        sys.exit(0 if success else 1)
    
    elif args.command == 'run':
        run_server(args.host, args.port)
    
    else:
        parser.print_help()
        sys.exit(1)


if __name__ == '__main__':
    main()
