#!/usr/bin/env python3
"""
Tests for Pewpi Login System and Token Builder
test_pewpi_login.py - Integration tests for Pewpi Login module

Tests for:
- Token hash parsing and category associations
- Color mapping functionality
- View mode switching behavior
- Button generation
- Error handling
"""

import os
import sys
import json
import unittest
import tempfile
import shutil

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from pewpi_login import (
    register_user, sign_in, logout, get_user_info,
    update_token_count, add_user_token, add_mega_hash,
    load_users, save_users, hash_password
)

from build_token import (
    score_content, calculate_value, format_value,
    build_token, generate_mega_hash, infinity_hash,
    MIN_VALUE, MAX_VALUE
)


class TestPewpiLogin(unittest.TestCase):
    """Test user authentication functionality."""

    @classmethod
    def setUpClass(cls):
        """Set up test fixtures."""
        # Use temp directory for test data
        cls.original_users_file = os.path.join(
            os.path.dirname(os.path.abspath(__file__)), "users.json"
        )
        cls.backup_exists = os.path.exists(cls.original_users_file)
        if cls.backup_exists:
            with open(cls.original_users_file) as f:
                cls.backup_data = f.read()

    @classmethod
    def tearDownClass(cls):
        """Restore original state."""
        if cls.backup_exists:
            with open(cls.original_users_file, 'w') as f:
                f.write(cls.backup_data)
        elif os.path.exists(cls.original_users_file):
            # Reset to empty state
            save_users({"users": {}, "sessions": {}})

    def setUp(self):
        """Reset users before each test."""
        save_users({"users": {}, "sessions": {}})

    def test_register_user_success(self):
        """Test successful user registration."""
        result = register_user("testuser", "testpass123")
        self.assertTrue(result["success"])

        users = load_users()
        self.assertIn("testuser", users["users"])
        self.assertEqual(users["users"]["testuser"]["token_count"], 0)

    def test_register_user_duplicate(self):
        """Test registering duplicate username."""
        register_user("duplicate", "pass1")
        result = register_user("duplicate", "pass2")
        self.assertFalse(result["success"])
        self.assertIn("error", result)

    def test_sign_in_success(self):
        """Test successful sign in."""
        register_user("logintest", "mypassword")
        result = sign_in("logintest", "mypassword")
        self.assertTrue(result["success"])
        self.assertIn("session_token", result)
        self.assertEqual(result["username"], "logintest")

    def test_sign_in_wrong_password(self):
        """Test sign in with wrong password."""
        register_user("wrongpass", "correct")
        result = sign_in("wrongpass", "incorrect")
        self.assertFalse(result["success"])
        self.assertEqual(result["error"], "Invalid password")

    def test_sign_in_nonexistent_user(self):
        """Test sign in with nonexistent user."""
        result = sign_in("nobody", "anything")
        self.assertFalse(result["success"])
        self.assertEqual(result["error"], "User not found")

    def test_logout(self):
        """Test logout functionality."""
        register_user("logouttest", "pass")
        login_result = sign_in("logouttest", "pass")
        session_token = login_result["session_token"]

        logout_result = logout(session_token)
        self.assertTrue(logout_result["success"])

        # Verify session is gone
        users = load_users()
        self.assertNotIn(session_token, users["sessions"])

    def test_update_token_count(self):
        """Test token count updates."""
        register_user("counter", "pass")
        login_result = sign_in("counter", "pass")
        session_token = login_result["session_token"]

        # Update count
        update_token_count(session_token, 5)
        user_info = get_user_info(session_token)
        self.assertEqual(user_info["token_count"], 5)

        # Update again
        update_token_count(session_token, 3)
        user_info = get_user_info(session_token)
        self.assertEqual(user_info["token_count"], 8)

    def test_add_user_token(self):
        """Test adding tokens to user record."""
        register_user("tokenuser", "pass")
        login_result = sign_in("tokenuser", "pass")
        session_token = login_result["session_token"]

        add_user_token(session_token, "hash123abc")
        user_info = get_user_info(session_token)

        self.assertEqual(user_info["token_count"], 1)
        self.assertEqual(len(user_info["tokens_created"]), 1)
        self.assertEqual(user_info["tokens_created"][0]["hash"], "hash123abc")


