"""
Test VideoAgent with mocked video_maker and FFmpeg runner injection.
This test verifies the specific requirements for Step 7.
"""
import pytest
import os
from unittest.mock import patch, MagicMock
from coordinator import VideoAgent
from tests.mocks.video_shims import verify_mock_ffmpeg_active, mock_subprocess_run


class TestVideoAgentMocked:
    """Test VideoAgent with mocked dependencies."""
    
    def test_video_maker_injection(self):
        """Test that video_maker can be injected into VideoAgent."""
        def mock_video_maker(*args, **kwargs):
            return "/mock/planned/video.mp4"
        
        agent = VideoAgent(video_maker=mock_video_maker)
        assert agent.video_maker == mock_video_maker
        
        # Verify it's passed to worker environment
        env = agent._create_worker_environment()
        assert env["video_maker"] == mock_video_maker
    
    def test_ffmpeg_runner_injection(self):
        """Test that FFmpeg runner can be injected into VideoAgent."""
        def mock_ffmpeg_runner(cmd, **kwargs):
            return MagicMock(returncode=0, stdout="mock output", stderr="")
        
        agent = VideoAgent(ffmpeg_runner=mock_ffmpeg_runner)
        assert agent.ffmpeg_runner == mock_ffmpeg_runner
        
        # Verify it's passed to worker environment
        env = agent._create_worker_environment()
        assert env["ffmpeg_runner"] == mock_ffmpeg_runner
    
    def test_mocked_mode_returns_planned_paths(self):
        """Test that VideoAgent returns planned paths in mocked mode."""
        def mock_video_maker(*args, **kwargs):
            return "/mock/planned/video.mp4"
        
        def mock_ffmpeg_runner(cmd, **kwargs):
            return MagicMock(returncode=0, stdout="mock ffmpeg output", stderr="")
        
        agent = VideoAgent(
            model="gpt-4",
            video_maker=mock_video_maker,
            ffmpeg_runner=mock_ffmpeg_runner
        )
        
        # Mock all workers to avoid external dependencies
        with patch('workers.StoryAnalysisWorker') as mock_story_worker, \
             patch('workers.ClipChooserWorker') as mock_clip_worker, \
             patch('workers.NarrationWorker') as mock_narration_worker, \
             patch('workers.BGMWorker') as mock_bgm_worker, \
             patch('workers.AssemblyWorker') as mock_assembly_worker:
            
            # Configure mock workers with minimal valid responses
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
            
            # Run the agent with a simple script
            result = agent.run("Test script with mock dependencies")
            
            # Verify we get planned paths, not necessarily playable videos
            assert result is not None, "Mocked mode should return complete plan"
            assert "clips" in result, "Result should contain clips"
            assert "timeline" in result, "Result should contain timeline"
            assert "total_duration" in result, "Result should contain total_duration"
            assert result["total_duration"] > 0, "Total duration should be positive"
            
            # Verify that timeline contains structured data (planned paths)
            timeline = result["timeline"]
            assert isinstance(timeline, list), "Timeline should be a list"
            
            # In mocked mode, we should get structured output without actual video processing
            if verify_mock_ffmpeg_active():
                assert len(timeline) > 0, "Timeline should not be empty in mocked mode"
    
    def test_end_to_end_flow_without_external_binaries(self):
        """Test that VideoAgent end-to-end flow works without external binaries."""
        # Set up mocked dependencies
        def mock_video_maker(*args, **kwargs):
            # Return planned path instead of creating actual video
            return f"/mock/planned/{args[0] if args else 'video'}.mp4"
        
        def mock_ffmpeg_runner(cmd, **kwargs):
            # Mock successful ffmpeg execution
            return MagicMock(returncode=0, stdout="Mock FFmpeg execution", stderr="")
        
        # Create agent with injected dependencies
        agent = VideoAgent(
            model="gpt-4",
            video_maker=mock_video_maker,
            ffmpeg_runner=mock_ffmpeg_runner
        )
        
        # Verify dependencies are injected
        assert agent.video_maker == mock_video_maker
        assert agent.ffmpeg_runner == mock_ffmpeg_runner
        
        # Verify worker environment gets the dependencies
        env = agent._create_worker_environment()
        assert env["video_maker"] == mock_video_maker
        assert env["ffmpeg_runner"] == mock_ffmpeg_runner
        
        # Test that environment is created without external dependencies
        assert env["model"] == "gpt-4"
        assert "config" in env
        assert "shared_data" in env
    
    def test_mock_ffmpeg_active_assertions(self):
        """Test extra assertions when MOCK_FFMPEG=1 is active."""
        if not verify_mock_ffmpeg_active():
            pytest.skip("MOCK_FFMPEG not active")
        
        def mock_video_maker(*args, **kwargs):
            return "/mock/planned/video.mp4"
        
        agent = VideoAgent(video_maker=mock_video_maker)
        
        # Assertions specific to mocked mode
        assert verify_mock_ffmpeg_active(), "Mock FFmpeg should be active"
        assert agent.video_maker is not None, "Video maker should be injected in mocked mode"
        
        # Verify that in mocked mode, we expect planned paths not playable videos
        env = agent._create_worker_environment()
        video_maker = env.get("video_maker")
        if video_maker:
            result = video_maker("test_input", 0, 10, "test_output.mp4")
            assert isinstance(result, str), "Video maker should return path string in mocked mode"
            assert result.endswith(".mp4"), "Video maker should return video file path in mocked mode"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
