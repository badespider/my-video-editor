"""
Unit tests for utils module.
Tests the call_model wrapper and helper functions.
"""

import unittest
from unittest.mock import patch, MagicMock
import sys
import os

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import utils
import config


class TestUtils(unittest.TestCase):
    """Test cases for utils module."""

    def test_call_model_default(self):
        """Test call_model with default configuration."""
        result = utils.call_model("Test prompt")
        self.assertIn("Mock response", result)
        self.assertIn(config.MODEL, result)

    def test_call_model_override(self):
        """Test call_model with model override."""
        result = utils.call_model("Test prompt", model="openai")
        self.assertIn("openai", result)

    def test_validate_json_output_valid(self):
        """Test JSON validation with valid input."""
        json_str = '{"test": "value"}'
        result = utils.validate_json_output(json_str)
        self.assertEqual(result["test"], "value")

    def test_validate_json_output_invalid(self):
        """Test JSON validation with invalid input."""
        with self.assertRaises(ValueError):
            utils.validate_json_output("invalid json")

    def test_truncate_input_within_limit(self):
        """Test input truncation when within limits."""
        text = "short text"
        result = utils.truncate_input(text, max_words=10)
        self.assertEqual(result, text)

    def test_truncate_input_over_limit(self):
        """Test input truncation when over limits."""
        text = " ".join(["word"] * 100)
        result = utils.truncate_input(text, max_words=50)
        self.assertEqual(len(result.split()), 50)

    def test_create_structured_prompt(self):
        """Test structured prompt creation."""
        prompt = utils.create_structured_prompt("task", "context", "format")
        self.assertIn("Task: task", prompt)
        self.assertIn("Context:", prompt)
        self.assertIn("Output Format: format", prompt)


if __name__ == "__main__":
    unittest.main()
