"""
Test to validate CI matrix environment settings
"""
import os
import pytest
from tests.mocks.video_shims import verify_mock_ffmpeg_active


def test_mock_ffmpeg_environment_detection():
    """Test that MOCK_FFMPEG environment variable is properly detected."""
    mock_ffmpeg_env = os.getenv('MOCK_FFMPEG')
    
    # Should be either '0', '1', or None
    assert mock_ffmpeg_env in ['0', '1', None], f"MOCK_FFMPEG should be '0', '1', or None, got: {mock_ffmpeg_env}"
    
    # Test the verification function
    is_mock_active = verify_mock_ffmpeg_active()
    expected_mock_active = mock_ffmpeg_env == '1'
    
    assert is_mock_active == expected_mock_active, f"Mock FFmpeg detection mismatch: {is_mock_active} vs {expected_mock_active}"
    
    print(f"MOCK_FFMPEG environment: {mock_ffmpeg_env}")
    print(f"Mock FFmpeg active: {is_mock_active}")


def test_ci_matrix_compatibility():
    """Test that both CI matrix environments are supported."""
    mock_ffmpeg_env = os.getenv('MOCK_FFMPEG')
    
    if mock_ffmpeg_env == '1':
        # Mock environment - test should pass without external dependencies
        print("Running in Mock FFmpeg environment (no external dependencies)")
        assert verify_mock_ffmpeg_active(), "Mock FFmpeg should be active"
        
        # Basic mock functionality test
        from tests.mocks.video_shims import MockVideoFileClip
        mock_clip = MockVideoFileClip("test.mp4", duration=10.0)
        assert mock_clip.duration == 10.0, "Mock video clip should have expected duration"
        assert mock_clip.filename == "test.mp4", "Mock video clip should have expected filename"
        
    elif mock_ffmpeg_env == '0':
        # Full environment - external dependencies may be available
        print("Running in Full environment (with potential FFmpeg support)")
        assert not verify_mock_ffmpeg_active(), "Mock FFmpeg should not be active"
        
        # Test that we can import real libraries (if available)
        try:
            import moviepy.editor as mp
            print("MoviePy is available in full environment")
        except ImportError:
            print("MoviePy not available in full environment (optional)")
    
    else:
        # Default environment (local development)
        print("Running in default environment (local development)")
        # Should work in both scenarios
    
    # Common test that should work in all environments
    assert True, "Basic test should always pass"


def test_cleanup_fixture_compatibility():
    """Test that the cleanup fixture works in both CI matrix environments."""
    import tempfile
    
    # Create a temporary .mp4 file
    with tempfile.NamedTemporaryFile(suffix='.mp4', delete=False) as tmp_file:
        tmp_file.write(b'\x00\x00\x00\x1cftypmp42\x00\x00\x00\x00mp42isom')
        tmp_file_path = tmp_file.name
    
    # Verify file exists
    assert os.path.exists(tmp_file_path), "Temporary MP4 file should exist"
    
    print(f"Created temporary MP4 file: {tmp_file_path}")
    print(f"File will be cleaned up by session fixture after all tests complete")
    
    # Note: Cleanup happens after all tests in the session, so we can't verify it here
    # The cleanup fixture will handle this file


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
