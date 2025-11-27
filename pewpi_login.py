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


# ============================================================================
# Extended Pewpi Login Module - Category Management and View Modes
# ============================================================================

import os
import sys
import json
import hashlib
import logging
import datetime
import re
import html
from typing import Dict, List, Optional, Tuple, Any

# ------------------------------ CONFIG ------------------------------
ROOT_DIR = os.path.dirname(os.path.abspath(__file__))
CATEGORY_TOKENS_FILE = os.path.join(ROOT_DIR, "category_tokens.json")
TOKENS_DIR = os.path.join(ROOT_DIR, "tokens")
RESEARCH_INDEX_FILE = os.path.join(ROOT_DIR, "research_index.json")

# Logging configuration
LOG_FORMAT = "[%(asctime)s] %(levelname)s - %(name)s: %(message)s"
LOG_DATE_FORMAT = "%Y-%m-%d %H:%M:%S"

# Initialize logger
logging.basicConfig(
    level=logging.INFO,
    format=LOG_FORMAT,
    datefmt=LOG_DATE_FORMAT
)
logger = logging.getLogger("pewpi_login")


# ------------------------------ EXCEPTIONS ------------------------------
class PewpiLoginError(Exception):
    """Base exception for pewpi_login module."""
    pass


class CategoryNotFoundError(PewpiLoginError):
    """Raised when a specified category is not found."""
    pass


class TokenNotFoundError(PewpiLoginError):
    """Raised when a specified token is not found."""
    pass


class InvalidConfigError(PewpiLoginError):
    """Raised when configuration is invalid or malformed."""
    pass


# ------------------------------ COLOR UTILITIES ------------------------------
class ColorManager:
    """Manages color mappings and highlighting for categories."""
    
    DEFAULT_COLORS = {
        "green": "#22c55e",
        "orange": "#f97316",
        "blue": "#3b82f6",
        "pink": "#ec4899",
        "red": "#ef4444",
        "yellow": "#eab308",
        "purple": "#a855f7"
    }
    
    def __init__(self, color_map: Optional[Dict[str, str]] = None):
        """Initialize ColorManager with optional custom color map."""
        self.color_map = color_map or self.DEFAULT_COLORS.copy()
        logger.debug(f"ColorManager initialized with {len(self.color_map)} colors")
    
    def get_hex_color(self, color_name: str) -> str:
        """Get hex color code for a color name."""
        hex_color = self.color_map.get(color_name.lower(), "#808080")
        logger.debug(f"Color lookup: {color_name} -> {hex_color}")
        return hex_color
    
    def highlight_text(self, text: str, color_name: str, mode: str = "word") -> str:
        """
        Apply highlighting to text based on the specified mode.
        
        Args:
            text: Text to highlight
            color_name: Color name for highlighting
            mode: 'word', 'sentence', or 'plain'
        
        Returns:
            HTML-formatted text with highlighting
        """
        if mode == "plain":
            return text
        
        hex_color = self.get_hex_color(color_name)
        # Escape HTML to prevent XSS
        escaped_text = html.escape(text)
        
        if mode == "word":
            return f'<span style="background-color: {hex_color}; padding: 0 2px; border-radius: 2px;">{escaped_text}</span>'
        elif mode == "sentence":
            return f'<span style="border-left: 3px solid {hex_color}; padding-left: 8px; display: block; margin: 4px 0;">{escaped_text}</span>'
        
        return text


