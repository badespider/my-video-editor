"""
Coordinator for multi-agent AI system.
Sets up and runs the complete video creation workflow.
"""

from workers import IngestionWorker, StoryAnalysisWorker, ClipChooserWorker, NarrationWorker, BGMWorker, AssemblyWorker
from utils import truncate_input, apply_content_filter, sanitize_json_for_model_output
import config
import logging
from typing import Dict, Any, Optional

# Configure logging
logging.basicConfig(level=getattr(logging, config.LOG_LEVEL))
logger = logging.getLogger(__name__)


class VideoAgent:
    """
    High-Level Planner (HLP) for orchestrating the complete video creation workflow.
    Sequentially instantiates workers, passes shared state, and includes verification.
    """

    def __init__(self, model: str = None):
        """
        Initialize VideoAgent with optional model override.
        
        Args:
            model: Override default model from config
        """
        self.model = model or config.MODEL
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
            "story_analysis": StoryAnalysisWorker(environment),
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
            
            # Step 4: Narration Generation
            logger.info("=== Step 3: Narration Generation ===")
            narration_output = self._execute_with_retry(
                "narration",
                self.workers["narration"].run,
                clips_output,
                ["narration"]
            )
            
            # Step 5: BGM Suggestions
            logger.info("=== Step 4: BGM Suggestions ===")
            bgm_output = self._execute_with_retry(
                "bgm",
                self.workers["bgm"].run,
                clips_output,
                ["bgm_options"]
            )
            
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
            
            # Step 4: Narration Generation based on clips
            logger.info("=== Step 3: Narration Generation ===")
            narration_output = self._execute_with_retry(
                "narration",
                self.workers["narration"].run,
                clips_output,
                ["narration"]
            )
            
            # Step 5: BGM Suggestions based on clips
            logger.info("=== Step 4: BGM Suggestions ===")
            bgm_output = self._execute_with_retry(
                "bgm",
                self.workers["bgm"].run,
                clips_output,
                ["bgm_options"]
            )
            
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


# Convenience functions for backward compatibility with existing tests
def analyze_story(script: str) -> Dict[str, Any]:
    """Standalone function for story analysis."""
    worker = StoryAnalysisWorker({})
    return worker.run(script)

def choose_clip_descriptions(analysis: Dict[str, Any]) -> list:
    """Standalone function for clip selection."""
    worker = ClipChooserWorker({})
    result = worker.run(analysis)
    return result.get("clips", [])

def generate_narration(script: str) -> str:
    """Standalone function for narration generation."""
    # For backward compatibility, create clips from script first
    analysis_worker = StoryAnalysisWorker({})
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
