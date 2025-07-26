# Workers for the multi-agent AI system.
# Each class corresponds to a specific task in the workflow chain.

from utils import call_model, validate_json_output, validate_scene_structure, sanitize_json_for_model_output, get_video_info, extract_clip, assemble_clips, generate_narration_audio, detect_scenes
import config
import os
import json
from typing import Dict, Any, List

# Base class for all workers
def validate_common_json_structure(data: dict, expected_key: str) -> bool:
    """
    Validate that the common JSON structure is correct.
    """
    return expected_key in data


class BaseWorker:
    def __init__(self, state: dict):
        self.state = state

    def run(self, input_data: dict) -> dict:
        raise NotImplementedError("Must implement run method")


# Worker for ingesting raw footage
class IngestionWorker(BaseWorker):
    def run(self, video_path: str) -> dict:
        """
        Handle video footage for indexing using dynamic scene detection.
        Phase 2: Rules 2.1, 2.2 - Full video analysis with scoring
        """
        if not os.path.exists(video_path):
            raise FileNotFoundError(f"Video path not found: {video_path}")

        # Get video info for validation (Rule 1.3)
        video_info = get_video_info(video_path)
        duration = video_info.get("duration", 300)
        
        # Validate video duration limit
        if duration > config.VIDEO_MAX_DURATION:
            raise ValueError(f"Video duration {duration}s exceeds maximum {config.VIDEO_MAX_DURATION}s")
        
        # Use new dynamic scene detection (Rule 2.1, 2.2)
        scenes = detect_scenes(video_path)
        
        # Validate coverage requirement (Rule 1.1)
        total_coverage = sum(scene["end"] - scene["start"] for scene in scenes)
        coverage_percentage = total_coverage / duration
        
        if coverage_percentage < config.COVERAGE_REQUIREMENT:
            raise ValueError(f"Scene coverage {coverage_percentage:.1%} below required {config.COVERAGE_REQUIREMENT:.1%}")
        
        # Log successful ingestion
        import logging
        logger = logging.getLogger(__name__)
        logger.info(f"Video ingestion successful: {len(scenes)} scenes, {coverage_percentage:.1%} coverage")
        
        return {
            "scenes": scenes, 
            "total_duration": duration, 
            "video_path": video_path,
            "coverage_percentage": coverage_percentage,
            "scene_count": len(scenes)
        }


# Worker for story analysis
class StoryAnalysisWorker(BaseWorker):
    def run(self, script: str) -> dict:
        prompt = f"""
Analyze this story and break it down into visual scenes suitable for video creation. 
Return ONLY valid JSON with exactly this format:

{{
  "scenes": [
    {{
      "id": 1,
      "description": "Detective arrives at foggy city scene",
      "duration": 10
    }},
    {{
      "id": 2,
      "description": "Investigation begins in dark alleyways", 
      "duration": 8
    }}
  ]
}}

Story to analyze:
{script[:800]}

Requirements:
- Maximum {config.MAX_SCENES} scenes
- Each scene should be 60-120 seconds duration (1-2 minutes)
- Focus on visually compelling moments suitable for longer anime sequences
- Use clear, descriptive language
- Return ONLY the JSON, no other text
"""
        response = call_model(prompt)
        json_output = validate_json_output(response)
        scenes = json_output.get("scenes", [])[:config.MAX_SCENES]
        validated_scenes = [scene for scene in scenes if validate_scene_structure(scene)]
        return sanitize_json_for_model_output({"scenes": validated_scenes})


