#!/usr/bin/env python3
"""
Tests for Pewpi Login System and Token Builder
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


if __name__ == "__main__":
    unittest.main(verbosity=2)
