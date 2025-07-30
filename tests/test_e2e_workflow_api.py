"""
Comprehensive End-to-End Workflow API Integration Tests
Tests the complete E2E workflow functionality including REST endpoints,
WebSocket connections, and workflow orchestration.
"""

import pytest
import asyncio
import json
import time
from unittest.mock import Mock, AsyncMock, patch
from fastapi.testclient import TestClient
from fastapi.websockets import WebSocket
import sys
import os

# Add project root to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.api import app
from backend.workflow_orchestrator import WorkflowOrchestrator, WorkflowStatus, WorkflowStage
from backend.session_manager import SessionManager, SessionData


class TestE2EWorkflowEndpoints:
    """Test E2E workflow REST API endpoints."""
    
    @pytest.fixture
    def client(self):
        """Create FastAPI test client."""
        return TestClient(app)
    
    @pytest.fixture
    def mock_session(self):
        """Create mock session for testing."""
        session = Mock(spec=SessionData)
        session.session_id = "test_session_123"
        session.filename = "test_video.mp4"
        session.video_path = "/path/to/video.mp4"
        session.preview_path = "/path/to/preview.mp4"
        session.edits = []
        session.analysis = None
        session.suggestions = None
        return session
    
    def test_start_e2e_workflow_success(self, client, mock_session):
        """Test successful E2E workflow start."""
        session_id = "test_session_123"
        
        with patch('backend.api.session_manager.get_session', return_value=AsyncMock(return_value=mock_session)), \
             patch('backend.api.workflow_orchestrator.start_workflow', return_value=AsyncMock(return_value={
                 "status": "success",
                 "workflow_id": "workflow_123",
                 "session_id": session_id,
                 "workflow_config": {},
                 "user_preferences": {}
             })):
            
            response = client.post(f"/workflow/start/{session_id}", json={
                "workflow_config": {"quality": "high"},
                "user_preferences": {"style": "cinematic"}
            })
            
            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "success"
            assert data["message"] == "E2E workflow started successfully"
    
    def test_start_e2e_workflow_session_not_found(self, client):
        """Test E2E workflow start with nonexistent session."""
        session_id = "nonexistent_session"
        
        with patch('backend.api.session_manager.get_session', return_value=AsyncMock(return_value=None)):
            response = client.post(f"/workflow/start/{session_id}", json={})
            
            assert response.status_code == 404
            data = response.json()
            assert data["detail"] == "Session not found"
    
    def test_get_workflow_status_success(self, client):
        """Test getting workflow status successfully."""
        workflow_id = "test_workflow_123"
        
        mock_status = {
            "workflow_id": workflow_id,
            "status": "RUNNING",
            "stage": "ANALYZE_VIDEO",
            "progress": 50,
            "message": "Analyzing video content..."
        }
        
        with patch('backend.api.workflow_orchestrator.get_workflow_status', return_value=mock_status):
            response = client.get(f"/workflow/status/{workflow_id}")
            
            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "success"
            assert data["workflow_status"] == mock_status
    
    def test_get_workflow_status_not_found(self, client):
        """Test getting status of nonexistent workflow."""
        workflow_id = "nonexistent_workflow"
        
        with patch('backend.api.workflow_orchestrator.get_workflow_status', return_value=None):
            response = client.get(f"/workflow/status/{workflow_id}")
            
            assert response.status_code == 404
            data = response.json()
            assert data["detail"] == "Workflow not found"
    
    def test_cancel_workflow_success(self, client):
        """Test successful workflow cancellation."""
        workflow_id = "test_workflow_123"
        
        with patch('backend.api.workflow_orchestrator.cancel_workflow', return_value=AsyncMock(return_value=True)):
            response = client.post(f"/workflow/cancel/{workflow_id}")
            
            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "success"
            assert data["message"] == "Workflow cancelled successfully"
            assert data["workflow_id"] == workflow_id
    
    def test_cancel_workflow_not_found(self, client):
        """Test cancelling nonexistent workflow."""
        workflow_id = "nonexistent_workflow"
        
        with patch('backend.api.workflow_orchestrator.cancel_workflow', return_value=AsyncMock(return_value=False)):
            response = client.post(f"/workflow/cancel/{workflow_id}")
            
            assert response.status_code == 404
            data = response.json()
            assert data["detail"] == "Workflow not found or already completed"
    
    def test_get_workflow_history(self, client):
        """Test getting workflow history."""
        mock_history = [
            {
                "workflow_id": "workflow_1",
                "session_id": "session_1",
                "status": "COMPLETED",
                "start_time": time.time() - 3600,
                "end_time": time.time() - 3300
            },
            {
                "workflow_id": "workflow_2",
                "session_id": "session_2", 
                "status": "FAILED",
                "start_time": time.time() - 1800,
                "end_time": time.time() - 1500
            }
        ]
        
        with patch('backend.api.workflow_orchestrator.get_workflow_history', return_value=mock_history):
            response = client.get("/workflow/history?limit=10")
            
            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "success"
            assert data["workflow_history"] == mock_history
            assert data["total_returned"] == 2
    
    def test_batch_start_workflows_success(self, client, mock_session):
        """Test starting multiple workflows in batch."""
        session_ids = ["session_1", "session_2", "session_3"]
        
        with patch('backend.api.session_manager.get_session', return_value=AsyncMock(return_value=mock_session)), \
             patch('backend.api.workflow_orchestrator.start_workflow', return_value=AsyncMock(return_value={
                 "workflow_id": "test_workflow_id",
                 "status": "success"
             })):
            
            response = client.post("/workflow/batch_start", json={
                "session_ids": session_ids,
                "workflow_config": {"quality": "medium"}
            })
            
            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "completed"
            assert data["summary"]["total_requested"] == 3
            assert data["summary"]["successful_starts"] == 3
            assert data["summary"]["failed_starts"] == 0
    
    def test_batch_start_workflows_empty_list(self, client):
        """Test batch start with empty session list."""
        response = client.post("/workflow/batch_start", json={
            "session_ids": []
        })
        
        assert response.status_code == 400
        data = response.json()
        assert data["detail"] == "No session IDs provided"
    
    def test_batch_start_workflows_size_limit(self, client):
        """Test batch start with too many sessions."""
        session_ids = [f"session_{i}" for i in range(15)]  # Exceed limit of 10
        
        response = client.post("/workflow/batch_start", json={
            "session_ids": session_ids
        })
        
        assert response.status_code == 400
        data = response.json()
        assert data["detail"] == "Batch size cannot exceed 10 sessions"
    
    def test_get_active_workflows(self, client):
        """Test getting active workflows."""
        mock_active = [
            {
                "workflow_id": "workflow_1",
                "session_id": "session_1",
                "status": "RUNNING",
                "stage": "ANALYZE_VIDEO",
                "progress": 30
            },
            {
                "workflow_id": "workflow_2", 
                "session_id": "session_2",
                "status": "RUNNING",
                "stage": "GENERATE_SUGGESTIONS",
                "progress": 70
            }
        ]
        
        with patch('backend.api.workflow_orchestrator.active_workflows', {"workflow_1", "workflow_2"}), \
             patch('backend.api.workflow_orchestrator.get_workflow_status', side_effect=mock_active):
            
            response = client.get("/workflow/active")
            
            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "success"
            assert data["total_active"] == 2
            assert len(data["active_workflows"]) == 2


