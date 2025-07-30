"""
Unit tests for Phase 3: Develop Workers
Tests Rule 3.1 (Worker Modularity), Rule 3.2 (Clip Diversity), and Rule 3.3 (Assembly Rules)
"""

import unittest
import os
import sys
import shutil
from pathlib import Path
from unittest.mock import patch, MagicMock

# Add parent directory to path to import modules
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from tests.utils.video_helper import make_dummy_video
from tests.mocks.video_shims import MockVideoFileClip, MockCompositeVideoClip, mock_concatenate_videoclips, create_mock_video_file

import config
from workers import IngestionWorker, StoryAnalysisWorker, ClipChooserWorker, NarrationWorker, BGMWorker, AssemblyWorker
from utils import get_video_info


class TestPhase3Workers(unittest.TestCase):
    """Test Phase 3 Workers"""
    
    def setUp(self):
        """Set up test dependencies and create temp directory"""
        self.video_path = "test_video.mp4"
        self.temp_dir = "temp_test"
        os.makedirs(self.temp_dir, exist_ok=True)
        
        # Create a mock video file
        make_dummy_video(Path(self.video_path))

        # Store original config value
        self.original_output_dir = config.VIDEO_OUTPUT_DIR
        config.VIDEO_OUTPUT_DIR = self.temp_dir  # Use temp directory for outputs

    def tearDown(self):
        """Clean up test dependencies and remove temp files"""
        if os.path.exists(self.video_path):
            os.remove(self.video_path)
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)
        
        # Restore original config value
        config.VIDEO_OUTPUT_DIR = self.original_output_dir

    def test_ingestion_worker(self):
        """Test IngestionWorker processes video and outputs scenes"""
        worker = IngestionWorker(state={})
        result = worker.run(self.video_path)

        self.assertIn("scenes", result)
        self.assertIn("coverage_percentage", result)
        self.assertIn("total_duration", result)
        self.assertGreater(len(result["scenes"]), 0)

    def test_clip_chooser_worker(self):
        """Test ClipChooserWorker selects diverse scenes"""
        analysis = {
            "video_path": self.video_path,
            "total_duration": 300,
            "scenes": [
                {"start": 0, "end": 30, "score": 0.9, "description": "Action scene", "mood": "intense"},
                {"start": 40, "end": 70, "score": 0.8, "description": "Mystery scene", "mood": "mysterious"},
                {"start": 80, "end": 120, "score": 0.7, "description": "Drama scene", "mood": "sad"},
            ]
        }
        worker = ClipChooserWorker(state={})
        result = worker.run(analysis)
        
        self.assertIn("clips", result)
        self.assertGreater(len(result["clips"]), 0)

    def test_narration_worker(self):
        """Test NarrationWorker generates narration text"""
        clips_data = {
            "clips": [
                {"description": "Action scene", "mood": "intense", "duration": 15},
                {"description": "Mystery scene", "mood": "mysterious", "duration": 20},
            ]
        }
        worker = NarrationWorker(state={})
        result = worker.run(clips_data)
        
        self.assertIn("narration", result)
        self.assertIn("word_count", result)
        self.assertGreater(len(result["narration"]), 0)

    def test_bgm_worker(self):
        """Test BGMWorker generates BGM options"""
        clips_data = {
            "clips": [
                {"description": "Action scene", "mood": "intense", "duration": 15},
                {"description": "Mystery scene", "mood": "mysterious", "duration": 20},
            ]
        }
        worker = BGMWorker(state={})
        result = worker.run(clips_data)
        
        self.assertIn("bgm_options", result)
        self.assertIn("mood_analysis", result)
        self.assertGreater(len(result["bgm_options"]), 0)

    def test_assembly_worker(self):
        """Test AssemblyWorker assembles video clips into final video"""
        clips = {
            "clips": [
                {"path": os.path.join(self.temp_dir, "clip_1.mp4"), "description": "Action scene", "duration": 10},
                {"path": os.path.join(self.temp_dir, "clip_2.mp4"), "description": "Mystery scene", "duration": 15}
            ]
        }
        narrations = {"narration": "In a dramatic turn of events, the story unfolds."}
        bgms = {"bgm_options": ["Epic orchestral", "Dramatic music"]}

        # Create mock clips
        for clip in clips["clips"]:
            create_mock_video_file(clip["path"])

        worker = AssemblyWorker(state={})
        result = worker.run(clips, narrations, bgms)

        self.assertIn("final_video", result)
        self.assertIn("plan", result)
        self.assertIn("clips", result["plan"])
        self.assertIn("narrations", result["plan"])
        self.assertIn("bgms", result["plan"])
        self.assertIn("timeline", result["plan"])
        self.assertIn("total_duration", result["plan"])

        # Assert logical outputs instead of file existence
        self.assertTrue(result["plan"]["total_duration"] > 0)
        self.assertGreater(len(result["plan"]["timeline"]), 0)

    def test_story_analysis_worker(self):
        """Test StoryAnalysisWorker analyzes script and creates scenes"""
        script = "A young detective investigates a mysterious case in a foggy city."
        worker = StoryAnalysisWorker(state={})
        result = worker.run(script)
        
        self.assertIn("scenes", result)
        scenes = result["scenes"]
        self.assertIsInstance(scenes, list)
        
        # Check scene structure
        for scene in scenes:
            self.assertIn("id", scene)
            self.assertIn("description", scene)
            self.assertIn("duration", scene)


