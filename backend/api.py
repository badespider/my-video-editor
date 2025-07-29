"""
FastAPI backend for multi-agent AI video creation system.
Provides REST API endpoints for frontend integration.
"""

from fastapi import FastAPI, HTTPException, UploadFile, File, WebSocket, WebSocketDisconnect
from fastapi.responses import FileResponse
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
from typing import Optional, Dict, List
from pathlib import Path

# Add parent directory to path to import project modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from coordinator import VideoAgent
import config
from utils.utils import call_memories_placeholder, trim_video, apply_edit_commands, generate_video_thumbnail, suggest_video_edits, analyze_video_content, generate_optimization_recommendations

# Phase 1: Session Management (Rule 1.1)
# In-memory session store (use Redis for production)
sessions: Dict[str, Dict] = {}
active_connections: Dict[str, WebSocket] = {}

# Session cleanup task
async def cleanup_sessions():
    """Clean up expired sessions periodically."""
    while True:
        current_time = time.time()
        expired_sessions = []
        
        for session_id, session_data in sessions.items():
            if current_time - session_data.get('last_activity', 0) > config.SESSION_TIMEOUT:
                expired_sessions.append(session_id)
        
        for session_id in expired_sessions:
            await cleanup_session(session_id)
        
        await asyncio.sleep(60)  # Check every minute

# Define lifespan context
@asynccontextmanager
async def lifespan_context(app: FastAPI):
    # Start cleanup task on startup
    asyncio.create_task(cleanup_sessions())
    yield
    # Any cleanup on shutdown can go here

# Initialize FastAPI app with lifespan
app = FastAPI(title="AI Video Creation API", lifespan=lifespan_context)

async def cleanup_session(session_id: str):
    """Clean up a specific session."""
    if session_id in sessions:
        session_data = sessions[session_id]
        
        # Clean up temporary files
        video_path = session_data.get('video_path')
        preview_path = session_data.get('preview_path')
        
        for path in [video_path, preview_path]:
            if path and os.path.exists(path):
                try:
                    os.remove(path)
                except Exception as e:
                    print(f"Failed to cleanup file {path}: {e}")
        
        # Clean up session data
        del sessions[session_id]
        
        # Close WebSocket connection if active
        if session_id in active_connections:
            try:
                await active_connections[session_id].close()
            except:
                pass
            del active_connections[session_id]
        
        print(f"Cleaned up session: {session_id}")

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
    start_time: str
    end_time: str


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


@app.get("/")
async def root():
    """Root endpoint."""
    return {"message": "AI Video Creation API"}


@app.post("/upload/video")
async def upload_video(file: UploadFile = File(...)):
    """Upload video file and create a new editing session."""
    try:
        # Validate upload
        if not validate_upload(file):
            raise HTTPException(status_code=400, detail="Invalid file type or upload failed validation")
        
        # Check session limit
        if len(sessions) >= config.MAX_SESSIONS:
            raise HTTPException(status_code=429, detail="Maximum sessions reached. Please try again later.")
        
        # Create new session
        session_id = str(uuid.uuid4())
        
        # Sanitize filename
        sanitized_filename = sanitize_filename(file.filename)
        file_path = os.path.join(config.UPLOAD_DIR, f"{session_id}_{sanitized_filename}")
        
        # Ensure upload directory exists
        os.makedirs(config.UPLOAD_DIR, exist_ok=True)
        
        # Save uploaded file
        with open(file_path, "wb") as f:
            content = await file.read()
            f.write(content)
        
        # Initialize session
        sessions[session_id] = {
            "video_path": file_path,
            "edits": [],
            "preview_path": file_path,
            "last_activity": time.time(),
            "filename": sanitized_filename,
            "file_size": len(content),
            "video_duration": 0  # Will be populated later
        }
        
        print(f"Video uploaded: {file_path} for session {session_id}")
        return {"session_id": session_id, "filename": sanitized_filename}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.websocket("/ws/edit/{session_id}")
