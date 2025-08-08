"""
Configuration file for multi-agent AI video creation system.
Centralizes model selection, API keys, and system parameters.
Follows Rule 1.1: Config-Driven Design for easy model switching.
"""

import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Environment Settings
ENV = os.getenv('ENV', 'dev')  # 'dev', 'prod', 'test'
DEBUG = ENV == 'dev'

# Environment-Specific Configurations (Rule 1.2)
# Use environment variable growth to load proper settings
ENV_CONFIG = {
    'dev': {
        'LOG_LEVEL': 'DEBUG',
        'AUTO_CLEANUP': False,
        'MOCK_MODE': True,
        'ENABLE_REAL_APIS': False,
    },
    'prod': {
        'LOG_LEVEL': 'INFO',
        'AUTO_CLEANUP': True,
        'MOCK_MODE': False,
        'ENABLE_REAL_APIS': True,
    },
    'test': {
        'LOG_LEVEL': 'DEBUG',
        'AUTO_CLEANUP': False,
        'MOCK_MODE': True,
        'ENABLE_REAL_APIS': False,
    }
}
# Apply the ENV_CONFIG specific settings
CONFIG = ENV_CONFIG.get(ENV, {})
LOG_LEVEL = CONFIG.get('LOG_LEVEL', 'DEBUG')
AUTO_CLEANUP = CONFIG.get('AUTO_CLEANUP', False)
MOCK_MODE = CONFIG.get('MOCK_MODE', True)
ENABLE_REAL_APIS = CONFIG.get('ENABLE_REAL_APIS', not MOCK_MODE)

# Model Configuration - Change this to switch AI models (Rule 1.1)
MODEL = "gpt-4"  # Primary model: "gpt-4", "grok-4", "memories-ai", "mock"
MODEL_BACKUP = "gpt-3.5-turbo"  # Fallback model for retries
MODEL_TEMPERATURE = 0.7  # Model creativity (0.0-1.0)
MODEL_MAX_TOKENS = 2000  # Maximum response tokens

# API Configuration - All keys loaded from environment variables for security
API_KEYS = {
    "grok": os.getenv('GROK_API_KEY', ''),  # Grok API key from environment
    "openai": os.getenv('OPENAI_API_KEY', ''),  # OpenAI API key from environment
    "anthropic": os.getenv('ANTHROPIC_API_KEY', ''),  # Anthropic API key from environment
    "memories": os.getenv('MEMORIES_AI_KEY', ''),  # Memories.ai API key from environment
}

# GameSDK Configuration
GAME_API_KEY = API_KEYS.get('openai', '')  # Use OpenAI key for GameSDK for now

# Model Endpoints
ENDPOINTS = {
    "grok-4": "https://api.x.ai/v1/chat/completions",
    "openai": "https://api.openai.com/v1/chat/completions",
    "anthropic": "https://api.anthropic.com/v1/messages",
}

# Workflow Parameters
MAX_SCENES = 20  # Limit scenes for efficiency
MAX_CLIP_DURATION = 120  # Max clip duration in seconds (2 minutes)
MAX_NARRATION_WORDS = 400  # Longer narration for longer clips
MAX_BGM_OPTIONS = 3  # Limit BGM suggestions

# Input Limits
MAX_SCRIPT_WORDS = 10000  # Max script size for scalability

# Video Processing Settings
VIDEO_MAX_DURATION = 4000  # Increased to handle longer videos
CLIP_MIN_DURATION = 5  # Seconds
VIDEO_OUTPUT_DIR = "C:\\Users\\dimit\\Videos\\anime"  # Directory for generated video clips
FINAL_VIDEO_OUTPUT_DIR = "C:\\Users\\dimit\\Videos\\anime"  # Directory for final assembled videos

# Scene Detection Settings (Phase 1: Rule 1.1)
USE_REAL_DETECTION = True  # Enable real detection for Phase 1.1 testing
SCENE_DETECTION_THRESHOLD = 12.0  # Content change threshold for PySceneDetect (lower = fewer scenes)
MIN_SCENE_DURATION = 15.0  # Minimum scene length in seconds (increased for better quality)
MAX_SCENES_PER_VIDEO = 20  # Limit for performance
COVERAGE_REQUIREMENT = 0.3  # 30% video coverage minimum (Rule 1.1) - Lowered for testing
SCENE_SCORE_THRESHOLD = 0.0  # Minimum score for clip selection (Rule 3.2) - Set to 0 for testing
MAX_CLIPS = 20  # Maximum number of clips to extract - Increased for 20-minute video

