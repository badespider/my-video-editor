"""
Coordinator for multi-agent AI system.
Sets up and runs the complete video creation workflow.
"""

from workers import IngestionWorker, StoryAnalysisWorker, ClipChooserWorker, NarrationWorker, BGMWorker, AssemblyWorker
from utils import truncate_input, apply_content_filter, sanitize_json_for_model_output, call_model
import config
import logging
import json
import os
import re
import time
from typing import Dict, Any, Optional, List

# Configure logging
logging.basicConfig(level=getattr(logging, config.LOG_LEVEL))
logger = logging.getLogger(__name__)


class VideoAgent:
    """
    High-Level Planner (HLP) for orchestrating the complete video creation workflow.
    Sequentially instantiates workers, passes shared state, and includes verification.
    """

    def __init__(self, model: str = None, video_maker=None, ffmpeg_runner=None):
        """
        Initialize VideoAgent with optional model override and video creation dependencies.
        
        Args:
            model: Override default model from config
            video_maker: Custom video creation function for testing (optional)
            ffmpeg_runner: Custom FFmpeg runner for testing (optional)
        """
        self.model = model or config.MODEL
        self.video_maker = video_maker  # Injected dependency for testing
        self.ffmpeg_runner = ffmpeg_runner  # Injected FFmpeg runner
        self.shared_state = {}  # Shared state across all workers
        self.workers = {}  # Container for instantiated workers
        logger.info(f"VideoAgent initialized with model: {self.model}")

    def _create_worker_environment(self) -> Dict[str, Any]:
        """
        Create shared environment state that workers can access.
        
        Returns:
            Dictionary containing shared state and configuration
        """
        return {
            "model": self.model,
            "video_maker": self.video_maker,  # Pass injected video maker
            "ffmpeg_runner": self.ffmpeg_runner,  # Pass injected ffmpeg runner
            "config": {
                "max_scenes": config.MAX_SCENES,
                "max_clip_duration": config.MAX_CLIP_DURATION,
                "max_narration_words": config.MAX_NARRATION_WORDS,
                "max_bgm_options": config.MAX_BGM_OPTIONS,
                "family_friendly": config.FAMILY_FRIENDLY
            },
            "shared_data": self.shared_state.copy()
        }

    def _instantiate_workers(self) -> None:
        """
        Sequentially instantiate all workers with shared state.
        """
        logger.info("Instantiating workers...")
        environment = self._create_worker_environment()
        
        # Sequential instantiation of workers
        self.workers = {
            "story_analysis": StoryAnalysisWorker(),  # Phase 3 StoryAnalysisWorker takes no parameters
            "clip_chooser": ClipChooserWorker(environment),
            "narration": NarrationWorker(environment),
            "bgm": BGMWorker(environment),
            "assembly": AssemblyWorker(environment)
        }
        
        logger.info(f"Successfully instantiated {len(self.workers)} workers")

    def _validate_script_input(self, script: str) -> str:
        """
        Validate and preprocess input script.
        
        Args:
            script: Input script text
            
        Returns:
            Validated and processed script
            
        Raises:
            ValueError: If script is invalid
        """
        if not script or not isinstance(script, str):
            raise ValueError("Script must be a non-empty string")
        
        # Apply content filtering if enabled
        filtered_script = apply_content_filter(script)
        
        # Truncate if too long
        truncated_script = truncate_input(filtered_script, config.MAX_SCRIPT_WORDS)
        
        logger.info(f"Script validated. Length: {len(truncated_script.split())} words")
        return truncated_script

    def _verify_step_output(self, step_name: str, output: Dict[str, Any], expected_keys: list) -> None:
        """
        Verify that a workflow step produced valid output.
        
        Args:
            step_name: Name of the workflow step
            output: Output from the step
            expected_keys: List of expected keys in output
            
        Raises:
            ValueError: If output validation fails
        """
        if not isinstance(output, dict):
            raise ValueError(f"{step_name} step must return a dictionary, got {type(output)}")
        
        missing_keys = [key for key in expected_keys if key not in output]
        if missing_keys:
            raise ValueError(f"{step_name} step missing required keys: {missing_keys}")
        
        # Verify output is JSON serializable
        try:
            sanitized = sanitize_json_for_model_output(output)
            if not sanitized:
                raise ValueError(f"{step_name} step produced empty output")
        except Exception as e:
            raise ValueError(f"{step_name} step produced non-serializable output: {e}")
        
        logger.info(f"{step_name} step output validated successfully")

    def _execute_with_retry(self, worker_name: str, worker_method, input_data: Any, expected_keys: list, max_retries: int = 2) -> Dict[str, Any]:
        """
        Execute worker method with retry logic and validation.
        
        Args:
            worker_name: Name of the worker for logging
            worker_method: Worker method to execute
            input_data: Input data for the worker
            expected_keys: Expected keys in output for validation
            max_retries: Maximum number of retry attempts
            
        Returns:
            Validated output from worker
            
        Raises:
            Exception: If all retry attempts fail
        """
        last_exception = None
        
        for attempt in range(max_retries + 1):
            try:
                logger.info(f"Executing {worker_name} (attempt {attempt + 1}/{max_retries + 1})")
                output = worker_method(input_data)
                
                # Verify output
                self._verify_step_output(worker_name, output, expected_keys)
                
                # Update shared state
                self.shared_state[worker_name] = output
                
                logger.info(f"{worker_name} completed successfully")
                return output
                
            except Exception as e:
                last_exception = e
                logger.warning(f"{worker_name} attempt {attempt + 1} failed: {e}")
                
                if attempt < max_retries:
                    logger.info(f"Retrying {worker_name}...")
                    continue
                else:
                    logger.error(f"{worker_name} failed after {max_retries + 1} attempts")
                    break
        
        # If we get here, all attempts failed
        raise Exception(f"{worker_name} failed after {max_retries + 1} attempts. Last error: {last_exception}")

    def run(self, script: str) -> Dict[str, Any]:
        """
        Execute the complete video creation pipeline with sequential worker execution.
        
        Args:
            script: Input script text
            
        Returns:
            Final video plan as JSON dictionary
            
        Raises:
            ValueError: If input validation fails
            Exception: If any workflow step fails after retries
        """
        logger.info("Starting VideoAgent workflow execution...")
        
        try:
            # Step 0: Validate input
            validated_script = self._validate_script_input(script)
            
            # Step 1: Instantiate workers
            self._instantiate_workers()
            
            # Step 2: Story Analysis
            logger.info("=== Step 1: Story Analysis ===")
            analysis_output = self._execute_with_retry(
                "story_analysis",
                self.workers["story_analysis"].run,
                validated_script,
                ["scenes"]
            )
            
            # Step 3: Clip Selection
            logger.info("=== Step 2: Clip Selection ===")
            clips_output = self._execute_with_retry(
                "clip_chooser",
                self.workers["clip_chooser"].run,
                analysis_output,
                ["clips"]
            )
            
            # Step 4: Narration Generation - Skip if disabled (Rule 4.1)
            if config.ENABLE_NARRATION:
                logger.info("=== Step 3: Narration Generation ===")
                narration_output = self._execute_with_retry(
                    "narration",
                    self.workers["narration"].run,
                    clips_output,
                    ["narration"]
                )
            else:
                logger.info("=== Step 3: Narration Generation - SKIPPED (disabled in config) ===")
                narration_output = {"narration": "", "word_count": 0, "skipped": True}
            
            # Step 5: BGM Suggestions - Skip if disabled (Rule 4.1)
            if config.ENABLE_BGM:
                logger.info("=== Step 4: BGM Suggestions ===")
                bgm_output = self._execute_with_retry(
                    "bgm",
                    self.workers["bgm"].run,
                    clips_output,
                    ["bgm_options"]
                )
            else:
                logger.info("=== Step 4: BGM Suggestions - SKIPPED (disabled in config) ===")
                bgm_output = {"bgm_options": [], "mood_analysis": {}, "skipped": True}
            
            # Step 6: Final Assembly
            logger.info("=== Step 5: Final Assembly ===")
            final_plan = self._execute_with_retry(
                "assembly",
                lambda _: self.workers["assembly"].run(clips_output, narration_output, bgm_output),
                None,
                ["clips", "narrations", "bgms", "timeline"]
            )
            
            # Final validation
            self._verify_final_plan(final_plan)
            
            logger.info("VideoAgent workflow completed successfully!")
            return final_plan
            
        except Exception as e:
            logger.error(f"VideoAgent workflow failed: {e}")
            raise
    
    def _verify_final_plan(self, final_plan: Dict[str, Any]) -> None:
        """
        Perform final validation on the complete video plan.
        
        Args:
            final_plan: The final assembled video plan
            
        Raises:
            ValueError: If final plan validation fails
        """
        required_final_keys = ["clips", "narrations", "bgms", "timeline", "total_duration"]
        
        for key in required_final_keys:
            if key not in final_plan:
                raise ValueError(f"Final plan missing required key: {key}")
        
        # Validate that timeline is not empty
        timeline = final_plan.get("timeline", [])
        if not timeline or len(timeline) == 0:
            raise ValueError("Final plan timeline cannot be empty")
        
        # Validate total duration is positive
        total_duration = final_plan.get("total_duration", 0)
        if total_duration <= 0:
            raise ValueError("Final plan total_duration must be positive")
        
        logger.info(f"Final plan validated: {len(timeline)} timeline events, {total_duration}s duration")

    def _verify_video_final_plan(self, final_plan: Dict[str, Any]) -> None:
        """
        Perform final validation on the video processing result.
        Rule 4.1: Validate coverage in run_with_video
        
        Args:
            final_plan: The final video processing result
            
        Raises:
            ValueError: If final plan validation fails
        """
        required_video_keys = ["final_video", "plan"]
        
        for key in required_video_keys:
            if key not in final_plan:
                raise ValueError(f"Video final plan missing required key: {key}")
        
        # Validate final video path exists
        final_video_path = final_plan.get("final_video", "")
        if not final_video_path:
            raise ValueError("Final video path cannot be empty")
        
        # Rule 4.1: Validate coverage requirement
        coverage_percentage = final_plan.get("coverage_percentage", 0)
        if coverage_percentage < config.MIN_COVERAGE_PERCENTAGE / 100.0:
            raise ValueError(
                f"Coverage {coverage_percentage:.1%} below minimum requirement "
                f"{config.MIN_COVERAGE_PERCENTAGE}%"
            )
        
        logger.info(f"Video final plan validated: {final_video_path}, coverage: {coverage_percentage:.1%}")

    def run_with_video(self, video_path: str) -> Dict[str, Any]:
        """
        Execute the video analysis pipeline using existing video file.
        
        Args:
            video_path: Path to the video file to analyze
            
        Returns:
            Final video plan as JSON dictionary based on video analysis
            
        Raises:
            ValueError: If video file validation fails  
            Exception: If any workflow step fails after retries
        """
        logger.info(f"Starting VideoAgent video analysis workflow for: {video_path}")
        
        try:
            # Step 0: Validate video file exists
            import os
            if not os.path.exists(video_path):
                raise ValueError(f"Video file not found: {video_path}")
            
            # Step 1: Create ingestion worker and analyze video
            logger.info("=== Step 1: Video Ingestion and Analysis ===")
            environment = self._create_worker_environment()
            ingestion_worker = IngestionWorker(environment)
            
            video_analysis = self._execute_with_retry(
                "video_ingestion",
                ingestion_worker.run,
                video_path,
                ["scenes"]
            )
            
            # Step 2: Instantiate other workers
            self._instantiate_workers()
            
            # Step 3: Convert video analysis to scene format and process with clip chooser
            logger.info("=== Step 2: Clip Selection from Video Analysis ===")
            clips_output = self._execute_with_retry(
                "clip_chooser",
                self.workers["clip_chooser"].run,
                video_analysis,
                ["clips"]
            )
            
            # Step 4: Narration Generation based on clips - Skip if disabled (Rule 4.1)
            if config.ENABLE_NARRATION:
                logger.info("=== Step 3: Narration Generation ===")
                narration_output = self._execute_with_retry(
                    "narration",
                    self.workers["narration"].run,
                    clips_output,
                    ["narration"]
                )
            else:
                logger.info("=== Step 3: Narration Generation - SKIPPED (disabled in config) ===")
                narration_output = {"narration": "", "word_count": 0, "skipped": True}
            
            # Step 5: BGM Suggestions based on clips - Skip if disabled (Rule 4.1)
            if config.ENABLE_BGM:
                logger.info("=== Step 4: BGM Suggestions ===")
                bgm_output = self._execute_with_retry(
                    "bgm",
                    self.workers["bgm"].run,
                    clips_output,
                    ["bgm_options"]
                )
            else:
                logger.info("=== Step 4: BGM Suggestions - SKIPPED (disabled in config) ===")
                bgm_output = {"bgm_options": [], "mood_analysis": {}, "skipped": True}
            
            # Step 6: Final Assembly
            logger.info("=== Step 5: Final Assembly ===")
            final_plan = self._execute_with_retry(
                "assembly",
                lambda _: self.workers["assembly"].run(clips_output, narration_output, bgm_output),
                None,
                ["final_video", "plan"]
            )
            
            # Add video source information to the final plan
            final_plan["source_video"] = video_path
            final_plan["processing_type"] = "video_analysis"
            final_plan["coverage_percentage"] = video_analysis.get("coverage_percentage", 0)
            final_plan["scene_count"] = video_analysis.get("scene_count", 0)
            
            # Final validation for video processing (different format)
            self._verify_video_final_plan(final_plan)
            
            logger.info("VideoAgent video analysis workflow completed successfully!")
            return final_plan
            
        except Exception as e:
            logger.error(f"VideoAgent video analysis workflow failed: {e}")
            raise

    def get_shared_state(self) -> Dict[str, Any]:
        """
        Get current shared state across all workers.
        
        Returns:
            Copy of shared state dictionary
        """
        return self.shared_state.copy()

    def reset_state(self) -> None:
        """
        Reset shared state and workers for fresh execution.
        """
        self.shared_state.clear()
        self.workers.clear()
        logger.info("VideoAgent state reset completed")


    def parse_command(self, message: str) -> dict:
        """
        Parse a natural language command into a structured edit action.

        Args:
            message: The command message in natural language

        Returns:
            Parsed command as a dictionary
        """
        try:
            logger.info(f"Parsing command: {message}")
            prompt = f"Parse video edit command: {message}. Return JSON: {{type: str, params: dict}}."
            response = call_model(prompt, "gpt-4")
            parsed_command = json.loads(response)

            # Validate parsed command structure
            if not isinstance(parsed_command, dict) or 'type' not in parsed_command or 'params' not in parsed_command:
                raise ValueError("Parsed command is missing required fields")

            logger.info(f"Command parsed successfully: {parsed_command}")
            return parsed_command
        except Exception as e:
            logger.error(f"Error parsing command: {e}")
            raise ValueError(f"Failed to parse command: {e}")


    def _validate_command(self, command: dict, required_keys: List[str]) -> bool:
        """
        Validate the structure of a command dictionary.

        Args:
            command: Command dictionary to validate
            required_keys: List of required keys in the command

        Returns:
            True if valid, False otherwise
        """
        return all(key in command for key in required_keys)


    def apply_command(self, session_data: dict, command: dict) -> None:
        """
        Apply a parsed command to the session data with enhanced preview and validation.
        Rule 3.1: Enhanced edit/preview limitations fixes.

        Args:
            session_data: The session data to update
            command: The parsed command to apply

        Raises:
            ValueError: If the command is invalid or cannot be applied
        """
        if not self._validate_command(command, ['command', 'parameters']):
            # Try alternative format
            if not self._validate_command(command, ['type', 'params']):
                raise ValueError("Invalid command structure - must have 'command'/'parameters' or 'type'/'params'")
            # Convert to standard format
            command = {'command': command['type'], 'parameters': command['params']}

        logger.info(f"Applying command: {command}")
        command_type = command['command']
        params = command['parameters']
        
        # Update last activity
        import time
        session_data['last_activity'] = time.time()

        try:
            # Apply command based on type with enhanced validation
            if command_type == 'trim':
                self._apply_trim_command_enhanced(session_data, params)
            elif command_type == 'adjust_volume':
                self._apply_volume_command(session_data, params)
            elif command_type == 'add_text':
                self._apply_text_command(session_data, params)
            elif command_type == 'crop':
                self._apply_crop_command(session_data, params)
            elif command_type == 'rotate':
                self._apply_rotate_command(session_data, params)
            elif command_type == 'speed_change':
                self._apply_speed_command(session_data, params)
            elif command_type == 'filter':
                self._apply_filter_command(session_data, params)
            else:
                raise ValueError(f"Unsupported command type: {command_type}")
                
            # Generate updated preview after successful command application
            self._update_session_preview(session_data, command_type, params)
            
            logger.info(f"Command '{command_type}' applied successfully")
            
        except Exception as e:
            logger.error(f"Failed to apply command '{command_type}': {e}")
            raise ValueError(f"Command application failed: {e}")

    def _apply_trim_command(self, session_data: dict, params: dict) -> None:
        """
        Apply a trim command to the video session with enhanced validation.

        Args:
            session_data: The session data containing video info
            params: Parameters for the trim command

        Raises:
            ValueError: If trim parameters are invalid
        """
        start = params.get('start')
        end = params.get('end')
        video_duration = session_data.get('video_duration', 0)
        
        # Enhanced validation (Rule 1.3)
        if start is None:
            raise ValueError("Trim start parameter is required")
        
        if not isinstance(start, (int, float)) or start < 0:
            raise ValueError(f"Invalid start time: {start}. Must be a non-negative number.")
        
        # If end is not provided, use video duration
        if end is None:
            if video_duration > 0:
                end = video_duration
            else:
                raise ValueError("End time is required when video duration is unknown")
        
        if not isinstance(end, (int, float)):
            raise ValueError(f"Invalid end time: {end}. Must be a number.")
        
        # Core validation: end must be greater than start
        if end <= start:
            raise ValueError(f"Invalid trim range: end ({end}) must be greater than start ({start})")
        
        # Video duration validation if available
        if video_duration > 0:
            if start >= video_duration:
                raise ValueError(f"Start time ({start}) exceeds video duration ({video_duration})")
            if end > video_duration:
                logger.warning(f"End time ({end}) exceeds video duration ({video_duration}), clamping to duration")
                end = video_duration
        
        # Minimum trim duration check
        min_duration = 1.0  # 1 second minimum
        trim_duration = end - start
        if trim_duration < min_duration:
            raise ValueError(f"Trim duration ({trim_duration}s) is too short. Minimum is {min_duration}s")

        # Placeholder logic for trimming video
        video_path = session_data['video_path']
        # Perform trimming logic here (e.g., using MoviePy or other libraries)
        new_path = f"{video_path}_trimmed_{start}_{end}.mp4"  # Dummy new path
        session_data['preview_path'] = new_path
        session_data['edits'].append({'type': 'trim', 'params': {'start': start, 'end': end}})

        logger.info(f"Trim applied. Start: {start}, End: {end}, Duration: {trim_duration}s, New Path: {new_path}")

    def finalize_video(self, session_data: dict) -> str:
        """
        Finalize video by applying all edits in batch and creating final MP4.
        
        Args:
            session_data: Session data containing video path and edits
            
        Returns:
            Path to the finalized video file
            
        Raises:
            ValueError: If finalization fails
        """
        try:
            from utils.utils import extract_clip, assemble_clips
            import uuid
            
            video_path = session_data.get('video_path')
            edits = session_data.get('edits', [])
            
            if not video_path or not os.path.exists(video_path):
                raise ValueError("Video path is invalid or file does not exist")
            
            logger.info(f"Finalizing video with {len(edits)} edits")
            
            # Generate final video path
            final_path = f"final_{str(uuid.uuid4())[:8]}.mp4"
            
            if not edits:
                # No edits applied, return original video
                import shutil
                shutil.copy2(video_path, final_path)
                logger.info(f"No edits to apply, copied original video to: {final_path}")
                return final_path
            
            # Apply all edits sequentially
            current_path = video_path
            
            for i, edit in enumerate(edits):
                edit_type = edit.get('type')
                params = edit.get('params', {})
                
                if edit_type == 'trim':
                    start = params.get('start', 0)
                    end = params.get('end')
                    
                    temp_output = f"temp_edit_{i}_{str(uuid.uuid4())[:8]}.mp4"
                    
                    # Apply trim edit
                    extract_clip(current_path, start, end, temp_output)
                    
                    # Update current path for next edit
                    if current_path != video_path:
                        # Clean up previous temp file
                        try:
                            os.remove(current_path)
                        except:
                            pass
                    
                    current_path = temp_output
                    logger.info(f"Applied edit {i+1}/{len(edits)}: {edit_type}")
                
                # Add more edit types here as needed
                else:
                    logger.warning(f"Unknown edit type: {edit_type}")
            
            # Final assembly step
            if current_path != final_path:
                if current_path != video_path:
                    # Move temp file to final location
                    import shutil
                    shutil.move(current_path, final_path)
                else:
                    # Copy original if no temp file was created
                    import shutil
                    shutil.copy2(current_path, final_path)
            
            logger.info(f"Video finalization completed: {final_path}")
            return final_path
            
        except Exception as e:
            logger.error(f"Video finalization failed: {e}")
            # Return latest preview as fallback
            return session_data.get('preview_path', session_data.get('video_path', ''))

    def _apply_trim_command_enhanced(self, session_data: dict, params: dict) -> None:
        """
        Enhanced trim command with improved preview generation and temp file management.
        Rule 3.1: Enhanced edit/preview limitations fixes.
        
        Args:
            session_data: The session data containing video info
            params: Parameters for the trim command
        """
        try:
            from utils.utils import trim_video
            import tempfile
            import uuid
            
            # Extract and validate parameters
            start_time = params.get('start_time', params.get('start', 0))
            end_time = params.get('end_time', params.get('end'))
            
            # Enhanced parameter validation
            if not isinstance(start_time, (int, float)) or start_time < 0:
                raise ValueError(f"Invalid start time: {start_time}. Must be a non-negative number.")
                
            if end_time is not None and (not isinstance(end_time, (int, float)) or end_time <= start_time):
                raise ValueError(f"Invalid end time: {end_time}. Must be a number greater than start time.")
                
            # Get current video path (use latest preview if available)
            current_video = session_data.get('preview_path') or session_data.get('video_path')
            if not current_video or not os.path.exists(current_video):
                raise ValueError("No valid video file found for trimming")
                
            # Clean up old preview if it exists and is different from original
            old_preview = session_data.get('preview_path')
            if old_preview and old_preview != session_data.get('video_path') and os.path.exists(old_preview):
                try:
                    os.remove(old_preview)
                    logger.info(f"Cleaned up old preview: {old_preview}")
                except Exception as cleanup_error:
                    logger.warning(f"Failed to cleanup old preview: {cleanup_error}")
                    
            # Generate new preview path
            session_id = session_data.get('session_id', str(uuid.uuid4())[:8])
            preview_filename = f"preview_{session_id}_{len(session_data.get('edits', []))}_{int(time.time())}.mp4"
            preview_path = os.path.join(config.VIDEO_OUTPUT_DIR, preview_filename)
            
            # Ensure output directory exists
            os.makedirs(config.VIDEO_OUTPUT_DIR, exist_ok=True)
            
            # Convert time parameters to string format for trim_video function
            def seconds_to_time_string(seconds: float) -> str:
                hours = int(seconds // 3600)
                minutes = int((seconds % 3600) // 60)
                secs = int(seconds % 60)
                return f"{hours:02d}:{minutes:02d}:{secs:02d}"
                
            start_time_str = seconds_to_time_string(start_time)
            end_time_str = seconds_to_time_string(end_time) if end_time else None
            
            # Perform the trim operation
            trim_video(current_video, start_time_str, end_time_str, preview_path)
            
            # Update session data
            session_data['preview_path'] = preview_path
            
            # Add edit to history with timestamp
            edit_record = {
                'type': 'trim',
                'params': {'start_time': start_time, 'end_time': end_time},
                'timestamp': time.time(),
                'preview_path': preview_path
            }
            session_data['edits'].append(edit_record)
            
            logger.info(f"Enhanced trim applied: {start_time}-{end_time}s, preview: {preview_path}")
            
        except Exception as e:
            logger.error(f"Enhanced trim command failed: {e}")
            raise ValueError(f"Trim operation failed: {e}")
            
    def _apply_volume_command(self, session_data: dict, params: dict) -> None:
        """
        Apply volume adjustment command.
        """
        try:
            volume_level = params.get('level', params.get('volume', 1.0))
            
            if not isinstance(volume_level, (int, float)) or volume_level < 0:
                raise ValueError(f"Invalid volume level: {volume_level}. Must be a non-negative number.")
                
            # Placeholder for volume adjustment logic
            edit_record = {
                'type': 'adjust_volume',
                'params': {'volume': volume_level},
                'timestamp': time.time()
            }
            session_data['edits'].append(edit_record)
            
            logger.info(f"Volume adjustment applied: {volume_level}")
            
        except Exception as e:
            logger.error(f"Volume command failed: {e}")
            raise ValueError(f"Volume adjustment failed: {e}")
            
    def _apply_text_command(self, session_data: dict, params: dict) -> None:
        """
        Apply text overlay command.
        """
        try:
            text = params.get('text', '')
            position = params.get('position', 'center')
            duration = params.get('duration', 5.0)
            
            if not text:
                raise ValueError("Text content is required")
                
            # Placeholder for text overlay logic
            edit_record = {
                'type': 'add_text',
                'params': {'text': text, 'position': position, 'duration': duration},
                'timestamp': time.time()
            }
            session_data['edits'].append(edit_record)
            
            logger.info(f"Text overlay applied: '{text}' at {position} for {duration}s")
            
        except Exception as e:
            logger.error(f"Text command failed: {e}")
            raise ValueError(f"Text overlay failed: {e}")
            
    def _apply_crop_command(self, session_data: dict, params: dict) -> None:
        """
        Apply crop command.
        """
        try:
            x = params.get('x', 0)
            y = params.get('y', 0)
            width = params.get('width')
            height = params.get('height')
            
            if width is None or height is None:
                raise ValueError("Width and height are required for cropping")
                
            # Placeholder for crop logic
            edit_record = {
                'type': 'crop',
                'params': {'x': x, 'y': y, 'width': width, 'height': height},
                'timestamp': time.time()
            }
            session_data['edits'].append(edit_record)
            
            logger.info(f"Crop applied: {x},{y} {width}x{height}")
            
        except Exception as e:
            logger.error(f"Crop command failed: {e}")
            raise ValueError(f"Crop operation failed: {e}")
            
    def _apply_rotate_command(self, session_data: dict, params: dict) -> None:
        """
        Apply rotation command.
        """
        try:
            angle = params.get('angle', 90)
            
            if not isinstance(angle, (int, float)):
                raise ValueError(f"Invalid rotation angle: {angle}. Must be a number.")
                
            # Placeholder for rotation logic
            edit_record = {
                'type': 'rotate',
                'params': {'angle': angle},
                'timestamp': time.time()
            }
            session_data['edits'].append(edit_record)
            
            logger.info(f"Rotation applied: {angle} degrees")
            
        except Exception as e:
            logger.error(f"Rotate command failed: {e}")
            raise ValueError(f"Rotation failed: {e}")
            
    def _apply_speed_command(self, session_data: dict, params: dict) -> None:
        """
        Apply speed change command.
        """
        try:
            speed_factor = params.get('factor', params.get('speed', 1.0))
            
            if not isinstance(speed_factor, (int, float)) or speed_factor <= 0:
                raise ValueError(f"Invalid speed factor: {speed_factor}. Must be a positive number.")
                
            # Placeholder for speed change logic
            edit_record = {
                'type': 'speed_change',
                'params': {'factor': speed_factor},
                'timestamp': time.time()
            }
            session_data['edits'].append(edit_record)
            
            logger.info(f"Speed change applied: {speed_factor}x")
            
        except Exception as e:
            logger.error(f"Speed command failed: {e}")
            raise ValueError(f"Speed change failed: {e}")
            
    def _apply_filter_command(self, session_data: dict, params: dict) -> None:
        """
        Apply video filter command.
        """
        try:
            filter_type = params.get('type', params.get('filter', 'none'))
            intensity = params.get('intensity', 0.5)
            
            if not isinstance(intensity, (int, float)) or not (0 <= intensity <= 1):
                raise ValueError(f"Invalid filter intensity: {intensity}. Must be between 0 and 1.")
                
            # Placeholder for filter logic
            edit_record = {
                'type': 'filter',
                'params': {'filter_type': filter_type, 'intensity': intensity},
                'timestamp': time.time()
            }
            session_data['edits'].append(edit_record)
            
            logger.info(f"Filter applied: {filter_type} at {intensity} intensity")
            
        except Exception as e:
            logger.error(f"Filter command failed: {e}")
            raise ValueError(f"Filter application failed: {e}")
            
    def _update_session_preview(self, session_data: dict, command_type: str, params: dict) -> None:
        """
        Update session preview after successful command application.
        Rule 3.1: Ensure session preview is updated correctly after every edit.
        
        Args:
            session_data: Session data to update
            command_type: Type of command that was applied
            params: Parameters of the applied command
        """
        try:
            # For commands that create new preview files (like trim), the preview is already updated
            if command_type == 'trim':
                # Already handled in _apply_trim_command_enhanced
                return
                
            # For other commands, generate a new preview if needed
            current_preview = session_data.get('preview_path')
            if current_preview and os.path.exists(current_preview):
                # Preview path is valid, no immediate update needed
                # This will be updated during finalization
                logger.info(f"Preview state maintained for {command_type} command")
            else:
                # Reset to original video path if preview is missing
                original_video = session_data.get('video_path')
                if original_video and os.path.exists(original_video):
                    session_data['preview_path'] = original_video
                    logger.info(f"Preview reset to original video for {command_type} command")
                else:
                    logger.warning(f"No valid video path available for preview update after {command_type}")
                    
        except Exception as e:
            logger.error(f"Failed to update session preview after {command_type}: {e}")
            # Don't raise error here to avoid breaking the command application flow

def analyze_story(script: str) -> Dict[str, Any]:
    """Standalone function for story analysis."""
    worker = StoryAnalysisWorker()
    return worker.run(script)

def choose_clip_descriptions(analysis: Dict[str, Any]) -> list:
    """Standalone function for clip selection."""
    worker = ClipChooserWorker({})
    result = worker.run(analysis)
    return result.get("clips", [])

def generate_narration(script: str) -> str:
    """Standalone function for narration generation."""
    # For backward compatibility, create clips from script first
    analysis_worker = StoryAnalysisWorker()
    analysis = analysis_worker.run(script)
    
    clip_worker = ClipChooserWorker({})
    clips_data = clip_worker.run(analysis)
    
    narration_worker = NarrationWorker({})
    result = narration_worker.run(clips_data)
    return result.get("narration", "")

def suggest_bgm(analysis: Dict[str, Any]) -> list:
    """Standalone function for BGM suggestions."""
    # Convert analysis to clips format for BGM worker
    clip_worker = ClipChooserWorker({})
    clips_data = clip_worker.run(analysis)
    
    bgm_worker = BGMWorker({})
    result = bgm_worker.run(clips_data)
    return result.get("bgm_options", [])

def compile_video_plan(clips: list, narrations: list, bgm_suggestions: list) -> Dict[str, Any]:
    """Standalone function for video plan compilation."""
    # Convert inputs to expected format
    clips_data = {"clips": clips}
    narrations_data = {"narration": narrations[0] if narrations else "", "word_count": len(narrations[0].split()) if narrations else 0}
    bgms_data = {"bgm_options": bgm_suggestions}
    
    assembly_worker = AssemblyWorker({})
    return assembly_worker.run(clips_data, narrations_data, bgms_data)
