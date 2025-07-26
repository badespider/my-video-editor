"""
Utility functions for multi-agent AI system.
Includes call_model wrapper and helper functions for model switching.
"""

import json
import logging
import os
from typing import Dict, Any, Optional, List
import config

# Video processing availability check
moviepu_available = False
gtts_available = False
try:
    from moviepy import VideoFileClip, concatenate_videoclips, AudioFileClip
    moviepu_available = True
    print("INFO: MoviePy is available - using real video processing")
except ImportError as e:
    print(f"WARNING: MoviePy not available - using mock video processing: {e}")
    moviepu_available = False

# Check for PySceneDetect availability (Phase 2)
pyscenedetect_available = False
try:
    import scenedetect
    pyscenedetect_available = True
    print("INFO: PySceneDetect is available - using real scene detection")
except ImportError as e:
    print(f"WARNING: PySceneDetect not available - using mock scene detection: {e}")
    pyscenedetect_available = False

try:
    from gtts import gTTS
    import io
    gtts_available = True
    logging.info("gTTS is available - using real text-to-speech")
except ImportError:
    logging.warning("gTTS not available - using mock text-to-speech")

try:
    import openai
    HAS_OPENAI = True
except ImportError:
    HAS_OPENAI = False

try:
    from game import GameSDK
except ImportError:
    # Fallback for when GAME SDK is not available
    GameSDK = None
    logging.warning("GAME SDK not available - using mock implementation")

# Configure logging
logging.basicConfig(level=getattr(logging, config.LOG_LEVEL))
logger = logging.getLogger(__name__)


def _call_grok_direct(prompt: str, model: str = "grok-4") -> str:
    """
    Direct call to Grok API when GAME SDK is not available.
    
    Args:
        prompt: The prompt to send to Grok
        model: Grok model to use
    
    Returns:
        Response from Grok API
    """
    api_key = os.getenv('GROK_API_KEY') or config.API_KEYS.get('grok', '')
    
    if not api_key:
        logger.warning("No Grok API key found, falling back to mock")
        return _generate_mock_response(prompt, model)
    
    try:
        import requests
        
        headers = {
            'Authorization': f'Bearer {api_key}',
            'Content-Type': 'application/json'
        }
        
        data = {
            'model': model,
            'messages': [
                {'role': 'system', 'content': 'You are a helpful assistant that responds in valid JSON format.'},
                {'role': 'user', 'content': prompt}
            ],
            'temperature': 0.7,
            'max_tokens': 2000
        }
        
        response = requests.post(
            config.ENDPOINTS['grok-4'],
            headers=headers,
            json=data,
            timeout=30
        )
        
        response.raise_for_status()
        content = response.json()['choices'][0]['message']['content']
        
        logger.info(f"Successfully received response from Grok {model}")
        logger.debug(f"Grok response content: {content[:200]}...")
        return content
        
    except Exception as e:
        logger.error(f"Grok API call failed: {e}")
        logger.warning("Falling back to mock response")
        return _generate_mock_response(prompt, model)


def _call_openai_direct(prompt: str, model: str = "gpt-3.5-turbo") -> str:
    """
    Direct call to OpenAI API when GAME SDK is not available.
    
    Args:
        prompt: The prompt to send to OpenAI
        model: OpenAI model to use
    
    Returns:
        Response from OpenAI API
    """
    api_key = os.getenv('OPENAI_API_KEY') or config.API_KEYS.get('openai', '')
    
    if not api_key:
        logger.warning("No OpenAI API key found, falling back to mock")
        return _generate_mock_response(prompt, model)
    
    try:
        client = openai.OpenAI(api_key=api_key)
        
        response = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": "You are a helpful assistant that responds in valid JSON format."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7,
            max_tokens=2000
        )
        
        content = response.choices[0].message.content
        logger.info(f"Successfully received response from OpenAI {model}")
        logger.debug(f"OpenAI response content: {content[:200]}...")
        return content
        
    except Exception as e:
        logger.error(f"OpenAI API call failed: {e}")
        logger.warning("Falling back to mock response")
        return _generate_mock_response(prompt, model)