class TestE2EWorkflowWebSocket:
    """Test E2E workflow WebSocket functionality."""
    
    @pytest.fixture
    def client(self):
        """Create FastAPI test client."""
        return TestClient(app)
    
    def test_workflow_websocket_connection(self, client):
        """Test WebSocket connection for workflow progress."""
        workflow_id = "test_workflow_123"
        
        mock_status = {
            "workflow_id": workflow_id,
            "status": "RUNNING",
            "stage": "ANALYZE_VIDEO",
            "progress": 25,
            "message": "Analyzing video content..."
        }
        
        with patch('backend.api.workflow_orchestrator.get_workflow_status', return_value=mock_status):
            with client.websocket_connect(f"/ws/workflow/{workflow_id}") as websocket:
                # Should receive initial status
                data = websocket.receive_text()
                message = json.loads(data)
                
                assert message["type"] == "workflow_status"
                assert message["workflow_id"] == workflow_id
                assert message["status"] == "RUNNING"
    
    def test_workflow_websocket_ping_pong(self, client):
        """Test WebSocket ping/pong functionality."""
        workflow_id = "test_workflow_123"
        
        with patch('backend.api.workflow_orchestrator.get_workflow_status', return_value={}):
            with client.websocket_connect(f"/ws/workflow/{workflow_id}") as websocket:
                # Skip initial status message
                websocket.receive_text()
                
                # Send ping
                websocket.send_text(json.dumps({"type": "ping"}))
                
                # Should receive pong
                data = websocket.receive_text()
                message = json.loads(data)
                
                assert message["type"] == "pong"
                assert "timestamp" in message
    
    def test_workflow_websocket_nonexistent_workflow(self, client):
        """Test WebSocket connection for nonexistent workflow."""
        workflow_id = "nonexistent_workflow"
        
        with patch('backend.api.workflow_orchestrator.get_workflow_status', return_value=None):
            with client.websocket_connect(f"/ws/workflow/{workflow_id}") as websocket:
                # Should receive error message
                data = websocket.receive_text()
                message = json.loads(data)
                
                assert message["type"] == "error"
                assert "not found" in message["message"]


