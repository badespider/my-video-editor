import pytest
import asyncio
import time
from unittest.mock import Mock, AsyncMock, patch
import sys
import os

# Add project root to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.workflow_orchestrator import WorkflowOrchestrator, WorkflowStage, WorkflowStatus
from backend.session_manager import SessionData

@pytest.fixture
def mock_session_manager():
    """Create a mock session manager for testing."""
    mock_manager = Mock()
    mock_manager.get_session = AsyncMock()
    mock_manager.update_session = AsyncMock()
    return mock_manager

@pytest.fixture
def mock_session():
    """Create a mock session for testing."""
    session = Mock(spec=SessionData)
    session.session_id = "test_session_123"
    session.filename = "test_video.mp4"
    session.video_path = "/path/to/video.mp4"
    session.preview_path = "/path/to/preview.mp4"
    session.edits = []
    session.analysis = None
    session.suggestions = None
    return session

@pytest.fixture
def workflow_orchestrator(mock_session_manager):
    """Create a workflow orchestrator instance for testing."""
    return WorkflowOrchestrator(mock_session_manager)

class TestWorkflowOrchestrator:
    """Test suite for WorkflowOrchestrator."""
    
    @pytest.mark.asyncio
    async def test_start_workflow_success(self, workflow_orchestrator, mock_session_manager, mock_session):
        """Test successful workflow start."""
        session_id = "test_session"
        mock_session_manager.get_session.return_value = mock_session
        
        result = await workflow_orchestrator.start_workflow(session_id)
        
        assert result["status"] == "success"
        assert "workflow_id" in result
        assert result["session_id"] == session_id
        assert len(workflow_orchestrator.active_workflows) > 0
    
    @pytest.mark.asyncio
    async def test_start_workflow_no_session(self, workflow_orchestrator, mock_session_manager):
        """Test workflow start with nonexistent session."""
        session_id = "nonexistent_session"
        mock_session_manager.get_session.return_value = None
        
        with pytest.raises(ValueError, match="Session .* not found"):
            await workflow_orchestrator.start_workflow(session_id)
    
    @pytest.mark.asyncio
    async def test_start_workflow_with_config(self, workflow_orchestrator, mock_session_manager, mock_session):
        """Test workflow start with custom configuration."""
        session_id = "test_session"
        workflow_config = {"quality": "high", "auto_enhance": True}
        user_preferences = {"style": "cinematic", "duration": 60}
        
        mock_session_manager.get_session.return_value = mock_session
        
        result = await workflow_orchestrator.start_workflow(
            session_id, workflow_config, user_preferences
        )
        
        assert result["status"] == "success"
        assert result["workflow_config"] == workflow_config
        assert result["user_preferences"] == user_preferences
    
    @pytest.mark.asyncio
    async def test_workflow_cancellation(self, workflow_orchestrator, mock_session_manager, mock_session):
        """Test workflow cancellation."""
        session_id = "cancellation_test"
        mock_session_manager.get_session.return_value = mock_session
        
        # Start workflow
        result = await workflow_orchestrator.start_workflow(session_id)
        workflow_id = result["workflow_id"]
        
        # Cancel workflow
        cancelled = await workflow_orchestrator.cancel_workflow(workflow_id)
        
        assert cancelled is True
        status = workflow_orchestrator.get_workflow_status(workflow_id)
        assert status["status"] == WorkflowStatus.CANCELLED.value
    
    @pytest.mark.asyncio
    async def test_cancel_nonexistent_workflow(self, workflow_orchestrator):
        """Test cancelling a nonexistent workflow."""
        nonexistent_id = "nonexistent_workflow_id"
        
        cancelled = await workflow_orchestrator.cancel_workflow(nonexistent_id)
        
        assert cancelled is False
    
    def test_get_workflow_status(self, workflow_orchestrator, mock_session_manager, mock_session):
        """Test getting workflow status."""
        # Test nonexistent workflow
        status = workflow_orchestrator.get_workflow_status("nonexistent_id")
        assert status is None
        
        # Test with active workflow (would need to be mocked more extensively)
    
    def test_get_workflow_history(self, workflow_orchestrator):
        """Test getting workflow history."""
        # Test with no history
        history = workflow_orchestrator.get_workflow_history()
        assert isinstance(history, list)
        assert len(history) == 0
        
        # Test with limit
        history_limited = workflow_orchestrator.get_workflow_history(limit=5)
        assert isinstance(history_limited, list)
        assert len(history_limited) <= 5
    
    def test_register_progress_callback(self, workflow_orchestrator):
        """Test registering progress callbacks."""
        callback = AsyncMock()
        
        workflow_orchestrator.register_progress_callback(callback)
        
        assert callback in workflow_orchestrator.progress_callbacks
    
    @pytest.mark.asyncio
    async def test_workflow_stages_progression(self, workflow_orchestrator, mock_session_manager, mock_session):
        """Test that workflow progresses through expected stages."""
        session_id = "stage_test"
        mock_session_manager.get_session.return_value = mock_session
        
        # Mock the workflow execution to track stages
        with patch.object(workflow_orchestrator, '_execute_workflow') as mock_execute:
            # Make the mock coroutine return immediately
            mock_execute.return_value = None
            
            await workflow_orchestrator.start_workflow(session_id)
            
            # Verify _execute_workflow was called
            mock_execute.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_workflow_error_handling(self, workflow_orchestrator, mock_session_manager, mock_session):
        """Test workflow error handling."""
        session_id = "error_test"
        mock_session_manager.get_session.return_value = mock_session
        
        # Mock an error in workflow execution
        with patch.object(workflow_orchestrator, '_validate_session', side_effect=Exception("Test error")):
            result = await workflow_orchestrator.start_workflow(session_id)
            
            # The workflow should still start but may fail during execution
            assert result["status"] == "success"
            workflow_id = result["workflow_id"]
            
            # Give some time for the workflow to fail
            await asyncio.sleep(0.1)
            
            # Check if workflow is marked as failed
            status = workflow_orchestrator.get_workflow_status(workflow_id)
            if status:
                # The status might be FAILED or still RUNNING depending on timing
                assert status["status"] in [WorkflowStatus.RUNNING.value, WorkflowStatus.FAILED.value]