# ------------------------------ TOKEN HASH MANAGER ------------------------------
class TokenHashManager:
    """Manages token hashes and their category associations."""
    
    def __init__(self, config_path: str = CATEGORY_TOKENS_FILE):
        """
        Initialize TokenHashManager.
        
        Args:
            config_path: Path to category_tokens.json configuration file
        """
        self.config_path = config_path
        self.categories: Dict[str, Dict] = {}
        self.color_map: Dict[str, str] = {}
        self.token_to_category: Dict[str, str] = {}
        self._load_config()
    
    def _load_config(self) -> None:
        """Load configuration from JSON file."""
        logger.info(f"Loading category tokens config from: {self.config_path}")
        
        if not os.path.exists(self.config_path):
            logger.warning(f"Config file not found: {self.config_path}. Creating default.")
            self._create_default_config()
            return
        
        try:
            with open(self.config_path, "r", encoding="utf-8") as f:
                data = json.load(f)
        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON in config file: {e}")
            raise InvalidConfigError(f"Invalid JSON in {self.config_path}: {e}")
        
        self.categories = data.get("categories", {})
        self.color_map = data.get("color_map", ColorManager.DEFAULT_COLORS)
        
        # Build reverse lookup: token_hash -> category
        for cat_name, cat_data in self.categories.items():
            for token_hash in cat_data.get("token_hashes", []):
                self.token_to_category[token_hash] = cat_name
        
        logger.info(f"Loaded {len(self.categories)} categories with {len(self.token_to_category)} token mappings")
    
    def _create_default_config(self) -> None:
        """Create default configuration file."""
        default_config = {
            "categories": {
                "engineering": {
                    "color": "green",
                    "display_name": "Engineering",
                    "description": "Engineering and technical research",
                    "token_hashes": [],
                    "keywords": ["quantum", "physics", "electron", "vector", "tensor", "algorithm", "neural", "lattice"]
                },
                "ceo": {
                    "color": "orange",
                    "display_name": "CEO",
                    "description": "Executive and leadership research",
                    "token_hashes": [],
                    "keywords": ["business", "strategy", "leadership", "management", "executive", "market", "revenue"]
                },
                "import": {
                    "color": "blue",
                    "display_name": "Import",
                    "description": "Import and data acquisition research",
                    "token_hashes": [],
                    "keywords": ["import", "data", "acquisition", "transfer", "source", "stream"]
                },
                "investigate": {
                    "color": "pink",
                    "display_name": "Investigate",
                    "description": "Investigation and analysis research",
                    "token_hashes": [],
                    "keywords": ["analysis", "investigate", "research", "study", "examine", "explore"]
                },
                "routes": {
                    "color": "red",
                    "display_name": "Routes",
                    "description": "Routing and pathway research",
                    "token_hashes": [],
                    "keywords": ["route", "path", "network", "connection", "channel", "pipeline"]
                },
                "data": {
                    "color": "yellow",
                    "display_name": "Data",
                    "description": "Data science and storage research",
                    "token_hashes": [],
                    "keywords": ["data", "storage", "database", "information", "record", "archive"]
                },
                "assimilation": {
                    "color": "purple",
                    "display_name": "Assimilation",
                    "description": "Integration and assimilation research",
                    "token_hashes": [],
                    "keywords": ["integration", "merge", "combine", "assimilate", "synthesis", "fusion"]
                }
            },
            "color_map": ColorManager.DEFAULT_COLORS,
            "metadata": {
                "version": "1.0.0",
                "last_updated": datetime.datetime.now(datetime.timezone.utc).isoformat(),
                "description": "Category-token mapping for Pewpi Infinity Research Portal"
            }
        }
        
        with open(self.config_path, "w", encoding="utf-8") as f:
            json.dump(default_config, f, indent=2)
        
        self.categories = default_config["categories"]
        self.color_map = default_config["color_map"]
        logger.info(f"Created default config at: {self.config_path}")
    
    def save_config(self) -> None:
        """Save current configuration to JSON file."""
        data = {
            "categories": self.categories,
            "color_map": self.color_map,
            "metadata": {
                "version": "1.0.0",
                "last_updated": datetime.datetime.now(datetime.timezone.utc).isoformat(),
                "description": "Category-token mapping for Pewpi Infinity Research Portal"
            }
        }
        
        with open(self.config_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)
        
        logger.info(f"Saved config to: {self.config_path}")
    
    def get_category(self, category_name: str) -> Dict:
        """
        Get category data by name.
        
        Args:
            category_name: Name of the category
        
        Returns:
            Category data dictionary
        
        Raises:
            CategoryNotFoundError: If category doesn't exist
        """
        if category_name not in self.categories:
            logger.error(f"Category not found: {category_name}")
            raise CategoryNotFoundError(f"Category '{category_name}' not found")
        
        return self.categories[category_name]
    
    def get_category_for_token(self, token_hash: str) -> Optional[str]:
        """
        Get the category name associated with a token hash.
        
        Args:
            token_hash: SHA256 hash of the token
        
        Returns:
            Category name or None if not found
        """
        return self.token_to_category.get(token_hash)
    
    def get_color_for_category(self, category_name: str) -> str:
        """Get the color associated with a category."""
        try:
            category = self.get_category(category_name)
            return category.get("color", "gray")
        except CategoryNotFoundError:
            return "gray"
    
    def add_token_to_category(self, token_hash: str, category_name: str) -> None:
        """
        Associate a token hash with a category.
        
        Args:
            token_hash: SHA256 hash of the token
            category_name: Name of the category
        """
        if category_name not in self.categories:
            logger.error(f"Cannot add token to non-existent category: {category_name}")
            raise CategoryNotFoundError(f"Category '{category_name}' not found")
        
        if token_hash not in self.categories[category_name]["token_hashes"]:
            self.categories[category_name]["token_hashes"].append(token_hash)
            self.token_to_category[token_hash] = category_name
            logger.info(f"Added token {token_hash[:12]}... to category: {category_name}")
    
    def get_all_categories(self) -> List[Dict]:
        """
        Get all categories with their metadata.
        
        Returns:
            List of category dictionaries with name, color, display_name
        """
        result = []
        for name, data in self.categories.items():
            result.append({
                "name": name,
                "color": data.get("color", "gray"),
                "display_name": data.get("display_name", name.title()),
                "description": data.get("description", ""),
                "token_count": len(data.get("token_hashes", [])),
                "keywords": data.get("keywords", [])
            })
        return result
    
    def categorize_by_keywords(self, text: str) -> str:
        """
        Determine category for text based on keyword matching.
        
        Args:
            text: Text content to categorize
        
        Returns:
            Best matching category name, defaults to 'data'
        """
        text_lower = text.lower()
        best_match = "data"
        best_score = 0
        
        for cat_name, cat_data in self.categories.items():
            keywords = cat_data.get("keywords", [])
            score = sum(1 for kw in keywords if kw.lower() in text_lower)
            if score > best_score:
                best_score = score
                best_match = cat_name
        
        logger.debug(f"Text categorized as '{best_match}' with score {best_score}")
        return best_match


