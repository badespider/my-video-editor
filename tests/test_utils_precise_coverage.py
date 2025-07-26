"""
Precise tests to hit exact lines for 100% coverage of utils.py.
"""

import unittest
from unittest.mock import patch, MagicMock
import sys
import os

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import utils
import config


class DirectTestForCoverage(unittest.TestCase):
    def test_backup_model_lines_73_74(self):
        """Test lines 73-74 using backup mock implementation."""
        original_model = config.MODEL
        original_backup = config.MODEL_BACKUP
        original_game_sdk = utils.GameSDK

        try:
            config.MODEL = "primary"
            config.MODEL_BACKUP = "backup"
            
            # Setup mock so primary fails, backup falls to mock
            def failing_primary_call(*args, **kwargs):
                raise Exception("Primary call failed")

            mock_sdk = MagicMock()
            mock_sdk.llm.call.side_effect = failing_primary_call

            utils.GameSDK = lambda: mock_sdk

            # Directly use call_model to simulate with primary failure
            with patch('utils.GameSDK', None):
                result = utils.call_model("prompt", model="primary")
                self.assertIn("Mock response from backup", result)

        finally:
            config.MODEL = original_model
            config.MODEL_BACKUP = original_backup
            utils.GameSDK = original_game_sdk

    def test_clips_structure_lines_216_217(self):
        """Test lines 216-217 to trigger TypeError and AttributeError."""
        class ProblemClip:
            def __contains__(self, key):
                raise AttributeError("Simulated error")

        clips_data = [ProblemClip()]
        self.assertFalse(utils.validate_clips_structure(clips_data))

        class ProblemClipTypeError:
            def __contains__(self, key):
                raise TypeError("Simulated error")

        clips_data_type_error = [ProblemClipTypeError()]
        self.assertFalse(utils.validate_clips_structure(clips_data_type_error))


if __name__ == "__main__":
    unittest.main()
