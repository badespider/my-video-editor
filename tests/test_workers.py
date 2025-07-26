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
import config


class TestWorkers(unittest.TestCase):
    """Test cases for workers module."""

    @patch('workers.call_model')
    @patch('workers.validate_json_output')
    def test_story_analysis_worker(self, mock_validate, mock_call):
        """Test StoryAnalysisWorker"""
        mock_call.return_value = '{"scenes": [{"id": 1, "description": "Scene 1", "duration": 5}]}'
        mock_validate.return_value = {"scenes": [{"id": 1, "description": "Scene 1", "duration": 5}]}
        worker = workers.StoryAnalysisWorker(state={})

        script = "This is a test script to analyze."
        result = worker.run(script)
        
        mock_call.assert_called_once()
        mock_validate.assert_called_once()
        self.assertIn("scenes", result)

    def test_clip_chooser_worker(self):
        """Test ClipChooserWorker with scene analysis"""
        worker = workers.ClipChooserWorker(state={})

        # Test with sample scenes
        analysis = {
            "scenes": [
                {"id": 1, "description": "A fierce battle scene with intense fighting", "duration": 15},
                {"id": 2, "description": "A happy celebration with joy and laughter", "duration": 12}
            ]
        }
        result = worker.run(analysis)

        # Check structure and validation
        self.assertIn("clips", result)
        clips = result["clips"]
        self.assertEqual(len(clips), 2)
        
        # Test first clip (intense mood)
        self.assertEqual(clips[0]["mood"], "intense")
        self.assertEqual(clips[0]["duration"], 10)  # Fixed 10-second clips
        self.assertIn("fierce battle", clips[0]["description"].lower())
        
        # Test second clip (happy mood)
        self.assertEqual(clips[1]["mood"], "happy")
        self.assertEqual(clips[1]["duration"], 10)
        
    def test_clip_chooser_worker_validation(self):
        """Test ClipChooserWorker validation"""
        worker = workers.ClipChooserWorker(state={})
        
        # Test with invalid input
        with self.assertRaises(ValueError):
            worker.run({})
        
        with self.assertRaises(ValueError):
            worker.run({"invalid": "data"})
            
    def test_clip_chooser_mood_extraction(self):
        """Test mood extraction logic"""
        worker = workers.ClipChooserWorker(state={})
        
        # Test different mood keywords
        test_cases = [
            ("A sad death scene with crying", "sad"),
            ("Mysterious shadows in the dark", "mysterious"),
            ("Intense battle with fierce conflict", "intense"),
            ("Happy celebration with joy", "happy"),
            ("Normal everyday scene", "neutral")
        ]
        
        for description, expected_mood in test_cases:
            mood = worker._extract_mood(description)
            self.assertEqual(mood, expected_mood, f"Failed for: {description}")

    def test_narration_worker(self):
        """Test NarrationWorker"""
        worker = workers.NarrationWorker(state={})

        script = "This is a test script to narrate."
        result = worker.run(script)

        # Check the stub implementation returns expected structure
        self.assertIn("narration", result)
        self.assertEqual(result["narration"], "Default narration text.")

    def test_bgm_worker(self):
        """Test BGMWorker"""
        worker = workers.BGMWorker(state={})

        analysis = {"scenes": []}
        result = worker.run(analysis)

        # Check the stub implementation returns expected structure
        self.assertIn("bgm_options", result)
        self.assertEqual(result["bgm_options"], ["Default BGM Option 1"])

    def test_assembly_worker(self):
        """Test AssemblyWorker"""
        worker = workers.AssemblyWorker(state={})

        clips = {"clips": [{"description": "Clip 1"}]}
        narrations = {"narrations": "Narration text"}
        bgms = {"bgm_options": ["BGM Option"]}

        result = worker.run(clips, narrations, bgms)
        self.assertIn("timeline", result)

if __name__ == "__main__":
    unittest.main()