class TestPhase3WorkerModularity(unittest.TestCase):
    """Test Rule 3.1: Worker Modularity"""
    
    def test_worker_base_class(self):
        """Test that all workers inherit from BaseWorker and have run method"""
        from workers.workers import BaseWorker
        
        workers = [IngestionWorker, StoryAnalysisWorker, ClipChooserWorker, 
                  NarrationWorker, BGMWorker, AssemblyWorker]
        
        for worker_class in workers:
            # Check inheritance
            self.assertTrue(issubclass(worker_class, BaseWorker))
            
            # Check run method exists
            self.assertTrue(hasattr(worker_class, 'run'))
            self.assertTrue(callable(getattr(worker_class, 'run')))

    def test_worker_state_sharing(self):
        """Test that workers can share state via dict"""
        shared_state = {"test_key": "test_value"}
        worker = IngestionWorker(state=shared_state)
        
        self.assertEqual(worker.state, shared_state)
        self.assertEqual(worker.state["test_key"], "test_value")


class TestPhase3ClipDiversity(unittest.TestCase):
    """Test Rule 3.2: Clip Diversity"""
    
    def test_diverse_scene_selection(self):
        """Test that clips are selected from different parts of video"""
        analysis = {
            "video_path": "test_video.mp4",
            "total_duration": 300,  # 5 minutes
            "scenes": [
                # First third (0-100s)
                {"start": 10, "end": 40, "score": 0.9, "description": "Opening scene", "mood": "happy"},
                {"start": 50, "end": 80, "score": 0.5, "description": "Setup scene", "mood": "neutral"},
                
                # Middle third (100-200s)
                {"start": 120, "end": 150, "score": 0.8, "description": "Action scene", "mood": "intense"},
                {"start": 160, "end": 190, "score": 0.6, "description": "Dialog scene", "mood": "neutral"},
                
                # Last third (200-300s)
                {"start": 220, "end": 250, "score": 0.7, "description": "Climax scene", "mood": "dramatic"},
                {"start": 260, "end": 290, "score": 0.4, "description": "Ending scene", "mood": "peaceful"},
            ]
        }
        
        # Create temp video file
        make_dummy_video(Path("test_video.mp4"))
        
        try:
            worker = ClipChooserWorker(state={})
            result = worker.run(analysis)
            
            clips = result["clips"]
            self.assertGreater(len(clips), 0)
            
            # Check that clips come from different thirds
            first_third_clips = [c for c in clips if c["start_time"] < 100]
            middle_third_clips = [c for c in clips if 100 <= c["start_time"] < 200]
            last_third_clips = [c for c in clips if c["start_time"] >= 200]
            
            # Should have coverage from multiple thirds
            coverage_count = sum([
                len(first_third_clips) > 0,
                len(middle_third_clips) > 0,
                len(last_third_clips) > 0
            ])
            
            self.assertGreaterEqual(coverage_count, 2, "Should have clips from at least 2 thirds of video")
            
        finally:
            if os.path.exists("test_video.mp4"):
                os.remove("test_video.mp4")

    def test_scene_score_threshold(self):
        """Test that only scenes above threshold are selected"""
        analysis = {
            "video_path": "test_video.mp4",
            "total_duration": 300,
            "scenes": [
                {"start": 0, "end": 30, "score": 0.8, "description": "High score scene", "mood": "intense"},
                {"start": 40, "end": 70, "score": 0.3, "description": "Low score scene", "mood": "neutral"},
                {"start": 80, "end": 110, "score": 0.6, "description": "Medium score scene", "mood": "happy"},
            ]
        }
        
        # Create temp video file
        make_dummy_video(Path("test_video.mp4"))
        
        try:
            worker = ClipChooserWorker(state={})
            result = worker.run(analysis)
            
            clips = result["clips"]
            
            # All selected clips should have score >= threshold
            for clip in clips:
                self.assertGreaterEqual(clip["score"], config.SCENE_SCORE_THRESHOLD)
                
        finally:
            if os.path.exists("test_video.mp4"):
                os.remove("test_video.mp4")


if __name__ == '__main__':
    unittest.main()
