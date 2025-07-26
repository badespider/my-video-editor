"""
Unit tests for coordinator module.
Tests the VideoAgent class and workflow orchestration.
"""

import unittest
from unittest.mock import patch, MagicMock
import sys
import os

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from coordinator import VideoAgent
import config


class TestCoordinator(unittest.TestCase):
    """Test cases for coordinator module."""

    def setUp(self):
        """Set up test fixtures."""
        self.agent = VideoAgent()
        self.test_script = "Test script for video creation"

    def test_init_default_model(self):
        """Test VideoAgent initialization with default model."""
        agent = VideoAgent()
        self.assertEqual(agent.model, config.MODEL)

    def test_init_custom_model(self):
        """Test VideoAgent initialization with custom model."""
        agent = VideoAgent(model="openai")
        self.assertEqual(agent.model, "openai")

    @patch('coordinator.analyze_story')
    @patch('coordinator.choose_clip_descriptions')
    @patch('coordinator.generate_narration')
    @patch('coordinator.suggest_bgm')
    @patch('coordinator.compile_video_plan')
    def test_run_workflow(self, mock_compile, mock_bgm, mock_narration, mock_clips, mock_analysis):
        """Test complete workflow execution."""
        # Setup mocks
        mock_analysis.return_value = {"scenes": ["scene1"]}
        mock_clips.return_value = ["clip1", "clip2"]
        mock_narration.return_value = "Generated narration"
        mock_bgm.return_value = ["track1", "track2"]
        mock_compile.return_value = {
            "clips": ["clip1", "clip2"],
            "narrations": ["Generated narration"],
            "bgms": ["track1", "track2"],
            "timeline": "Complete timeline"
        }
        
        # Execute workflow
        result = self.agent.run(self.test_script)
        
        # Verify all functions were called
        mock_analysis.assert_called_once_with(self.test_script)
        mock_clips.assert_called_once_with({"scenes": ["scene1"]})
        mock_narration.assert_called_once_with(self.test_script)
        mock_bgm.assert_called_once_with({"scenes": ["scene1"]})
        mock_compile.assert_called_once_with(
            ["clip1", "clip2"], 
            ["Generated narration"], 
            ["track1", "track2"]
        )
        
        # Verify result structure
        self.assertIn("clips", result)
        self.assertIn("narrations", result)
        self.assertIn("bgms", result)
        self.assertIn("timeline", result)


if __name__ == "__main__":
    unittest.main()