def _generate_mock_response(prompt: str, model: str) -> str:
    """
    Generate mock JSON responses based on prompt content for testing.
    
    Args:
        prompt: The prompt being sent to the model
        model: The model being called
    
    Returns:
        Mock JSON response as string
    """
    prompt_lower = prompt.lower()
    
    # Story analysis mock response
    if "analyze" in prompt_lower and "story" in prompt_lower:
        return json.dumps({
            "scenes": [
                {
                    "id": 1,
                    "description": "Detective arrives at foggy city scene",
                    "duration": 10
                },
                {
                    "id": 2,
                    "description": "Investigation begins in dark alleyways",
                    "duration": 8
                },
                {
                    "id": 3,
                    "description": "Neon lights illuminate the mystery",
                    "duration": 12
                }
            ]
        })
    
    # Clip chooser mock response
    elif "clip" in prompt_lower:
        return json.dumps({
            "clips": [
                {
                    "id": 1,
                    "description": "Clip for Detective arrives at foggy city scene",
                    "duration": 10,
                    "mood": "mysterious",
                    "scene_id": 1
                }
            ]
        })
    
    # Narration mock response
    elif "narrat" in prompt_lower:
        return json.dumps({
            "narration": "In the shadows, Detective arrives at foggy city scene.",
            "word_count": 10
        })
    
    # BGM mock response
    elif "bgm" in prompt_lower or "music" in prompt_lower:
        return json.dumps({
            "bgm_options": [
                "Mysterious ambient soundscape with urban echoes",
                "Film noir jazz with saxophone undertones"
            ],
            "mood_analysis": {"mysterious": 1}
        })
    
    # Assembly mock response
    elif "assembl" in prompt_lower or "final" in prompt_lower:
        return json.dumps({
            "final_video_plan": {
                "timeline": [
                    {
                        "type": "clip",
                        "content": "Detective arrives at foggy city scene",
                        "duration": 10
                    }
                ],
                "total_duration": 10,
                "narration_overlay": "In the shadows, Detective arrives at foggy city scene.",
                "bgm": "Mysterious ambient soundscape with urban echoes"
            }
        })
    
    # Default mock response
    return json.dumps({
        "mock_response": f"Generated by {model}",
        "prompt_preview": prompt[:50] + "..."
    })


def call_model(prompt: str, model: str = None, **kwargs) -> str:
    """
    Central wrapper for AI model calls that routes to GAME SDK's LLM wrapper.
    Handles try/except, retries with backup model, and logs errors.
    
    Args:
        prompt: The prompt to send to the AI model
        model: Override default model from config
        **kwargs: Additional parameters for the model call
    
    Returns:
        Response from the AI model
    
    Raises:
        Exception: If both primary and backup model calls fail
    """
    selected_model = model or config.MODEL
    
    # First attempt with selected model
    try:
        logger.info(f"Calling model: {selected_model}")
        logger.debug(f"Prompt: {prompt[:100]}...")
        
        if GameSDK is not None:
            # Use GAME SDK's LLM wrapper
            sdk = GameSDK()
            response = sdk.llm.call(prompt, model=selected_model, **kwargs)
            logger.info(f"Successfully received response from {selected_model}")
            return response
        else:
            # Try model-specific APIs if available
            if selected_model == "grok-4":
                return _call_grok_direct(prompt, selected_model)
            elif HAS_OPENAI and (selected_model == "openai" or selected_model.startswith("gpt")):
                openai_model = "gpt-3.5-turbo" if selected_model == "openai" else selected_model
                return _call_openai_direct(prompt, openai_model)
            else:
                # Fallback mock implementation when model is not available
                logger.warning(f"Using mock implementation for {selected_model}")
                # Return valid JSON for different types of prompts
                return _generate_mock_response(prompt, selected_model)
            
    except Exception as e:
        logger.error(f"Primary model call failed with {selected_model}: {e}")
        
        # Retry with backup model if different from primary
        backup_model = config.MODEL_BACKUP
        if backup_model and backup_model != selected_model:
            try:
                logger.info(f"Retrying with backup model: {backup_model}")
                
                if GameSDK is not None:
                    sdk = GameSDK()
                    response = sdk.llm.call(prompt, model=backup_model, **kwargs)
                    logger.info(f"Successfully received response from backup model {backup_model}")
                    return response
                else:
                    # Fallback mock implementation
                    logger.warning(f"Using mock implementation for backup model {backup_model}")
                    return f"Mock response from {backup_model} for prompt: {prompt[:50]}..."
                    
            except Exception as backup_error:
                logger.error(f"Backup model call also failed with {backup_model}: {backup_error}")
                raise Exception(f"Both primary ({selected_model}) and backup ({backup_model}) model calls failed. Primary error: {e}, Backup error: {backup_error}")
        else:
            logger.error(f"No backup model available or backup is same as primary")
            raise Exception(f"Model call failed with {selected_model}: {e}")


