"""
Utility functions for multi-agent AI system.
Includes call_model wrapper and helper functions for model switching.
"""

import json
import logging
from typing import Dict, Any, Optional
import config

# Configure logging
logging.basicConfig(level=getattr(logging, config.LOG_LEVEL))
logger = logging.getLogger(__name__)


def call_model(prompt: str, model: str = None, **kwargs) -> str:
    """
    Central wrapper for AI model calls. Enables easy model switching.
    
    Args:
        prompt: The prompt to send to the AI model
        model: Override default model from config
        **kwargs: Additional parameters for the model call
    
    Returns:
        Response from the AI model
    
    Raises:
        Exception: If model call fails
    """
    try:
        selected_model = model or config.MODEL
        
        # TODO: Implement actual API calls based on selected_model
        # For MVP, return mock response
        logger.info(f"Calling model: {selected_model}")
        logger.debug(f"Prompt: {prompt[:100]}...")
        
        # Mock response for testing
        return f"Mock response from {selected_model} for prompt: {prompt[:50]}..."
        
    except Exception as e:
        logger.error(f"Model call failed: {e}")
        # Fallback logic can be added here
        raise


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