class ClipChooserWorker(BaseWorker):
    def run(self, analysis: dict) -> dict:
        """
        Extract clips using intelligent selection from scored scenes.
        Phase 3: Rules 3.1, 3.2 - Content-based selection across full video
        """
        if not analysis or "scenes" not in analysis:
            raise ValueError("Analysis must contain 'scenes' key")
        
        scenes = analysis.get('scenes', [])
        video_path = analysis.get('video_path', '')
        total_duration = analysis.get('total_duration', 0)
        
        if not scenes:
            raise ValueError("No scenes found in analysis")
        
        # Phase 3: Rule 3.1 - Content-based selection with coverage
        selected_scenes = self._select_diverse_scenes(scenes, total_duration)
        
        clips = []
        for i, scene in enumerate(selected_scenes):
            # Phase 3: Rule 3.2 - Apply extraction constraints
            start = scene["start"]
            duration = scene["end"] - scene["start"]
            
            # Limit clip duration to MAX_CLIP_DURATION
            actual_duration = min(duration, config.MAX_CLIP_DURATION)
            end = start + actual_duration
            
            # Only extract if scene score meets threshold
            if scene.get("score", 0) >= config.SCENE_SCORE_THRESHOLD:
                description = scene["description"]
                mood = scene.get("mood", "neutral")
                clip_path = os.path.join(config.VIDEO_OUTPUT_DIR, f"clip_{i}.mp4")
                
                extract_clip(video_path, start, end, clip_path)
                clips.append({
                    "id": i+1, 
                    "description": description, 
                    "path": clip_path, 
                    "duration": actual_duration,
                    "mood": mood,
                    "score": scene.get("score", 0),
                    "start_time": start,
                    "end_time": end
                })

        # Log clip selection results
        import logging
        logger = logging.getLogger(__name__)
        logger.info(f"Selected {len(clips)} clips from {len(scenes)} scenes using intelligent selection")
        
        return {"clips": clips}
    
    def _select_diverse_scenes(self, scenes: List[Dict], total_duration: float) -> List[Dict]:
        """
        Select scenes ensuring diversity across the video timeline.
        Rule 3.1: Sort by score, ensure coverage from first/middle/last thirds
        """
        # Sort scenes by score (highest first)
        sorted_scenes = sorted(scenes, key=lambda s: s.get("score", 0), reverse=True)
        
        # Divide video into thirds for coverage
        third_duration = total_duration / 3
        first_third = [s for s in sorted_scenes if s["start"] < third_duration]
        middle_third = [s for s in sorted_scenes if third_duration <= s["start"] < 2 * third_duration]
        last_third = [s for s in sorted_scenes if s["start"] >= 2 * third_duration]
        
        selected = []
        max_clips = min(config.MAX_CLIPS, len(sorted_scenes))
        
        # Ensure at least one clip from each third if available
        coverage_clips = []
        if first_third:
            coverage_clips.append(first_third[0])
        if middle_third:
            coverage_clips.append(middle_third[0])
        if last_third:
            coverage_clips.append(last_third[0])
        
        # Add coverage clips first
        selected.extend(coverage_clips)
        
        # Fill remaining slots with highest scoring scenes not already selected
        remaining_scenes = [s for s in sorted_scenes if s not in selected]
        remaining_slots = max_clips - len(selected)
        
        selected.extend(remaining_scenes[:remaining_slots])
        
        # Final sort by timeline position for logical ordering
        selected_sorted = sorted(selected, key=lambda s: s["start"])
        
        import logging
        logger = logging.getLogger(__name__)
        logger.info(f"Selected scenes coverage: First third: {len([s for s in selected if s['start'] < third_duration])}, "
                   f"Middle third: {len([s for s in selected if third_duration <= s['start'] < 2*third_duration])}, "
                   f"Last third: {len([s for s in selected if s['start'] >= 2*third_duration])}")
        
        return selected_sorted
    
    def _extract_mood(self, description: str) -> str:
        """Extract mood from scene description using simple rules."""
        description_lower = description.lower()
        
        if any(word in description_lower for word in ["fight", "battle", "conflict", "intense"]):
            return "intense"
        elif any(word in description_lower for word in ["sad", "crying", "death", "tragic"]):
            return "sad"
        elif any(word in description_lower for word in ["happy", "joy", "celebration", "laugh"]):
            return "happy"
        elif any(word in description_lower for word in ["mysterious", "suspense", "dark", "unknown"]):
            return "mysterious"
        else:
            return "neutral"
    
    def _validate_clips(self, clips: list) -> list:
        """Validate clips meet duration and structure requirements."""
        validated = []
        for clip in clips:
            # Ensure duration is within limits
            if clip.get("duration", 0) > config.MAX_CLIP_DURATION:
                clip["duration"] = config.MAX_CLIP_DURATION
            
            # Ensure required fields exist
            required_fields = ["id", "description", "duration", "mood"]
            if all(field in clip for field in required_fields):
                validated.append(clip)
        
        return validated


