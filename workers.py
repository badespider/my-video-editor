# Workers for the multi-agent AI system.
# Each function corresponds to a specific task in the workflow chain.

from utils import call_model, validate_json_output
import config


def analyze_story(script: str) -> dict:
    """
    Analyzes the provided story script, returning structured data.
    """
    prompt = f"Analyze this story: {script[:100]}..."
    response = call_model(prompt)
    return validate_json_output(response)


def choose_clip_descriptions(analysis: dict) -> list:
    """
    Choose video clip descriptions based on scene analysis.
    """
    prompt = f"Generate clip descriptions based on analysis: {analysis}"
    response = call_model(prompt)
    return validate_json_output(response)


def generate_narration(script: str) -> str:
    """
    Generate a narration text based on the provided script.
    """
    prompt = f"Generate narration for this script: {script[:100]}..."
    response = call_model(prompt)
    return response


def suggest_bgm(analysis: dict) -> list:
    """
    Suggest background music options based on scene analysis.
    """
    prompt = f"Suggest background music based on analysis: {analysis}"
    response = call_model(prompt)
    return validate_json_output(response)


def compile_video_plan(clips: list, narrations: list, bgms: list) -> dict:
    """
    Compiles the final video plan including clips, narration, and BGM.
    """
    return {
        "clips": clips,
        "narrations": narrations,
        "bgms": bgms,
        "timeline": "Compiled Timeline description..."
    }
