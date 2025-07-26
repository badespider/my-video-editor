"""
FastAPI backend for multi-agent AI video creation system.
Provides REST API endpoints for frontend integration.
"""

from fastapi import FastAPI, HTTPException, UploadFile, File
from pydantic import BaseModel
import sys
import os
import tempfile
import shutil
from typing import Optional

# Add parent directory to path to import project modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from coordinator import VideoAgent
import config

app = FastAPI(title="AI Video Creation API")


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


@app.get("/")
async def root():
    """Root endpoint."""
    return {"message": "AI Video Creation API"}


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


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