def validate_json_output(output: str) -> Dict[Any, Any]:
    """
    Validates and parses JSON output from AI models.
    
    Args:
        output: JSON string from model
    
    Returns:
        Parsed JSON dict
    
    Raises:
        ValueError: If JSON is invalid
    """
    try:
        parsed = json.loads(output)
        return parsed
    except json.JSONDecodeError as e:
        logger.error(f"Invalid JSON output: {e}")
        logger.error(f"Raw output was: '{output}'")
        logger.error(f"Output length: {len(output)} chars")
        raise ValueError(f"Model returned invalid JSON: {e}")


def apply_content_filter(text: str) -> str:
    """
    Apply family-friendly content filtering if enabled.
    
    Args:
        text: Input text to filter
    
    Returns:
        Filtered text
    """
    if not config.FAMILY_FRIENDLY:
        return text
    
    # Basic content filtering - expand as needed
    filtered_text = text
    # TODO: Implement actual content filtering logic
    
    return filtered_text


def truncate_input(text: str, max_words: int = None) -> str:
    """
    Truncate input text to stay within limits.
    
    Args:
        text: Input text
        max_words: Maximum word count (uses config default if None)
    
    Returns:
        Truncated text
    """
    max_words = max_words or config.MAX_SCRIPT_WORDS
    words = text.split()
    
    if len(words) <= max_words:
        return text
    
    logger.warning(f"Truncating input from {len(words)} to {max_words} words")
    return " ".join(words[:max_words])


def create_structured_prompt(task: str, context: str, output_format: str) -> str:
    """
    Create structured prompts for consistent AI responses.
    
    Args:
        task: The specific task description
        context: Context/input data
        output_format: Expected output format description
    
    Returns:
        Formatted prompt string
    """
    prompt = f"""
Task: {task}

Context:
{context}

Output Format: {output_format}

Additional Instructions:
- Be precise and factual
- Avoid hallucinations
- Ground responses in provided context
"""
    
    if config.FAMILY_FRIENDLY:
        prompt += "\n- Keep content family-friendly"
    
    return prompt.strip()


# JSON Validation Helpers
def validate_scene_structure(scene_data: Dict[Any, Any]) -> bool:
    """
    Validates that scene data has required structure for video creation.
    
    Args:
        scene_data: Scene dictionary to validate
    
    Returns:
        True if valid, False otherwise
    """
    required_fields = ['id', 'description', 'duration']
    try:
        return all(field in scene_data for field in required_fields)
    except (TypeError, AttributeError):
        return False


def validate_clips_structure(clips_data: list) -> bool:
    """
    Validates that clips data has proper structure.
    
    Args:
        clips_data: List of clip dictionaries to validate
    
    Returns:
        True if valid, False otherwise
    """
    if not isinstance(clips_data, list):
        return False
    
    required_fields = ['description', 'duration', 'mood']
    try:
        return all(
            isinstance(clip, dict) and 
            all(field in clip for field in required_fields)
            for clip in clips_data
        )
    except (TypeError, AttributeError):
        return False


