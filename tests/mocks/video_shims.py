"""
Video processing shims for unit test isolation.

This module provides lightweight mock implementations of FFmpeg subprocess calls
and MoviePy classes to enable unit testing without requiring actual video processing
dependencies. Activated when MOCK_FFMPEG=1 environment variable is set.

Follows Rule 2.3: Enhanced Error Handling and Testing with comprehensive mocking
for CI/CD pipeline compatibility.
"""

import os
import subprocess
import logging
from unittest.mock import Mock, MagicMock, patch
from typing import List, Tuple, Any, Optional, Union
import pytest

# Configure logging for mock mode indication
logger = logging.getLogger(__name__)

# Log when mock mode is enabled
if os.getenv('MOCK_FFMPEG') == '1':
    logger.info("Mock mode enabled - using video processing shims")


class MockVideoFileClip:
    """Lightweight stub for MoviePy VideoFileClip class."""
    
    def __init__(self, filename: str, *args, **kwargs):
        self.filename = filename
        self.duration = kwargs.get('duration', 60.0)  # Default 1 minute
        self.fps = kwargs.get('fps', 30.0)
        self.size = kwargs.get('size', (1920, 1080))
        self.w, self.h = self.size
        self.audio = MockAudioFileClip() if kwargs.get('has_audio', True) else None
        self._closed = False
    
    def subclipped(self, start_time: float, end_time: float) -> 'MockVideoFileClip':
        """Mock subclip creation."""
        duration = max(0.1, end_time - start_time)
        return MockVideoFileClip(
            f"{self.filename}_subclip",
            duration=duration,
            fps=self.fps,
            size=self.size,
            has_audio=self.audio is not None
        )
    
    def subclip(self, start_time: float, end_time: float) -> 'MockVideoFileClip':
        """Alternative subclip method name."""
        return self.subclipped(start_time, end_time)
    
    def with_fps(self, fps: float) -> 'MockVideoFileClip':
        """Mock fps setting."""
        self.fps = fps
        return self
    
    def with_duration(self, duration: float) -> 'MockVideoFileClip':
        """Mock duration setting."""
        self.duration = duration
        return self
    
    def with_audio(self, audio) -> 'MockVideoFileClip':
        """Mock audio setting."""
        self.audio = audio
        return self
    
    def with_position(self, position) -> 'MockVideoFileClip':
        """Mock position setting."""
        self.position = position
        return self
    
    def fx(self, effect, *args, **kwargs) -> 'MockVideoFileClip':
        """Mock effects application."""
        # Simulate effect application without actual processing
        if hasattr(effect, '__name__'):
            effect_name = effect.__name__
        else:
            effect_name = str(effect)
        
        # Adjust duration for speed effects
        if 'speed' in effect_name.lower() and args:
            speed_factor = args[0]
            self.duration = self.duration / speed_factor
        
        return self
    
    def write_videofile(self, filename: str, *args, **kwargs) -> None:
        """Mock video file writing."""
        # Create a minimal placeholder file
        dirname = os.path.dirname(filename)
        if dirname:  # Only create directory if dirname is not empty
            os.makedirs(dirname, exist_ok=True)
        with open(filename, 'wb') as f:
            # Write minimal MP4 header
            f.write(b'\x00\x00\x00\x1cftypmp42\x00\x00\x00\x00mp42isom')
            f.write(b'\x00\x00\x00\x64moov\x00\x00\x00\x64trak')
    
    def get_frame(self, time: float) -> Any:
        """Mock frame extraction."""
        import numpy as np
        return np.zeros((self.h, self.w, 3), dtype=np.uint8)
    
    def close(self) -> None:
        """Mock cleanup."""
        self._closed = True