# ------------------------------ BUTTON GENERATOR ------------------------------
class ButtonGenerator:
    """Generates dynamic color-coded buttons for categories."""
    
    def __init__(self, token_manager: TokenHashManager, color_manager: ColorManager):
        """
        Initialize ButtonGenerator.
        
        Args:
            token_manager: TokenHashManager instance
            color_manager: ColorManager instance
        """
        self.token_manager = token_manager
        self.color_manager = color_manager
        logger.debug("ButtonGenerator initialized")
    
    def generate_button_html(self, category_name: str, articles: List[Dict]) -> str:
        """
        Generate HTML for a single category button with article links.
        
        Args:
            category_name: Name of the category
            articles: List of article dictionaries with 'title', 'url', 'hash'
        
        Returns:
            HTML string for the button
        """
        try:
            category = self.token_manager.get_category(category_name)
        except CategoryNotFoundError:
            logger.warning(f"Generating button for unknown category: {category_name}")
            category = {"color": "gray", "display_name": category_name.title()}
        
        color = category.get("color", "gray")
        display_name = category.get("display_name", category_name.title())
        hex_color = self.color_manager.get_hex_color(color)
        
        # Generate article links
        article_links = ""
        for article in articles[:10]:  # Limit to 10 articles
            title = article.get("title", "Untitled")
            url = article.get("url", "#")
            article_links += f'<li><a href="{url}" target="_blank">{title}</a></li>\n'
        
        if not article_links:
            article_links = "<li>No research articles yet.</li>"
        
        html = f'''
        <div class="category-button" data-category="{category_name}" style="border-color: {hex_color};">
            <div class="button-header" style="background: linear-gradient(135deg, {hex_color}33, transparent);">
                <span class="button-title">{display_name}</span>
                <span class="button-color-tag" style="color: {hex_color};">({color.title()})</span>
            </div>
            <ul class="button-articles">
                {article_links}
            </ul>
        </div>
        '''
        
        logger.debug(f"Generated button HTML for category: {category_name}")
        return html
    
    def generate_all_buttons_html(self, research_index: List[Dict]) -> str:
        """
        Generate HTML for all category buttons.
        
        Args:
            research_index: List of research article records
        
        Returns:
            Complete HTML string for all buttons
        """
        # Group articles by category/role
        articles_by_category: Dict[str, List[Dict]] = {}
        
        for article in research_index:
            role = article.get("role", "data")
            if role not in articles_by_category:
                articles_by_category[role] = []
            articles_by_category[role].append(article)
        
        # Generate buttons for all categories
        buttons_html = '<div class="category-buttons-container">\n'
        
        categories = self.token_manager.get_all_categories()
        for cat in categories:
            cat_name = cat["name"]
            articles = articles_by_category.get(cat_name, [])
            buttons_html += self.generate_button_html(cat_name, articles)
        
        buttons_html += '</div>'
        
        logger.info(f"Generated {len(categories)} category buttons")
        return buttons_html
    
    def generate_button_data_json(self, research_index: List[Dict]) -> str:
        """
        Generate JSON data structure for dynamic button rendering.
        
        Args:
            research_index: List of research article records
        
        Returns:
            JSON string for frontend consumption
        """
        # Group articles by category/role
        articles_by_category: Dict[str, List[Dict]] = {}
        
        for article in research_index:
            role = article.get("role", "data")
            if role not in articles_by_category:
                articles_by_category[role] = []
            articles_by_category[role].append({
                "hash": article.get("hash", ""),
                "title": article.get("title", "Untitled"),
                "url": article.get("url", ""),
                "timestamp": article.get("timestamp", ""),
                "source_url": article.get("source_url", "")
            })
        
        result = {
            "categories": [],
            "color_map": self.color_manager.color_map
        }
        
        categories = self.token_manager.get_all_categories()
        for cat in categories:
            cat_name = cat["name"]
            result["categories"].append({
                "name": cat_name,
                "display_name": cat["display_name"],
                "color": cat["color"],
                "hex_color": self.color_manager.get_hex_color(cat["color"]),
                "articles": articles_by_category.get(cat_name, []),
                "article_count": len(articles_by_category.get(cat_name, []))
            })
        
        return json.dumps(result, indent=2)


