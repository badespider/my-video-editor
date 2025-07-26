"""
Unit tests for workers module.
Tests individual worker functions for the AI pipeline.
"""

import unittest
from unittest.mock import patch, MagicMock
import sys
import os

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import workers


class TestWorkers(unittest.TestCase):
    """Test cases for workers module."""

    @patch('workers.call_model')
    @patch('workers.validate_json_output')
    def test_analyze_story(self, mock_validate, mock_call):
        """Test story analysis worker."""
        mock_call.return_value = '{"scenes": []}'
        mock_validate.return_value = {"scenes": []}
        
        result = workers.analyze_story("Test script")
        
        mock_call.assert_called_once()
        mock_validate.assert_called_once()
        self.assertEqual(result, {"scenes": []})

    @patch('workers.call_model')
    @patch('workers.validate_json_output')
    def test_choose_clip_descriptions(self, mock_validate, mock_call):
        """Test clip description worker."""
        mock_call.return_value = '["clip1", "clip2"]'
        mock_validate.return_value = ["clip1", "clip2"]
        
        result = workers.choose_clip_descriptions({"scenes": []})
        
        mock_call.assert_called_once()
        mock_validate.assert_called_once()
        self.assertEqual(result, ["clip1", "clip2"])

    @patch('workers.call_model')
    def test_generate_narration(self, mock_call):
        """Test narration generation worker."""
        mock_call.return_value = "Generated narration text"
        
        result = workers.generate_narration("Test script")
        
        mock_call.assert_called_once()
        self.assertEqual(result, "Generated narration text")

    @patch('workers.call_model')
    @patch('workers.validate_json_output')
    def test_suggest_bgm(self, mock_validate, mock_call):
        """Test BGM suggestion worker."""
        mock_call.return_value = '["track1", "track2"]'
        mock_validate.return_value = ["track1", "track2"]
        
        result = workers.suggest_bgm({"scenes": []})
        
        mock_call.assert_called_once()
        mock_validate.assert_called_once()
        self.assertEqual(result, ["track1", "track2"])

    def test_compile_video_plan(self):
        """Test video plan compilation."""
        clips = ["clip1", "clip2"]
        narrations = ["narration1"]
        bgms = ["track1", "track2"]
        
        result = workers.compile_video_plan(clips, narrations, bgms)
        
        self.assertEqual(result["clips"], clips)
        self.assertEqual(result["narrations"], narrations)
        self.assertEqual(result["bgms"], bgms)
        self.assertIn("timeline", result)


if __name__ == "__main__":
    unittest.main()
