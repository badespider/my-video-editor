"""
Unit tests for Phase 1: Setup and Configuration
Tests Rule 1.1 (Config-Driven Design) and Rule 1.2 (Project Structure)
"""

import unittest
import os
import sys

# Add parent directory to path to import modules
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import config


class TestPhase1Configuration(unittest.TestCase):
    """Test Rule 1.1: Config-Driven Design"""
    
    def test_config_loads_successfully(self):
        """Assert config loads correctly in unittests"""
        self.assertIsNotNone(config.MODEL)
        self.assertIsNotNone(config.MODEL_BACKUP)
        self.assertIsInstance(config.API_KEYS, dict)
    
    def test_model_configuration(self):
        """Test model switching configuration"""
        valid_models = ['gpt-4', 'grok-4', 'memories-ai', 'mock', 'gpt-3.5-turbo']
        self.assertIn(config.MODEL, valid_models)
        self.assertIn(config.MODEL_BACKUP, valid_models)
    
    def test_environment_settings(self):
        """Test environment-based configuration"""
        valid_environments = ['dev', 'prod', 'test']
        self.assertIn(config.ENV, valid_environments)
        self.assertIsInstance(config.DEBUG, bool)
        self.assertIsInstance(config.MOCK_MODE, bool)
    
    def test_video_processing_settings(self):
        """Test video processing configuration values"""
        self.assertGreater(config.VIDEO_MAX_DURATION, 0)
        self.assertGreater(config.CLIP_MIN_DURATION, 0)
        self.assertIsNotNone(config.VIDEO_OUTPUT_DIR)
    
    def test_coverage_requirements(self):
        """Test coverage and threshold configurations"""
        self.assertGreaterEqual(config.COVERAGE_REQUIREMENT, 0.0)
        self.assertLessEqual(config.COVERAGE_REQUIREMENT, 1.0)
        self.assertGreaterEqual(config.MIN_COVERAGE_PERCENTAGE, 0)
        self.assertLessEqual(config.MIN_COVERAGE_PERCENTAGE, 100)
    
    def test_file_format_configuration(self):
        """Test supported file formats"""
        self.assertIsInstance(config.SUPPORTED_VIDEO_FORMATS, list)
        self.assertIsInstance(config.SUPPORTED_AUDIO_FORMATS, list)
        self.assertTrue(len(config.SUPPORTED_VIDEO_FORMATS) > 0)
        self.assertTrue(len(config.SUPPORTED_AUDIO_FORMATS) > 0)


class TestPhase1ProjectStructure(unittest.TestCase):
    """Test Rule 1.2: Project Structure"""
    
    def test_directory_structure(self):
        """Verify folder structure exists"""
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        
        # Check required directories exist
        required_dirs = ['workers', 'utils', 'tests', 'backend', 'temp']
        for directory in required_dirs:
            dir_path = os.path.join(base_dir, directory)
            self.assertTrue(os.path.exists(dir_path), f"Directory {directory} should exist")
    
    def test_module_imports(self):
        """Test that modules can be imported from new structure"""
        try:
            import workers
            import utils
            self.assertTrue(True, "Modules imported successfully")
        except ImportError as e:
            self.fail(f"Failed to import modules: {e}")
    
    def test_gitignore_exists(self):
        """Test that .gitignore file exists"""
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        gitignore_path = os.path.join(base_dir, '.gitignore')
        self.assertTrue(os.path.exists(gitignore_path), ".gitignore file should exist")
    
    def test_config_fallbacks(self):
        """Test default values when config values missing (mitigation)"""
        # Test that config has reasonable defaults
        self.assertIsNotNone(config.MODEL)
        self.assertIsNotNone(config.MODEL_BACKUP)
        
        # Test environment fallback
        if not hasattr(config, 'ENV') or not config.ENV:
            self.assertEqual(config.ENV, 'dev', "Should default to 'dev' environment")


if __name__ == '__main__':
    unittest.main()