class TestBuildToken(unittest.TestCase):
    """Test token building and valuation."""

    def test_score_content_basic(self):
        """Test basic content scoring."""
        text = "This is a simple test content."
        score, analysis = score_content(text)

        self.assertGreater(score, 0)
        self.assertIn("word_count", analysis)
        self.assertIn("char_count", analysis)

    def test_score_content_with_keywords(self):
        """Test scoring with boost keywords."""
        text_no_keywords = "Hello world this is basic text."
        text_with_keywords = "quantum hydrogen fusion reactor plasma"

        score_no_kw, _ = score_content(text_no_keywords)
        score_with_kw, analysis = score_content(text_with_keywords)

        self.assertGreater(score_with_kw, score_no_kw)
        self.assertIn("keyword_matches", analysis)
        self.assertIn("quantum", analysis["keyword_matches"])

    def test_score_content_special_keywords(self):
        """Test high-value special keywords."""
        text = "This contains pewpi and kris special tokens."
        score, analysis = score_content(text)

        # pewpi and kris have high bonuses
        self.assertGreater(score, 10000)

    def test_calculate_value_min(self):
        """Test minimum value calculation."""
        value = calculate_value(0)
        self.assertEqual(value, MIN_VALUE)

    def test_calculate_value_scaling(self):
        """Test value scaling at different score levels."""
        value_low = calculate_value(50)
        value_mid = calculate_value(500)
        value_high = calculate_value(5000)
        value_very_high = calculate_value(50000)

        self.assertLess(value_low, value_mid)
        self.assertLess(value_mid, value_high)
        self.assertLess(value_high, value_very_high)

    def test_calculate_value_max(self):
        """Test maximum value cap."""
        value = calculate_value(999999999999)
        self.assertLessEqual(value, MAX_VALUE)

    def test_format_value(self):
        """Test value formatting."""
        self.assertEqual(format_value(100), "$100.00")
        self.assertIn("K", format_value(5000))
        self.assertIn("M", format_value(5000000))
        self.assertIn("B", format_value(5000000000))

    def test_build_token(self):
        """Test token creation."""
        text = "Test quantum research content for token generation."
        token = build_token(text, source_type="text")

        self.assertIn("hash", token)
        self.assertIn("timestamp", token)
        self.assertIn("score", token)
        self.assertIn("value", token)
        self.assertIn("value_formatted", token)
        self.assertEqual(token["source_type"], "text")
        self.assertEqual(len(token["hash"]), 64)

    def test_infinity_hash(self):
        """Test hash generation."""
        text = "Test content"
        hash1 = infinity_hash(text)
        hash2 = infinity_hash(text)

        self.assertEqual(hash1, hash2)  # Same input = same hash
        self.assertEqual(len(hash1), 64)

        hash3 = infinity_hash(text + "different")
        self.assertNotEqual(hash1, hash3)  # Different input = different hash


class TestMegaHash(unittest.TestCase):
    """Test mega hash generation."""

    def setUp(self):
        """Create test tokens."""
        self.token1 = build_token("Quantum research paper on fusion reactors")
        self.token2 = build_token("Hydrogen energy analysis and thermodynamics")
        self.token3 = build_token("Neural network AI algorithm implementation")

    def test_mega_hash_minimum_tokens(self):
        """Test mega hash requires minimum 2 tokens."""
        result = generate_mega_hash(["single_hash"])
        self.assertIn("error", result)

    def test_mega_hash_success(self):
        """Test successful mega hash creation."""
        hashes = [self.token1["hash"], self.token2["hash"]]
        result = generate_mega_hash(hashes)

        self.assertIn("mega_hash", result)
        self.assertIn("component_count", result)
        self.assertIn("value", result)
        self.assertEqual(result["component_count"], 2)
        self.assertEqual(result["type"], "MEGA_HASH")

    def test_mega_hash_high_value(self):
        """Test mega hash has minimum $963B value."""
        hashes = [self.token1["hash"], self.token2["hash"], self.token3["hash"]]
        result = generate_mega_hash(hashes)

        # Minimum mega hash value is $963 billion
        self.assertGreaterEqual(result["value"], 963_000_000_000)

    def test_mega_hash_more_components_higher_value(self):
        """Test more components = higher value."""
        result2 = generate_mega_hash([self.token1["hash"], self.token2["hash"]])
        result3 = generate_mega_hash([
            self.token1["hash"],
            self.token2["hash"],
            self.token3["hash"]
        ])

        self.assertGreater(result3["value"], result2["value"])


