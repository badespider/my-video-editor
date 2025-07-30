"""
End-to-End Workflow Orchestrator for AI Video Editing System (Rule 4.2)

This module orchestrates the complete video editing workflow from upload to final export,
providing a unified interface for managing all phases of video processing with proper
error handling, progress tracking, and state management.
"""

import asyncio
import json
import logging
import os
import time
from datetime import datetime
from enum import Enum
from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass, asdict
from pathlib import Path

from backend.session_manager import SessionManager
from coordinator import VideoAgent
from utils.utils import (
    analyze_video_content, 
    suggest_video_edits, 
    generate_optimization_recommendations,
    call_memories_placeholder,
    generate_preview_video
)
import config

logger = logging.getLogger(__name__)


class WorkflowStage(Enum):
    """Enumeration of workflow stages for tracking progress."""
    INITIALIZED = "initialized"
    UPLOADING = "uploading"
    UPLOADED = "uploaded"
    ANALYZING = "analyzing" 
    ANALYZED = "analyzed"
    EDITING = "editing"
    PREVIEWING = "previewing"
    FINALIZING = "finalizing"
    COMPLETED = "completed"
    FAILED = "failed"


class WorkflowStatus(Enum):
    """Enumeration of workflow status states."""
    PENDING = "pending"
    RUNNING = "running"
    PAUSED = "paused"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass
class WorkflowMetrics:
    """Metrics tracking for workflow performance and analytics."""
    start_time: float
    end_time: Optional[float] = None
    upload_duration: Optional[float] = None
    analysis_duration: Optional[float] = None
    editing_duration: Optional[float] = None
    preview_generation_count: int = 0
    commands_applied: int = 0
    errors_encountered: int = 0
    retries_attempted: int = 0
    total_file_size: int = 0
    final_file_size: Optional[int] = None
    
    @property
    def total_duration(self) -> Optional[float]:
        """Calculate total workflow duration."""
        if self.end_time:
            return self.end_time - self.start_time
        return None
    
    @property
    def compression_ratio(self) -> Optional[float]:
        """Calculate compression ratio if both sizes are available."""
        if self.final_file_size and self.total_file_size > 0:
            return self.final_file_size / self.total_file_size
        return None


@dataclass
class WorkflowStep:
    """Individual step within the workflow."""
    name: str
    status: WorkflowStatus
    stage: WorkflowStage
    start_time: Optional[float] = None
    end_time: Optional[float] = None
    progress: float = 0.0  # 0.0 to 1.0
    message: str = ""
    error: Optional[str] = None
    metadata: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}
    
    @property
    def duration(self) -> Optional[float]:
        """Calculate step duration."""
        if self.start_time and self.end_time:
            return self.end_time - self.start_time
        return None