# System Settings
FAMILY_FRIENDLY = True  # Enable content filtering

# Phase-specific Configuration (Rule Development Plan)
# Phase 2: Core Utilities
API_TIMEOUT = 30  # Seconds for API calls
API_RETRY_COUNT = 3  # Number of retries for failed API calls

# Phase 3: Worker Configuration
WORKER_TIMEOUT = 300  # Seconds for worker execution
CLIP_DIVERSITY_THRESHOLD = 0.8  # Minimum diversity score for clip selection
ASSEMBLY_VALIDATION = True  # Validate assembly results

# Phase 4: Integration Settings
COVERAGE_RETRY_LIMIT = 3  # Retry attempts if coverage < 80%
API_RATE_LIMIT = 100  # Requests per minute

# Phase 1 Rules: Audio Preservation and Feature Control
# Rule 1.1: Audio Preservation Priority
PRESERVE_ORIGINAL_AUDIO = True  # Default: preserve original audio during extraction/assembly

# Rule 1.2: Hold Narration/BGM - Enabled for testing
ENABLE_NARRATION = True  # Enable narration worker for content-specific testing
ENABLE_BGM = True  # Enable BGM worker for full audio mix testing

# Rule 1.3: Editing Flexibility - Support user prompts
ENABLE_CUSTOM_PROMPTS = True  # Allow user prompts for clip selection
DEFAULT_SELECTION_PROMPT = "Select the most visually interesting and important scenes"  # Fallback prompt

# Phase 5: Cleanup and Testing
TEMP_DIR = "temp"  # Directory for temporary files
KEEP_INTERMEDIATE_FILES = DEBUG  # Keep intermediate files for debugging

# File Paths and Extensions
SUPPORTED_VIDEO_FORMATS = ['.mp4', '.avi', '.mov', '.mkv']
SUPPORTED_AUDIO_FORMATS = ['.mp3', '.wav', '.aac']
OUTPUT_VIDEO_FORMAT = '.mp4'
OUTPUT_AUDIO_FORMAT = '.mp3'

# Performance Settings
MAX_CONCURRENT_WORKERS = 4  # Maximum parallel worker processes
CHUNK_SIZE = 1024 * 1024  # 1MB chunks for file processing
MEMORY_LIMIT = 2 * 1024 * 1024 * 1024  # 2GB memory limit

# Enhanced Config Options (Phase 1 - Improved Rule Plan)
# Advanced editing features
ENABLE_PROMPT_EDITING = True
PROMPT_REQUIRED = False

# Performance optimization
VIDEO_CHUNK_SIZE = 300  # seconds
ENABLE_PARALLEL_PROCESSING = True
WORKER_TIMEOUT = 120  # seconds
ENABLE_FFMPEG = False  # FFmpeg integration for faster processing

# Phase 1 Rule 1.1: Enhanced Real Detection
ADAPTIVE_MIN_SCENE_LEN = True  # Enable adaptive scene length calculation
SCENE_VARIETY_THRESHOLD = 0.6  # Threshold for scene variety scoring
ENHANCED_SCENE_SCORING = True  # Enable multi-factor scene scoring

# Memories.ai integration (Phase 6)
# Note: Use MEMORIES_AI_KEY to align with Rule 6.1 and .env guidance
MEMORIES_AI_KEY = os.getenv("MEMORIES_AI_KEY", os.getenv("MEMORIES_AI_API_KEY", ""))
MEMORIES_AI_BASE_URL = os.getenv("MEMORIES_AI_BASE_URL", "https://api.memories.ai/v1")
# Feature flags
USE_REAL_AI = os.getenv("USE_REAL_AI", "false").lower() == "true"  # Default False during dev per Rule 6.1
ENABLE_MEMORIES_AI = os.getenv("ENABLE_MEMORIES_AI", "true").lower() == "true"
memories_available = bool(MEMORIES_AI_KEY)  # Flag for API availability