class TestIntegration(unittest.TestCase):
    """Integration tests for the complete workflow."""

    def setUp(self):
        """Reset state."""
        save_users({"users": {}, "sessions": {}})

    def test_full_user_token_workflow(self):
        """Test complete user registration, login, and token creation."""
        # Register
        reg_result = register_user("integrationuser", "pass123")
        self.assertTrue(reg_result["success"])

        # Login
        login_result = sign_in("integrationuser", "pass123")
        self.assertTrue(login_result["success"])
        session = login_result["session_token"]

        # Create token
        token = build_token("Integration test quantum research data")
        add_user_token(session, token["hash"])

        # Verify
        user_info = get_user_info(session)
        self.assertEqual(user_info["token_count"], 1)
        self.assertEqual(user_info["tokens_created"][0]["hash"], token["hash"])

        # Logout
        logout_result = logout(session)
        self.assertTrue(logout_result["success"])


# Import additional classes for extended tests
from pewpi_login import (
    PewpiLogin,
    TokenHashManager,
    ColorManager,
    ButtonGenerator,
    ViewModeManager,
    ResearchIndexSyncer,
    CategoryNotFoundError,
    TokenNotFoundError,
    InvalidConfigError
)


class TestColorManager(unittest.TestCase):
    """Tests for ColorManager class."""
    
    def test_default_colors(self):
        """Test default color map initialization."""
        cm = ColorManager()
        self.assertIn("green", cm.color_map)
        self.assertIn("orange", cm.color_map)
        self.assertEqual(cm.color_map["green"], "#22c55e")
    
    def test_custom_colors(self):
        """Test custom color map."""
        custom = {"red": "#ff0000", "blue": "#0000ff"}
        cm = ColorManager(custom)
        self.assertEqual(cm.get_hex_color("red"), "#ff0000")
        self.assertEqual(cm.get_hex_color("blue"), "#0000ff")
    
    def test_unknown_color_fallback(self):
        """Test fallback for unknown colors."""
        cm = ColorManager()
        self.assertEqual(cm.get_hex_color("unknown"), "#808080")
    
    def test_highlight_text_plain_mode(self):
        """Test plain text mode returns unchanged text."""
        cm = ColorManager()
        text = "Test content"
        result = cm.highlight_text(text, "green", mode="plain")
        self.assertEqual(result, text)
    
    def test_highlight_text_word_mode(self):
        """Test word highlighting mode."""
        cm = ColorManager()
        text = "Test"
        result = cm.highlight_text(text, "green", mode="word")
        self.assertIn("background-color:", result)
        self.assertIn("#22c55e", result)
        self.assertIn("Test", result)
    
    def test_highlight_text_sentence_mode(self):
        """Test sentence highlighting mode."""
        cm = ColorManager()
        text = "Test sentence."
        result = cm.highlight_text(text, "orange", mode="sentence")
        self.assertIn("border-left:", result)
        self.assertIn("#f97316", result)