class NarrationWorker(BaseWorker):
    def run(self, clips_data: dict) -> dict:
        """Generate narration based on clips with word limit validation."""
        if not clips_data or "clips" not in clips_data:
            raise ValueError("Input must contain 'clips' key")
        
        clips = clips_data.get("clips", [])
        
        # Generate narration text based on clips (rule-based approach)
        narration_parts = []
        
        for clip in clips:
            clip_description = clip.get("description", "")
            mood = clip.get("mood", "neutral")
            
            # Generate narration segment based on mood and description
            segment = self._generate_narration_segment(clip_description, mood)
            narration_parts.append(segment)
        
        # Combine all parts
        full_narration = " ".join(narration_parts)
        
        # Validate and truncate if necessary
        validated_narration = self._validate_narration(full_narration)
        
        return sanitize_json_for_model_output({
            "narration": validated_narration,
            "word_count": len(validated_narration.split())
        })
    
    def _generate_narration_segment(self, description: str, mood: str) -> str:
        """Generate a narration segment based on clip description and mood."""
        # Simple rule-based narration generation
        mood_prefixes = {
            "intense": "In a dramatic turn of events,",
            "sad": "With heavy hearts,",
            "happy": "Filled with joy,",
            "mysterious": "In the shadows,",
            "neutral": "As the story unfolds,"
        }
        
        prefix = mood_prefixes.get(mood, mood_prefixes["neutral"])
        
        # Extract key elements from description
        cleaned_description = description.replace("Clip for ", "").replace("...", "")
        
        return f"{prefix} {cleaned_description}."
    
    def _validate_narration(self, narration: str) -> str:
        """Validate narration meets word count limits."""
        words = narration.split()
        
        if len(words) <= config.MAX_NARRATION_WORDS:
            return narration
        
        # Truncate to word limit while maintaining sentence structure
        truncated_words = words[:config.MAX_NARRATION_WORDS]
        truncated_text = " ".join(truncated_words)
        
        # Try to end on a complete sentence
        last_period = truncated_text.rfind('.')
        if last_period > len(truncated_text) * 0.8:  # If period is in last 20%
            truncated_text = truncated_text[:last_period + 1]
        
        return truncated_text


class BGMWorker(BaseWorker):
    def run(self, clips_data: dict) -> dict:
        """Generate BGM options based on clip moods with validation."""
        if not clips_data or "clips" not in clips_data:
            raise ValueError("Input must contain 'clips' key")
        
        clips = clips_data.get("clips", [])
        
        # Analyze predominant moods in clips
        mood_counts = {}
        for clip in clips:
            mood = clip.get("mood", "neutral")
            mood_counts[mood] = mood_counts.get(mood, 0) + 1
        
        # Generate BGM options based on mood analysis
        bgm_options = self._generate_bgm_options(mood_counts)
        
        # Validate options don't exceed limit
        validated_options = self._validate_bgm_options(bgm_options)
        
        return sanitize_json_for_model_output({
            "bgm_options": validated_options,
            "mood_analysis": mood_counts
        })
    
    def _generate_bgm_options(self, mood_counts: dict) -> list:
        """Generate BGM options based on mood distribution."""
        # Mood to BGM mapping (rule-based)
        mood_bgm_map = {
            "intense": [
                "Epic orchestral with dramatic crescendos",
                "Heavy electronic beats with tension",
                "Cinematic action music with percussion"
            ],
            "sad": [
                "Melancholic piano with soft strings",
                "Ambient emotional soundscape",
                "Slow acoustic guitar with minor chords"
            ],
            "happy": [
                "Uplifting pop melody with bright instruments",
                "Cheerful acoustic folk music",
                "Positive electronic with upbeat tempo"
            ],
            "mysterious": [
                "Dark ambient with subtle tension",
                "Ethereal synths with mysterious undertones",
                "Minimalist piano with reverb effects"
            ],
            "neutral": [
                "Gentle instrumental background music",
                "Soft ambient atmospheric sounds",
                "Light classical with moderate tempo"
            ]
        }
        
        options = []
        
        # Get most common mood
        if mood_counts:
            primary_mood = max(mood_counts.keys(), key=lambda k: mood_counts[k])
            options.extend(mood_bgm_map.get(primary_mood, mood_bgm_map["neutral"]))
        
        # Add options for secondary moods if significant
        for mood, count in mood_counts.items():
            if count > 1 and mood != primary_mood:  # Secondary mood with multiple clips
                options.extend(mood_bgm_map.get(mood, [])[:1])  # Add one option
        
        return list(set(options))  # Remove duplicates
    
    def _validate_bgm_options(self, options: list) -> list:
        """Validate BGM options don't exceed maximum limit."""
        if len(options) <= config.MAX_BGM_OPTIONS:
            return options
        
        # Return top options up to limit
        return options[:config.MAX_BGM_OPTIONS]


