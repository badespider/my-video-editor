import pytest
from pathlib import Path
import tempfile
import os

from tests.utils.video_helper import make_dummy_video, skip_if_no_video_support, _has_ffmpeg

import shutil
from unittest.mock import patch


@pytest.fixture
def non_existent_moviepy():
    with patch('tests.utils.video_helper.MOVIEPY_AVAILABLE', False):
        yield

@pytest.fixture
def existent_moviepy():
    with patch('tests.utils.video_helper.MOVIEPY_AVAILABLE', True):
        yield


def test_make_dummy_video_fallback_base64(non_existent_moviepy):
    """Ensure fallback to base64 when MoviePy is unavailable."""
    with tempfile.TemporaryDirectory() as temp_dir:
        video_path = Path(temp_dir) / "test_video.mp4"

        result = make_dummy_video(video_path)

        assert result == video_path
        assert video_path.exists()
        assert video_path.stat().st_size > 0


def test_make_dummy_video_moviepy_failure():
    """Test fallback when MoviePy fails explicitly."""
    import tests.utils.video_helper as helper
    
    # Only run this test if MoviePy is actually available
    if not helper.MOVIEPY_AVAILABLE:
        pytest.skip("MoviePy not available, cannot test MoviePy failure")
    
    with patch.object(helper.mp, 'ColorClip') as mock_color_clip:
        mock_color_clip.side_effect = Exception("Failed to create video")

        with tempfile.TemporaryDirectory() as temp_dir:
            video_path = Path(temp_dir) / "test_video.mp4"

            result = make_dummy_video(video_path)

            assert result == video_path
            assert video_path.exists()
            assert video_path.stat().st_size > 0
def test_make_dummy_video():
    """Test that make_dummy_video creates a video file."""
    with tempfile.TemporaryDirectory() as temp_dir:
        video_path = Path(temp_dir) / "test_video.mp4"
        
        result = make_dummy_video(video_path)
        
        assert result == video_path
        assert video_path.exists()
        assert video_path.stat().st_size > 0


def test_make_dummy_video_with_custom_params():
    """Test make_dummy_video with custom parameters."""
    with tempfile.TemporaryDirectory() as temp_dir:
        video_path = Path(temp_dir) / "custom_video.mp4"
        
        result = make_dummy_video(video_path, duration=1.0, size=(128, 128), fps=10)
        
        assert result == video_path
        assert video_path.exists()
        assert video_path.stat().st_size > 0


def test_skip_if_no_video_support():
    """Test the skip function (it should not fail in normal circumstances)."""
    # This test mainly ensures the function can be called without error
    # The actual xfail behavior would be tested in integration tests
    class MockPytest:
        def __init__(self):
            self.skipped = False
            self.skip_reason = None
            
        def xfail(self, reason):
            self.skipped = True
            self.skip_reason = reason
    
    mock_pytest = MockPytest()
    # This should not raise an exception
    skip_if_no_video_support(mock_pytest)
    # We don't assert anything specific since the behavior depends on system setup


def test_has_ffmpeg():
    """Test FFmpeg availability check."""
    # This tests the actual system state, so we just ensure it doesn't crash
    result = _has_ffmpeg()
    assert isinstance(result, bool)


def test_has_ffmpeg_no_ffmpeg():
    """Test FFmpeg availability when FFmpeg is not available."""
    with patch('tests.utils.video_helper.subprocess.run') as mock_run:
        mock_run.side_effect = FileNotFoundError("ffmpeg not found")
        result = _has_ffmpeg()
        assert result is False


def test_has_ffmpeg_error():
    """Test FFmpeg availability when ffmpeg returns error."""
    from subprocess import CalledProcessError
    with patch('tests.utils.video_helper.subprocess.run') as mock_run:
        mock_run.side_effect = CalledProcessError(1, "ffmpeg")
        result = _has_ffmpeg()
        assert result is False


def test_skip_if_no_video_support_no_moviepy_no_ffmpeg():
    """Test skip function when neither MoviePy nor FFmpeg is available."""
    with patch('tests.utils.video_helper.MOVIEPY_AVAILABLE', False), \
         patch('tests.utils.video_helper._has_ffmpeg', return_value=False):
        
        class MockPytest:
            def __init__(self):
                self.skipped = False
                self.skip_reason = None
                
            def xfail(self, reason):
                self.skipped = True
                self.skip_reason = reason
        
        mock_pytest = MockPytest()
        skip_if_no_video_support(mock_pytest)
        assert mock_pytest.skipped is True
        assert "Neither MoviePy nor FFmpeg" in mock_pytest.skip_reason


def test_skip_if_no_video_support_no_moviepy_no_asset():
    """Test skip function when MoviePy is unavailable and no minimal.mp4 exists."""
    with patch('tests.utils.video_helper.MOVIEPY_AVAILABLE', False), \
         patch('tests.utils.video_helper._has_ffmpeg', return_value=True), \
         patch('tests.utils.video_helper.Path.exists', return_value=False):
        
        class MockPytest:
            def __init__(self):
                self.skipped = False
                self.skip_reason = None
                
            def xfail(self, reason):
                self.skipped = True
                self.skip_reason = reason
        
        mock_pytest = MockPytest()
        skip_if_no_video_support(mock_pytest)
        assert mock_pytest.skipped is True
        assert "minimal.mp4 fallback is missing" in mock_pytest.skip_reason


def test_make_dummy_video_with_asset_fallback(non_existent_moviepy):
    """Test fallback to assets/minimal.mp4 when it exists."""
    with tempfile.TemporaryDirectory() as temp_dir:
        # Create a mock asset file
        assets_dir = Path(temp_dir) / "tests" / "assets"
        assets_dir.mkdir(parents=True, exist_ok=True)
        minimal_mp4_path = assets_dir / "minimal.mp4"
        minimal_mp4_path.write_bytes(b"mock video data")
        
        video_path = Path(temp_dir) / "test_video.mp4"
        
        with patch('tests.utils.video_helper.Path') as mock_path_class:
            # Mock the Path constructor to return our test path
            mock_path_instance = Path(minimal_mp4_path)
            mock_path_class.return_value = mock_path_instance
            
            # Mock the exists method to return True
            with patch.object(Path, 'exists', return_value=True):
                with patch('tests.utils.video_helper.shutil.copy') as mock_copy:
                    result = make_dummy_video(video_path)
                    mock_copy.assert_called_once()
                    assert result == video_path
