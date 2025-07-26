"""
Coordinator for multi-agent AI system.
Sets up and runs the complete video creation workflow.
"""

from workers import analyze_story, choose_clip_descriptions, generate_narration, suggest_bgm, compile_video_plan
import config


class VideoAgent:
    """
    Central agent for orchestrating the video creation process.
    """

    def __init__(self, model: str = None):
        """
        Initialize with optional model override.
        """
        self.model = model or config.MODEL

    def run(self, script: str) -> dict:
        """
        Execute the full video creation pipeline.
        """
        print("Starting workflow execution...")
        analysis = analyze_story(script)
        clips = choose_clip_descriptions(analysis)
        narration = generate_narration(script)
        bgm_suggestions = suggest_bgm(analysis)

        video_plan = compile_video_plan(clips, [narration], bgm_suggestions)

        print("Workflow completed.")
        return video_plan
