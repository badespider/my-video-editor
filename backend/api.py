"""
FastAPI backend for multi-agent AI video creation system.
Provides REST API endpoints for frontend integration.
"""

from fastapi import FastAPI, HTTPException, UploadFile, File, WebSocket, WebSocketDisconnect, Header, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, StreamingResponse
from pydantic import BaseModel
from contextlib import asynccontextmanager
import sys
import os
import tempfile
import shutil
import json
import uuid
import time
import asyncio
import logging
from typing import Optional, Dict, List, Any
from backend.session_manager import SessionManager
from backend.workflow_orchestrator import WorkflowOrchestrator

# Initialize session manager and workflow orchestrator
session_manager = SessionManager()
workflow_orchestrator = WorkflowOrchestrator(session_manager)
from pathlib import Path

logger = logging.getLogger(__name__)

# Add parent directory to path to import project modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from coordinator import VideoAgent
import config
from utils.utils import call_memories_placeholder, trim_video, apply_edit_commands, generate_video_thumbnail, suggest_video_edits, analyze_video_content, generate_optimization_recommendations

# Auth
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import jwt
from datetime import datetime, timedelta

# Phase 1: Session Management (Rule 1.1)
# Initialize FastAPI app with lifespan context

# Define lifespan context
@asynccontextmanager
async def lifespan_context(app: FastAPI):
    # Start cleanup task on startup
    await session_manager.start()
    yield
    # Cleanup on shutdown
    await session_manager.stop()
app = FastAPI(title="AI Video Creation API", lifespan=lifespan_context)

security = HTTPBearer(auto_error=False)

# Mock users for dev (can be moved to config if needed)
MOCK_USERS = {
    "admin": {"password": "admin", "role": "admin"},
    "user": {"password": "user", "role": "user"},
}


def generate_jwt(user_id: str, role: str = "user", expires_in: int = None) -> str:
    exp_seconds = expires_in or getattr(config, 'ACCESS_TOKEN_EXPIRES_SECONDS', 3600)
    payload = {
        "sub": user_id,
        "role": role,
        "exp": datetime.utcnow() + timedelta(seconds=exp_seconds),
        "iat": datetime.utcnow(),
        "nbf": datetime.utcnow(),
    }
    return jwt.encode(payload, getattr(config, 'JWT_SECRET', 'dev'), algorithm=getattr(config, 'JWT_ALGORITHM', 'HS256'))


def decode_jwt(token: str) -> dict:
    return jwt.decode(token, getattr(config, 'JWT_SECRET', 'dev'), algorithms=[getattr(config, 'JWT_ALGORITHM', 'HS256')])


async def get_current_user(request: Request, credentials: HTTPAuthorizationCredentials = None):
    # Only enforce auth when configured
    if getattr(config, 'WS_TOKEN_VALIDATION', 'simple') != 'jwt':
        return {"user_id": "guest", "role": "user"}
    if not credentials:
        raise HTTPException(status_code=401, detail="Authorization required")
    try:
        token = credentials.credentials
        data = decode_jwt(token)
        request.state.user_id = data.get("sub", "guest")
        request.state.role = data.get("role", "user")
        return {"user_id": request.state.user_id, "role": request.state.role}
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid token")

# Configure CORS for frontend integration (Phase 1: Rule 1.1)
FRONTEND_ORIGIN = os.getenv('FRONTEND_ORIGIN', 'http://localhost:3000')

