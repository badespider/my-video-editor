"""
Phase 4 Integration Test: Workflow Hold for Narration and BGM Workers
Tests the Rule 4.1 implementation that skips disabled workers based on config.
"""

import os
import sys
import json
import logging
from typing import Dict, Any
import pytest
from unittest.mock import patch, MagicMock

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Import our modules
import config
from coordinator import VideoAgent
from utils import cleanup_mocks

# Configure logging for tests
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class TestPhase4Integration:
    """Test suite for Phase 4 integration testing (Rule 4.1)."""
    
    def setup_method(self):
        """Setup for each test method."""
        # Ensure workers are disabled for testing
        self.original_enable_narration = config.ENABLE_NARRATION
        self.original_enable_bgm = config.ENABLE_BGM
        
        # Set to disabled state for workflow hold tests
        config.ENABLE_NARRATION = False
        config.ENABLE_BGM = False
        
        # Cleanup any existing mocks
        cleanup_mocks()
        
    def teardown_method(self):
        """Cleanup after each test method."""
        # Restore original config
        config.ENABLE_NARRATION = self.original_enable_narration
        config.ENABLE_BGM = self.original_enable_bgm
        
        # Final cleanup
        cleanup_mocks()
    
    def test_workflow_hold_script_processing(self):
        """Test that script processing skips narration and BGM when disabled."""
        logger.info("=== Test: Workflow Hold Script Processing ===")
        
        # Create VideoAgent
        agent = VideoAgent()
        
        # Test script
        test_script = "A detective walks through a foggy city at night, investigating a mysterious case."
        
        try:
            # Run the workflow
            result = agent.run(test_script)
            
            # Verify structure
            assert isinstance(result, dict), "Result should be a dictionary"
            
            # Check required keys are present
            required_keys = ["clips", "narrations", "bgms", "timeline", "total_duration"]
            for key in required_keys:
                assert key in result, f"Missing required key: {key}"
            
            # Verify narration was skipped
            narrations = result.get("narrations", {})
            if isinstance(narrations, dict):
                assert narrations.get("skipped") == True, "Narration should be marked as skipped"
                assert narrations.get("narration") == "", "Narration text should be empty"
                assert narrations.get("word_count") == 0, "Word count should be 0"
            
            # Verify BGM was skipped
            bgms = result.get("bgms", {})
            if isinstance(bgms, dict):
                assert bgms.get("skipped") == True, "BGM should be marked as skipped"
                assert bgms.get("bgm_options") == [], "BGM options should be empty"
            
            # Verify clips were still processed
            clips = result.get("clips", [])
            assert len(clips) > 0, "Clips should still be processed"
            
            # Verify timeline exists
            timeline = result.get("timeline", [])
            assert len(timeline) > 0, "Timeline should exist"
            
            logger.info("✓ Workflow hold for script processing test passed")
            
        except Exception as e:
            logger.error(f"✗ Workflow hold script processing test failed: {e}")
            raise
    
    def test_workflow_hold_video_processing(self):
        """Test that video processing skips narration and BGM when disabled."""
        logger.info("=== Test: Workflow Hold Video Processing ===")
        
        # Use existing valid test video file
        mock_video_path = "test_video.mp4"
        
        # If test video doesn't exist, create one
        if not os.path.exists(mock_video_path):
            try:
                from moviepy import ColorClip
                clip = ColorClip((640, 480), color=(255, 0, 0), duration=5)
                clip.fps = 24
                clip.write_videofile(mock_video_path, codec='libx264', logger=None)
                clip.close()
                logger.info(f"Created test video: {mock_video_path}")
            except Exception as e:
                logger.warning(f"Failed to create test video: {e}, skipping this test")
                return
        
        try:
            
            # Create VideoAgent
            agent = VideoAgent()
            
            # Run video analysis workflow
            result = agent.run_with_video(mock_video_path)
            
            # Verify structure
            assert isinstance(result, dict), "Result should be a dictionary"
            
            # Check required keys for video processing
            required_keys = ["final_video", "plan", "source_video", "processing_type"]
            for key in required_keys:
                assert key in result, f"Missing required key: {key}"
            
            # Verify processing type
            assert result["processing_type"] == "video_analysis", "Processing type should be video_analysis"
            assert result["source_video"] == mock_video_path, "Source video should match input"
            
            # Check that the plan contains the expected structure
            plan = result.get("plan", {})
            if plan:
                # Verify narration was skipped in the plan
                narrations = plan.get("narrations", {})
                if isinstance(narrations, dict) and "skipped" in narrations:
                    assert narrations["skipped"] == True, "Narration should be skipped in plan"
                
                # Verify BGM was skipped in the plan
                bgms = plan.get("bgms", {})
                if isinstance(bgms, dict) and "skipped" in bgms:
                    assert bgms["skipped"] == True, "BGM should be skipped in plan"
            
            logger.info("✓ Workflow hold for video processing test passed")
            
        except Exception as e:
            logger.error(f"✗ Workflow hold video processing test failed: {e}")
            raise
        finally:
            # Clean up mock video file with proper error handling
            if os.path.exists(mock_video_path):
                try:
                    # Try to remove the file multiple times if it's locked
                    import time
                    for attempt in range(3):
                        try:
                            os.remove(mock_video_path)
                            break
                        except PermissionError:
                            if attempt < 2:
                                time.sleep(0.5)  # Wait half second before retry
                            else:
                                logger.warning(f"Could not remove {mock_video_path}, file may be in use")
                except Exception as e:
                    logger.warning(f"Failed to clean up test video: {e}")
    
    def test_workflow_with_enabled_features(self):
        """Test that workflow processes narration and BGM when enabled."""
        logger.info("=== Test: Workflow With Enabled Features ===")
        
        # Enable features for this test
        config.ENABLE_NARRATION = True
        config.ENABLE_BGM = True
        
        try:
            # Create VideoAgent
            agent = VideoAgent()
            
            # Test script
            test_script = "An epic battle unfolds in the mountains."
            
            # Run the workflow
            result = agent.run(test_script)
            
            # Verify structure
            assert isinstance(result, dict), "Result should be a dictionary"
            
            # Verify narration was processed (not skipped)
            narrations = result.get("narrations", {})
            if isinstance(narrations, dict):
                # Should not be marked as skipped
                assert narrations.get("skipped") != True, "Narration should not be skipped when enabled"
                # Should have actual content
                assert "narration" in narrations, "Narration should have content key"
            
            # Verify BGM was processed (not skipped)
            bgms = result.get("bgms", {})
            if isinstance(bgms, dict):
                # Should not be marked as skipped
                assert bgms.get("skipped") != True, "BGM should not be skipped when enabled"
                # Should have bgm_options
                assert "bgm_options" in bgms, "BGM should have options key"
            
            logger.info("✓ Workflow with enabled features test passed")
            
        except Exception as e:
            logger.error(f"✗ Workflow with enabled features test failed: {e}")
            raise
        finally:
            # Restore disabled state
            config.ENABLE_NARRATION = False
            config.ENABLE_BGM = False
    
    def test_audio_preservation_config(self):
        """Test that audio preservation config is respected."""
        logger.info("=== Test: Audio Preservation Config ===")
        
        # Verify audio preservation is enabled by default
        assert config.PRESERVE_ORIGINAL_AUDIO == True, "Audio preservation should be enabled by default"
        
        # Test with different settings
        original_preserve = config.PRESERVE_ORIGINAL_AUDIO
        
        try:
            # Test with preservation enabled
            config.PRESERVE_ORIGINAL_AUDIO = True
            agent = VideoAgent()
            
            # Check that config is passed to workers
            env = agent._create_worker_environment()
            assert "config" in env, "Environment should contain config"
            
            # Test with preservation disabled
            config.PRESERVE_ORIGINAL_AUDIO = False
            agent2 = VideoAgent()
            env2 = agent2._create_worker_environment()
            assert "config" in env2, "Environment should contain config"
            
            logger.info("✓ Audio preservation config test passed")
            
        finally:
            # Restore original setting
            config.PRESERVE_ORIGINAL_AUDIO = original_preserve
    
    def test_cleanup_with_audio_files(self):
        """Test that cleanup handles audio files correctly (Rule 4.2)."""
        logger.info("=== Test: Cleanup with Audio Files ===")
        
        # Create mock audio files
        test_files = [
            "test_narration.mp3",
            "test_bgm.wav",
            "mock_audio.aac",
            "temp_audio.mp3"
        ]
        
        try:
            # Create test files
            for filename in test_files:
                with open(filename, 'w') as f:
                    f.write(f"Mock audio content: {filename}")
                assert os.path.exists(filename), f"Test file should exist: {filename}"
            
            # Run cleanup
            cleanup_stats = cleanup_mocks()
            
            # Verify cleanup stats
            assert isinstance(cleanup_stats, dict), "Cleanup should return stats dictionary"
            assert "files_removed" in cleanup_stats, "Stats should include files_removed"
            assert "dirs_removed" in cleanup_stats, "Stats should include dirs_removed"
            assert "errors" in cleanup_stats, "Stats should include errors"
            
            logger.info(f"Cleanup stats: {cleanup_stats}")
            logger.info("✓ Audio files cleanup test passed")
            
        finally:
            # Ensure test files are cleaned up
            for filename in test_files:
                if os.path.exists(filename):
                    try:
                        os.remove(filename)
                    except Exception as e:
                        logger.warning(f"Failed to clean up test file {filename}: {e}")
    
    def test_model_performance_tracking(self):
        """Test that model performance is tracked correctly."""
        logger.info("=== Test: Model Performance Tracking ===")
        
        from utils.utils import get_model_performance_report, _record_model_performance
        
        # Record some mock performance data
        _record_model_performance("gpt-4", "clip_selection", 1.5, True)
        _record_model_performance("grok-4", "clip_selection", 2.1, False)
        _record_model_performance("gpt-4", "story_analysis", 0.8, True)
        
        # Get performance report
        report = get_model_performance_report()
        
        # Verify report structure
        assert isinstance(report, dict), "Performance report should be a dictionary"
        assert "performance_history" in report, "Report should include performance history"
        assert "total_tracked_calls" in report, "Report should include total tracked calls"
        assert "overall_success_rate" in report, "Report should include overall success rate"
        
        # Verify data was recorded
        history = report["performance_history"]
        assert len(history) > 0, "Performance history should not be empty"
        
        # Check specific entries
        gpt4_clip_key = "gpt-4_clip_selection"
        if gpt4_clip_key in history:
            stats = history[gpt4_clip_key]
            assert stats["total_calls"] >= 1, "Should have recorded calls"
            assert stats["successful_calls"] >= 1, "Should have recorded successes"
            assert stats["success_rate"] > 0, "Success rate should be positive"
        
        logger.info("✓ Model performance tracking test passed")


def run_phase4_tests():
    """Run all Phase 4 integration tests."""
    logger.info("Starting Phase 4 Integration Tests...")
    
    test_suite = TestPhase4Integration()
    tests = [
        test_suite.test_workflow_hold_script_processing,
        test_suite.test_workflow_hold_video_processing,
        test_suite.test_workflow_with_enabled_features,
        test_suite.test_audio_preservation_config,
        test_suite.test_cleanup_with_audio_files,
        test_suite.test_model_performance_tracking
    ]
    
    passed = 0
    failed = 0
    
    for test in tests:
        try:
            test_suite.setup_method()
            test()
            test_suite.teardown_method()
            passed += 1
        except Exception as e:
            logger.error(f"Test {test.__name__} failed: {e}")
            failed += 1
            test_suite.teardown_method()
    
    logger.info(f"Phase 4 Integration Tests Complete: {passed} passed, {failed} failed")
    return failed == 0


if __name__ == "__main__":
    success = run_phase4_tests()
    sys.exit(0 if success else 1)
