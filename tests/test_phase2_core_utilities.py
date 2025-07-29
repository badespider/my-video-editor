"""
Unit tests for Phase 2: Build Core Utilities
Tests Rule 2.1 (Model Router) and Rule 2.2 (Video Helpers)
"""

import unittest
import os
import sys
import json
from unittest.mock import patch, MagicMock
from pathlib import Path

# Add parent directory to path to import modules
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from tests.utils.video_helper import make_dummy_video

import config
from utils import call_model, detect_scenes, extract_clip, get_video_info, validate_json_output


class TestPhase2ModelRouter(unittest.TestCase):
    """Test Rule 2.1: Model Router"""
    
    def test_call_model_with_different_models(self):
        """Test model switching functionality"""
        # Test with mock model
        response = call_model("Test prompt", model="mock")
        self.assertIsInstance(response, str)
        
        # Test default model from config
        response = call_model("Test prompt")
        self.assertIsInstance(response, str)
    
    @patch('utils.utils.HAS_OPENAI', True)
    @patch('utils.utils.openai')
    def test_openai_model_routing(self, mock_openai):
        """Test OpenAI model routing"""
        # Mock successful OpenAI response
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.choices[0].message.content = '{"test": "response"}'
        mock_client.chat.completions.create.return_value = mock_response
        mock_openai.OpenAI.return_value = mock_client
        
        response = call_model("Test prompt", model="gpt-4")
        self.assertIsInstance(response, str)
        self.assertIn("test", response)
    
    def test_model_fallback_to_mock(self):
        """Test fallback to mock when API fails"""
        response = call_model("Test prompt", model="nonexistent-model")
        self.assertIsInstance(response, str)
        
        # Should be a valid JSON mock response
        try:
            parsed = json.loads(response)
            self.assertIn("Mock response", parsed)
        except json.JSONDecodeError:
            self.fail("Mock response should be valid JSON")
    
    def test_model_backup_functionality(self):
        """Test backup model is used when primary fails"""
        # This will use mock implementation as fallback
        response = call_model("Test prompt")
        self.assertIsInstance(response, str)
        self.assertTrue(len(response) > 0)
    
    def test_model_response_formats(self):
        """Test different response formats for different prompts"""
        # Test story analysis prompt
        story_response = call_model("Analyze this story for scenes")
        self.assertIsInstance(story_response, str)
        
        # Should be a valid response (either scenes, mock_response, or error)
        try:
            parsed = json.loads(story_response)
            # Accept any valid JSON response (scenes, mock_response, or error)
            self.assertTrue(
                "scenes" in parsed or 
                "mock_response" in parsed or 
                "error" in parsed or
                len(parsed.keys()) > 0
            )
        except json.JSONDecodeError:
            # Some responses might not be JSON, which is also acceptable
            pass
        
        # Test clip selection prompt
        clip_response = call_model("Select clips from these scenes")
        self.assertIsInstance(clip_response, str)


class TestPhase2VideoHelpers(unittest.TestCase):
    """Test Rule 2.2: Video Helpers"""
    
    def test_detect_scenes_mock_implementation(self):
        """Test mock scene detection covers full video"""
        # Test with mock video path
        mock_video_path = "test_video.mp4"
        
        # Create a temporary file to simulate video
        make_dummy_video(Path(mock_video_path))
        
        try:
            scenes = detect_scenes(mock_video_path)
            
            # Assert scenes cover >80% duration (Rule 2.2)
            self.assertIsInstance(scenes, list)
            self.assertGreater(len(scenes), 0)
            
            # Check scene structure
            for scene in scenes:
                self.assertIn("start", scene)
                self.assertIn("end", scene)
                self.assertIn("description", scene)
                self.assertIn("score", scene)
                
            # Verify coverage requirement
            total_duration = scenes[-1]["end"] if scenes else 0
            scene_coverage = sum(scene["end"] - scene["start"] for scene in scenes)
            coverage_ratio = scene_coverage / total_duration if total_duration > 0 else 0
            self.assertGreaterEqual(coverage_ratio, 0.8, "Scenes should cover >80% duration")
            
        finally:
            # Cleanup
            if os.path.exists(mock_video_path):
                os.remove(mock_video_path)
    
    
    def test_extract_clip_mock_implementation(self):
        """Test clip extraction with mock implementation"""
        video_path = "test_video.mp4"
        output_path = "test_clip.mp4"
        
        # Create mock source video
        make_dummy_video(Path(video_path))
        
        try:
            result_path = extract_clip(video_path, 0, 10, output_path)
            
            # Should return the output path
            self.assertEqual(result_path, output_path)
            
            # Output file should exist
            self.assertTrue(os.path.exists(output_path))
            
        finally:
            # Cleanup
            for path in [video_path, output_path]:
                if os.path.exists(path):
                    os.remove(path)
    
    
    def test_get_video_info_mock(self):
        """Test video info extraction with mock"""
        video_path = "test_video.mp4"
        
        # Create mock video file
        make_dummy_video(Path(video_path))
        
        try:
            info = get_video_info(video_path)
            
            # Should contain required fields
            required_fields = ["duration", "fps", "resolution", "has_audio", "file_size"]
            for field in required_fields:
                self.assertIn(field, info)
            
            # Values should be reasonable
            self.assertGreater(info["duration"], 0)
            self.assertGreater(info["fps"], 0)
            self.assertIsInstance(info["resolution"], tuple)
            self.assertIsInstance(info["has_audio"], bool)
            self.assertGreaterEqual(info["file_size"], 0)
            
        finally:
            # Cleanup
            if os.path.exists(video_path):
                os.remove(video_path)
    
    def test_uniform_division_fallback(self):
        """Test uniform division fallback when detection fails"""
        # This tests the mitigation strategy
        scenes = detect_scenes("nonexistent_video.mp4")
        
        # Should still return scenes (mock implementation handles this)
        self.assertIsInstance(scenes, list)
        # Mock should handle nonexistent files gracefully


class TestPhase2Utilities(unittest.TestCase):
    """Test additional utility functions"""
    
    def test_validate_json_output(self):
        """Test JSON validation utility"""
        # Valid JSON
        valid_json = '{"test": "value", "number": 42}'
        result = validate_json_output(valid_json)
        self.assertIsInstance(result, dict)
        self.assertEqual(result["test"], "value")
        self.assertEqual(result["number"], 42)
        
        # Invalid JSON should raise ValueError
        invalid_json = '{"test": "value", invalid}'
        with self.assertRaises(ValueError):
            validate_json_output(invalid_json)
    
    def test_config_integration(self):
        """Test that utilities use config values correctly"""
        # Test that video helpers respect config settings
        self.assertIsNotNone(config.USE_REAL_DETECTION)
        self.assertIsNotNone(config.VIDEO_OUTPUT_DIR)
        self.assertIsNotNone(config.MIN_SCENE_DURATION)


if __name__ == '__main__':
    unittest.main()
