from pathlib import Path
from typing import Tuple
import base64
import shutil
import subprocess

try:
    import moviepy.editor as mp
    MOVIEPY_AVAILABLE = True
except ImportError:
    MOVIEPY_AVAILABLE = False


def make_dummy_video(path: Path, duration: float = 0.5, size: Tuple[int, int] = (64, 64), fps: int = 5) -> Path:
    """
    Create a dummy video using MoviePy or fallback to a base64 encoded MP4.

    :param path: Output path for the video file.
    :param duration: Duration of the video in seconds.
    :param size: Size of the video (width, height).
    :param fps: Frames per second.
    :return: Path to the created video file.
    """
    if MOVIEPY_AVAILABLE:
        try:
            # Try to use MoviePy to generate a solid-color clip
            clip = mp.ColorClip(size, color=(255, 0, 0), duration=duration)
            clip = clip.set_fps(fps)
            clip.write_videofile(str(path), codec='libx264')
            return path
        except Exception as e:
            # If MoviePy fails for any reason, fall back to the minimal MP4
            pass
    
    # Fallback strategy if MoviePy is unavailable or fails
    # Try to use the minimal.mp4 from assets
    minimal_mp4_path = Path('tests/assets/minimal.mp4')
    if minimal_mp4_path.exists():
        shutil.copy(minimal_mp4_path, path)
    else:
        # Base64-encoded minimal video as a placeholder
        minimal_mp4_base64 = (
            "AAAAIGZ0eXBtcDQxAAAAAG1wNDFpc29tAAAAHG1kYXQ="
        )

        minimal_mp4_data = base64.b64decode(minimal_mp4_base64)
        with open(path, 'wb') as f:
            f.write(minimal_mp4_data)

    return path


def _has_ffmpeg():
    """Check if FFmpeg is available on the system."""
    try:
        subprocess.run(['ffmpeg', '-version'], capture_output=True, check=True)
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        return False


def skip_if_no_video_support(pytest):
    """
    Skip tests if video support is not available.

    :param pytest: The pytest module.
    """
    if not MOVIEPY_AVAILABLE and not _has_ffmpeg():
        pytest.xfail("Neither MoviePy nor FFmpeg is available for video support.")
    elif not MOVIEPY_AVAILABLE:
        # Check if we have the minimal MP4 file as fallback
        minimal_mp4_path = Path('tests/assets/minimal.mp4')
        if not minimal_mp4_path.exists():
            pytest.xfail("MoviePy is not available and minimal.mp4 fallback is missing.")