class TestTokenHashManager(unittest.TestCase):
    """Tests for TokenHashManager class."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.test_dir = tempfile.mkdtemp()
        self.config_path = os.path.join(self.test_dir, "category_tokens.json")
        
        # Create test config
        self.test_config = {
            "categories": {
                "engineering": {
                    "color": "green",
                    "display_name": "Engineering",
                    "description": "Test engineering",
                    "token_hashes": ["hash123"],
                    "keywords": ["quantum", "physics"]
                },
                "ceo": {
                    "color": "orange",
                    "display_name": "CEO",
                    "description": "Test CEO",
                    "token_hashes": [],
                    "keywords": ["business", "strategy"]
                }
            },
            "color_map": {
                "green": "#22c55e",
                "orange": "#f97316"
            },
            "metadata": {
                "version": "1.0.0"
            }
        }
        
        with open(self.config_path, "w") as f:
            json.dump(self.test_config, f)
    
    def tearDown(self):
        """Clean up test fixtures."""
        shutil.rmtree(self.test_dir)
    
    def test_load_config(self):
        """Test loading configuration from file."""
        thm = TokenHashManager(self.config_path)
        self.assertEqual(len(thm.categories), 2)
        self.assertIn("engineering", thm.categories)
        self.assertIn("ceo", thm.categories)
    
    def test_get_category(self):
        """Test getting category data."""
        thm = TokenHashManager(self.config_path)
        cat = thm.get_category("engineering")
        self.assertEqual(cat["color"], "green")
        self.assertEqual(cat["display_name"], "Engineering")
    
    def test_get_category_not_found(self):
        """Test CategoryNotFoundError for unknown category."""
        thm = TokenHashManager(self.config_path)
        with self.assertRaises(CategoryNotFoundError):
            thm.get_category("nonexistent")
    
    def test_get_category_for_token(self):
        """Test token-to-category lookup."""
        thm = TokenHashManager(self.config_path)
        category = thm.get_category_for_token("hash123")
        self.assertEqual(category, "engineering")
    
    def test_get_category_for_unknown_token(self):
        """Test lookup for unknown token returns None."""
        thm = TokenHashManager(self.config_path)
        category = thm.get_category_for_token("unknown_hash")
        self.assertIsNone(category)
    
    def test_add_token_to_category(self):
        """Test adding token to category."""
        thm = TokenHashManager(self.config_path)
        thm.add_token_to_category("new_hash", "ceo")
        self.assertEqual(thm.get_category_for_token("new_hash"), "ceo")
        self.assertIn("new_hash", thm.categories["ceo"]["token_hashes"])
    
    def test_add_token_to_invalid_category(self):
        """Test adding token to non-existent category raises error."""
        thm = TokenHashManager(self.config_path)
        with self.assertRaises(CategoryNotFoundError):
            thm.add_token_to_category("hash", "nonexistent")
    
    def test_get_color_for_category(self):
        """Test getting color for category."""
        thm = TokenHashManager(self.config_path)
        color = thm.get_color_for_category("engineering")
        self.assertEqual(color, "green")
    
    def test_categorize_by_keywords(self):
        """Test keyword-based categorization."""
        thm = TokenHashManager(self.config_path)
        
        # Test engineering keywords
        text = "This is about quantum physics research."
        category = thm.categorize_by_keywords(text)
        self.assertEqual(category, "engineering")
        
        # Test CEO keywords
        text = "Business strategy for growth."
        category = thm.categorize_by_keywords(text)
        self.assertEqual(category, "ceo")
    
    def test_get_all_categories(self):
        """Test getting all categories."""
        thm = TokenHashManager(self.config_path)
        categories = thm.get_all_categories()
        self.assertEqual(len(categories), 2)
        
        names = [c["name"] for c in categories]
        self.assertIn("engineering", names)
        self.assertIn("ceo", names)
    
    def test_save_config(self):
        """Test saving configuration."""
        thm = TokenHashManager(self.config_path)
        thm.add_token_to_category("new_hash", "ceo")
        thm.save_config()
        
        # Reload and verify
        thm2 = TokenHashManager(self.config_path)
        self.assertEqual(thm2.get_category_for_token("new_hash"), "ceo")
    
    def test_create_default_config(self):
        """Test creating default config when file doesn't exist."""
        new_path = os.path.join(self.test_dir, "new_config.json")
        thm = TokenHashManager(new_path)
        
        self.assertTrue(os.path.exists(new_path))
        self.assertEqual(len(thm.categories), 7)  # Default has 7 categories