class TestE2EWorkflowIntegration:
    """Integration tests for complete E2E workflow functionality."""
    
    @pytest.fixture
    def client(self):
        """Create FastAPI test client."""
        return TestClient(app)
    
    @pytest.fixture
    def mock_session(self):
        """Create mock session for testing."""
        session = Mock(spec=SessionData)
        session.session_id = "integration_test_session"
        session.filename = "integration_test.mp4"
        session.video_path = "/path/to/integration_test.mp4"
        session.preview_path = "/path/to/integration_test_preview.mp4"
        session.edits = []
        session.analysis = None
        session.suggestions = None
        return session
    
    @pytest.mark.asyncio
    async def test_complete_e2e_workflow_lifecycle(self, client, mock_session):
        """Test complete E2E workflow from start to completion."""
        session_id = "integration_test_session"
        
        # Mock workflow orchestrator methods
        mock_workflow_id = "integration_workflow_123"
        
        # 1. Start workflow
        with patch('backend.api.session_manager.get_session', return_value=AsyncMock(return_value=mock_session)), \
             patch('backend.api.workflow_orchestrator.start_workflow', return_value=AsyncMock(return_value={
                 "status": "success",
                 "workflow_id": mock_workflow_id,
                 "session_id": session_id,
                 "workflow_config": {"quality": "high"},
                 "user_preferences": {"style": "professional"}
             })):
            
            start_response = client.post(f"/workflow/start/{session_id}", json={
                "workflow_config": {"quality": "high"},
                "user_preferences": {"style": "professional"}
            })
            
            assert start_response.status_code == 200
            start_data = start_response.json()
            assert start_data["status"] == "success"
            workflow_id = mock_workflow_id
        
        # 2. Check workflow status
        mock_running_status = {
            "workflow_id": workflow_id,
            "status": "RUNNING",
            "stage": "ANALYZE_VIDEO",
            "progress": 40,
            "message": "Analyzing video content..."
        }
        
        with patch('backend.api.workflow_orchestrator.get_workflow_status', return_value=mock_running_status):
            status_response = client.get(f"/workflow/status/{workflow_id}")
            
            assert status_response.status_code == 200
            status_data = status_response.json()
            assert status_data["workflow_status"]["status"] == "RUNNING"
            assert status_data["workflow_status"]["progress"] == 40
        
        # 3. Simulate workflow completion
        mock_completed_status = {
            "workflow_id": workflow_id,
            "status": "COMPLETED",
            "stage": "CLEANUP_EXPORT",
            "progress": 100,
            "message": "Workflow completed successfully"
        }
        
        with patch('backend.api.workflow_orchestrator.get_workflow_status', return_value=mock_completed_status):
            final_status_response = client.get(f"/workflow/status/{workflow_id}")
            
            assert final_status_response.status_code == 200
            final_status_data = final_status_response.json()
            assert final_status_data["workflow_status"]["status"] == "COMPLETED"
            assert final_status_data["workflow_status"]["progress"] == 100
        
        # 4. Verify workflow appears in history
        mock_history = [{
            "workflow_id": workflow_id,
            "session_id": session_id,
            "status": "COMPLETED",
            "start_time": time.time() - 300,
            "end_time": time.time(),
            "total_duration": 300,
            "stages_completed": 8
        }]
        
        with patch('backend.api.workflow_orchestrator.get_workflow_history', return_value=mock_history):
            history_response = client.get("/workflow/history")
            
            assert history_response.status_code == 200
            history_data = history_response.json()
            assert len(history_data["workflow_history"]) == 1
            assert history_data["workflow_history"][0]["workflow_id"] == workflow_id
            assert history_data["workflow_history"][0]["status"] == "COMPLETED"
    
    @pytest.mark.asyncio
    async def test_e2e_workflow_error_handling(self, client, mock_session):
        """Test E2E workflow error handling and recovery."""
        session_id = "error_test_session"
        
        # Test workflow start with session manager error
        with patch('backend.api.session_manager.get_session', side_effect=Exception("Database error")):
            response = client.post(f"/workflow/start/{session_id}", json={})
            
            assert response.status_code == 500
            data = response.json()
            assert "Workflow start failed" in data["detail"]
        
        # Test workflow status with orchestrator error
        workflow_id = "error_workflow_123"
        
        with patch('backend.api.workflow_orchestrator.get_workflow_status', side_effect=Exception("Status error")):
            response = client.get(f"/workflow/status/{workflow_id}")
            
            assert response.status_code == 500
            data = response.json()
            assert "Failed to get workflow status" in data["detail"]
        
        # Test workflow cancellation with orchestrator error
        with patch('backend.api.workflow_orchestrator.cancel_workflow', side_effect=Exception("Cancel error")):
            response = client.post(f"/workflow/cancel/{workflow_id}")
            
            assert response.status_code == 500
            data = response.json()
            assert "Failed to cancel workflow" in data["detail"]