class AssemblyWorker(BaseWorker):
    def run(self, clips: dict, narrations: dict, bgms: dict) -> dict:
        """Assemble clips into a final video file with optional narration and BGM."""
        # Validate inputs
        self._validate_inputs(clips, narrations, bgms)

        # Extract paths for video clips
        clip_paths = [clip["path"] for clip in clips.get("clips", [])]

        # Generate real narration audio from text
        narration_text = narrations.get("narration", "")
        narrative_audio = None
        if narration_text:
            narrative_audio = generate_narration_audio(narration_text, "narration.mp3")
        
        # Setup optional music (for now, we'll use None since we don't have real BGM files)
        bgm_path = None  # TODO: Add real BGM file support

        # Use utility to assemble the final video
        final_path = assemble_clips(clip_paths, narrative_audio, bgm_path)

        # Return result
        return {"final_video": final_path, "plan": "Assembled with narration and BGM"}
    
    def _validate_inputs(self, clips: dict, narrations: dict, bgms: dict) -> None:
        """Validate that all required inputs are present and properly structured."""
        # Validate clips
        if not clips or "clips" not in clips:
            raise ValueError("Clips data must contain 'clips' key")
        
        clips_list = clips.get("clips", [])
        if not clips_list:
            raise ValueError("Must have at least one clip")
        
        # Validate narrations
        if not narrations or "narration" not in narrations:
            raise ValueError("Narrations data must contain 'narration' key")
        
        # Validate BGMs
        if not bgms or "bgm_options" not in bgms:
            raise ValueError("BGMs data must contain 'bgm_options' key")
        
        bgm_options = bgms.get("bgm_options", [])
        if not bgm_options:
            raise ValueError("Must have at least one BGM option")
    
    def _generate_timeline(self, clips: dict, narrations: dict, bgms: dict) -> list:
        """Generate detailed timeline combining clips, narration, and BGM."""
        clips_list = clips.get("clips", [])
        narration_text = narrations.get("narration", "")
        selected_bgm = bgms.get("bgm_options", ["Default BGM"])[0]  # Use first BGM option
        
        timeline = []
        current_time = 0.0
        
        # Add opening with BGM start
        timeline.append({
            "time": current_time,
            "event": "bgm_start",
            "description": f"Start background music: {selected_bgm}",
            "duration": sum(clip.get("duration", 10) for clip in clips_list)
        })
        
        # Add narration start (overlays entire video)
        if narration_text:
            timeline.append({
                "time": current_time,
                "event": "narration_start",
                "description": f"Begin narration: {narration_text[:100]}...",
                "duration": sum(clip.get("duration", 10) for clip in clips_list)
            })
        
        # Add each clip to timeline
        for i, clip in enumerate(clips_list):
            clip_duration = clip.get("duration", 10)
            
            timeline.append({
                "time": current_time,
                "event": "clip_start",
                "clip_id": clip.get("id", i + 1),
                "description": clip.get("description", f"Clip {i + 1}"),
                "mood": clip.get("mood", "neutral"),
                "duration": clip_duration
            })
            
            current_time += clip_duration
            
            timeline.append({
                "time": current_time,
                "event": "clip_end",
                "clip_id": clip.get("id", i + 1)
            })
        
        # Add closing events
        timeline.append({
            "time": current_time,
            "event": "narration_end",
            "description": "End narration"
        })
        
        timeline.append({
            "time": current_time,
            "event": "bgm_end",
            "description": "Fade out background music"
        })
        
        return timeline
    
    def _calculate_total_duration(self, clips: dict) -> float:
        """Calculate total duration of the video from clips."""
        clips_list = clips.get("clips", [])
        total = sum(clip.get("duration", 10) for clip in clips_list)
        return float(total)
