"""
Test configuration and fixtures for the AI Video Editor
"""
import pytest
import tempfile
import os
import shutil
from pathlib import Path
import sys
import glob

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import video helper
from tests.utils.video_helper import make_dummy_video

from coordinator import VideoAgent
import config

@pytest.fixture
def temp_dir():
    """Create a temporary directory for testing."""
    temp_dir = tempfile.mkdtemp()
    yield temp_dir
    shutil.rmtree(temp_dir, ignore_errors=True)

@pytest.fixture
def sample_video_path(temp_dir):
    """Create a mock video file for testing."""
    video_path = os.path.join(temp_dir, "test_video.mp4")
    # Create a dummy file (in real tests, you'd use a real video file)
    make_dummy_video(Path(video_path))
    return video_path

@pytest.fixture
def video_path(tmp_path):
    """Create a dummy video using video_helper for convenient testing."""
    video_file = tmp_path / "clip.mp4"
    return make_dummy_video(video_file)

@pytest.fixture
def video_agent():
    """Create a VideoAgent instance for testing."""
    return VideoAgent()

@pytest.fixture
def sample_script():
    """Sample script for testing video generation."""
    return """
    A beautiful sunset over mountains with birds flying.
    The camera pans slowly across the landscape.
    Peaceful music plays in the background.
    """

@pytest.fixture
def mock_session():
    """Mock session data for testing."""
    return {
        "video_path": "/path/to/video.mp4",
        "edits": [],
        "preview_path": "/path/to/video.mp4",
        "last_activity": 1234567890,
        "filename": "test_video.mp4",
        "file_size": 1000000,
        "video_duration": 60.0
    }

@pytest.fixture
def sample_edit_commands():
    """Sample edit commands for testing."""
    return [
        {
            "type": "trim",
            "start_time": "00:00:10",
            "end_time": "00:00:30",
            "confidence": 0.9
        },
        {
            "type": "enhance",
            "target": "brightness",
            "value": 1.2,
            "confidence": 0.8
        }
    ]

@pytest.fixture
def sample_preferences():
    """Sample user preferences for testing."""
    return {
        "style": "cinematic",
        "pace": "moderate",
        "target_duration": 60,
        "quality": "high"
    }

# Override config settings for testing
@pytest.fixture(autouse=True)
def override_config(temp_dir):
    """Override configuration settings for testing."""
    original_upload_dir = config.UPLOAD_DIR
    original_output_dir = config.VIDEO_OUTPUT_DIR
    
    config.UPLOAD_DIR = os.path.join(temp_dir, "uploads")
    config.VIDEO_OUTPUT_DIR = os.path.join(temp_dir, "outputs")
    
    # Create directories
    os.makedirs(config.UPLOAD_DIR, exist_ok=True)
    os.makedirs(config.VIDEO_OUTPUT_DIR, exist_ok=True)
    
    yield
    
    # Restore original settings
    config.UPLOAD_DIR = original_upload_dir
    config.VIDEO_OUTPUT_DIR = original_output_dir


@pytest.fixture(scope="session", autouse=True)
def cleanup_mp4_files():
    """Session fixture to clean up any .mp4 files created during tests.
    
    This fixture runs after all tests are complete and removes any .mp4 files
    created under tmp_path directories to prevent test artifacts from accumulating.
    """
    yield  # Let all tests run first
    
    # Find and remove all .mp4 files in temporary directories
    temp_dirs = [
        tempfile.gettempdir(),  # System temp directory
        os.getcwd(),  # Current working directory
    ]
    
    for temp_dir in temp_dirs:
        if os.path.exists(temp_dir):
            # Find all .mp4 files recursively
            mp4_pattern = os.path.join(temp_dir, "**", "*.mp4")
            mp4_files = glob.glob(mp4_pattern, recursive=True)
            
            for mp4_file in mp4_files:
                try:
                    # Only remove files in pytest temp directories
                    if "pytest" in mp4_file or "tmp" in mp4_file.lower():
                        os.remove(mp4_file)
                        print(f"Cleaned up test artifact: {mp4_file}")
                except OSError as e:
                    # Log but don't fail on cleanup issues
                    print(f"Warning: Could not remove {mp4_file}: {e}")