class TestButtonGenerator(unittest.TestCase):
    """Tests for ButtonGenerator class."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.test_dir = tempfile.mkdtemp()
        self.config_path = os.path.join(self.test_dir, "category_tokens.json")
        
        test_config = {
            "categories": {
                "engineering": {
                    "color": "green",
                    "display_name": "Engineering",
                    "description": "Test",
                    "token_hashes": [],
                    "keywords": []
                }
            },
            "color_map": {"green": "#22c55e"},
            "metadata": {"version": "1.0.0"}
        }
        
        with open(self.config_path, "w") as f:
            json.dump(test_config, f)
        
        self.token_manager = TokenHashManager(self.config_path)
        self.color_manager = ColorManager(self.token_manager.color_map)
        self.button_gen = ButtonGenerator(self.token_manager, self.color_manager)
    
    def tearDown(self):
        """Clean up test fixtures."""
        shutil.rmtree(self.test_dir)
    
    def test_generate_button_html(self):
        """Test generating button HTML."""
        articles = [
            {"title": "Test Article", "url": "test.json", "hash": "abc123"}
        ]
        html = self.button_gen.generate_button_html("engineering", articles)
        
        self.assertIn("category-button", html)
        self.assertIn("Engineering", html)
        self.assertIn("Test Article", html)
        self.assertIn("#22c55e", html)
    
    def test_generate_button_html_empty_articles(self):
        """Test generating button HTML with no articles."""
        html = self.button_gen.generate_button_html("engineering", [])
        self.assertIn("No research articles yet", html)
    
    def test_generate_button_data_json(self):
        """Test generating button data JSON."""
        research_index = [
            {"hash": "abc", "role": "engineering", "title": "Test", "url": "test.json"}
        ]
        json_str = self.button_gen.generate_button_data_json(research_index)
        data = json.loads(json_str)
        
        self.assertIn("categories", data)
        self.assertIn("color_map", data)
        
        eng_cat = next(c for c in data["categories"] if c["name"] == "engineering")
        self.assertEqual(eng_cat["article_count"], 1)


class TestViewModeManager(unittest.TestCase):
    """Tests for ViewModeManager class."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.test_dir = tempfile.mkdtemp()
        self.config_path = os.path.join(self.test_dir, "category_tokens.json")
        
        test_config = {
            "categories": {
                "engineering": {
                    "color": "green",
                    "display_name": "Engineering",
                    "description": "Test",
                    "token_hashes": [],
                    "keywords": ["quantum", "physics"]
                }
            },
            "color_map": {"green": "#22c55e"},
            "metadata": {"version": "1.0.0"}
        }
        
        with open(self.config_path, "w") as f:
            json.dump(test_config, f)
        
        self.token_manager = TokenHashManager(self.config_path)
        self.color_manager = ColorManager(self.token_manager.color_map)
        self.view_manager = ViewModeManager(self.color_manager, self.token_manager)
    
    def tearDown(self):
        """Clean up test fixtures."""
        shutil.rmtree(self.test_dir)
    
    def test_default_mode(self):
        """Test default view mode is plain."""
        self.assertEqual(self.view_manager.current_mode, "plain")
    
    def test_set_mode_valid(self):
        """Test setting valid view modes."""
        for mode in ["sentence", "word", "plain"]:
            self.view_manager.set_mode(mode)
            self.assertEqual(self.view_manager.current_mode, mode)
    
    def test_set_mode_invalid(self):
        """Test invalid mode defaults to plain."""
        self.view_manager.set_mode("invalid")
        self.assertEqual(self.view_manager.current_mode, "plain")
    
    def test_highlight_content_plain(self):
        """Test plain mode returns unchanged content."""
        self.view_manager.set_mode("plain")
        content = "Test quantum physics content."
        tokens = {"engineering": ["quantum", "physics"]}
        result = self.view_manager.highlight_content(content, tokens)
        self.assertEqual(result, content)
    
    def test_highlight_content_word(self):
        """Test word highlighting mode."""
        self.view_manager.set_mode("word")
        content = "quantum physics"
        tokens = {"engineering": ["quantum", "physics"]}
        result = self.view_manager.highlight_content(content, tokens)
        self.assertIn("highlight-word", result)
        self.assertIn("#22c55e", result)
    
    def test_generate_toggle_html(self):
        """Test toggle HTML generation."""
        html = self.view_manager.generate_toggle_html()
        self.assertIn("view-mode-toggle", html)
        self.assertIn("Sentence", html)
        self.assertIn("Word", html)
        self.assertIn("Plain Text", html)
    
    def test_generate_toggle_styles(self):
        """Test toggle styles generation."""
        styles = self.view_manager.generate_toggle_styles()
        self.assertIn(".view-mode-toggle", styles)
        self.assertIn(".toggle-btn", styles)
        self.assertIn(".highlight-word", styles)
    
    def test_generate_toggle_script(self):
        """Test toggle script generation."""
        script = self.view_manager.generate_toggle_script()
        self.assertIn("setViewMode", script)
        self.assertIn("applyHighlighting", script)