class TestE2EWorkflowPerformance:
    """Performance and load tests for E2E workflow functionality."""
    
    @pytest.fixture
    def client(self):
        """Create FastAPI test client."""
        return TestClient(app)
    
    @pytest.fixture
    def mock_session(self):
        """Create mock session for testing."""
        session = Mock(spec=SessionData)
        session.session_id = "perf_test_session"
        session.filename = "perf_test.mp4"
        session.video_path = "/path/to/perf_test.mp4"
        session.preview_path = "/path/to/perf_test_preview.mp4"
        session.edits = []
        return session
    
    def test_concurrent_workflow_starts(self, client, mock_session):
        """Test starting multiple workflows concurrently."""
        session_ids = [f"concurrent_session_{i}" for i in range(5)]
        
        with patch('backend.api.session_manager.get_session', return_value=AsyncMock(return_value=mock_session)), \
             patch('backend.api.workflow_orchestrator.start_workflow', return_value=AsyncMock(return_value={
                 "status": "success",
                 "workflow_id": "concurrent_workflow",
                 "session_id": "test_session"
             })):
            
            # Start multiple workflows rapidly
            responses = []
            start_time = time.time()
            
            for session_id in session_ids:
                response = client.post(f"/workflow/start/{session_id}", json={})
                responses.append(response)
            
            end_time = time.time()
            
            # Verify all requests succeeded
            for response in responses:
                assert response.status_code == 200
                data = response.json()
                assert data["status"] == "success"
            
            # Verify reasonable response time (under 5 seconds for 5 requests)
            total_time = end_time - start_time
            assert total_time < 5.0
    
    def test_workflow_status_polling_performance(self, client):
        """Test performance of frequent workflow status polling."""
        workflow_id = "polling_test_workflow"
        
        mock_status = {
            "workflow_id": workflow_id,
            "status": "RUNNING",
            "stage": "ANALYZE_VIDEO",
            "progress": 50,
            "message": "Analyzing video content..."
        }
        
        with patch('backend.api.workflow_orchestrator.get_workflow_status', return_value=mock_status):
            # Poll status rapidly
            start_time = time.time()
            
            for _ in range(20):  # 20 rapid polls
                response = client.get(f"/workflow/status/{workflow_id}")
                assert response.status_code == 200
            
            end_time = time.time()
            
            # Verify reasonable response time (under 2 seconds for 20 polls)
            total_time = end_time - start_time
            assert total_time < 2.0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
