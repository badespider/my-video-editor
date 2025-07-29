"""
Mock implementations for unit testing.

This package contains lightweight mock implementations and shims for external
dependencies to enable isolated unit testing without requiring actual video
processing libraries or system utilities.
"""

from .video_shims import (
    MockVideoFileClip,
    MockAudioFileClip,
    MockColorClip,
    MockTextClip,
    MockCompositeVideoClip,
    MockAudioClip,
    mock_concatenate_videoclips,
    mock_subprocess_run,
    video_shims,
    create_mock_video_file,
    verify_mock_ffmpeg_active
)

__all__ = [
    'MockVideoFileClip',
    'MockAudioFileClip',
    'MockColorClip', 
    'MockTextClip',
    'MockCompositeVideoClip',
    'MockAudioClip',
    'mock_concatenate_videoclips',
    'mock_subprocess_run',
    'video_shims',
    'create_mock_video_file',
    'verify_mock_ffmpeg_active'
]