class TestPewpiLogin(unittest.TestCase):
    """Integration tests for PewpiLogin facade class."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.test_dir = tempfile.mkdtemp()
        self.config_path = os.path.join(self.test_dir, "category_tokens.json")
        self.tokens_dir = os.path.join(self.test_dir, "tokens")
        self.research_index = os.path.join(self.test_dir, "research_index.json")
        
        os.makedirs(self.tokens_dir, exist_ok=True)
        
        # Create test config
        test_config = {
            "categories": {
                "engineering": {
                    "color": "green",
                    "display_name": "Engineering",
                    "description": "Test",
                    "token_hashes": [],
                    "keywords": ["quantum", "physics"]
                },
                "data": {
                    "color": "yellow",
                    "display_name": "Data",
                    "description": "Test",
                    "token_hashes": [],
                    "keywords": ["data", "storage"]
                }
            },
            "color_map": {"green": "#22c55e", "yellow": "#eab308"},
            "metadata": {"version": "1.0.0"}
        }
        
        with open(self.config_path, "w") as f:
            json.dump(test_config, f)
        
        # Create empty research index
        with open(self.research_index, "w") as f:
            json.dump([], f)
    
    def tearDown(self):
        """Clean up test fixtures."""
        shutil.rmtree(self.test_dir)
    
    def test_initialization(self):
        """Test PewpiLogin initialization."""
        pewpi = PewpiLogin(self.config_path)
        self.assertIsNotNone(pewpi.token_manager)
        self.assertIsNotNone(pewpi.color_manager)
        self.assertIsNotNone(pewpi.button_generator)
        self.assertIsNotNone(pewpi.view_mode_manager)
    
    def test_get_categories(self):
        """Test getting all categories."""
        pewpi = PewpiLogin(self.config_path)
        categories = pewpi.get_categories()
        self.assertEqual(len(categories), 2)
    
    def test_validate_success(self):
        """Test successful validation."""
        pewpi = PewpiLogin(self.config_path)
        result = pewpi.validate()
        self.assertTrue(result["valid"])
        self.assertEqual(result["categories_count"], 2)
    
    def test_generate_html_components(self):
        """Test HTML component generation."""
        pewpi = PewpiLogin(self.config_path)
        components = pewpi.generate_html_components()
        
        self.assertIn("toggle_html", components)
        self.assertIn("toggle_styles", components)
        self.assertIn("toggle_script", components)
        
        self.assertIn("view-mode-toggle", components["toggle_html"])


class TestErrorHandling(unittest.TestCase):
    """Tests for error handling scenarios."""
    
    def test_invalid_json_config(self):
        """Test handling of invalid JSON config file."""
        test_dir = tempfile.mkdtemp()
        config_path = os.path.join(test_dir, "invalid.json")
        
        try:
            with open(config_path, "w") as f:
                f.write("{ invalid json }")
            
            with self.assertRaises(InvalidConfigError):
                TokenHashManager(config_path)
        finally:
            shutil.rmtree(test_dir)
    
    def test_missing_tokens_directory(self):
        """Test handling of missing tokens directory."""
        test_dir = tempfile.mkdtemp()
        config_path = os.path.join(test_dir, "config.json")
        
        try:
            test_config = {
                "categories": {"test": {"color": "green", "display_name": "Test", "description": "", "token_hashes": [], "keywords": []}},
                "color_map": {"green": "#22c55e"},
                "metadata": {}
            }
            with open(config_path, "w") as f:
                json.dump(test_config, f)
            
            thm = TokenHashManager(config_path)
            syncer = ResearchIndexSyncer(thm)
            
            # Override tokens_dir to a non-existent path
            syncer.tokens_dir = os.path.join(test_dir, "nonexistent_tokens")
            
            # Should not raise, just return empty list
            tokens = syncer.scan_tokens()
            self.assertEqual(tokens, [])
        finally:
            shutil.rmtree(test_dir)


if __name__ == "__main__":
    unittest.main(verbosity=2)