# ------------------------------ VIEW MODE MANAGER ------------------------------
class ViewModeManager:
    """Manages toggle view modes for content display."""
    
    MODES = ["sentence", "word", "plain"]
    
    def __init__(self, color_manager: ColorManager, token_manager: TokenHashManager):
        """
        Initialize ViewModeManager.
        
        Args:
            color_manager: ColorManager instance
            token_manager: TokenHashManager instance
        """
        self.color_manager = color_manager
        self.token_manager = token_manager
        self.current_mode = "plain"
        logger.debug(f"ViewModeManager initialized with mode: {self.current_mode}")
    
    def set_mode(self, mode: str) -> None:
        """
        Set the current view mode.
        
        Args:
            mode: One of 'sentence', 'word', or 'plain'
        """
        if mode not in self.MODES:
            logger.warning(f"Invalid mode '{mode}', defaulting to 'plain'")
            mode = "plain"
        
        self.current_mode = mode
        logger.info(f"View mode set to: {mode}")
    
    def highlight_content(self, content: str, category_tokens: Dict[str, List[str]]) -> str:
        """
        Apply highlighting to content based on category tokens and current mode.
        
        Args:
            content: Text content to highlight
            category_tokens: Dict mapping category names to lists of tokens/words
        
        Returns:
            HTML-formatted content with appropriate highlighting
        """
        if self.current_mode == "plain":
            return content
        
        if self.current_mode == "word":
            return self._highlight_words(content, category_tokens)
        elif self.current_mode == "sentence":
            return self._highlight_sentences(content, category_tokens)
        
        return content
    
    def _highlight_words(self, content: str, category_tokens: Dict[str, List[str]]) -> str:
        """Highlight individual words based on category tokens."""
        # First escape the entire content to prevent XSS
        result = html.escape(content)
        
        for category, tokens in category_tokens.items():
            color = self.token_manager.get_color_for_category(category)
            hex_color = self.color_manager.get_hex_color(color)
            
            for token in tokens:
                # Escape the token and use it for matching in already-escaped content
                escaped_token = html.escape(token)
                # Case-insensitive replacement with preserved case
                pattern = re.compile(re.escape(escaped_token), re.IGNORECASE)
                replacement = f'<span class="highlight-word" style="background-color: {hex_color}40; border-bottom: 2px solid {hex_color};">{escaped_token}</span>'
                result = pattern.sub(replacement, result)
        
        return result
    
    def _highlight_sentences(self, content: str, category_tokens: Dict[str, List[str]]) -> str:
        """Highlight sentences based on category tokens."""
        # Split content into sentences
        sentences = re.split(r'(?<=[.!?])\s+', content)
        result_sentences = []
        
        for sentence in sentences:
            # Determine which category this sentence belongs to
            best_category = None
            best_score = 0
            
            sentence_lower = sentence.lower()
            for category, tokens in category_tokens.items():
                score = sum(1 for token in tokens if token.lower() in sentence_lower)
                if score > best_score:
                    best_score = score
                    best_category = category
            
            # Escape the sentence to prevent XSS
            escaped_sentence = html.escape(sentence)
            
            if best_category and best_score > 0:
                color = self.token_manager.get_color_for_category(best_category)
                hex_color = self.color_manager.get_hex_color(color)
                highlighted = f'<span class="highlight-sentence" style="border-left: 4px solid {hex_color}; padding-left: 10px; display: block; background-color: {hex_color}15; margin: 4px 0;">{escaped_sentence}</span>'
                result_sentences.append(highlighted)
            else:
                result_sentences.append(escaped_sentence)
        
        return " ".join(result_sentences)
    
    def generate_toggle_html(self) -> str:
        """
        Generate HTML for the view mode toggle control.
        
        Returns:
            HTML string for the toggle control
        """
        toggle_html = '''
        <div class="view-mode-toggle" id="view-mode-toggle">
            <span class="toggle-label">View Mode:</span>
            <div class="toggle-buttons">
                <button class="toggle-btn" data-mode="sentence" title="Highlight sentences by category">
                    Sentence
                </button>
                <button class="toggle-btn" data-mode="word" title="Highlight words by category">
                    Word
                </button>
                <button class="toggle-btn active" data-mode="plain" title="Plain text without highlighting">
                    Plain Text
                </button>
            </div>
        </div>
        '''
        return toggle_html
    
    def generate_toggle_styles(self) -> str:
        """
        Generate CSS styles for the toggle control and highlights.
        
        Returns:
            CSS string for toggle styling
        """
        styles = '''
        .view-mode-toggle {
            display: flex;
            align-items: center;
            gap: 12px;
            padding: 10px 14px;
            background: rgba(10, 20, 40, 0.8);
            border-radius: 12px;
            border: 1px solid rgba(100, 160, 255, 0.4);
            margin-bottom: 14px;
        }
        .toggle-label {
            font-size: 0.85rem;
            font-weight: 600;
            color: #a0c8ff;
        }
        .toggle-buttons {
            display: flex;
            gap: 6px;
        }
        .toggle-btn {
            padding: 6px 12px;
            font-size: 0.8rem;
            border: 1px solid rgba(100, 160, 255, 0.5);
            border-radius: 8px;
            background: rgba(30, 60, 100, 0.5);
            color: #d0e0ff;
            cursor: pointer;
            transition: all 0.15s ease;
        }
        .toggle-btn:hover {
            background: rgba(60, 100, 160, 0.6);
            border-color: rgba(120, 180, 255, 0.7);
        }
        .toggle-btn.active {
            background: linear-gradient(135deg, #2563eb, #3b82f6);
            border-color: #60a5fa;
            color: #ffffff;
            box-shadow: 0 0 10px rgba(59, 130, 246, 0.5);
        }
        .highlight-word {
            border-radius: 2px;
            padding: 0 2px;
        }
        .highlight-sentence {
            border-radius: 4px;
        }
        '''
        return styles
    
    def generate_toggle_script(self) -> str:
        """
        Generate JavaScript for toggle functionality.
        
        Returns:
            JavaScript string for toggle behavior
        """
        script = '''
        (function() {
            const toggleBtns = document.querySelectorAll('.toggle-btn');
            let currentMode = 'plain';
            
            // Category keywords for highlighting
            const categoryKeywords = {
                engineering: ['quantum', 'physics', 'electron', 'vector', 'tensor', 'algorithm', 'neural', 'lattice', 'atomic', 'photon'],
                ceo: ['business', 'strategy', 'leadership', 'management', 'executive', 'market', 'revenue', 'growth'],
                import: ['import', 'data', 'acquisition', 'transfer', 'source', 'stream', 'input'],
                investigate: ['analysis', 'investigate', 'research', 'study', 'examine', 'explore', 'discover'],
                routes: ['route', 'path', 'network', 'connection', 'channel', 'pipeline', 'flow'],
                data: ['data', 'storage', 'database', 'information', 'record', 'archive', 'file'],
                assimilation: ['integration', 'merge', 'combine', 'assimilate', 'synthesis', 'fusion', 'unity']
            };
            
            const categoryColors = {
                engineering: '#22c55e',
                ceo: '#f97316',
                import: '#3b82f6',
                investigate: '#ec4899',
                routes: '#ef4444',
                data: '#eab308',
                assimilation: '#a855f7'
            };
            
            function setViewMode(mode) {
                currentMode = mode;
                toggleBtns.forEach(btn => {
                    btn.classList.toggle('active', btn.dataset.mode === mode);
                });
                
                // Apply highlighting to content
                applyHighlighting(mode);
                
                console.log('[PewpiLogin] View mode changed to:', mode);
            }
            
            // HTML escape function to prevent XSS
            function escapeHtml(text) {
                const div = document.createElement('div');
                div.textContent = text;
                return div.innerHTML;
            }
            
            function applyHighlighting(mode) {
                const contentElements = document.querySelectorAll('.token-card, .research-content, .article-content');
                
                contentElements.forEach(el => {
                    // Store original text if not already stored
                    if (!el.dataset.originalText) {
                        el.dataset.originalText = el.textContent;
                    }
                    
                    if (mode === 'plain') {
                        el.textContent = el.dataset.originalText;
                    } else {
                        let content = el.dataset.originalText;
                        content = highlightContent(content, mode);
                        el.innerHTML = content;
                    }
                });
            }
            
            function highlightContent(content, mode) {
                if (mode === 'word') {
                    return highlightWords(content);
                } else if (mode === 'sentence') {
                    return highlightSentences(content);
                }
                return escapeHtml(content);
            }
            
            function highlightWords(content) {
                // First escape the content to prevent XSS
                let result = escapeHtml(content);
                for (const [category, keywords] of Object.entries(categoryKeywords)) {
                    const color = categoryColors[category];
                    keywords.forEach(keyword => {
                        const escapedKeyword = escapeHtml(keyword);
                        const regex = new RegExp('\\\\b(' + escapedKeyword.replace(/[.*+?^${}()|[\\]\\\\]/g, '\\\\$&') + ')\\\\b', 'gi');
                        result = result.replace(regex, 
                            '<span class="highlight-word" style="background-color: ' + color + '40; border-bottom: 2px solid ' + color + ';">$1</span>');
                    });
                }
                return result;
            }
            
            function highlightSentences(content) {
                // Split by sentence boundaries
                const sentences = content.split(/(?<=[.!?])\\s+/);
                return sentences.map(sentence => {
                    let bestCategory = null;
                    let bestScore = 0;
                    
                    const sentenceLower = sentence.toLowerCase();
                    for (const [category, keywords] of Object.entries(categoryKeywords)) {
                        const score = keywords.filter(kw => sentenceLower.includes(kw)).length;
                        if (score > bestScore) {
                            bestScore = score;
                            bestCategory = category;
                        }
                    }
                    
                    // Escape the sentence to prevent XSS
                    const escapedSentence = escapeHtml(sentence);
                    
                    if (bestCategory && bestScore > 0) {
                        const color = categoryColors[bestCategory];
                        return '<span class="highlight-sentence" style="border-left: 4px solid ' + color + '; padding-left: 10px; display: block; background-color: ' + color + '15; margin: 4px 0;">' + escapedSentence + '</span>';
                    }
                    return escapedSentence;
                }).join(' ');
            }
            
            // Attach event listeners
            toggleBtns.forEach(btn => {
                btn.addEventListener('click', () => setViewMode(btn.dataset.mode));
            });
            
            // Export for external use
            window.PewpiViewMode = {
                setMode: setViewMode,
                getMode: () => currentMode,
                categoryKeywords: categoryKeywords,
                categoryColors: categoryColors
            };
            
            console.log('[PewpiLogin] View mode toggle initialized');
        })();
        '''
        return script