class MockAudioFileClip:
    """Lightweight stub for MoviePy AudioFileClip class."""
    
    def __init__(self, filename: str = None, *args, **kwargs):
        self.filename = filename
        self.duration = kwargs.get('duration', 60.0)
        self.fps = kwargs.get('fps', 44100)
        self._closed = False
    
    def with_duration(self, duration: float) -> 'MockAudioFileClip':
        """Mock duration setting."""
        self.duration = duration
        return self
    
    def with_volume_scaled(self, factor: float) -> 'MockAudioFileClip':
        """Mock volume scaling."""
        self.volume_factor = factor
        return self
    
    def overlay(self, other_audio) -> 'MockAudioFileClip':
        """Mock audio overlay."""
        return self
    
    def write_audiofile(self, filename: str, *args, **kwargs) -> None:
        """Mock audio file writing."""
        os.makedirs(os.path.dirname(filename), exist_ok=True)
        with open(filename, 'wb') as f:
            # Write minimal MP3 header
            f.write(b'\xff\xfb\x90\x00' + b'\x00' * 1024)
    
    def close(self) -> None:
        """Mock cleanup."""
        self._closed = True


class MockColorClip:
    """Lightweight stub for MoviePy ColorClip class."""
    
    def __init__(self, size: Tuple[int, int], color: Tuple[int, int, int], duration: float, *args, **kwargs):
        self.size = size
        self.w, self.h = size
        self.color = color
        self.duration = duration
        self.fps = kwargs.get('fps', 24)
        self.audio = None
    
    def with_fps(self, fps: float) -> 'MockColorClip':
        """Mock fps setting."""
        self.fps = fps
        return self
    
    def with_duration(self, duration: float) -> 'MockColorClip':
        """Mock duration setting."""
        self.duration = duration
        return self
    
    def write_videofile(self, filename: str, *args, **kwargs) -> None:
        """Mock video file writing."""
        os.makedirs(os.path.dirname(filename), exist_ok=True)
        with open(filename, 'wb') as f:
            f.write(b'\x00\x00\x00\x1cftypmp42\x00\x00\x00\x00mp42isom')
    
    def close(self) -> None:
        """Mock cleanup."""
        pass


class MockTextClip:
    """Lightweight stub for MoviePy TextClip class."""
    
    def __init__(self, text: str, *args, **kwargs):
        self.text = text
        self.font_size = kwargs.get('font_size', 24)
        self.color = kwargs.get('color', 'white')
        self.duration = kwargs.get('duration', 5.0)
        self.size = (640, 480)  # Default text clip size
        self.w, self.h = self.size
    
    def with_position(self, position) -> 'MockTextClip':
        """Mock position setting."""
        self.position = position
        return self
    
    def with_duration(self, duration: float) -> 'MockTextClip':
        """Mock duration setting."""
        self.duration = duration
        return self
    
    def close(self) -> None:
        """Mock cleanup."""
        pass


class MockCompositeVideoClip:
    """Lightweight stub for MoviePy CompositeVideoClip class."""
    
    def __init__(self, clips: List[Any], *args, **kwargs):
        self.clips = clips
        self.duration = max((getattr(clip, 'duration', 5.0) for clip in clips), default=5.0)
        self.fps = getattr(clips[0], 'fps', 24) if clips else 24
        self.size = getattr(clips[0], 'size', (640, 480)) if clips else (640, 480)
        self.w, self.h = self.size
        self.audio = None
    
    def with_fps(self, fps: float) -> 'MockCompositeVideoClip':
        """Mock fps setting."""
        self.fps = fps
        return self
    
    def with_duration(self, duration: float) -> 'MockCompositeVideoClip':
        """Mock duration setting."""
        self.duration = duration
        return self
    
    def write_videofile(self, filename: str, *args, **kwargs) -> None:
        """Mock video file writing."""
        dirname = os.path.dirname(filename)
        if dirname:  # Only create directory if dirname is not empty
            os.makedirs(dirname, exist_ok=True)
        with open(filename, 'wb') as f:
            f.write(b'\x00\x00\x00\x1cftypmp42\x00\x00\x00\x00mp42isom')
    
    def close(self) -> None:
        """Mock cleanup."""
        for clip in self.clips:
            if hasattr(clip, 'close'):
                clip.close()


class MockAudioClip:
    """Lightweight stub for MoviePy AudioClip class."""
    
    def __init__(self, make_frame, duration: float, fps: int = 44100):
        self.make_frame = make_frame
        self.duration = duration
        self.fps = fps
    
    def write_audiofile(self, filename: str, *args, **kwargs) -> None:
        """Mock audio file writing."""
        os.makedirs(os.path.dirname(filename), exist_ok=True)
        with open(filename, 'wb') as f:
            f.write(b'\xff\xfb\x90\x00' + b'\x00' * 1024)
    
    def close(self) -> None:
        """Mock cleanup."""
        pass