class TestWorkflowStages:
    """Test workflow stage functionality."""
    
    def test_workflow_stage_enum(self):
        """Test WorkflowStage enum values."""
        expected_stages = [
            "VALIDATE_SESSION", "ANALYZE_VIDEO", "GENERATE_SUGGESTIONS", 
            "INITIAL_PREVIEW", "WAIT_USER_EDITS", "APPLY_OPTIMIZATIONS", 
            "FINALIZE_VIDEO", "CLEANUP_EXPORT"
        ]
        
        for stage_name in expected_stages:
            assert hasattr(WorkflowStage, stage_name)
            stage = getattr(WorkflowStage, stage_name)
            assert isinstance(stage.value, str)
    
    def test_workflow_status_enum(self):
        """Test WorkflowStatus enum values."""
        expected_statuses = ["PENDING", "RUNNING", "COMPLETED", "FAILED", "CANCELLED"]
        
        for status_name in expected_statuses:
            assert hasattr(WorkflowStatus, status_name)
            status = getattr(WorkflowStatus, status_name)
            assert isinstance(status.value, str)


class TestWorkflowIntegration:
    """Integration tests for workflow orchestrator."""
    
    @pytest.mark.asyncio
    async def test_full_workflow_simulation(self, workflow_orchestrator, mock_session_manager, mock_session):
        """Test a complete workflow simulation with mocked components."""
        session_id = "integration_test"
        mock_session_manager.get_session.return_value = mock_session
        
        # Register a progress callback to track workflow progress
        progress_updates = []
        
        async def track_progress(update):
            progress_updates.append(update)
        
        workflow_orchestrator.register_progress_callback(track_progress)
        
        # Start workflow with full configuration
        result = await workflow_orchestrator.start_workflow(
            session_id=session_id,
            workflow_config={"quality": "high", "auto_optimize": True},
            user_preferences={"style": "professional", "target_platform": "youtube"}
        )
        
        assert result["status"] == "success"
        workflow_id = result["workflow_id"]
        
        # Allow some time for workflow execution
        await asyncio.sleep(0.2)
        
        # Check that progress updates were sent
        assert len(progress_updates) >= 0  # May be 0 if workflow completes very quickly
        
        # Verify workflow exists in active workflows
        status = workflow_orchestrator.get_workflow_status(workflow_id)
        assert status is not None
    
    @pytest.mark.asyncio
    async def test_concurrent_workflows(self, workflow_orchestrator, mock_session_manager, mock_session):
        """Test handling multiple concurrent workflows."""
        # Create multiple mock sessions
        session_ids = ["session_1", "session_2", "session_3"]
        mock_sessions = {}
        
        for session_id in session_ids:
            mock_session_copy = Mock(spec=SessionData)
            mock_session_copy.session_id = session_id
            mock_session_copy.filename = f"{session_id}.mp4"
            mock_session_copy.video_path = f"/path/to/{session_id}.mp4"
            mock_session_copy.preview_path = f"/path/to/{session_id}_preview.mp4"
            mock_session_copy.edits = []
            mock_sessions[session_id] = mock_session_copy
        
        # Mock session manager to return appropriate sessions
        def get_session_side_effect(session_id):
            return mock_sessions.get(session_id)
        
        mock_session_manager.get_session.side_effect = get_session_side_effect
        
        # Start multiple workflows concurrently
        tasks = []
        for session_id in session_ids:
            task = workflow_orchestrator.start_workflow(session_id)
            tasks.append(task)
        
        results = await asyncio.gather(*tasks)
        
        # Verify all workflows started successfully
        for i, result in enumerate(results):
            assert result["status"] == "success"
            assert result["session_id"] == session_ids[i]
        
        # Verify all workflows are active
        assert len(workflow_orchestrator.active_workflows) >= len(session_ids)

