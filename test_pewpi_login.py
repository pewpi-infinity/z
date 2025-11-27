#!/usr/bin/env python3
"""
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
