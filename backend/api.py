"""
FastAPI backend for multi-agent AI video creation system.
Provides REST API endpoints for frontend integration.
"""

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import sys
import os

# Add parent directory to path to import project modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from coordinator import VideoAgent

app = FastAPI(title="AI Video Creation API")


class ScriptRequest(BaseModel):
    """Request model for script processing."""
    script: str
    model: str = None


class VideoResponse(BaseModel):
    """Response model for video plan."""
    clips: list
    narrations: list
    bgms: list
    timeline: str


@app.get("/")
async def root():
    """Root endpoint."""
    return {"message": "AI Video Creation API"}


@app.post("/create-video", response_model=VideoResponse)
async def create_video(request: ScriptRequest):
    """
    Create a video plan from the provided script.
    """
    try:
        agent = VideoAgent(model=request.model)
        result = agent.run(request.script)
        
        return VideoResponse(
            clips=result.get("clips", []),
            narrations=result.get("narrations", []),
            bgms=result.get("bgms", []),
            timeline=result.get("timeline", "")
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
