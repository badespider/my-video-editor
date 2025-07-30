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

    @patch('coordinator.AssemblyWorker')
    @patch('coordinator.BGMWorker')
    @patch('coordinator.NarrationWorker')
    @patch('coordinator.ClipChooserWorker')
    @patch('coordinator.StoryAnalysisWorker')
    def test_run_workflow(self, mock_story_worker, mock_clip_worker, mock_narration_worker, mock_bgm_worker, mock_assembly_worker):
        """Test complete workflow execution."""
        # Setup mock workers
        mock_story_instance = mock_story_worker.return_value
        mock_story_instance.run.return_value = {"scenes": [{"description": "scene1", "duration": 10}]}
        
        mock_clip_instance = mock_clip_worker.return_value
        mock_clip_instance.run.return_value = {"clips": [{"description": "clip1", "duration": 5}]}
        
        mock_narration_instance = mock_narration_worker.return_value
        mock_narration_instance.run.return_value = {"narration": "Generated narration"}
        
        mock_bgm_instance = mock_bgm_worker.return_value
        mock_bgm_instance.run.return_value = {"bgm_options": ["track1", "track2"]}
        
        mock_assembly_instance = mock_assembly_worker.return_value
        mock_assembly_instance.run.return_value = {
            "clips": [{"description": "clip1", "duration": 5}],
            "narrations": ["Generated narration"],
            "bgms": ["track1", "track2"],
            "timeline": ["Complete timeline"],
            "total_duration": 60.0
        }
        
        # Execute workflow
        result = self.agent.run(self.test_script)
        
        # Verify all workers were instantiated and called
        mock_story_worker.assert_called_once()
        mock_story_instance.run.assert_called_once_with(self.test_script)
        
        mock_clip_worker.assert_called_once()
        mock_clip_instance.run.assert_called_once()
        
        mock_narration_worker.assert_called_once()
        mock_narration_instance.run.assert_called_once()
        
        mock_bgm_worker.assert_called_once()
        mock_bgm_instance.run.assert_called_once()
        
        mock_assembly_worker.assert_called_once()
        mock_assembly_instance.run.assert_called_once()
        
        # Verify result structure
        self.assertIn("clips", result)
        self.assertIn("narrations", result)
        self.assertIn("bgms", result)
        self.assertIn("timeline", result)


if __name__ == "__main__":
    unittest.main()