def sanitize_json_for_model_output(data: Dict[Any, Any]) -> Dict[Any, Any]:
    """
    Sanitizes dictionary data to ensure it's JSON serializable.
    
    Args:
        data: Dictionary to sanitize
    
    Returns:
        Sanitized dictionary
    """
    def _sanitize(obj):
        if isinstance(obj, dict):
            return {str(k): _sanitize(v) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [_sanitize(item) for item in obj]
        elif isinstance(obj, (str, int, float, bool)) or obj is None:
            return obj
        else:
            # Convert non-serializable objects to string
            return str(obj)
    
    return _sanitize(data)


def cleanup_mocks() -> None:
    """
    Clean up mock files and data for production deployment.
    
    Removes temporary files and mock data that shouldn't exist in production.
    """
    mock_files = [
        "mock_video.mp4",
        "temp_analysis.json", 
        "mock_scenes.json",
        "test_output.json"
    ]
    
    for file_path in mock_files:
        if os.path.exists(file_path):
            try:
                os.remove(file_path)
                logger.info(f"Cleaned up mock file: {file_path}")
            except Exception as e:
                logger.warning(f"Failed to clean up {file_path}: {e}")
    
    logger.info("Mock cleanup completed")


# Scene Detection Functions (Phase 2: Rules 2.1, 2.2)

def detect_scenes(video_path: str) -> List[Dict[str, Any]]:
    """
    Detect scenes in video using content-based analysis.
    Falls back to uniform division if real detection unavailable.
    """
    if config.USE_REAL_DETECTION and pyscenedetect_available:
        return _detect_scenes_real(video_path)
    else:
        return _detect_scenes_mock(video_path)


def _detect_scenes_real(video_path: str) -> List[Dict[str, Any]]:
    """Real scene detection using PySceneDetect"""
    # Dummy implementation (actual PySceneDetect processing would go here)
    return []


def _detect_scenes_mock(video_path: str) -> List[Dict[str, Any]]:
    """Mock scene detection for testing - Dynamic version covering full video"""
    # Get video info to create realistic scene distribution
    video_info = get_video_info(video_path)
    total_duration = video_info["duration"]
    
    # Create dynamic scenes based on video duration (Rule 2.1)
    import random
    random.seed(hash(video_path))  # Consistent results for same video
    
    # Calculate number of scenes (3-10 as per rule)
    min_scenes = max(3, int(total_duration / 120))  # At least 1 scene per 2 minutes
    max_scenes = min(config.MAX_SCENES_PER_VIDEO, int(total_duration / 30))  # Max 1 scene per 30s
    num_scenes = min(max_scenes, max(min_scenes, random.randint(3, 10)))
    
    scenes = []
    scene_descriptions = [
        "Opening sequence", "Character introduction", "Setting establishment", 
        "Rising action", "Conflict development", "Tension building",
        "Climactic moment", "Resolution begins", "Final confrontation", 
        "Conclusion", "Epilogue", "Transition scene"
    ]
    
    moods = ["calm", "tense", "intense", "mysterious", "dramatic", "peaceful"]
    
    # Distribute scenes across full video duration
    segment_duration = total_duration / num_scenes
    
    for i in range(num_scenes):
        start_time = i * segment_duration
        # Add some randomness to scene lengths while respecting minimums
        length_variation = random.uniform(0.7, 1.3)
        scene_length = max(config.MIN_SCENE_DURATION, segment_duration * length_variation)
        end_time = min(start_time + scene_length, total_duration)
        
        # Ensure we don't go past the video end
        if i == num_scenes - 1:
            end_time = total_duration
        
        scenes.append({
            "start": start_time,
            "end": end_time,
            "description": scene_descriptions[i % len(scene_descriptions)],
            "mood": random.choice(moods)
        })
    
    # Apply scene scoring (Rule 2.2)
    for scene in scenes:
        scene["score"] = calculate_scene_score(scene, total_duration)
    
    logger.info(f"Mock scene detection: Generated {len(scenes)} scenes covering {total_duration:.1f}s")
    return scenes


def calculate_scene_score(scene: Dict[str, Any], total_duration: float) -> float:
    """
    Calculate scene importance score based on multiple factors.
    Higher scores indicate more interesting/important scenes.
    
    Args:
        scene: Scene dictionary with start, end, description, mood
        total_duration: Total video duration in seconds
    
    Returns:
        Scene score (0.0 to 1.0)
    """
    # Base score from scene duration (longer scenes get higher base score)
    duration = scene["end"] - scene["start"]
    duration_score = min(duration / 60.0, 1.0)  # Cap at 1 minute
    
    # Position score - favor scenes from different parts of video
    position = scene["start"] / total_duration
    # Create a curve that favors middle sections slightly
    position_score = 1.0 - abs(position - 0.5) * 0.5
    
    # Mood-based scoring
    mood_scores = {
        "intense": 1.0,
        "dramatic": 0.9,
        "mysterious": 0.8,
        "tense": 0.7,
        "calm": 0.5,
        "peaceful": 0.4
    }
    mood_score = mood_scores.get(scene["mood"], 0.6)
    
    # Combine scores with weighted average
    final_score = (
        duration_score * 0.3 +
        position_score * 0.3 +
        mood_score * 0.4
    )
    
    return min(final_score, 1.0)


# Video Processing Functions
def extract_clip(video_path: str, start_time: float, end_time: float, output_path: str) -> str:
    """
    Extract a clip from a video file.
    
    Args:
        video_path: Path to source video file
        start_time: Start time in seconds
        end_time: End time in seconds
        output_path: Path for the extracted clip
    
    Returns:
        Path to the extracted clip file
    """
    # Ensure output directory exists
    os.makedirs(config.VIDEO_OUTPUT_DIR, exist_ok=True)
    
    if not moviepu_available:
        # Mock implementation: Create placeholder file
        mock_content = f"Mock clip from {start_time}s to {end_time}s extracted from {video_path}"
        with open(output_path, 'w') as f:
            f.write(mock_content)
        logger.info(f"Mock extracted clip: {output_path}")
        return output_path
    
    try:
        # Real extraction using MoviePy
        video_clip = VideoFileClip(video_path)
        clip = video_clip.subclipped(start_time, end_time)
        clip.write_videofile(output_path, codec="libx264", logger=None)
        video_clip.close()
        clip.close()
        logger.info(f"Successfully extracted clip: {output_path}")
        return output_path
    except Exception as e:
        logger.error(f"Failed to extract clip: {e}")
        # Fallback to mock
        mock_content = f"Mock clip from {start_time}s to {end_time}s (real extraction failed)"
        with open(output_path, 'w') as f:
            f.write(mock_content)
        return output_path


def assemble_clips(clip_paths: List[str], narration_audio: str = None, bgm_path: str = None, output_path: str = "thefinal.mp4") -> str:
    """
    Assemble multiple clips into a final video with optional narration and BGM.
    
    Args:
        clip_paths: List of paths to video clips
        narration_audio: Path to narration audio file (optional)
        bgm_path: Path to background music file (optional)
        output_path: Path for the final assembled video
    
    Returns:
        Path to the final assembled video
    """
    # Ensure output directory exists
    os.makedirs(config.VIDEO_OUTPUT_DIR, exist_ok=True)
    final_output = os.path.join(config.VIDEO_OUTPUT_DIR, output_path)
    
    if not moviepu_available:
        # Mock implementation: Create placeholder file
        mock_content = f"Mock assembled video from clips: {', '.join(clip_paths)}"
        if narration_audio:
            mock_content += f"\nWith narration: {narration_audio}"
        if bgm_path:
            mock_content += f"\nWith BGM: {bgm_path}"
        
        with open(final_output, 'w') as f:
            f.write(mock_content)
        logger.info(f"Mock assembled video: {final_output}")
        return final_output
    
    try:
        # Real assembly using MoviePy
        clips = [VideoFileClip(path) for path in clip_paths if os.path.exists(path)]
        
        if not clips:
            raise ValueError("No valid clips found to assemble")
        
        final_video = concatenate_videoclips(clips)
        
        # Add narration if provided
        if narration_audio and os.path.exists(narration_audio):
            narration = AudioFileClip(narration_audio)
            final_video = final_video.with_audio(narration)
        
        # Add background music if provided
        if bgm_path and os.path.exists(bgm_path):
            bgm = AudioFileClip(bgm_path).with_volume_scaled(0.3)  # Lower volume for BGM
            if final_video.audio:
                # Mix with existing audio
                final_audio = final_video.audio.with_duration(final_video.duration)
                mixed_audio = final_audio.overlay(bgm)
                final_video = final_video.with_audio(mixed_audio)
            else:
                # Set as main audio
                final_video = final_video.with_audio(bgm.with_duration(final_video.duration))
        
        # Write final video
        final_video.write_videofile(final_output, codec="libx264", logger=None)
        
        # Clean up
        for clip in clips:
            clip.close()
        final_video.close()
        
        logger.info(f"Successfully assembled video: {final_output}")
        return final_output
        
    except Exception as e:
        logger.error(f"Failed to assemble video: {e}")
        # Fallback to mock
        mock_content = f"Mock assembled video (real assembly failed): {', '.join(clip_paths)}"
        with open(final_output, 'w') as f:
            f.write(mock_content)
        return final_output


def get_video_info(video_path: str) -> Dict[str, Any]:
    """
    Get basic information about a video file.
    
    Args:
        video_path: Path to the video file
    
    Returns:
        Dictionary containing video information
    """
    if not os.path.exists(video_path):
        # Return mock info for nonexistent files (Rule 2.2: Uniform division fallback)
        logger.warning(f"Video file not found: {video_path}, using mock info")
        return {
            "duration": 300.0,  # 5 minutes mock for testing
            "fps": 30.0,
            "resolution": (1920, 1080),
            "has_audio": True,
            "file_size": 0,
            "mock": True,
            "error": "File not found"
        }
    
    if not moviepu_available:
        # Mock implementation
        return {
            "duration": 300.0,  # 5 minutes mock
            "fps": 30.0,
            "resolution": (1920, 1080),
            "has_audio": True,
            "file_size": os.path.getsize(video_path) if os.path.exists(video_path) else 0
        }
    
    try:
        # Real video analysis using MoviePy
        clip = VideoFileClip(video_path)
        info = {
            "duration": clip.duration,
            "fps": clip.fps,
            "resolution": clip.size,
            "has_audio": clip.audio is not None,
            "file_size": os.path.getsize(video_path)
        }
        clip.close()
        logger.info(f"Retrieved video info for: {video_path}")
        return info
        
    except Exception as e:
        logger.error(f"Failed to get video info: {e}")
        # Fallback to mock info
        return {
            "duration": 300.0,
            "fps": 30.0,
            "resolution": (1920, 1080),
            "has_audio": True,
            "file_size": os.path.getsize(video_path) if os.path.exists(video_path) else 0,
            "error": str(e)
        }


def generate_narration_audio(text: str, output_path: str = "narration.mp3", language: str = "en") -> str:
    """
    Generate audio narration from text using text-to-speech.
    
    Args:
        text: Text to convert to speech
        output_path: Path for the generated audio file
        language: Language code for speech synthesis
    
    Returns:
        Path to the generated audio file
    """
    # Ensure output directory exists
    os.makedirs(config.VIDEO_OUTPUT_DIR, exist_ok=True)
    full_output_path = os.path.join(config.VIDEO_OUTPUT_DIR, output_path)
    
    if not gtts_available:
        # Mock implementation: Create placeholder file
        mock_content = f"Mock audio narration: {text[:100]}..."
        with open(full_output_path, 'w') as f:
            f.write(mock_content)
        logger.info(f"Mock generated narration audio: {full_output_path}")
        return full_output_path
    
    try:
        # Real text-to-speech using gTTS
        tts = gTTS(text=text, lang=language, slow=False)
        tts.save(full_output_path)
        logger.info(f"Successfully generated narration audio: {full_output_path}")
        return full_output_path
        
    except Exception as e:
        logger.error(f"Failed to generate narration audio: {e}")
        # Fallback to mock
        mock_content = f"Mock audio narration (TTS failed): {text[:100]}..."
        with open(full_output_path, 'w') as f:
            f.write(mock_content)
        return full_output_path


def create_silence_audio(duration: float, output_path: str = "silence.mp3") -> str:
    """
    Create a silent audio track of specified duration.
    
    Args:
        duration: Duration in seconds
        output_path: Path for the generated audio file
    
    Returns:
        Path to the generated silence audio file
    """
    # Ensure output directory exists
    os.makedirs(config.VIDEO_OUTPUT_DIR, exist_ok=True)
    full_output_path = os.path.join(config.VIDEO_OUTPUT_DIR, output_path)
    
    if not moviepu_available:
        # Mock implementation
        mock_content = f"Mock silence audio: {duration}s"
        with open(full_output_path, 'w') as f:
            f.write(mock_content)
        logger.info(f"Mock generated silence audio: {full_output_path}")
        return full_output_path
    
    try:
        # Create silence using MoviePy
        from moviepy.audio.AudioClip import AudioClip
        import numpy as np
        
        def make_frame(t):
            return np.array([0.0, 0.0])  # Stereo silence
        
        silence_clip = AudioClip(make_frame, duration=duration, fps=44100)
        silence_clip.write_audiofile(full_output_path, logger=None)
        silence_clip.close()
        
        logger.info(f"Successfully generated silence audio: {full_output_path}")
        return full_output_path
        
    except Exception as e:
        logger.error(f"Failed to generate silence audio: {e}")
        # Fallback to mock
        mock_content = f"Mock silence audio (generation failed): {duration}s"
        with open(full_output_path, 'w') as f:
            f.write(mock_content)
        return full_output_path