# Motion analysis
ENABLE_MOTION_DETECTION = False  # Disable motion detection to avoid type errors
MOTION_THRESHOLD = 0.3

# Phase 2: Enhanced Motion Detection Configuration
MOTION_DETECTION_THRESHOLD = 16  # Background subtractor variance threshold
MOTION_DIFF_THRESHOLD = 25       # Frame difference threshold for basic motion
MAX_MOTION_FRAMES = 50           # Maximum frames to analyze per scene
MIN_CLIP_DURATION = 2.0          # Minimum clip duration for trimming
TARGET_VIDEO_DURATION = 1200     # Target duration for trimming (20 minutes)

# Audio preservation (enhanced)
AUDIO_CODEC = "aac"
AUDIO_BITRATE = "128k"

# Validation Rules
MIN_VIDEO_DURATION = 10  # Minimum video duration in seconds
MAX_VIDEO_SIZE = 500 * 1024 * 1024  # 500MB maximum video size
MIN_COVERAGE_PERCENTAGE = 80  # Minimum coverage percentage for success

# Phase 1: Session Management and Security (Rule 1.1, 1.3)
MAX_EDITS = 20  # Maximum edits per session
SESSION_TIMEOUT = 1800  # Session timeout in seconds (30 minutes)
MAX_SESSIONS = 100  # Maximum concurrent sessions
UPLOAD_DIR = "temp"  # Directory for uploaded files
PREVIEW_DIR = "previews"  # Directory for preview files

# WebSocket Configuration
WS_HEARTBEAT_INTERVAL = 30  # WebSocket heartbeat interval in seconds
WS_MAX_MESSAGE_SIZE = 1024 * 1024  # 1MB max message size

# Security Settings
ALLOWED_UPLOAD_EXTENSIONS = [".mp4", ".avi", ".mov", ".mkv"]  # Only video files
MAX_FILENAME_LENGTH = 255
SANITIZE_FILENAMES = True

# Rate Limiting
CHAT_RATE_LIMIT = 10  # Messages per minute per session
UPLOAD_RATE_LIMIT = 5  # Uploads per hour per IP

# Large file configuration
LARGE_FILE_THRESHOLD = 50 * 1024 * 1024  # Treat files larger than 50MB as large for Range requests.

# Redis Configuration (Rule 1.4: Scalability Edges Setup)
REDIS_HOST = os.getenv('REDIS_HOST', 'localhost')
REDIS_PORT = int(os.getenv('REDIS_PORT', '6379'))
REDIS_DB = int(os.getenv('REDIS_DB', '0'))
REDIS_PASSWORD = os.getenv('REDIS_PASSWORD', None)
USE_REDIS = os.getenv('USE_REDIS', 'false').lower() == 'true'
REDIS_SESSION_TTL = 3600  # 1 hour TTL for Redis sessions

# WebSocket Authentication (Rule 1.4)
WS_TOKEN_VALIDATION = os.getenv('WS_TOKEN_VALIDATION', 'simple')  # 'simple', 'jwt', or 'disabled'
WS_SECRET_KEY = os.getenv('WS_SECRET_KEY', 'dev_secret_key_change_in_production')
WS_DEFAULT_TOKEN = 'dev_token'  # Default token for development

# Frontend Integration Settings (Phase 1)
FRONTEND_ORIGIN = os.getenv('FRONTEND_ORIGIN', 'http://localhost:3000')
API_BASE_URL = os.getenv('API_BASE_URL', 'http://localhost:8000')
WS_BASE_URL = os.getenv('WS_BASE_URL', 'ws://localhost:8000')

# JWT Authentication (Phase 6 Rule 6.2)
JWT_SECRET = os.getenv('JWT_SECRET', 'dev_jwt_secret_change_in_production')
JWT_ALGORITHM = 'HS256'
ACCESS_TOKEN_EXPIRES_SECONDS = int(os.getenv('ACCESS_TOKEN_EXPIRES_SECONDS', '3600'))  # 1 hour
REFRESH_TOKEN_EXPIRES_SECONDS = int(os.getenv('REFRESH_TOKEN_EXPIRES_SECONDS', '604800'))  # 7 days