# ------------------------------ RESEARCH INDEX SYNCER ------------------------------
class ResearchIndexSyncer:
    """Synchronizes tokens with research index and categories."""
    
    def __init__(self, token_manager: TokenHashManager):
        """
        Initialize ResearchIndexSyncer.
        
        Args:
            token_manager: TokenHashManager instance
        """
        self.token_manager = token_manager
        self.tokens_dir = TOKENS_DIR
        self.research_index_path = RESEARCH_INDEX_FILE
        logger.debug("ResearchIndexSyncer initialized")
    
    def scan_tokens(self) -> List[Dict]:
        """
        Scan tokens directory and read token data.
        
        Returns:
            List of token data dictionaries
        """
        tokens = []
        
        if not os.path.isdir(self.tokens_dir):
            logger.warning(f"Tokens directory not found: {self.tokens_dir}")
            return tokens
        
        for fname in os.listdir(self.tokens_dir):
            if not fname.endswith(".json"):
                continue
            
            fpath = os.path.join(self.tokens_dir, fname)
            try:
                with open(fpath, "r", encoding="utf-8") as f:
                    data = json.load(f)
                tokens.append(data)
                logger.debug(f"Loaded token: {fname}")
            except (json.JSONDecodeError, IOError) as e:
                logger.warning(f"Failed to load token {fname}: {e}")
        
        logger.info(f"Scanned {len(tokens)} tokens from {self.tokens_dir}")
        return tokens
    
    def categorize_token(self, token_data: Dict) -> str:
        """
        Determine category for a token based on its content.
        
        Args:
            token_data: Token data dictionary
        
        Returns:
            Category name
        """
        # Check if token hash is already mapped
        token_hash = token_data.get("hash", "")
        existing_category = self.token_manager.get_category_for_token(token_hash)
        if existing_category:
            return existing_category
        
        # Categorize based on content
        content = ""
        content += token_data.get("research", "")
        content += " " + token_data.get("raw_text", "")
        content += " " + token_data.get("notes", "")
        
        category = self.token_manager.categorize_by_keywords(content)
        
        # Add to category mapping
        if token_hash:
            self.token_manager.add_token_to_category(token_hash, category)
        
        return category
    
    def sync_index(self) -> List[Dict]:
        """
        Synchronize tokens with research index.
        
        Returns:
            Updated research index records
        """
        logger.info("Starting research index synchronization")
        
        tokens = self.scan_tokens()
        records = []
        
        for token in tokens:
            token_hash = token.get("hash", "")
            category = self.categorize_token(token)
            
            # Extract title from research content
            research = token.get("research", "")
            title_match = re.search(r'\[.*?\]\s*(.+?)(?:\n|$)', research)
            title = title_match.group(1).strip() if title_match else f"Token {token_hash[:8]}…"
            
            record = {
                "hash": token_hash,
                "role": category,
                "title": title,
                "url": f"tokens/{token_hash}.json",
                "source_url": token.get("source_url", ""),
                "timestamp": token.get("timestamp", ""),
                "notes": token.get("notes", ""),
                "value": token.get("value", 0)
            }
            records.append(record)
        
        # Sort by timestamp
        records.sort(key=lambda r: (r.get("timestamp", ""), r.get("hash", "")))
        
        # Save updated index
        with open(self.research_index_path, "w", encoding="utf-8") as f:
            json.dump(records, f, indent=2)
        
        # Save updated category mappings
        self.token_manager.save_config()
        
        logger.info(f"Synchronized {len(records)} records to research index")
        return records


