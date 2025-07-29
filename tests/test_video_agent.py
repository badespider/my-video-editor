"""
Tests for VideoAgent functionality
"""
import pytest
import os
from unittest.mock import patch, MagicMock
from pathlib import Path
from coordinator import VideoAgent
from tests.utils.video_helper import make_dummy_video
from tests.mocks.video_shims import verify_mock_ffmpeg_active, mock_subprocess_run


class TestVideoAgent:
    """Test cases for VideoAgent class."""
    
    def test_video_agent_initialization(self):
        """Test VideoAgent can be initialized."""
        agent = VideoAgent()
        assert agent is not None
        assert agent.model == "gpt-4"  # Default model from config
        assert agent.video_maker is None  # Default no injection
        assert agent.ffmpeg_runner is None  # Default no injection
    
    def test_video_agent_with_custom_model(self):
        """Test VideoAgent initialization with custom model."""
        agent = VideoAgent(model="gpt-4")
        assert agent.model == "gpt-4"
    
    def test_video_agent_with_mock_dependencies(self):
        """Test VideoAgent initialization with mocked video maker and FFmpeg runner."""
        def mock_video_maker(*args, **kwargs):
            return "/mock/path/video.mp4"
        
        agent = VideoAgent(model="gpt-4", video_maker=mock_video_maker, ffmpeg_runner=mock_subprocess_run)
        assert agent.model == "gpt-4"
        assert agent.video_maker == mock_video_maker
        assert agent.ffmpeg_runner == mock_subprocess_run
        
        # Test that environment passes the injected dependencies
        env = agent._create_worker_environment()
        assert env["video_maker"] == mock_video_maker
        assert env["ffmpeg_runner"] == mock_subprocess_run
    
    def test_parse_command_trim(self, video_agent):
        """Test parsing a trim command."""
        command = video_agent.parse_command("trim the video from 10 seconds to 30 seconds")
        assert command["type"] == "trim"
        assert "start_time" in command
        assert "end_time" in command
    
    def test_parse_command_enhance(self, video_agent):
        """Test parsing an enhance command."""
        command = video_agent.parse_command("make the video brighter")
        assert command["type"] == "enhance"
        assert "target" in command
    
    def test_parse_command_invalid(self, video_agent):
        """Test handling of invalid commands."""
        with pytest.raises(ValueError):
            video_agent.parse_command("invalid command that makes no sense")
    
    @patch('utils.utils.call_memories_placeholder')
    def test_run_with_script(self, mock_call, video_agent, sample_script):
        """Test running video generation with script."""
        mock_call.return_value = {
            "clips": {"clip1": {"description": "sunset scene"}},
            "narrations": {"narr1": {"text": "Beautiful sunset"}},
            "bgms": {"bgm1": {"type": "peaceful"}},
            "timeline": [{"type": "clip", "id": "clip1"}],
            "total_duration": 60.0,
            "assembly_metadata": {"version": "1.0"}
        }
        
        result = video_agent.run(sample_script)
        
        assert "clips" in result
        assert "narrations" in result
        assert "bgms" in result
        assert "timeline" in result
        assert result["total_duration"] == 60.0
        mock_call.assert_called_once()
        
        # Additional assertions for mocked mode
        if verify_mock_ffmpeg_active():
            assert "timeline" in result, "Mocked mode should return planned paths"
            assert isinstance(result["timeline"], list), "Timeline should be a list in mocked mode"
            # Verify we get planned paths, not necessarily playable videos
            for timeline_item in result["timeline"]:
                assert "type" in timeline_item, "Timeline items should have type in mocked mode"
    
    def test_apply_command_trim(self, video_agent, mock_session):
        """Test applying a trim command to a session."""
        command = {
            "type": "trim",
            "start_time": "00:00:10",
            "end_time": "00:00:30"
        }
        
        with patch('utils.utils.trim_video') as mock_trim:
            video_agent.apply_command(mock_session, command)
            mock_trim.assert_called_once()
            assert len(mock_session["edits"]) == 1
            assert mock_session["edits"][0]["type"] == "trim"
    
    def test_apply_command_enhance(self, video_agent, mock_session):
        """Test applying an enhance command to a session."""
        command = {
            "type": "enhance",
            "target": "brightness",
            "value": 1.2
        }
        
        with patch('utils.utils.apply_edit_commands') as mock_apply:
            video_agent.apply_command(mock_session, command)
            mock_apply.assert_called_once()
            assert len(mock_session["edits"]) == 1
            assert mock_session["edits"][0]["type"] == "enhance"
    
    def test_finalize_video(self, video_agent, mock_session, temp_dir):
        """Test finalizing a video with edits."""
        import os
        
        # Create a mock video file
        video_path = os.path.join(temp_dir, "test_video.mp4")
        make_dummy_video(Path(video_path))
        
        mock_session["video_path"] = video_path
        mock_session["edits"] = [
            {"type": "trim", "start_time": "00:00:10", "end_time": "00:00:30"}
        ]
        
        with patch('utils.utils.apply_edit_commands') as mock_apply:
            result = video_agent.finalize_video(mock_session)
            mock_apply.assert_called_once()
            assert result is not None
    
    @patch('utils.utils.call_memories_placeholder')
    def test_run_with_video(self, mock_call, video_agent, sample_video_path):
        """Test running video processing with uploaded video."""
        mock_call.return_value = {
            "final_video": "/path/to/final.mp4",
            "plan": "Processing plan",
            "source_video": sample_video_path,
            "processing_type": "enhancement",
            "coverage_percentage": 85.5,
            "scene_count": 5
        }
        
        result = video_agent.run_with_video(sample_video_path)
        
        assert "final_video" in result
        assert "plan" in result
        assert result["source_video"] == sample_video_path
        assert result["coverage_percentage"] == 85.5
        mock_call.assert_called_once()
        
        # Additional assertions for mocked mode
        if verify_mock_ffmpeg_active():
            assert "final_video" in result, "Mocked mode should return planned video path"
            assert "plan" in result, "Mocked mode should include processing plan"
            assert isinstance(result["coverage_percentage"], (int, float)), "Coverage should be numeric in mocked mode"
            # Verify we get planned paths, not necessarily playable videos
            final_video_path = result["final_video"]
            assert isinstance(final_video_path, str), "Final video path should be string in mocked mode"
    
    def test_error_handling(self, video_agent):
        """Test error handling in VideoAgent methods."""
        with pytest.raises(Exception):
            video_agent.run("")  # Empty script should raise error
        
        with pytest.raises(Exception):
            video_agent.run_with_video("nonexistent_file.mp4")  # Nonexistent file should raise error
    
    def test_end_to_end_with_mocked_video_maker(self, sample_script):
        """Test VideoAgent end-to-end flow with mocked video maker and FFmpeg runner."""
        # Mock video maker that returns planned paths
        def mock_video_maker(*args, **kwargs):
            return "/mock/planned/video.mp4"
        
        # Mock FFmpeg runner
        def mock_ffmpeg_runner(cmd, **kwargs):
            return MagicMock(returncode=0, stdout="mock ffmpeg output", stderr="")
        
        # Create VideoAgent with injected dependencies
        agent = VideoAgent(
            model="gpt-4o-mini",
            video_maker=mock_video_maker,
            ffmpeg_runner=mock_ffmpeg_runner
        )
        
        # Mock the worker calls to avoid actual model calls
        with patch('workers.StoryAnalysisWorker') as mock_story_worker, \
             patch('workers.ClipChooserWorker') as mock_clip_worker, \
             patch('workers.NarrationWorker') as mock_narration_worker, \
             patch('workers.BGMWorker') as mock_bgm_worker, \
             patch('workers.AssemblyWorker') as mock_assembly_worker:
            
            # Configure mock workers
            mock_story_worker.return_value.run.return_value = {
                "scenes": [{"description": "test scene", "start": 0, "end": 10}]
            }
            mock_clip_worker.return_value.run.return_value = {
                "clips": [{"description": "test clip", "duration": 10}]
            }
            mock_narration_worker.return_value.run.return_value = {
                "narration": "test narration", "word_count": 2
            }
            mock_bgm_worker.return_value.run.return_value = {
                "bgm_options": [{"type": "peaceful", "duration": 10}]
            }
            mock_assembly_worker.return_value.run.return_value = {
                "clips": {"clip1": {"path": "/mock/planned/video.mp4"}},
                "narrations": {"narr1": {"text": "test narration"}},
                "bgms": {"bgm1": {"type": "peaceful"}},
                "timeline": [{"type": "clip", "id": "clip1", "path": "/mock/planned/video.mp4"}],
                "total_duration": 10.0
            }
            
            # Run the agent
            result = agent.run(sample_script)
            
            # Assert that we get planned paths, not necessarily playable videos
            assert "clips" in result
            assert "timeline" in result
            assert result["total_duration"] > 0
            
            # Verify that timeline contains planned paths from mocked video maker
            timeline = result["timeline"]
            assert isinstance(timeline, list)
            if timeline:
                timeline_item = timeline[0]
                assert "path" in timeline_item or "id" in timeline_item
            
            # In mocked mode, we should get structured output without actual video processing
            if verify_mock_ffmpeg_active():
                assert result is not None, "Mocked mode should return complete plan"
                assert "timeline" in result, "Mocked mode should include timeline"