async def websocket_endpoint(websocket: WebSocket, session_id: str):
    """WebSocket endpoint to handle video editing sessions with command parsing."""
    await websocket.accept()
    active_connections[session_id] = websocket

    if session_id not in sessions:
        sessions[session_id] = {
            "video_path": None,
            "edits": [],
            "preview_path": None,
            "last_activity": time.time()
        }

    session = sessions[session_id]
    agent = VideoAgent()

    try:
        while True:
            data = await websocket.receive_text()
            session["last_activity"] = time.time()
            
            try:
                # Parse natural language command using VideoAgent
                command = agent.parse_command(data)
                
                # Apply the command to the session
                agent.apply_command(session, command)
                
                # Send response with preview URL
                response = {
                    "status": "success",
                    "command": command,
                    "preview_url": f"/preview/{session_id}",
                    "edits_count": len(session["edits"])
                }
                await websocket.send_text(json.dumps(response))
                
            except Exception as cmd_error:
                # Send error response
                error_response = {
                    "status": "error",
                    "message": str(cmd_error),
                    "input": data
                }
                await websocket.send_text(json.dumps(error_response))

    except WebSocketDisconnect:
        print(f"Client disconnected: {session_id}")
        if session_id in active_connections:
            del active_connections[session_id]


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
def get_preview(session_id: str):
    """Serve preview video for a session."""
    try:
        if session_id not in sessions:
            raise HTTPException(status_code=404, detail="Session not found")
        
        session_data = sessions[session_id]
        preview_path = session_data.get('preview_path')
        
        if not preview_path or not os.path.exists(preview_path):
            raise HTTPException(status_code=404, detail="Preview not available")
        
        return FileResponse(preview_path, media_type="video/mp4")
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/finalize/{session_id}")
async def finalize_video(session_id: str):
    """Finalize video with all applied edits."""
    try:
        if session_id not in sessions:
            raise HTTPException(status_code=404, detail="Session not found")
        
        session_data = sessions[session_id]
        agent = VideoAgent()
        
        # Use the finalize_video method from VideoAgent
        final_path = agent.finalize_video(session_data)
        
        # Update session with final video path
        session_data['final_video_path'] = final_path
        session_data['finalized'] = True
        session_data['last_activity'] = time.time()
        
        return {
            "status": "success",
            "final_video_path": final_path,
            "edits_applied": len(session_data.get('edits', [])),
            "session_id": session_id
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/session/{session_id}")
def get_session_info(session_id: str):
    """Get information about a session."""
    try:
        if session_id not in sessions:
            raise HTTPException(status_code=404, detail="Session not found")
        
        session_data = sessions[session_id].copy()
        # Remove sensitive file paths for security
        safe_data = {
            "session_id": session_id,
            "filename": session_data.get('filename', 'unknown'),
            "edits_count": len(session_data.get('edits', [])),
            "finalized": session_data.get('finalized', False),
            "last_activity": session_data.get('last_activity', 0),
            "file_size": session_data.get('file_size', 0)
        }
        
        return safe_data
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# Phase 3: Enhanced Video Editing Endpoints

@app.post("/trim/{session_id}")
async def trim_video_endpoint(session_id: str, request: TrimRequest):
    """Trim video for a session."""
    try:
        if session_id not in sessions:
            raise HTTPException(status_code=404, detail="Session not found")
        
        session_data = sessions[session_id]
        video_path = session_data.get('video_path')
        
        if not video_path or not os.path.exists(video_path):
            raise HTTPException(status_code=404, detail="Source video not found")
        
        # Generate output path for trimmed video
        output_filename = f"trimmed_{session_id}_{int(time.time())}.mp4"
        output_path = os.path.join(config.VIDEO_OUTPUT_DIR, output_filename)
        
        # Ensure output directory exists
        os.makedirs(config.VIDEO_OUTPUT_DIR, exist_ok=True)
        
        # Perform the trim operation
        trim_video(video_path, request.start_time, request.end_time, output_path)
        
        # Update session preview path
        session_data['preview_path'] = output_path
        session_data['last_activity'] = time.time()
        
        # Add edit to history
        edit_record = {
            "type": "trim",
            "start_time": request.start_time,
            "end_time": request.end_time,
            "timestamp": time.time()
        }
        session_data['edits'].append(edit_record)
        
        return {
            "status": "success",
            "output_path": output_filename,
            "preview_url": f"/preview/{session_id}",
            "edit_applied": edit_record
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/apply_edits/{session_id}")
async def apply_edit_commands_endpoint(session_id: str, request: EditCommandRequest):
    """Apply multiple edit commands to a session's video."""
    try:
        if session_id not in sessions:
            raise HTTPException(status_code=404, detail="Session not found")
        
        session_data = sessions[session_id]
        video_path = session_data.get('video_path')
        
        if not video_path or not os.path.exists(video_path):
            raise HTTPException(status_code=404, detail="Source video not found")
        
        # Generate output path for edited video
        output_filename = f"edited_{session_id}_{int(time.time())}.mp4"
        output_path = os.path.join(config.VIDEO_OUTPUT_DIR, output_filename)
        
        # Ensure output directory exists
        os.makedirs(config.VIDEO_OUTPUT_DIR, exist_ok=True)
        
        # Apply the edit commands
        apply_edit_commands(video_path, request.edits, output_path)
        
        # Update session preview path
        session_data['preview_path'] = output_path
        session_data['last_activity'] = time.time()
        
        # Add edits to history
        edit_record = {
            "type": "batch_edits",
            "edits": request.edits,
            "timestamp": time.time()
        }
        session_data['edits'].append(edit_record)
        
        return {
            "status": "success",
            "output_path": output_filename,
            "preview_url": f"/preview/{session_id}",
            "edits_applied": len(request.edits),
            "edit_record": edit_record
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/thumbnail/{session_id}")
async def generate_thumbnail_endpoint(session_id: str, request: ThumbnailRequest):
    """Generate a thumbnail for a session's video at specified time."""
    try:
        if session_id not in sessions:
            raise HTTPException(status_code=404, detail="Session not found")
        
        session_data = sessions[session_id]
        video_path = session_data.get('preview_path') or session_data.get('video_path')
        
        if not video_path or not os.path.exists(video_path):
            raise HTTPException(status_code=404, detail="Video not found")
        
        # Generate output path for thumbnail
        thumbnail_filename = f"thumb_{session_id}_{int(time.time())}.jpg"
        thumbnail_path = os.path.join(config.VIDEO_OUTPUT_DIR, thumbnail_filename)
        
        # Ensure output directory exists
        os.makedirs(config.VIDEO_OUTPUT_DIR, exist_ok=True)
        
        # Generate the thumbnail
        generate_video_thumbnail(video_path, request.time, thumbnail_path)
        
        # Update session activity
        session_data['last_activity'] = time.time()
        
        return {
            "status": "success",
            "thumbnail_path": thumbnail_filename,
            "thumbnail_url": f"/file/{thumbnail_filename}",
            "time": request.time
        }
        
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
    """Perform AI-powered video content analysis for a session."""
    try:
        if session_id not in sessions:
            raise HTTPException(status_code=404, detail="Session not found")
        
        session_data = sessions[session_id]
        video_path = session_data.get('preview_path') or session_data.get('video_path')
        
        if not video_path or not os.path.exists(video_path):
            raise HTTPException(status_code=404, detail="Video not found")
        
        # Perform AI-powered content analysis
        analysis_result = analyze_video_content(
            video_path, 
            detailed=request.detailed,
            preferences=request.preferences or {}
        )
        
        # Update session activity and cache analysis
        session_data['last_activity'] = time.time()
        session_data['analysis'] = analysis_result
        
        return {
            "status": "success",
            "session_id": session_id,
            "analysis": analysis_result,
            "timestamp": time.time()
        }
        
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


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