# ------------------------------ MAIN FACADE ------------------------------
class PewpiLogin:
    """
    Main facade class for Pewpi Login functionality.
    
    Provides unified access to token management, button generation,
    and view mode toggling.
    """
    
    def __init__(self, config_path: str = CATEGORY_TOKENS_FILE):
        """
        Initialize PewpiLogin.
        
        Args:
            config_path: Path to category_tokens.json configuration
        """
        logger.info("Initializing PewpiLogin...")
        
        self.token_manager = TokenHashManager(config_path)
        self.color_manager = ColorManager(self.token_manager.color_map)
        self.button_generator = ButtonGenerator(self.token_manager, self.color_manager)
        self.view_mode_manager = ViewModeManager(self.color_manager, self.token_manager)
        self.index_syncer = ResearchIndexSyncer(self.token_manager)
        
        logger.info("PewpiLogin initialized successfully")
    
    def sync(self) -> List[Dict]:
        """Synchronize tokens and research index."""
        return self.index_syncer.sync_index()
    
    def get_categories(self) -> List[Dict]:
        """Get all available categories."""
        return self.token_manager.get_all_categories()
    
    def get_button_data(self) -> str:
        """Get JSON data for dynamic button rendering."""
        try:
            with open(RESEARCH_INDEX_FILE, "r", encoding="utf-8") as f:
                research_index = json.load(f)
        except (IOError, json.JSONDecodeError):
            research_index = []
        
        return self.button_generator.generate_button_data_json(research_index)
    
    def generate_html_components(self) -> Dict[str, str]:
        """
        Generate all HTML components for the portal.
        
        Returns:
            Dictionary with 'toggle_html', 'toggle_styles', 'toggle_script'
        """
        return {
            "toggle_html": self.view_mode_manager.generate_toggle_html(),
            "toggle_styles": self.view_mode_manager.generate_toggle_styles(),
            "toggle_script": self.view_mode_manager.generate_toggle_script()
        }
    
    def validate(self) -> Dict[str, Any]:
        """
        Validate configuration and return status.
        
        Returns:
            Validation result dictionary
        """
        result = {
            "valid": True,
            "categories_count": len(self.token_manager.categories),
            "token_mappings_count": len(self.token_manager.token_to_category),
            "colors_defined": len(self.color_manager.color_map),
            "issues": []
        }
        
        # Check for categories without colors
        for cat_name, cat_data in self.token_manager.categories.items():
            color = cat_data.get("color", "")
            if color not in self.color_manager.color_map:
                result["issues"].append(f"Category '{cat_name}' has undefined color: {color}")
                result["valid"] = False
        
        # Check research index
        if os.path.exists(RESEARCH_INDEX_FILE):
            try:
                with open(RESEARCH_INDEX_FILE, "r", encoding="utf-8") as f:
                    index = json.load(f)
                result["research_index_count"] = len(index)
            except (IOError, json.JSONDecodeError) as e:
                result["issues"].append(f"Research index error: {e}")
                result["valid"] = False
        else:
            result["issues"].append("Research index file not found")
        
        logger.info(f"Validation complete. Valid: {result['valid']}")
        return result