def mock_concatenate_videoclips(clips: List[Any], *args, **kwargs) -> MockCompositeVideoClip:
    """Mock concatenate_videoclips function."""
    return MockCompositeVideoClip(clips)


def mock_subprocess_run(*args, **kwargs) -> subprocess.CompletedProcess:
    """Mock subprocess.run to immediately return success for ffmpeg calls."""
    # Check if this is an ffmpeg call
    if args and len(args) > 0:
        cmd = args[0]
        if isinstance(cmd, list) and len(cmd) > 0 and 'ffmpeg' in cmd[0]:
            # Mock successful ffmpeg execution
            return subprocess.CompletedProcess(
                args=cmd,
                returncode=0,
                stdout=b"ffmpeg version mock\n",
                stderr=b""
            )
    
    # For non-ffmpeg calls, use original behavior or return success
    return subprocess.CompletedProcess(
        args=args[0] if args else [],
        returncode=0,
        stdout=b"",
        stderr=b""
    )


# Mock effects functions
def mock_fadein(duration: float):
    """
    Mock fadein effect for MoviePy compatibility.
    
    Args:
        duration: Duration of fade effect in seconds
        
    Returns:
        Mock effect function that can be applied to clips
    """
    def effect_func(clip):
        return clip
    effect_func.__name__ = 'fadein'
    return effect_func


def mock_fadeout(duration: float):
    """
    Mock fadeout effect for MoviePy compatibility.
    
    Args:
        duration: Duration of fade effect in seconds
        
    Returns:
        Mock effect function that can be applied to clips
    """
    def effect_func(clip):
        return clip
    effect_func.__name__ = 'fadeout'
    return effect_func


def mock_speedx(factor: float):
    """
    Mock speed effect for MoviePy compatibility.
    
    Args:
        factor: Speed multiplication factor (e.g., 2.0 for double speed)
        
    Returns:
        Mock effect function that adjusts clip duration based on speed factor
    """
    def effect_func(clip):
        if hasattr(clip, 'duration'):
            clip.duration = clip.duration / factor
        return clip
    effect_func.__name__ = 'speedx'
    return effect_func


def mock_trim_video(input_path: str, start: float, end: float, output_path: str) -> str:
    """
    Mock video trimming for testing purposes.
    
    Args:
        input_path: Path to input video file
        start: Start time in seconds
        end: End time in seconds
        output_path: Path to output trimmed video file
        
    Returns:
        Path to the created mock trimmed video file
    """
    # Ensure directory exists
    dirname = os.path.dirname(output_path)
    if dirname:
        os.makedirs(dirname, exist_ok=True)
    
    # Create mock trimmed file with placeholder content
    with open(output_path, 'w') as f:
        f.write(f"Mock trimmed from {start} to {end}")
    
    return output_path