# Backend-only CORS configuration (frontend disconnected)
allowed_origins = [
    "http://localhost:8000",  # Backend itself for testing
    "http://127.0.0.1:8000",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Use session_manager for session handling and cleanup

def sanitize_filename(filename: str) -> str:
    """Sanitize uploaded filename for security."""
    # Remove path components and limit length
    filename = os.path.basename(filename)[:config.MAX_FILENAME_LENGTH]
    
    if config.SANITIZE_FILENAMES:
        # Remove potentially dangerous characters
        import re
        filename = re.sub(r'[^\w\-_\.]', '_', filename)
    
    return filename

def validate_upload(file: UploadFile) -> bool:
    """Validate uploaded file meets security requirements."""
    # Check file extension
    if file.filename:
        ext = Path(file.filename).suffix.lower()
        if ext not in config.ALLOWED_UPLOAD_EXTENSIONS:
            return False
    
    # Additional size/type checks could be added here
    return True


class ScriptRequest(BaseModel):
    """Request model for script processing."""
    script: str
    model: Optional[str] = None


class VideoProcessRequest(BaseModel):
    """Request model for video processing."""
    video_path: str
    model: Optional[str] = None


class VideoResponse(BaseModel):
    """Response model for video plan."""
    clips: dict
    narrations: dict
    bgms: dict
    timeline: list
    total_duration: float
    assembly_metadata: dict


class VideoProcessResponse(BaseModel):
    """Response model for video processing result."""
    final_video: str
    plan: str
    source_video: str
    processing_type: str
    coverage_percentage: Optional[float] = None
    scene_count: Optional[int] = None


class TrimRequest(BaseModel):
    """Request model for video trimming."""
    start_time: float
    end_time: float
    preview_only: Optional[bool] = True  # Generate preview by default
    quality: Optional[str] = "medium"  # low, medium, high


class PreviewRequest(BaseModel):
    """Request model for preview generation."""
    edits: Optional[List[dict]] = []
    quality: Optional[str] = "low"  # Faster preview generation
    duration_limit: Optional[int] = 30  # Limit preview to 30s by default


class EditRequest(BaseModel):
    """Enhanced edit request with preview options."""
    command: str
    parameters: dict
    preview_only: Optional[bool] = True
    auto_save: Optional[bool] = False


class EditCommandRequest(BaseModel):
    """Request model for applying edit commands."""
    edits: List[dict]


class ThumbnailRequest(BaseModel):
    """Request model for thumbnail generation."""
    time: str


class AIAnalysisRequest(BaseModel):
    """Request model for AI video analysis."""
    detailed: Optional[bool] = True
    preferences: Optional[Dict] = None


class AISuggestionsRequest(BaseModel):
    """Request model for AI editing suggestions."""
    preferences: Optional[Dict] = None
    max_suggestions: Optional[int] = 10


class OptimizationRequest(BaseModel):
    """Request model for optimization recommendations."""
    target_platform: Optional[str] = None
    quality_level: Optional[str] = "medium"


class WorkflowStartRequest(BaseModel):
    """Request model for starting E2E workflow (Rule 4.2)."""
    workflow_config: Optional[Dict[str, Any]] = None
    user_preferences: Optional[Dict[str, Any]] = None
    auto_start: Optional[bool] = True


@app.get("/")
async def root():
    """Root endpoint."""
    return {"message": "AI Video Creation API"}


# Auth endpoints (Rule 6.2)
class LoginRequest(BaseModel):
    username: str
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


@app.post("/auth/login", response_model=TokenResponse)
async def login(req: LoginRequest):
    user = MOCK_USERS.get(req.username)
    if not user or user.get("password") != req.password:
        raise HTTPException(status_code=401, detail="Invalid credentials")
    token = generate_jwt(user_id=req.username, role=user.get("role", "user"))
    return {"access_token": token, "token_type": "bearer"}


class RefreshRequest(BaseModel):
    token: str


@app.post("/auth/refresh", response_model=TokenResponse)
async def refresh(req: RefreshRequest):
    # Basic refresh: validate old token, issue new one with fresh expiry
    try:
        data = decode_jwt(req.token)
        new_token = generate_jwt(user_id=data.get("sub", "user"), role=data.get("role", "user"))
        return {"access_token": new_token, "token_type": "bearer"}
    except jwt.ExpiredSignatureError:
        # Even if expired, we can extract without verifying exp by options
        try:
            data = jwt.decode(req.token, getattr(config, 'JWT_SECRET', 'dev'), algorithms=[getattr(config, 'JWT_ALGORITHM', 'HS256')], options={"verify_exp": False})
            new_token = generate_jwt(user_id=data.get("sub", "user"), role=data.get("role", "user"))
            return {"access_token": new_token, "token_type": "bearer"}
        except Exception:
            raise HTTPException(status_code=401, detail="Invalid token")
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid token")


@app.post("/upload/video")
async def upload_video(file: UploadFile = File(...)):
    """Upload video file and create a new editing session."""
    try:
        # Check if file is provided
        if not file or not file.filename:
            raise HTTPException(status_code=400, detail="No file provided")
        
        # Validate file type first
        if not validate_upload(file):
            raise HTTPException(status_code=400, detail="Invalid file type or upload failed validation")
        
        # Read file content to check if empty
        content = await file.read()
        if len(content) == 0:
            raise HTTPException(status_code=400, detail="Empty file uploaded")
        
        # Create new session
        sanitized_filename = sanitize_filename(file.filename)
        file_size = len(content)
        session_id = await session_manager.create_session(sanitized_filename, file_size)
        
        # Build file path
        file_path = os.path.join(config.UPLOAD_DIR, f"{session_id}_{sanitized_filename}")

        # Ensure upload directory exists
        os.makedirs(config.UPLOAD_DIR, exist_ok=True)
        
        # Save uploaded file
        with open(file_path, "wb") as f:
            f.write(content)
        
        # Update session with file info
        await session_manager.update_session(session_id, video_path=file_path, preview_path=file_path)
        
        # Generate session token for WebSocket authentication (Phase 1: Rule 1.3)
        import secrets
        session_token = secrets.token_urlsafe(32)
        
        # Store token in session (in a real app, you'd use a proper session store)
        # For now, we'll add it to the session manager
        await session_manager.update_session(session_id, ws_token=session_token)
        
        logger.info(f"Video uploaded: {file_path} for session {session_id}")
        return {
            "session_id": session_id, 
            "filename": sanitized_filename,
            "ws_token": session_token
        }
        
    except HTTPException:
        raise
    except ValueError as e:
        raise HTTPException(status_code=429, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.websocket("/ws/edit/{session_id}")
async def websocket_endpoint(websocket: WebSocket, session_id: str, token: str = None):
    """Enhanced WebSocket endpoint for chat-based video editing with token authentication (Rule 3.1)."""
    
    # Step 1: Authenticate connection
    session = await session_manager.get_session(session_id)
    if not session:
        await websocket.close(code=4004, reason="Session not found")
        logger.error(f"Session {session_id} not found")
        return
    
    # Validate WebSocket token if provided
    if token and not session.is_ws_token_valid(token):
        await websocket.close(code=4001, reason="Invalid or expired token")
        logger.error(f"Invalid WebSocket token for session {session_id}")
        return
    
    await websocket.accept()
    await session_manager.register_websocket(session_id, websocket)
    
    # Send initial connection confirmation
    await websocket.send_text(json.dumps({
        "type": "connection_established",
        "session_id": session_id,
        "message": "Connected to editing session",
        "session_info": {
            "filename": session.filename,
            "edits_count": len(session.edits or []),
            "finalized": session.finalized,
            "has_preview": bool(session.preview_path)
        }
    }))
    
    agent = VideoAgent()
    logger.info(f"WebSocket connection established for session {session_id}")

    try:
        while True:
            data = await websocket.receive_text()
            
            # Update session activity
            session.update_activity()
            await session_manager.update_session(session_id, edits=session.edits)
            
            try:
                # Parse incoming message
                try:
                    message = json.loads(data)
                except json.JSONDecodeError:
                    await _send_error_response(websocket, "Invalid JSON format", "Message must be valid JSON", data)
                    continue
                
                # Validate message structure
                if not isinstance(message, dict):
                    await _send_error_response(websocket, "Invalid message structure", "Message must be a JSON object", data)
                    continue
                
                message_type = message.get("type", "unknown")
                logger.info(f"Processing WebSocket message type: {message_type}")
                
                # Handle different message types
                if message_type == "ping":
                    await _handle_ping(websocket, message)
                    
                elif message_type == "chat_command":
                    await _handle_chat_command(websocket, session, agent, message, session_id)
                    
                elif message_type == "structured_command":
                    await _handle_structured_command(websocket, session, agent, message, session_id)
                    
                elif message_type == "get_session_status":
                    await _handle_session_status(websocket, session, session_id)
                    
                elif message_type == "undo_last_edit":
                    await _handle_undo_command(websocket, session, session_id)
                    
                elif message_type == "get_ai_suggestions":
                    await _handle_ai_suggestions(websocket, session, message, session_id)
                    
                elif message_type == "apply_ai_suggestion":
                    await _handle_apply_ai_suggestion(websocket, session, agent, message, session_id)
                    
                elif message_type == "analyze_video":
                    await _handle_video_analysis(websocket, session, message, session_id)
                    
                elif message_type == "get_optimization_tips":
                    await _handle_optimization_tips(websocket, session, message, session_id)
                    
                else:
                    # Fallback: try to parse as legacy format
                    if "command" in message:
                        await _handle_legacy_command(websocket, session, agent, message, session_id)
                    else:
                        await _send_error_response(websocket, "Unknown message type", f"Message type '{message_type}' is not supported")
                    
            except Exception as cmd_error:
                logger.error(f"Error processing WebSocket message: {cmd_error}")
                await _send_error_response(websocket, "Command processing failed", str(cmd_error), data)

    except WebSocketDisconnect:
        logger.info(f"Client disconnected from session {session_id}")
    except Exception as e:
        logger.error(f"WebSocket error for session {session_id}: {e}")
    finally:
        await session_manager.unregister_websocket(session_id)


# WebSocket message handlers
async def _send_error_response(websocket: WebSocket, error_type: str, message: str, input_data: str = None):
    """Send structured error response via WebSocket."""
    error_response = {
        "type": "error",
        "error_type": error_type,
        "message": message,
        "timestamp": time.time()
    }
    if input_data:
        error_response["input"] = input_data
    
    await websocket.send_text(json.dumps(error_response))


async def _send_success_response(websocket: WebSocket, response_type: str, data: dict, session_id: str):
    """Send structured success response via WebSocket."""
    response = {
        "type": response_type,
        "status": "success",
        "session_id": session_id,
        "timestamp": time.time(),
        **data
    }
    await websocket.send_text(json.dumps(response))


async def _handle_ping(websocket: WebSocket, message: dict):
    """Handle ping messages for connection keepalive."""
    pong_response = {
        "type": "pong",
        "timestamp": time.time(),
        "echo": message.get("data")
    }
    await websocket.send_text(json.dumps(pong_response))


async def _handle_chat_command(websocket: WebSocket, session, agent: VideoAgent, message: dict, session_id: str):
    """Handle natural language chat commands."""
    chat_text = message.get("text", "")
    if not chat_text.strip():
        await _send_error_response(websocket, "Empty command", "Chat command text cannot be empty")
        return
    
    # Send processing acknowledgment
    await websocket.send_text(json.dumps({
        "type": "processing",
        "message": "Processing your request...",
        "command_text": chat_text
    }))
    
    try:
        # Parse natural language command
        parsed_command = agent.parse_command(chat_text)
        
        # Apply the command to the session
        session_dict = session.to_dict()
        agent.apply_command(session_dict, parsed_command)
        
        # Update session with new edits
        if 'edits' in session_dict:
            session.edits = session_dict['edits']
            await session_manager.update_session(session_id, edits=session.edits)
        
        # Send success response with details
        await _send_success_response(websocket, "command_completed", {
            "message": f"Successfully applied: {chat_text}",
            "parsed_command": parsed_command,
            "preview_url": f"/preview/{session_id}",
            "edits_count": len(session.edits or []),
            "latest_edit": session.edits[-1] if session.edits else None
        }, session_id)
        
    except Exception as e:
        await _send_error_response(websocket, "Command parsing failed", f"Could not process command: {str(e)}", chat_text)


async def _handle_structured_command(websocket: WebSocket, session, agent: VideoAgent, message: dict, session_id: str):
    """Handle structured commands with predefined parameters."""
    command_data = message.get("command")
    if not command_data or not isinstance(command_data, dict):
        await _send_error_response(websocket, "Invalid command structure", "Command data must be a valid object")
        return
    
    command_type = command_data.get("type", command_data.get("command"))
    parameters = command_data.get("parameters", command_data.get("params", {}))
    
    # Send processing acknowledgment
    await websocket.send_text(json.dumps({
        "type": "processing",
        "message": f"Applying {command_type} command...",
        "command_type": command_type
    }))
    
    try:
        # Structure command for VideoAgent
        structured_command = {
            "command": command_type,
            "parameters": parameters
        }
        
        # Apply the command to the session
        session_dict = session.to_dict()
        agent.apply_command(session_dict, structured_command)
        
        # Update session with new edits
        if 'edits' in session_dict:
            session.edits = session_dict['edits']
            await session_manager.update_session(session_id, edits=session.edits)
        
        # Send success response
        await _send_success_response(websocket, "command_completed", {
            "message": f"Successfully applied {command_type} command",
            "command": structured_command,
            "preview_url": f"/preview/{session_id}",
            "edits_count": len(session.edits or []),
            "latest_edit": session.edits[-1] if session.edits else None
        }, session_id)
        
    except Exception as e:
        await _send_error_response(websocket, "Command execution failed", f"Failed to apply {command_type}: {str(e)}")


async def _handle_session_status(websocket: WebSocket, session, session_id: str):
    """Handle session status requests."""
    status_data = {
        "session_id": session_id,
        "filename": session.filename,
        "file_size": session.file_size,
        "video_duration": session.video_duration,
        "edits_count": len(session.edits or []),
        "finalized": session.finalized,
        "last_activity": session.last_activity,
        "created_at": session.created_at,
        "has_preview": bool(session.preview_path),
        "has_analysis": bool(session.analysis),
        "edits_history": session.edits or []
    }
    
    await _send_success_response(websocket, "session_status", status_data, session_id)


async def _handle_undo_command(websocket: WebSocket, session, session_id: str):
    """Handle undo last edit command."""
    if not session.edits:
        await _send_error_response(websocket, "No edits to undo", "There are no edits in the current session to undo")
        return
    
    # Remove the last edit
    undone_edit = session.edits.pop()
    await session_manager.update_session(session_id, edits=session.edits)
    
    await _send_success_response(websocket, "undo_completed", {
        "message": "Successfully undid last edit",
        "undone_edit": undone_edit,
        "remaining_edits_count": len(session.edits),
        "preview_url": f"/preview/{session_id}"
    }, session_id)


async def _handle_legacy_command(websocket: WebSocket, session, agent: VideoAgent, message: dict, session_id: str):
    """Handle legacy command format for backward compatibility."""
    command_type = message.get("command")
    
    # Send processing acknowledgment
    await websocket.send_text(json.dumps({
        "type": "processing",
        "message": f"Processing legacy command: {command_type}"
    }))
    
    try:
        # Apply the command to the session
        session_dict = session.to_dict()
        agent.apply_command(session_dict, message)
        
        # Update session with new edits
        if 'edits' in session_dict:
            session.edits = session_dict['edits']
            await session_manager.update_session(session_id, edits=session.edits)
        
        # Send success response in legacy format
        legacy_response = {
            "type": "legacy_command_completed",
            "status": "success",
            "command": message,
            "preview_url": f"/preview/{session_id}",
            "edits_count": len(session.edits or [])
        }
        await websocket.send_text(json.dumps(legacy_response))
        
    except Exception as e:
        await _send_error_response(websocket, "Legacy command failed", f"Failed to process legacy command: {str(e)}")


# AI Suggestions WebSocket Handlers (Rule 3.2)
async def _handle_ai_suggestions(websocket: WebSocket, session, message: dict, session_id: str):
    """Handle AI suggestions request via WebSocket (Rule 3.2)."""
    # Send processing acknowledgment
    await websocket.send_text(json.dumps({
        "type": "processing",
        "message": "Generating AI suggestions for your video..."
    }))
    
    try:
        video_path = session.preview_path or session.video_path
        if not video_path or not os.path.exists(video_path):
            await _send_error_response(websocket, "Video not found", "No video available for AI analysis")
            return
        
        # Extract preferences from message
        preferences = message.get("preferences", {})
        max_suggestions = message.get("max_suggestions", 5)
        detailed_analysis = message.get("detailed_analysis", True)
        
        # Get or generate video analysis
        analysis = session.analysis
        if not analysis or detailed_analysis:
            analysis = await _get_video_analysis(video_path, detailed=detailed_analysis)
            session.analysis = analysis
            await session_manager.update_session(session_id, analysis=analysis)
        
        # Generate AI suggestions based on analysis
        suggestions = suggest_video_edits(
            video_path=video_path,
            analysis=analysis,
            preferences=preferences,
            max_suggestions=max_suggestions
        )
        
        # Store suggestions in session for future reference
        session.suggestions = suggestions
        await session_manager.update_session(session_id, suggestions=suggestions)
        
        # Send success response with suggestions
        await _send_success_response(websocket, "ai_suggestions_generated", {
            "message": f"Generated {len(suggestions.get('suggestions', []))} AI suggestions",
            "suggestions": suggestions,
            "analysis_used": bool(analysis),
            "preferences_applied": preferences,
            "total_suggestions": len(suggestions.get('suggestions', [])),
            "categories": list(suggestions.get('categories', {}).keys()) if 'categories' in suggestions else []
        }, session_id)
        
    except Exception as e:
        logger.error(f"AI suggestions generation failed: {e}")
        await _send_error_response(websocket, "AI suggestions failed", f"Could not generate suggestions: {str(e)}")


async def _handle_apply_ai_suggestion(websocket: WebSocket, session, agent: VideoAgent, message: dict, session_id: str):
    """Handle applying a specific AI suggestion via WebSocket (Rule 3.2)."""
    suggestion_id = message.get("suggestion_id")
    suggestion_data = message.get("suggestion")
    
    if not suggestion_id and not suggestion_data:
        await _send_error_response(websocket, "Invalid suggestion", "Either suggestion_id or suggestion data must be provided")
        return
    
    # Send processing acknowledgment
    await websocket.send_text(json.dumps({
        "type": "processing",
        "message": f"Applying AI suggestion: {suggestion_id or 'custom'}..."
    }))
    
    try:
        # Find suggestion in session if ID provided
        if suggestion_id and hasattr(session, 'suggestions') and session.suggestions:
            suggestions_list = session.suggestions.get('suggestions', [])
            suggestion_data = None
            
            for suggestion in suggestions_list:
                if suggestion.get('id') == suggestion_id:
                    suggestion_data = suggestion
                    break
            
            if not suggestion_data:
                await _send_error_response(websocket, "Suggestion not found", f"No suggestion found with ID: {suggestion_id}")
                return
        
        if not suggestion_data:
            await _send_error_response(websocket, "No suggestion data", "Could not find or parse suggestion data")
            return
        
        # Convert AI suggestion to command format
        command = await _convert_suggestion_to_command(suggestion_data)
        
        # Apply the command using VideoAgent
        session_dict = session.to_dict()
        agent.apply_command(session_dict, command)
        
        # Update session with new edits
        if 'edits' in session_dict:
            session.edits = session_dict['edits']
            await session_manager.update_session(session_id, edits=session.edits)
        
        # Send success response
        await _send_success_response(websocket, "ai_suggestion_applied", {
            "message": f"Successfully applied AI suggestion: {suggestion_data.get('title', 'Untitled')}",
            "suggestion_applied": suggestion_data,
            "converted_command": command,
            "preview_url": f"/preview/{session_id}",
            "edits_count": len(session.edits or []),
            "latest_edit": session.edits[-1] if session.edits else None
        }, session_id)
        
    except Exception as e:
        logger.error(f"Failed to apply AI suggestion: {e}")
        await _send_error_response(websocket, "Suggestion application failed", f"Could not apply suggestion: {str(e)}")


async def _handle_video_analysis(websocket: WebSocket, session, message: dict, session_id: str):
    """Handle video analysis request via WebSocket (Rule 3.2)."""
    # Send processing acknowledgment
    await websocket.send_text(json.dumps({
        "type": "processing",
        "message": "Analyzing your video content..."
    }))
    
    try:
        video_path = session.preview_path or session.video_path
        if not video_path or not os.path.exists(video_path):
            await _send_error_response(websocket, "Video not found", "No video available for analysis")
            return
        
        detailed = message.get("detailed", True)
        preferences = message.get("preferences", {})
        
        # Perform video analysis using Memories.ai placeholder
        analysis = await _get_video_analysis(video_path, detailed=detailed, preferences=preferences)
        
        # Store analysis in session
        session.analysis = analysis
        await session_manager.update_session(session_id, analysis=analysis)
        
        # Send analysis results
        await _send_success_response(websocket, "video_analysis_completed", {
            "message": "Video analysis completed successfully",
            "analysis": analysis,
            "detailed": detailed,
            "analysis_timestamp": time.time(),
            "video_insights": {
                "duration": analysis.get('duration', 0),
                "scenes_detected": len(analysis.get('scenes', [])),
                "quality_score": analysis.get('quality_score', 0),
                "content_tags": analysis.get('content_tags', [])
            }
        }, session_id)
        
    except Exception as e:
        logger.error(f"Video analysis failed: {e}")
        await _send_error_response(websocket, "Analysis failed", f"Could not analyze video: {str(e)}")


async def _handle_optimization_tips(websocket: WebSocket, session, message: dict, session_id: str):
    """Handle optimization tips request via WebSocket (Rule 3.2)."""
    # Send processing acknowledgment
    await websocket.send_text(json.dumps({
        "type": "processing",
        "message": "Generating optimization recommendations..."
    }))
    
    try:
        video_path = session.preview_path or session.video_path
        if not video_path or not os.path.exists(video_path):
            await _send_error_response(websocket, "Video not found", "No video available for optimization analysis")
            return
        
        target_platform = message.get("target_platform", "general")
        quality_level = message.get("quality_level", "medium")
        
        # Get existing analysis or generate basic one
        analysis = session.analysis
        if not analysis:
            analysis = await _get_video_analysis(video_path, detailed=False)
            session.analysis = analysis
            await session_manager.update_session(session_id, analysis=analysis)
        
        # Generate optimization recommendations
        recommendations = generate_optimization_recommendations(
            video_path=video_path,
            analysis=analysis,
            target_platform=target_platform,
            quality_level=quality_level
        )
        
        # Store recommendations in session
        session.optimization_recommendations = recommendations
        await session_manager.update_session(session_id, optimization_recommendations=recommendations)
        
        # Send optimization tips
        await _send_success_response(websocket, "optimization_tips_generated", {
            "message": f"Generated {len(recommendations.get('recommendations', []))} optimization tips",
            "recommendations": recommendations,
            "target_platform": target_platform,
            "quality_level": quality_level,
            "tips_count": len(recommendations.get('recommendations', [])),
            "categories": list(recommendations.get('categories', {}).keys()) if 'categories' in recommendations else []
        }, session_id)
        
    except Exception as e:
        logger.error(f"Optimization tips generation failed: {e}")
        await _send_error_response(websocket, "Optimization failed", f"Could not generate optimization tips: {str(e)}")


# Helper functions for AI processing
async def _get_video_analysis(video_path: str, detailed: bool = True, preferences: dict = None) -> dict:
    """Get video analysis using Memories.ai placeholder (Rule 1.2)."""
    try:
        # Use the existing call_memories_placeholder function
        analysis = call_memories_placeholder(
            video_path,
            detailed=detailed,
            preferences=preferences or {}
        )
        return analysis
    except Exception as e:
        logger.error(f"Video analysis failed: {e}")
        # Return basic analysis structure if Memories.ai fails
        return {
            "duration": 0,
            "scenes": [],
            "quality_score": 0.5,
            "content_tags": [],
            "error": str(e),
            "fallback": True
        }


async def _convert_suggestion_to_command(suggestion_data: dict) -> dict:
    """Convert AI suggestion format to VideoAgent command format."""
    suggestion_type = suggestion_data.get('type', 'unknown')
    parameters = suggestion_data.get('parameters', {})
    
    # Map suggestion types to command formats
    command_mapping = {
        'trim': {
            'command': 'trim',
            'parameters': {
                'start_time': parameters.get('start', 0),
                'end_time': parameters.get('end', 30)
            }
        },
        'volume_adjust': {
            'command': 'adjust_volume',
            'parameters': {
                'volume_factor': parameters.get('factor', 1.0)
            }
        },
        'add_text': {
            'command': 'add_text',
            'parameters': {
                'text': parameters.get('text', ''),
                'start_time': parameters.get('start_time', 0),
                'duration': parameters.get('duration', 5),
                'position': parameters.get('position', 'center')
            }
        },
        'crop': {
            'command': 'crop',
            'parameters': {
                'x': parameters.get('x', 0),
                'y': parameters.get('y', 0),
                'width': parameters.get('width', 1920),
                'height': parameters.get('height', 1080)
            }
        },
        'rotate': {
            'command': 'rotate',
            'parameters': {
                'angle': parameters.get('angle', 90)
            }
        },
        'speed_change': {
            'command': 'speed_change',
            'parameters': {
                'speed_factor': parameters.get('factor', 1.0)
            }
        },
        'filter': {
            'command': 'filter',
            'parameters': {
                'filter_type': parameters.get('filter_type', 'none'),
                'intensity': parameters.get('intensity', 0.5)
            }
        }
    }
    
    if suggestion_type in command_mapping:
        return command_mapping[suggestion_type]
    else:
        # Default command structure for unknown types
        return {
            'command': suggestion_type,
            'parameters': parameters
        }


@app.post("/generate", response_model=VideoResponse)
async def generate_video(request: ScriptRequest):
    """
    Generate a video plan from the provided script and return final JSON.
    
    Args:
        request: ScriptRequest containing script text and optional model override
        
    Returns:
        VideoResponse: Final JSON with clips, narrations, bgms, and timeline
    """
    try:
        # Validate script is not empty
        if not request.script or not request.script.strip():
            raise HTTPException(status_code=400, detail="Script cannot be empty")
        
        agent = VideoAgent(model=request.model)
        result = agent.run(request.script)
        
        return VideoResponse(
            clips=result.get("clips", {}),
            narrations=result.get("narrations", {}),
            bgms=result.get("bgms", {}),
            timeline=result.get("timeline", []),
            total_duration=result.get("total_duration", 0.0),
            assembly_metadata=result.get("assembly_metadata", {})
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/process_video", response_model=VideoProcessResponse)
async def process_video(video: UploadFile = File(...), model: Optional[str] = None):
    """
    Process an uploaded video file and return the final video result.
    
    Args:
        video: Uploaded video file for processing
        model: Optional model override
        
    Returns:
        VideoProcessResponse: Final processing result with video and metadata
    """
    try:
        # Create a temporary directory for processing
        with tempfile.TemporaryDirectory() as temp_dir:
            video_path = os.path.join(temp_dir, video.filename)
            
            # Save uploaded video to temporary path
            with open(video_path, 'wb') as f:
                shutil.copyfileobj(video.file, f)
            
            agent = VideoAgent(model=model)
            result = agent.run_with_video(video_path)
            
            return VideoProcessResponse(
                final_video=result.get("final_video"),
                plan=result.get("plan"),
                source_video=result.get("source_video"),
                processing_type=result.get("processing_type"),
                coverage_percentage=result.get("coverage_percentage", None),
                scene_count=result.get("scene_count", None)
            )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/preview/{session_id}")
async def get_preview(session_id: str, request: Request, range: str = Header(None)):
    """Serve preview video for a session with Range header support for streaming."""
    try:
        session = await session_manager.get_session(session_id)
        if not session:
            raise HTTPException(status_code=404, detail="Session not found")
        
        preview_path = session.preview_path
        
        if not preview_path or not os.path.exists(preview_path):
            raise HTTPException(status_code=404, detail="Preview not available")
        
        # Get file size
        file_size = os.path.getsize(preview_path)
        
        # Handle Range requests for streaming large videos
        if range:
            try:
                # Parse Range header: "bytes=start-end" or "bytes=start-"
                range_match = range.replace('bytes=', '')
                if '-' in range_match:
                    start_str, end_str = range_match.split('-', 1)
                    start = int(start_str) if start_str else 0
                    end = int(end_str) if end_str else file_size - 1
                else:
                    start = int(range_match)
                    end = file_size - 1
                
                # Validate range
                if start < 0 or end >= file_size or start > end:
                    raise HTTPException(status_code=416, detail="Range Not Satisfiable")
                
                # Calculate content length
                content_length = end - start + 1
                
                def generate_chunks():
                    """Generate file chunks for streaming."""
                    with open(preview_path, 'rb') as video_file:
                        video_file.seek(start)
                        remaining = content_length
                        chunk_size = 8192  # 8KB chunks
                        
                        while remaining > 0:
                            bytes_to_read = min(chunk_size, remaining)
                            chunk = video_file.read(bytes_to_read)
                            if not chunk:
                                break
                            remaining -= len(chunk)
                            yield chunk
                
                # Create streaming response with partial content
                headers = {
                    "Content-Range": f"bytes {start}-{end}/{file_size}",
                    "Accept-Ranges": "bytes",
                    "Content-Length": str(content_length),
                }
                
                return StreamingResponse(
                    generate_chunks(), 
                    status_code=206,  # Partial Content
                    media_type="video/mp4",
                    headers=headers
                )
                
            except ValueError as ve:
                raise HTTPException(status_code=400, detail=f"Invalid Range header: {ve}")
        
        # No Range header - serve full file
        # For large files, still use streaming but serve entire content
        if file_size > config.LARGE_FILE_THRESHOLD:
            def generate_full_chunks():
                """Generate full file chunks for large files."""
                with open(preview_path, 'rb') as video_file:
                    chunk_size = 8192  # 8KB chunks
                    while True:
                        chunk = video_file.read(chunk_size)
                        if not chunk:
                            break
                        yield chunk
            
            headers = {
                "Accept-Ranges": "bytes",
                "Content-Length": str(file_size),
            }
            
            return StreamingResponse(
                generate_full_chunks(),
                media_type="video/mp4", 
                headers=headers
            )
        
        # Small files - use regular FileResponse
        return FileResponse(preview_path, media_type="video/mp4")
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/generate_preview/{session_id}")
async def generate_preview_endpoint(session_id: str, request: PreviewRequest):
    """Generate preview video with applied edits (Rule 2.2: Integrate Preview & Finalization)."""
    try:
        session = await session_manager.get_session(session_id)
        if not session:
            raise HTTPException(status_code=404, detail="Session not found")
        
        video_path = session.video_path
        if not video_path or not os.path.exists(video_path):
            raise HTTPException(status_code=404, detail="Source video not found")
        
        # Generate preview with specified quality and duration limit  
        preview_filename = f"preview_{session_id}_{int(time.time())}.mp4"
        preview_path = os.path.join(config.VIDEO_OUTPUT_DIR, preview_filename)
        
        # Ensure output directory exists
        os.makedirs(config.VIDEO_OUTPUT_DIR, exist_ok=True)
        
        # Apply preview-specific processing (lower quality, duration limit)
        preview_result = await generate_preview_video(
            video_path=video_path,
            edits=request.edits or session.edits,
            output_path=preview_path,
            quality=request.quality,
            duration_limit=request.duration_limit
        )
        
        # Update session with preview path
        await session_manager.update_session(session_id, preview_path=preview_path)
        
        return {
            "status": "success",
            "preview_path": preview_filename,
            "preview_url": f"/preview/{session_id}",
            "quality": request.quality,
            "duration": preview_result.get("duration", 0),
            "file_size": preview_result.get("file_size", 0),
            "edits_applied": len(request.edits or session.edits)
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Preview generation failed: {str(e)}")


@app.post("/finalize/{session_id}")
async def finalize_video(session_id: str):
    """Finalize video with all applied edits."""
    try:
        session = await session_manager.get_session(session_id)
        if not session:
            raise HTTPException(status_code=404, detail="Session not found")
        
        # Check if there's a video to finalize
        video_path = session.video_path or session.preview_path
        if not video_path or not os.path.exists(video_path):
            raise HTTPException(status_code=400, detail="No video to finalize")
        
        agent = VideoAgent()
        
        # Use the finalize_video method from VideoAgent
        final_path = agent.finalize_video(session.to_dict())
        
        # Update session with final video path
        await session_manager.update_session(session_id, 
                                           final_video_path=final_path, 
                                           finalized=True)
        
        return {
            "status": "success",
            "final_video_path": final_path,
            "edits_applied": len(session.edits),
            "session_id": session_id
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/session/{session_id}")
async def get_session_info(session_id: str):
    """Get information about a session."""
    try:
        session = await session_manager.get_session(session_id)
        if not session:
            raise HTTPException(status_code=404, detail="Session not found")
        
        # Remove sensitive file paths for security
        safe_data = {
            "session_id": session_id,
            "filename": session.filename or 'unknown',
            "edits_count": len(session.edits),
            "finalized": session.finalized,
            "last_activity": session.last_activity,
            "file_size": session.file_size
        }
        
        return safe_data
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# Phase 3: Enhanced Video Editing Endpoints

@app.post("/trim/{session_id}")
async def trim_video_endpoint(session_id: str, request: TrimRequest):
    """Trim video for a session."""
    try:
        session = await session_manager.get_session(session_id)
        if not session:
            raise HTTPException(status_code=404, detail="Session not found")
        
        # Validate time parameters
        start_time = request.start_time
        end_time = request.end_time
        
        if start_time < 0 or end_time < 0:
            raise HTTPException(status_code=400, detail="Invalid time parameters - times cannot be negative")
        
        if start_time >= end_time:
            raise HTTPException(status_code=400, detail="Invalid time parameters - start time must be less than end time")
        
        video_path = session.video_path or session.preview_path
        
        if not video_path or not os.path.exists(video_path):
            raise HTTPException(status_code=404, detail="Source video not found")
        
        # Generate output path for trimmed video
        output_filename = f"trimmed_{session_id}_{int(time.time())}.mp4"
        output_path = os.path.join(config.VIDEO_OUTPUT_DIR, output_filename)
        
        # Ensure output directory exists
        os.makedirs(config.VIDEO_OUTPUT_DIR, exist_ok=True)
        
        # Convert float seconds to HH:MM:SS format for trim_video function
        def seconds_to_time_string(seconds: float) -> str:
            """Convert seconds to HH:MM:SS format."""
            hours = int(seconds // 3600)
            minutes = int((seconds % 3600) // 60)
            secs = int(seconds % 60)
            return f"{hours:02d}:{minutes:02d}:{secs:02d}"
        
        start_time_str = seconds_to_time_string(start_time)
        end_time_str = seconds_to_time_string(end_time)
        
        # Perform the trim operation
        trim_video(video_path, start_time_str, end_time_str, output_path)
        
        # Add edit to history
        edit_record = {
            "type": "trim",
            "start_time": request.start_time,
            "end_time": request.end_time,
            "timestamp": time.time()
        }
        
        new_edits = session.edits + [edit_record]
        await session_manager.update_session(session_id, preview_path=output_path, edits=new_edits)
        
        return {
            "status": "success",
            "output_path": output_filename,
            "preview_url": f"/preview/{session_id}",
            "edit_applied": edit_record
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/apply_edits/{session_id}")
async def apply_edit_commands_endpoint(session_id: str, request: EditCommandRequest):
    """Apply multiple edit commands to a session's video."""
    try:
        session = await session_manager.get_session(session_id)
        if not session:
            raise HTTPException(status_code=404, detail="Session not found")
        
        # Validate edits are provided
        if not request.edits or len(request.edits) == 0:
            raise HTTPException(status_code=400, detail="No edits provided")
        
        video_path = session.video_path
        
        if not video_path or not os.path.exists(video_path):
            raise HTTPException(status_code=404, detail="Source video not found")
        
        # Generate output path for edited video
        output_filename = f"edited_{session_id}_{int(time.time())}.mp4"
        output_path = os.path.join(config.VIDEO_OUTPUT_DIR, output_filename)
        
        # Ensure output directory exists
        os.makedirs(config.VIDEO_OUTPUT_DIR, exist_ok=True)
        
        # Apply the edit commands
        apply_edit_commands(video_path, request.edits, output_path)
        
        # Add edits to history
        edit_record = {
            "type": "batch_edits",
            "edits": request.edits,
            "timestamp": time.time()
        }
        
        new_edits = session.edits + [edit_record]
        await session_manager.update_session(session_id, preview_path=output_path, edits=new_edits)
        
        return {
            "status": "success",
            "output_path": output_filename,
            "preview_url": f"/preview/{session_id}",
            "edits_applied": len(request.edits),
            "edit_record": edit_record
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/thumbnail/{session_id}")
async def generate_thumbnail_endpoint(session_id: str, request: ThumbnailRequest):
    """Generate a thumbnail for a session's video at specified time."""
    try:
        session = await session_manager.get_session(session_id)
        if not session:
            raise HTTPException(status_code=404, detail="Session not found")
        
        video_path = session.preview_path or session.video_path
        
        if not video_path or not os.path.exists(video_path):
            raise HTTPException(status_code=400, detail="No video available for thumbnail generation")
        
        # Generate output path for thumbnail
        thumbnail_filename = f"thumb_{session_id}_{int(time.time())}.jpg"
        thumbnail_path = os.path.join(config.VIDEO_OUTPUT_DIR, thumbnail_filename)
        
        # Ensure output directory exists
        os.makedirs(config.VIDEO_OUTPUT_DIR, exist_ok=True)
        
        # Generate the thumbnail
        generate_video_thumbnail(video_path, request.time, thumbnail_path)
        
        # Update session activity
        await session_manager.update_session(session_id)
        
        return {
            "status": "success",
            "thumbnail_path": thumbnail_filename,
            "thumbnail_url": f"/file/{thumbnail_filename}",
            "time": request.time
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/file/{filename}")
def serve_file(filename: str):
    """Serve generated files (thumbnails, processed videos, etc.)."""
    try:
        file_path = os.path.join(config.VIDEO_OUTPUT_DIR, filename)
        
        if not os.path.exists(file_path):
            raise HTTPException(status_code=404, detail="File not found")
        
        # Determine media type based on extension
        ext = Path(filename).suffix.lower()
        if ext in ['.jpg', '.jpeg', '.png']:
            media_type = f"image/{ext[1:]}"
        elif ext in ['.mp4', '.avi', '.mov']:
            media_type = f"video/{ext[1:]}"
        else:
            media_type = "application/octet-stream"
        
        return FileResponse(file_path, media_type=media_type)
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# Phase 4: AI Suggestions and Analysis Endpoints

@app.post("/analyze/{session_id}")
async def analyze_video_endpoint(session_id: str, request: AIAnalysisRequest):
    """Perform AI-powered video content analysis for a session using Memories.ai placeholder."""
    try:
        session = await session_manager.get_session(session_id)
        if not session:
            raise HTTPException(status_code=404, detail="Session not found")
        
        video_path = session.preview_path or session.video_path
        
        if not video_path or not os.path.exists(video_path):
            raise HTTPException(status_code=404, detail="Video not found")
        
        # Use Memories.ai placeholder for analysis (Phase 1: Rule 1.2)
        analysis_result = call_memories_placeholder(
            video_path, 
            detailed=request.detailed
        )
        
        # Update session activity
        await session_manager.update_session(session_id)
        
        return {
            "status": "success",
            "session_id": session_id,
            "analysis": analysis_result,
            "timestamp": time.time()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")


@app.post("/suggestions/{session_id}")
async def get_edit_suggestions_endpoint(session_id: str, request: AISuggestionsRequest):
    """Get AI-powered video editing suggestions for a session."""
    try:
        if session_id not in sessions:
            raise HTTPException(status_code=404, detail="Session not found")
        
        session_data = sessions[session_id]
        video_path = session_data.get('preview_path') or session_data.get('video_path')
        
        if not video_path or not os.path.exists(video_path):
            raise HTTPException(status_code=404, detail="Video not found")
        
        # Get existing analysis if available, otherwise perform basic analysis
        analysis = session_data.get('analysis')
        if not analysis:
            analysis = analyze_video_content(video_path, detailed=False)
        
        # Generate AI-powered editing suggestions
        suggestions = suggest_video_edits(
            video_path,
            analysis=analysis,
            preferences=request.preferences or {},
            max_suggestions=request.max_suggestions
        )
        
        # Update session activity
        session_data['last_activity'] = time.time()
        session_data['suggestions'] = suggestions
        
        return {
            "status": "success",
            "session_id": session_id,
            "suggestions": suggestions,
            "suggestions_count": len(suggestions.get('suggestions', [])),
            "timestamp": time.time()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Suggestions generation failed: {str(e)}")


@app.post("/optimize/{session_id}")
async def get_optimization_recommendations_endpoint(session_id: str, request: OptimizationRequest):
    """Get AI-powered optimization recommendations for a session."""
    try:
        if session_id not in sessions:
            raise HTTPException(status_code=404, detail="Session not found")
        
        session_data = sessions[session_id]
        video_path = session_data.get('preview_path') or session_data.get('video_path')
        
        if not video_path or not os.path.exists(video_path):
            raise HTTPException(status_code=404, detail="Video not found")
        
        # Get existing analysis if available, otherwise perform basic analysis
        analysis = session_data.get('analysis')
        if not analysis:
            analysis = analyze_video_content(video_path, detailed=False)
        
        # Generate optimization recommendations
        recommendations = generate_optimization_recommendations(
            video_path,
            analysis=analysis,
            target_platform=request.target_platform,
            quality_level=request.quality_level
        )
        
        # Update session activity
        session_data['last_activity'] = time.time()
        session_data['optimization_recommendations'] = recommendations
        
        return {
            "status": "success",
            "session_id": session_id,
            "recommendations": recommendations,
            "recommendations_count": len(recommendations.get('recommendations', [])),
            "target_platform": request.target_platform,
            "quality_level": request.quality_level,
            "timestamp": time.time()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Optimization recommendations failed: {str(e)}")


@app.get("/ai_insights/{session_id}")
async def get_ai_insights_endpoint(session_id: str):
    """Get all available AI insights for a session (analysis, suggestions, optimizations)."""
    try:
        if session_id not in sessions:
            raise HTTPException(status_code=404, detail="Session not found")
        
        session_data = sessions[session_id]
        
        # Update session activity
        session_data['last_activity'] = time.time()
        
        # Collect all available AI insights
        insights = {
            "session_id": session_id,
            "has_analysis": 'analysis' in session_data,
            "has_suggestions": 'suggestions' in session_data,
            "has_optimization_recommendations": 'optimization_recommendations' in session_data,
            "analysis": session_data.get('analysis'),
            "suggestions": session_data.get('suggestions'),
            "optimization_recommendations": session_data.get('optimization_recommendations'),
            "edits_count": len(session_data.get('edits', [])),
            "timestamp": time.time()
        }
        
        return {
            "status": "success",
            "insights": insights
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to retrieve AI insights: {str(e)}")


# Phase 5: E2E Workflow Management Endpoints (Rule 4.2)

@app.post("/workflow/start/{session_id}")
async def start_e2e_workflow(session_id: str, request: WorkflowStartRequest):
    """Start a complete end-to-end workflow for a video editing session (Rule 4.2)."""
    try:
        # Validate session exists
        session = await session_manager.get_session(session_id)
        if not session:
            raise HTTPException(status_code=404, detail="Session not found")
        
        # Start the E2E workflow
        workflow_result = await workflow_orchestrator.start_workflow(
            session_id=session_id,
            workflow_config=request.workflow_config or {},
            user_preferences=request.user_preferences or {}
        )
        
        logger.info(f"Started E2E workflow for session {session_id}: {workflow_result['workflow_id']}")
        
        return {
            "status": "success",
            "message": "E2E workflow started successfully",
            **workflow_result
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to start E2E workflow for session {session_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Workflow start failed: {str(e)}")


@app.get("/workflow/status/{workflow_id}")
async def get_workflow_status(workflow_id: str):
    """Get the current status of an E2E workflow (Rule 4.2)."""
    try:
        status = workflow_orchestrator.get_workflow_status(workflow_id)
        
        if not status:
            raise HTTPException(status_code=404, detail="Workflow not found")
        
        return {
            "status": "success",
            "workflow_status": status
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get workflow status: {str(e)}")


@app.post("/workflow/cancel/{workflow_id}")
async def cancel_workflow(workflow_id: str):
    """Cancel an active E2E workflow (Rule 4.2)."""
    try:
        cancelled = await workflow_orchestrator.cancel_workflow(workflow_id)
        
        if not cancelled:
            raise HTTPException(status_code=404, detail="Workflow not found or already completed")
        
        return {
            "status": "success",
            "message": "Workflow cancelled successfully",
            "workflow_id": workflow_id
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to cancel workflow: {str(e)}")


@app.get("/workflow/history")
async def get_workflow_history(limit: Optional[int] = 10):
    """Get workflow execution history (Rule 4.2)."""
    try:
        history = workflow_orchestrator.get_workflow_history(limit=limit)
        
        return {
            "status": "success",
            "workflow_history": history,
            "total_returned": len(history)
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get workflow history: {str(e)}")


@app.websocket("/ws/workflow/{workflow_id}")
async def workflow_progress_websocket(websocket: WebSocket, workflow_id: str):
    """WebSocket endpoint for real-time workflow progress updates (Rule 4.2)."""
    await websocket.accept()
    logger.info(f"WebSocket connection established for workflow progress: {workflow_id}")
    
    # Register progress callback for this WebSocket
    async def progress_callback(progress_data: dict):
        if progress_data['workflow_id'] == workflow_id:
            try:
                await websocket.send_text(json.dumps({
                    "type": "workflow_progress",
                    "workflow_id": workflow_id,
                    **progress_data
                }))
            except Exception as e:
                logger.error(f"Failed to send progress update: {e}")
    
    workflow_orchestrator.register_progress_callback(progress_callback)
    
    try:
        # Send initial status if workflow exists
        initial_status = workflow_orchestrator.get_workflow_status(workflow_id)
        if initial_status:
            await websocket.send_text(json.dumps({
                "type": "workflow_status",
                "workflow_id": workflow_id,
                **initial_status
            }))
        else:
            await websocket.send_text(json.dumps({
                "type": "error",
                "message": f"Workflow {workflow_id} not found"
            }))
        
        # Keep connection alive and handle client messages
        while True:
            try:
                data = await websocket.receive_text()
                message = json.loads(data)
                
                if message.get("type") == "ping":
                    await websocket.send_text(json.dumps({
                        "type": "pong",
                        "timestamp": time.time()
                    }))
                elif message.get("type") == "get_status":
                    current_status = workflow_orchestrator.get_workflow_status(workflow_id)
                    if current_status:
                        await websocket.send_text(json.dumps({
                            "type": "workflow_status",
                            "workflow_id": workflow_id,
                            **current_status
                        }))
                
            except WebSocketDisconnect:
                break
            except Exception as e:
                logger.error(f"WebSocket message handling error: {e}")
                await websocket.send_text(json.dumps({
                    "type": "error",
                    "message": str(e)
                }))
                
    except WebSocketDisconnect:
        logger.info(f"WebSocket disconnected for workflow: {workflow_id}")
    except Exception as e:
        logger.error(f"WebSocket error for workflow {workflow_id}: {e}")
    finally:
        # Note: In a production system, you'd want to properly unregister the callback
        pass


@app.post("/workflow/batch_start")
async def start_batch_workflows(session_ids: List[str], workflow_config: Optional[Dict[str, Any]] = None):
    """Start E2E workflows for multiple sessions simultaneously (Rule 4.2)."""
    try:
        if not session_ids or len(session_ids) == 0:
            raise HTTPException(status_code=400, detail="No session IDs provided")
        
        if len(session_ids) > 10:  # Limit batch size
            raise HTTPException(status_code=400, detail="Batch size cannot exceed 10 sessions")
        
        results = []
        
        for session_id in session_ids:
            try:
                # Validate session exists
                session = await session_manager.get_session(session_id)
                if not session:
                    results.append({
                        "session_id": session_id,
                        "status": "failed",
                        "error": "Session not found"
                    })
                    continue
                
                # Start workflow
                workflow_result = await workflow_orchestrator.start_workflow(
                    session_id=session_id,
                    workflow_config=workflow_config or {},
                    user_preferences={}
                )
                
                results.append({
                    "session_id": session_id,
                    "status": "started",
                    "workflow_id": workflow_result["workflow_id"]
                })
                
            except Exception as e:
                results.append({
                    "session_id": session_id,
                    "status": "failed",
                    "error": str(e)
                })
        
        successful_starts = len([r for r in results if r["status"] == "started"])
        
        return {
            "status": "completed",
            "message": f"Batch workflow start completed: {successful_starts}/{len(session_ids)} successful",
            "results": results,
            "summary": {
                "total_requested": len(session_ids),
                "successful_starts": successful_starts,
                "failed_starts": len(session_ids) - successful_starts
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Batch workflow start failed: {str(e)}")


@app.get("/workflow/active")
async def get_active_workflows():
    """Get all currently active workflows (Rule 4.2)."""
    try:
        active_workflows = []
        
        for workflow_id in workflow_orchestrator.active_workflows:
            status = workflow_orchestrator.get_workflow_status(workflow_id)
            if status:
                active_workflows.append(status)
        
        return {
            "status": "success",
            "active_workflows": active_workflows,
            "total_active": len(active_workflows)
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get active workflows: {str(e)}")


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
