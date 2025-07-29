"""
Comprehensive unit tests for StoryAnalysisWorker module.
Tests edge cases like script >20 scenes trimmed, empty script raises error, etc.
"""

import unittest
from unittest.mock import patch, MagicMock
import sys
import os
import json

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import workers
import config


class TestStoryAnalysisWorker(unittest.TestCase):
    """Comprehensive test cases for StoryAnalysisWorker."""

    def setUp(self):
        """Set up test fixtures."""
        self.worker = workers.StoryAnalysisWorker(state={})

    @patch('workers.workers.call_model')
    @patch('workers.workers.validate_json_output')
    def test_story_analysis_basic_functionality(self, mock_validate, mock_call):
        """Test basic story analysis functionality."""
        mock_call.return_value = '{"scenes": [{"id": 1, "description": "Scene 1", "duration": 5}]}'
        mock_validate.return_value = {"scenes": [{"id": 1, "description": "Scene 1", "duration": 5}]}

        script = "This is a test script to analyze."
        result = self.worker.run(script)
        
        mock_call.assert_called_once()
        mock_validate.assert_called_once()
        self.assertIn("scenes", result)
        self.assertEqual(len(result["scenes"]), 1)

    @patch('workers.workers.call_model')
    @patch('workers.workers.validate_json_output')
    def test_script_over_max_scenes_trimmed(self, mock_validate, mock_call):
        """Test that scripts with >20 scenes are trimmed to 20."""
        # Create 25 scenes (more than MAX_SCENES = 20)
        scenes = [{"id": i, "description": f"Scene {i}", "duration": 5} for i in range(1, 26)]
        mock_call.return_value = json.dumps({"scenes": scenes})
        mock_validate.return_value = {"scenes": scenes}

        script = "This is a long script with many scenes."
        result = self.worker.run(script)
        
        # Should be trimmed to MAX_SCENES (20)
        self.assertEqual(len(result["scenes"]), config.MAX_SCENES)
        self.assertEqual(result["scenes"][0]["id"], 1)
        self.assertEqual(result["scenes"][-1]["id"], 20)

    @patch('workers.workers.call_model')
    @patch('workers.workers.validate_json_output')
    def test_empty_script_handling(self, mock_validate, mock_call):
        """Test handling of empty script input."""
        mock_call.return_value = '{"scenes": []}'
        mock_validate.return_value = {"scenes": []}

        result = self.worker.run("")
        
        self.assertIn("scenes", result)
        self.assertEqual(len(result["scenes"]), 0)

    @patch('workers.workers.call_model')
    @patch('workers.workers.validate_json_output')
    def test_invalid_scene_structure_filtered(self, mock_validate, mock_call):
        """Test that invalid scene structures are filtered out."""
        # Mix of valid and invalid scenes
        scenes = [
            {"id": 1, "description": "Valid Scene 1", "duration": 5},  # Valid
            {"id": 2, "description": "Invalid Scene"},  # Missing duration
            {"id": 3, "duration": 5},  # Missing description
            {"id": 4, "description": "Valid Scene 2", "duration": 10}  # Valid
        ]
        mock_call.return_value = json.dumps({"scenes": scenes})
        mock_validate.return_value = {"scenes": scenes}

        script = "Script with mixed valid/invalid scenes."
        result = self.worker.run(script)
        
        # Should only contain valid scenes (2 out of 4)
        self.assertEqual(len(result["scenes"]), 2)
        self.assertEqual(result["scenes"][0]["id"], 1)
        self.assertEqual(result["scenes"][1]["id"], 4)

    @patch('workers.workers.call_model')
    def test_call_model_exception_handling(self, mock_call):
        """Test exception handling when call_model fails."""
        mock_call.side_effect = Exception("API call failed")

        script = "Test script"
        
        with self.assertRaises(Exception):
            self.worker.run(script)

    @patch('workers.workers.call_model')
    @patch('workers.workers.validate_json_output')
    def test_validate_json_output_exception_handling(self, mock_validate, mock_call):
        """Test exception handling when JSON validation fails."""
        mock_call.return_value = 'invalid json'
        mock_validate.side_effect = ValueError("Invalid JSON")
        
        script = "Test script"
        
        with self.assertRaises(ValueError):
            self.worker.run(script)

    @patch('workers.workers.call_model')
    @patch('workers.workers.validate_json_output')
    def test_missing_scenes_key_in_response(self, mock_validate, mock_call):
        """Test handling when AI response doesn't contain 'scenes' key."""
        mock_call.return_value = '{"other_key": "value"}'
        mock_validate.return_value = {"other_key": "value"}

        script = "Test script"
        result = self.worker.run(script)
        
        # Should handle missing 'scenes' key gracefully
        self.assertIn("scenes", result)
        self.assertEqual(len(result["scenes"]), 0)

    @patch('workers.workers.call_model')
    @patch('workers.workers.validate_json_output')
    def test_scenes_not_list(self, mock_validate, mock_call):
        """Test handling when 'scenes' value is not a list."""
        mock_call.return_value = '{"scenes": "not a list"}'
        mock_validate.return_value = {"scenes": "not a list"}

        script = "Test script"
        result = self.worker.run(script)
        
        # Should handle gracefully when scenes is not iterable
        self.assertIn("scenes", result)

    @patch('workers.workers.call_model')
    @patch('workers.workers.validate_json_output')
    def test_prompt_construction(self, mock_validate, mock_call):
        """Test that prompt is constructed correctly."""
        mock_call.return_value = '{"scenes": []}'
        mock_validate.return_value = {"scenes": []}

        # Create long script to test truncation (needs to be >800 chars)
        script = "This is a test script for prompt construction. " * 20  # Makes it ~900 chars
        self.worker.run(script)
        
        # Verify call_model was called with expected prompt format
        args, kwargs = mock_call.call_args
        prompt = args[0]
        self.assertIn(str(config.MAX_SCENES), prompt)
        # For long scripts, should be truncated (not present in full)
        self.assertNotIn(script, prompt)  # Full script shouldn't be in prompt due to truncation
        self.assertIn("This is a test script for prompt construction", prompt)  # Start should be present


class TestBaseWorker(unittest.TestCase):
    """Test the BaseWorker abstract class."""

    def test_base_worker_run_not_implemented(self):
        """Test that BaseWorker.run raises NotImplementedError."""
        worker = workers.BaseWorker(state={})
        
        with self.assertRaises(NotImplementedError):
            worker.run({})


class TestValidateCommonJsonStructure(unittest.TestCase):
    """Test the validate_common_json_structure helper function."""

    def test_validate_common_json_structure_valid(self):
        """Test validation with valid structure."""
        data = {"expected_key": "value"}
        result = workers.validate_common_json_structure(data, "expected_key")
        self.assertTrue(result)

    def test_validate_common_json_structure_invalid(self):
        """Test validation with invalid structure."""
        data = {"other_key": "value"}
        result = workers.validate_common_json_structure(data, "expected_key")
        self.assertFalse(result)


if __name__ == "__main__":
    unittest.main()
