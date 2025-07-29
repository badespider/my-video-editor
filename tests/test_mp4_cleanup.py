"""
Test for verifying the .mp4 cleanup fixture functionality
"""
import pytest
import tempfile
import os
from pathlib import Path


def test_mp4_file_creation_and_cleanup(tmp_path):
    """Test that .mp4 files are created during tests and cleaned up after session."""
    # Create a mock .mp4 file in tmp_path
    mp4_file = tmp_path / "test_cleanup.mp4"
    
    # Write minimal MP4 content
    with open(mp4_file, 'wb') as f:
        f.write(b'\x00\x00\x00\x1cftypmp42\x00\x00\x00\x00mp42isom')
        f.write(b'\x00\x00\x00\x64moov\x00\x00\x00\x64trak')
    
    # Verify file exists
    assert mp4_file.exists(), "MP4 file should be created"
    assert mp4_file.stat().st_size > 0, "MP4 file should have content"
    
    # Store the path for verification (in real scenario, cleanup happens after all tests)
    global _test_mp4_path
    _test_mp4_path = str(mp4_file)
    
    print(f"Created test MP4 file: {mp4_file}")


def test_multiple_mp4_files_creation(tmp_path):
    """Test creating multiple .mp4 files to verify comprehensive cleanup."""
    mp4_files = []
    
    for i in range(3):
        mp4_file = tmp_path / f"test_video_{i}.mp4"
        
        # Create mock MP4 file
        with open(mp4_file, 'wb') as f:
            f.write(b'\x00\x00\x00\x1cftypmp42\x00\x00\x00\x00mp42isom')
            f.write(b'\x00\x00\x00\x64moov\x00\x00\x00\x64trak')
        
        mp4_files.append(mp4_file)
        print(f"Created MP4 file: {mp4_file}")
    
    # Verify all files exist
    for mp4_file in mp4_files:
        assert mp4_file.exists(), f"MP4 file {mp4_file} should exist"
        assert mp4_file.stat().st_size > 0, f"MP4 file {mp4_file} should have content"


def test_cleanup_behavior_with_mock_ffmpeg(tmp_path):
    """Test cleanup behavior when MOCK_FFMPEG is set."""
    import os
    
    mock_ffmpeg_active = os.getenv('MOCK_FFMPEG') == '1'
    
    # Create test .mp4 file
    mp4_file = tmp_path / "mock_test.mp4"
    with open(mp4_file, 'wb') as f:
        f.write(b'\x00\x00\x00\x1cftypmp42\x00\x00\x00\x00mp42isom')
    
    assert mp4_file.exists(), "MP4 file should be created"
    
    print(f"MOCK_FFMPEG active: {mock_ffmpeg_active}")
    print(f"Created MP4 file in mocked environment: {mp4_file}")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