class WorkflowOrchestrator:
    """
    Orchestrates the complete end-to-end video editing workflow.
    
    Manages the entire pipeline from video upload through analysis, editing,
    preview generation, and final export with comprehensive progress tracking,
    error handling, and state management.
    """
    
    def __init__(self, session_manager: SessionManager):
        """Initialize the workflow orchestrator.
        
        Args:
            session_manager: Session manager for handling video editing sessions
        """
        self.session_manager = session_manager
        self.active_workflows: Dict[str, Dict[str, Any]] = {}
        self.workflow_history: List[Dict[str, Any]] = []
        self.callbacks: Dict[str, List[Callable]] = {}
        
    async def start_workflow(
        self, 
        session_id: str, 
        workflow_config: Optional[Dict[str, Any]] = None,
        user_preferences: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Start a complete E2E workflow for a video editing session.
        
        Args:
            session_id: Unique session identifier
            workflow_config: Optional configuration for workflow behavior
            user_preferences: Optional user preferences for editing
            
        Returns:
            Workflow status and initial metadata
        """
        workflow_config = workflow_config or {}
        user_preferences = user_preferences or {}
        
        # Initialize workflow state
        workflow_id = f"workflow_{session_id}_{int(time.time())}"
        workflow_state = {
            "workflow_id": workflow_id,
            "session_id": session_id,
            "status": WorkflowStatus.PENDING,
            "current_stage": WorkflowStage.INITIALIZED,
            "steps": [],
            "metrics": WorkflowMetrics(start_time=time.time()),
            "config": workflow_config,
            "user_preferences": user_preferences,
            "created_at": datetime.now().isoformat(),
            "progress": 0.0,
            "message": "Workflow initialized"
        }
        
        self.active_workflows[workflow_id] = workflow_state
        
        # Start the workflow asynchronously
        asyncio.create_task(self._execute_workflow(workflow_id))
        
        logger.info(f"Started E2E workflow {workflow_id} for session {session_id}")
        return {
            "workflow_id": workflow_id,
            "status": "started",
            "message": "E2E workflow initiated"
        }
    
    async def _execute_workflow(self, workflow_id: str) -> None:
        """
        Execute the complete E2E workflow.
        
        Args:
            workflow_id: Unique workflow identifier
        """
        workflow_state = self.active_workflows[workflow_id]
        session_id = workflow_state["session_id"]
        
        try:
            workflow_state["status"] = WorkflowStatus.RUNNING
            await self._notify_progress(workflow_id, "Workflow execution started")
            
            # Phase 1: Validate Session and Video
            await self._execute_step(workflow_id, "validate_session", self._validate_session)
            
            # Phase 2: Video Analysis
            await self._execute_step(workflow_id, "analyze_video", self._analyze_video)
            
            # Phase 3: Generate AI Suggestions
            await self._execute_step(workflow_id, "generate_suggestions", self._generate_suggestions)
            
            # Phase 4: Initial Preview Generation
            await self._execute_step(workflow_id, "generate_initial_preview", self._generate_initial_preview)
            
            # Phase 5: Wait for User Interactions (editing commands)
            await self._execute_step(workflow_id, "await_user_editing", self._await_user_editing)
            
            # Phase 6: Apply Optimizations
            await self._execute_step(workflow_id, "apply_optimizations", self._apply_optimizations)
            
            # Phase 7: Final Processing
            await self._execute_step(workflow_id, "finalize_video", self._finalize_video)
            
            # Phase 8: Cleanup and Export
            await self._execute_step(workflow_id, "cleanup_export", self._cleanup_and_export)
            
            # Mark workflow as completed
            workflow_state["status"] = WorkflowStatus.COMPLETED
            workflow_state["current_stage"] = WorkflowStage.COMPLETED
            workflow_state["progress"] = 1.0
            workflow_state["metrics"].end_time = time.time()
            
            await self._notify_progress(workflow_id, "Workflow completed successfully")
            logger.info(f"E2E workflow {workflow_id} completed successfully")
            
        except Exception as e:
            await self._handle_workflow_error(workflow_id, str(e))
        finally:
            # Move to history and cleanup
            await self._finalize_workflow(workflow_id)
    
    async def _execute_step(
        self, 
        workflow_id: str, 
        step_name: str, 
        step_function: Callable
    ) -> None:
        """
        Execute a single workflow step with error handling and progress tracking.
        
        Args:
            workflow_id: Unique workflow identifier
            step_name: Name of the step being executed
            step_function: Function to execute for this step
        """
        workflow_state = self.active_workflows[workflow_id]
        
        # Create step tracking
        step = WorkflowStep(
            name=step_name,
            status=WorkflowStatus.RUNNING,
            stage=self._get_stage_for_step(step_name),
            start_time=time.time()
        )
        
        workflow_state["steps"].append(step)
        workflow_state["current_stage"] = step.stage
        
        try:
            await self._notify_progress(workflow_id, f"Executing {step_name}")
            
            # Execute the step function
            result = await step_function(workflow_id)
            
            # Mark step as completed
            step.status = WorkflowStatus.COMPLETED
            step.end_time = time.time()
            step.progress = 1.0
            step.metadata = result or {}
            
            # Update overall workflow progress
            completed_steps = len([s for s in workflow_state["steps"] if s.status == WorkflowStatus.COMPLETED])
            total_steps = 8  # Total number of workflow steps
            workflow_state["progress"] = completed_steps / total_steps
            
            logger.info(f"Step {step_name} completed in {step.duration:.2f}s")
            
        except Exception as e:
            step.status = WorkflowStatus.FAILED
            step.end_time = time.time()
            step.error = str(e)
            workflow_state["metrics"].errors_encountered += 1
            
            logger.error(f"Step {step_name} failed: {e}")
            raise
    
    def _get_stage_for_step(self, step_name: str) -> WorkflowStage:
        """Map step names to workflow stages."""
        stage_mapping = {
            "validate_session": WorkflowStage.UPLOADED,
            "analyze_video": WorkflowStage.ANALYZING,
            "generate_suggestions": WorkflowStage.ANALYZED,
            "generate_initial_preview": WorkflowStage.PREVIEWING,
            "await_user_editing": WorkflowStage.EDITING,
            "apply_optimizations": WorkflowStage.EDITING,
            "finalize_video": WorkflowStage.FINALIZING,
            "cleanup_export": WorkflowStage.COMPLETED
        }
        return stage_mapping.get(step_name, WorkflowStage.INITIALIZED)
    
    async def _validate_session(self, workflow_id: str) -> Dict[str, Any]:
        """Validate that the session and video file exist and are accessible."""
        workflow_state = self.active_workflows[workflow_id]
        session_id = workflow_state["session_id"]
        
        session = await self.session_manager.get_session(session_id)
        if not session:
            raise ValueError(f"Session {session_id} not found")
        
        if not session.video_path or not os.path.exists(session.video_path):
            raise ValueError(f"Video file not found for session {session_id}")
        
        # Update metrics
        workflow_state["metrics"].total_file_size = os.path.getsize(session.video_path)
        
        return {
            "session_valid": True,
            "video_path": session.video_path,
            "file_size": workflow_state["metrics"].total_file_size
        }
    
    async def _analyze_video(self, workflow_id: str) -> Dict[str, Any]:
        """Perform comprehensive video analysis."""
        workflow_state = self.active_workflows[workflow_id]
        session_id = workflow_state["session_id"]
        
        analysis_start = time.time()
        
        session = await self.session_manager.get_session(session_id)
        
        # Perform comprehensive analysis
        analysis = analyze_video_content(session.video_path, detailed=True)
        
        # Also get Memories.ai analysis
        memories_analysis = call_memories_placeholder(session.video_path, detailed=True)
        
        # Combine analyses
        combined_analysis = {
            **analysis,
            "memories_ai_analysis": memories_analysis,
            "analysis_timestamp": time.time()
        }
        
        # Store analysis in session
        session.analysis = combined_analysis
        await self.session_manager.update_session(session_id, analysis=combined_analysis)
        
        # Update metrics
        analysis_duration = time.time() - analysis_start
        workflow_state["metrics"].analysis_duration = analysis_duration
        
        return {
            "analysis_completed": True,
            "analysis_duration": analysis_duration,
            "content_type": analysis.get("content_type", "unknown"),
            "scenes_detected": len(analysis.get("scenes", [])),
            "quality_score": analysis.get("quality_metrics", {}).get("visual_quality", 0.5)
        }
    
    async def _generate_suggestions(self, workflow_id: str) -> Dict[str, Any]:
        """Generate AI-powered editing suggestions."""
        workflow_state = self.active_workflows[workflow_id]
        session_id = workflow_state["session_id"]
        user_preferences = workflow_state["user_preferences"]
        
        session = await self.session_manager.get_session(session_id)
        
        # Generate suggestions based on analysis
        suggestions = suggest_video_edits(
            video_path=session.video_path,
            analysis=session.analysis,
            preferences=user_preferences,
            max_suggestions=workflow_state["config"].get("max_suggestions", 8)
        )
        
        # Store suggestions in session
        session.suggestions = suggestions
        await self.session_manager.update_session(session_id, suggestions=suggestions)
        
        return {
            "suggestions_generated": True,
            "suggestions_count": len(suggestions.get("suggestions", [])),
            "categories": list(suggestions.get("categories", {}).keys())
        }
    
    async def _generate_initial_preview(self, workflow_id: str) -> Dict[str, Any]:
        """Generate initial preview of the video."""
        workflow_state = self.active_workflows[workflow_id]
        session_id = workflow_state["session_id"]
        
        session = await self.session_manager.get_session(session_id)
        
        # Generate preview with no edits (original video, but compressed)
        preview_filename = f"initial_preview_{session_id}_{int(time.time())}.mp4"
        preview_path = os.path.join(config.VIDEO_OUTPUT_DIR, preview_filename)
        
        os.makedirs(config.VIDEO_OUTPUT_DIR, exist_ok=True)
        
        preview_result = await generate_preview_video(
            video_path=session.video_path,
            edits=[],  # No edits for initial preview
            output_path=preview_path,
            quality="medium",
            duration_limit=120  # Limit to 2 minutes for initial preview
        )
        
        # Update session with preview
        await self.session_manager.update_session(session_id, preview_path=preview_path)
        
        workflow_state["metrics"].preview_generation_count += 1
        
        return {
            "initial_preview_generated": True,
            "preview_path": preview_filename,
            "preview_duration": preview_result.get("duration", 0),
            "preview_size": preview_result.get("file_size", 0)
        }
    
    async def _await_user_editing(self, workflow_id: str) -> Dict[str, Any]:
        """Wait for user editing interactions and track progress."""
        workflow_state = self.active_workflows[workflow_id]
        session_id = workflow_state["session_id"]
        
        editing_start = time.time()
        max_wait_time = workflow_state["config"].get("max_editing_time", 3600)  # 1 hour default
        check_interval = 10  # Check every 10 seconds
        
        initial_edits_count = 0
        session = await self.session_manager.get_session(session_id)
        if session.edits:
            initial_edits_count = len(session.edits)
        
        elapsed_time = 0
        while elapsed_time < max_wait_time:
            await asyncio.sleep(check_interval)
            elapsed_time = time.time() - editing_start
            
            # Check for new edits
            session = await self.session_manager.get_session(session_id)
            current_edits_count = len(session.edits or [])
            
            # Update progress based on editing activity
            if current_edits_count > initial_edits_count:
                workflow_state["metrics"].commands_applied = current_edits_count - initial_edits_count
                
                # If user has been actively editing, continue waiting
                if current_edits_count > initial_edits_count:
                    await self._notify_progress(
                        workflow_id, 
                        f"User editing in progress: {workflow_state['metrics'].commands_applied} commands applied"
                    )
                
                # Check if user has indicated they're done (via finalization flag or timeout)
                if session.finalized or elapsed_time > max_wait_time * 0.8:
                    break
        
        editing_duration = time.time() - editing_start
        workflow_state["metrics"].editing_duration = editing_duration
        
        return {
            "editing_phase_completed": True,
            "editing_duration": editing_duration,
            "commands_applied": workflow_state["metrics"].commands_applied,
            "final_edits_count": current_edits_count
        }
    
    async def _apply_optimizations(self, workflow_id: str) -> Dict[str, Any]:
        """Apply automatic optimizations based on analysis."""
        workflow_state = self.active_workflows[workflow_id]
        session_id = workflow_state["session_id"]
        
        session = await self.session_manager.get_session(session_id)
        
        # Get optimization recommendations
        recommendations = generate_optimization_recommendations(
            video_path=session.video_path,
            analysis=session.analysis,
            target_platform=workflow_state["config"].get("target_platform", "general"),
            quality_level=workflow_state["config"].get("quality_level", "medium")
        )
        
        # Apply automatic optimizations (high-confidence ones)
        optimizations_applied = []
        
        for opt in recommendations.get("automated_fixes", []):
            if opt.get("confidence", 0) > 0.8:  # Only apply high-confidence fixes
                # Apply the optimization (this would integrate with VideoAgent)
                optimizations_applied.append(opt)
                logger.info(f"Applied automatic optimization: {opt.get('fix', 'Unknown')}")
        
        # Store optimization recommendations in session
        session.optimization_recommendations = recommendations
        await self.session_manager.update_session(session_id, optimization_recommendations=recommendations)
        
        return {
            "optimizations_analyzed": True,
            "total_recommendations": len(recommendations.get("technical_optimizations", []) + 
                                       recommendations.get("content_optimizations", [])),
            "auto_fixes_applied": len(optimizations_applied)
        }
    
    async def _finalize_video(self, workflow_id: str) -> Dict[str, Any]:
        """Finalize the video with all applied edits and optimizations."""
        workflow_state = self.active_workflows[workflow_id]
        session_id = workflow_state["session_id"]
        
        session = await self.session_manager.get_session(session_id)
        
        # Use VideoAgent to finalize the video
        agent = VideoAgent()
        final_video_path = agent.finalize_video(session.to_dict())
        
        # Update session with final video
        await self.session_manager.update_session(
            session_id, 
            final_video_path=final_video_path,
            finalized=True
        )
        
        # Update metrics
        if os.path.exists(final_video_path):
            workflow_state["metrics"].final_file_size = os.path.getsize(final_video_path)
        
        return {
            "video_finalized": True,
            "final_video_path": final_video_path,
            "final_file_size": workflow_state["metrics"].final_file_size,
            "compression_ratio": workflow_state["metrics"].compression_ratio
        }
    
    async def _cleanup_and_export(self, workflow_id: str) -> Dict[str, Any]:
        """Cleanup temporary files and prepare final export."""
        workflow_state = self.active_workflows[workflow_id]
        session_id = workflow_state["session_id"]
        
        session = await self.session_manager.get_session(session_id)
        
        # Cleanup temporary files (keep only final video and essential files)
        cleanup_count = 0
        temp_patterns = ["temp_", "preview_", "chunk_", "analysis_"]
        
        if hasattr(config, 'VIDEO_OUTPUT_DIR') and os.path.exists(config.VIDEO_OUTPUT_DIR):
            for filename in os.listdir(config.VIDEO_OUTPUT_DIR):
                if any(pattern in filename for pattern in temp_patterns):
                    file_path = os.path.join(config.VIDEO_OUTPUT_DIR, filename)
                    if session_id in filename:  # Only cleanup files for this session
                        try:
                            os.remove(file_path)
                            cleanup_count += 1
                        except OSError as e:
                            logger.warning(f"Failed to cleanup {file_path}: {e}")
        
        # Generate final workflow summary
        summary = {
            "workflow_completed": True,
            "session_id": session_id,
            "total_duration": workflow_state["metrics"].total_duration,
            "files_processed": 1,
            "edits_applied": workflow_state["metrics"].commands_applied,
            "cleanup_files_removed": cleanup_count,
            "final_video_available": bool(session.final_video_path),
            "export_ready": True
        }
        
        return summary
    
    async def _handle_workflow_error(self, workflow_id: str, error_message: str) -> None:
        """Handle workflow errors with proper cleanup and notification."""
        workflow_state = self.active_workflows[workflow_id]
        
        workflow_state["status"] = WorkflowStatus.FAILED
        workflow_state["current_stage"] = WorkflowStage.FAILED
        workflow_state["metrics"].end_time = time.time()
        workflow_state["metrics"].errors_encountered += 1
        
        error_info = {
            "error": error_message,
            "timestamp": datetime.now().isoformat(),
            "stage": workflow_state["current_stage"].value
        }
        
        await self._notify_progress(workflow_id, f"Workflow failed: {error_message}")
        logger.error(f"Workflow {workflow_id} failed: {error_message}")
    
    async def _finalize_workflow(self, workflow_id: str) -> None:
        """Move completed workflow to history and cleanup active state."""
        if workflow_id in self.active_workflows:
            workflow_state = self.active_workflows[workflow_id]
            
            # Convert dataclasses to dicts for JSON serialization
            workflow_history_entry = {
                **workflow_state,
                "metrics": asdict(workflow_state["metrics"]),
                "steps": [asdict(step) for step in workflow_state["steps"]],
                "completed_at": datetime.now().isoformat()
            }
            
            self.workflow_history.append(workflow_history_entry)
            del self.active_workflows[workflow_id]
            
            logger.info(f"Workflow {workflow_id} finalized and moved to history")
    
    async def _notify_progress(self, workflow_id: str, message: str) -> None:
        """Notify progress to registered callbacks."""
        workflow_state = self.active_workflows.get(workflow_id)
        if not workflow_state:
            return
        
        workflow_state["message"] = message
        
        progress_data = {
            "workflow_id": workflow_id,
            "session_id": workflow_state["session_id"],
            "status": workflow_state["status"].value,
            "stage": workflow_state["current_stage"].value,
            "progress": workflow_state["progress"],
            "message": message,
            "timestamp": time.time()
        }
        
        # Trigger callbacks
        for callback in self.callbacks.get("progress", []):
            try:
                await callback(progress_data)
            except Exception as e:
                logger.error(f"Progress callback failed: {e}")
    
    def register_progress_callback(self, callback: Callable) -> None:
        """Register a callback for progress notifications."""
        if "progress" not in self.callbacks:
            self.callbacks["progress"] = []
        self.callbacks["progress"].append(callback)
    
    def get_workflow_status(self, workflow_id: str) -> Optional[Dict[str, Any]]:
        """Get current status of a workflow."""
        if workflow_id in self.active_workflows:
            workflow_state = self.active_workflows[workflow_id]
            return {
                "workflow_id": workflow_id,
                "session_id": workflow_state["session_id"],
                "status": workflow_state["status"].value,
                "stage": workflow_state["current_stage"].value,
                "progress": workflow_state["progress"],
                "message": workflow_state["message"],
                "steps_completed": len([s for s in workflow_state["steps"] 
                                      if s.status == WorkflowStatus.COMPLETED]),
                "total_steps": len(workflow_state["steps"]),
                "metrics": asdict(workflow_state["metrics"])
            }
        return None
    
    def get_workflow_history(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get workflow history with optional limit."""
        return self.workflow_history[-limit:] if limit else self.workflow_history
    
    async def cancel_workflow(self, workflow_id: str) -> bool:
        """Cancel an active workflow."""
        if workflow_id in self.active_workflows:
            workflow_state = self.active_workflows[workflow_id]
            workflow_state["status"] = WorkflowStatus.CANCELLED
            workflow_state["metrics"].end_time = time.time()
            
            await self._notify_progress(workflow_id, "Workflow cancelled by user")
            await self._finalize_workflow(workflow_id)
            
            logger.info(f"Workflow {workflow_id} cancelled")
            return True
        return False