# ------------------------------ CLI INTERFACE ------------------------------
def main():
    """Main CLI entry point."""
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Pewpi Login - Token and Category Management for Infinity Research Portal"
    )
    parser.add_argument(
        "--sync", 
        action="store_true",
        help="Synchronize tokens with research index"
    )
    parser.add_argument(
        "--generate-index",
        action="store_true",
        help="Generate research index from tokens"
    )
    parser.add_argument(
        "--validate",
        action="store_true",
        help="Validate configuration"
    )
    parser.add_argument(
        "--categories",
        action="store_true",
        help="List all categories"
    )
    parser.add_argument(
        "--button-data",
        action="store_true",
        help="Output button data JSON"
    )
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Enable verbose logging"
    )
    
    args = parser.parse_args()
    
    if args.verbose:
        logging.getLogger("pewpi_login").setLevel(logging.DEBUG)
    
    logger.info("∞ Pewpi Login - Infinity Research Portal ∞")
    
    try:
        pewpi = PewpiLogin()
        
        if args.sync or args.generate_index:
            records = pewpi.sync()
            print(f"Synchronized {len(records)} research records")
        
        if args.validate:
            result = pewpi.validate()
            print(json.dumps(result, indent=2))
        
        if args.categories:
            categories = pewpi.get_categories()
            for cat in categories:
                print(f"  - {cat['name']}: {cat['display_name']} ({cat['color']}) - {cat['token_count']} tokens")
        
        if args.button_data:
            print(pewpi.get_button_data())
        
        if not any([args.sync, args.generate_index, args.validate, args.categories, args.button_data]):
            # Default action: show status
            result = pewpi.validate()
            print(f"\n∞ Pewpi Login Status ∞")
            print(f"  Categories: {result['categories_count']}")
            print(f"  Token mappings: {result['token_mappings_count']}")
            print(f"  Research records: {result.get('research_index_count', 0)}")
            print(f"  Valid: {result['valid']}")
            
            if result['issues']:
                print("\nIssues:")
                for issue in result['issues']:
                    print(f"  - {issue}")
        
    except PewpiLoginError as e:
        logger.error(f"Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