# Pytest fixture for automatic mocking when MOCK_FFMPEG=1
@pytest.fixture(autouse=True)
def video_shims():
    """
    Automatically apply video processing shims when MOCK_FFMPEG=1 is set.
    
    This fixture patches MoviePy classes and subprocess.run for ffmpeg calls
    to enable unit testing without actual video processing dependencies.
    """
    if os.getenv('MOCK_FFMPEG') != '1':
        # Shims not enabled, skip patching
        yield
        return
    
    patches = []
    
    try:
        # Patch subprocess.run for ffmpeg calls
        subprocess_patch = patch('subprocess.run', side_effect=mock_subprocess_run)
        patches.append(subprocess_patch)
        subprocess_patch.start()
        
        # Patch MoviePy classes - try multiple import paths
        moviepy_patches = [
            # Main moviepy imports
            ('moviepy.VideoFileClip', MockVideoFileClip),
            ('moviepy.AudioFileClip', MockAudioFileClip),
            ('moviepy.ColorClip', MockColorClip),
            ('moviepy.TextClip', MockTextClip),
            ('moviepy.CompositeVideoClip', MockCompositeVideoClip),
            ('moviepy.concatenate_videoclips', mock_concatenate_videoclips),
            
            # Alternative import paths
            ('moviepy.editor.VideoFileClip', MockVideoFileClip),
            ('moviepy.editor.AudioFileClip', MockAudioFileClip),
            ('moviepy.editor.ColorClip', MockColorClip),
            ('moviepy.editor.TextClip', MockTextClip),
            ('moviepy.editor.CompositeVideoClip', MockCompositeVideoClip),
            ('moviepy.editor.concatenate_videoclips', mock_concatenate_videoclips),
            
            # Audio module
            ('moviepy.audio.AudioClip.AudioClip', MockAudioClip),
            
            # Effects modules
            ('moviepy.video.fx.all.fadein', mock_fadein),
            ('moviepy.video.fx.all.fadeout', mock_fadeout),
            ('moviepy.video.fx.all.speedx', mock_speedx),
            ('moviepy.video.fx.fadein', mock_fadein),
            ('moviepy.video.fx.fadeout', mock_fadeout),
            ('moviepy.video.fx.speedx', mock_speedx),
        ]
        
        for module_path, mock_class in moviepy_patches:
            try:
                mock_patch = patch(module_path, mock_class)
                patches.append(mock_patch)
                mock_patch.start()
            except (ImportError, AttributeError):
                # Module/attribute doesn't exist or isn't imported yet
                # This is expected for some import paths
                pass
        
        # Also patch any modules that might import moviepy
        utils_patches = [
            ('utils.utils.VideoFileClip', MockVideoFileClip),
            ('utils.utils.AudioFileClip', MockAudioFileClip),
            ('utils.utils.ColorClip', MockColorClip),
            ('utils.utils.CompositeVideoClip', MockCompositeVideoClip),
            ('utils.utils.concatenate_videoclips', mock_concatenate_videoclips),
            ('workers.workers.VideoFileClip', MockVideoFileClip),
            ('workers.workers.CompositeVideoClip', MockCompositeVideoClip),
            ('workers.workers.ColorClip', MockColorClip),
            ('workers.workers.TextClip', MockTextClip),
        ]
        
        for module_path, mock_class in utils_patches:
            try:
                mock_patch = patch(module_path, mock_class)
                patches.append(mock_patch)
                mock_patch.start()
            except (ImportError, AttributeError):
                # Module not imported yet or doesn't exist
                pass
        
        yield
        
    finally:
        # Stop all patches
        for patch_obj in reversed(patches):
            try:
                patch_obj.stop()
            except RuntimeError:
                # Patch was already stopped or never started
                pass


# Additional utility functions for tests
def create_mock_video_file(path: str, duration: float = 60.0, size: Tuple[int, int] = (640, 480)) -> None:
    """
    Create a mock video file for testing purposes.
    
    Args:
        path: Output file path
        duration: Mock duration in seconds
        size: Mock video dimensions (width, height)
    """
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, 'wb') as f:
        # Write minimal MP4 header with metadata
        header = (
            b'\x00\x00\x00\x1cftypmp42\x00\x00\x00\x00mp42isom'  # ftyp box
            b'\x00\x00\x00\x64moov'  # moov box
            b'\x00\x00\x00\x5ctrak'  # trak box
            b'\x00\x00\x00\x20tkhd\x00\x00\x00\x03'  # tkhd box
        )
        f.write(header)
        # Add mock duration and size metadata (simplified)
        f.write(int(duration).to_bytes(4, 'big'))
        f.write(size[0].to_bytes(2, 'big'))
        f.write(size[1].to_bytes(2, 'big'))


def verify_mock_ffmpeg_active() -> bool:
    """
    Verify that MOCK_FFMPEG environment variable is active.
    
    Returns:
        True if mocking is active, False otherwise
    """
    return os.getenv('MOCK_FFMPEG') == '1'


# Export mock classes for direct use in tests
__all__ = [
    'MockVideoFileClip',
    'MockAudioFileClip', 
    'MockColorClip',
    'MockTextClip',
    'MockCompositeVideoClip',
    'MockAudioClip',
    'mock_concatenate_videoclips',
    'mock_subprocess_run',
    'mock_fadein',
    'mock_fadeout', 
    'mock_speedx',
    'mock_trim_video',
    'video_shims',
    'create_mock_video_file',
    'verify_mock_ffmpeg_active'
]
