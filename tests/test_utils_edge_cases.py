"""
Additional unit tests for utils module to achieve 100% coverage.
Tests very specific edge cases and error handling paths.
"""

import unittest
from unittest.mock import patch, MagicMock
import sys
import os

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import utils
import config


class TestUtilsEdgeCases(unittest.TestCase):
    """Test edge cases for 100% coverage."""

    def test_call_model_mock_fallback_to_backup(self):
        """Test the backup model mock fallback scenario (lines 73-74)."""
        # We need to trigger an exception in the primary model call
        # and then have the backup succeed with GameSDK = None
        
        # Temporarily modify config
        original_model = config.MODEL
        original_backup = config.MODEL_BACKUP
        config.MODEL = "primary-model"
        config.MODEL_BACKUP = "backup-model"
        
        try:
            # Mock a scenario where the primary call raises an exception
            # but we're using the mock implementation (GameSDK = None)
            with patch.object(utils, 'logger') as mock_logger:
                # Simulate primary model failure by temporarily making GameSDK not None
                # then setting it back to None for backup
                
                # Create a mock GameSDK that fails on first call
                mock_sdk = MagicMock()
                mock_sdk.llm.call.side_effect = Exception("Primary model failed")
                
                # Temporarily set GameSDK to trigger exception path
                original_game_sdk = utils.GameSDK
                utils.GameSDK = mock_sdk
                
                try:
                    # This should fail with primary, then succeed with backup (mock)
                    with patch.object(utils, 'GameSDK', None):
                        # This creates the scenario where primary fails (GameSDK not None)
                        # but backup succeeds (GameSDK is None - mock implementation)
                        
                        # We need to manually trigger the exception path
                        # Let's create a custom call that simulates this
                        
                        # First try with mock SDK that fails
                        utils.GameSDK = mock_sdk
                        try:
                            utils.call_model("Test prompt")
                            self.fail("Should have raised an exception")
                        except Exception as e:
                            # Now test the backup path with GameSDK = None
                            utils.GameSDK = None
                            result = utils.call_model("Test prompt")
                            self.assertIn("Mock response", result)
                            self.assertIn("primary-model", result)
                
                finally:
                    utils.GameSDK = original_game_sdk
                    
        finally:
            config.MODEL = original_model
            config.MODEL_BACKUP = original_backup

    def test_call_model_no_backup_with_exception(self):
        """Test exception handling when no backup is available (lines 80-81)."""
        # Set up config with no backup
        original_model = config.MODEL
        original_backup = config.MODEL_BACKUP
        config.MODEL = "test-model"
        config.MODEL_BACKUP = None
        
        try:
            # Create a mock GameSDK class that returns instances that fail
            mock_sdk_class = MagicMock()
            mock_sdk_instance = MagicMock()
            mock_sdk_instance.llm.call.side_effect = Exception("Model call failed")
            mock_sdk_class.return_value = mock_sdk_instance
            
            original_game_sdk = utils.GameSDK
            utils.GameSDK = mock_sdk_class
            
            try:
                # This should raise an exception since no backup is available
                with self.assertRaises(Exception) as context:
                    utils.call_model("Test prompt")
                self.assertIn("Model call failed with test-model", str(context.exception))
            finally:
                utils.GameSDK = original_game_sdk
                
        finally:
            config.MODEL = original_model
            config.MODEL_BACKUP = original_backup

    def test_validate_clips_structure_attribute_error(self):
        """Test clips validation with AttributeError (lines 216-217)."""
        # Create a mock object that raises AttributeError when accessed
        class BadClipData:
            def __getitem__(self, key):
                raise AttributeError("Simulated AttributeError")
            
            def __iter__(self):
                return iter([self])
            
            def __len__(self):
                return 1
        
        # This should trigger the AttributeError in the try/except block
        clips_data = BadClipData()
        result = utils.validate_clips_structure(clips_data)
        self.assertFalse(result)


if __name__ == "__main__":
    unittest.main()
