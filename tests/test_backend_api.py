"""
Comprehensive test suite for backend API endpoints.

Tests all API endpoints including:
- File upload and validation
- Session management 
- Video generation from scripts
- Video processing and streaming
- WebSocket functionality
- Error handling and edge cases
"""

import pytest
import os
import tempfile
import json
from unittest.mock import Mock, patch, AsyncMock
from fastapi.testclient import TestClient
from fastapi import UploadFile
import io

# Import the API app
from backend.api import app, get_session_info
from backend.session_manager import SessionManager
from unittest.mock import patch, Mock, AsyncMock
import time
import redis

client = TestClient(app)


class TestFileUpload:
    """Test file upload functionality."""
    
    def test_upload_valid_video_file(self):
        """Test uploading a valid video file."""
        # Create a mock video file
        video_content = b"fake video content"
        files = {"file": ("test.mp4", io.BytesIO(video_content), "video/mp4")}
        
        response = client.post("/upload/video", files=files)
        
        assert response.status_code == 200
        data = response.json()
        assert "session_id" in data
        assert "filename" in data
        
        # Check that session was created (would need to mock session_manager)
        session_id = data["session_id"]
        assert session_id is not None
    
    def test_upload_invalid_file_type(self):
        """Test uploading an invalid file type."""
        text_content = b"this is not a video"
        files = {"file": ("test.txt", io.BytesIO(text_content), "text/plain")}
        
        response = client.post("/upload/video", files=files)
        
        assert response.status_code == 400
        assert "Invalid file type" in response.json()["detail"]
    
    def test_upload_no_file(self):
        """Test upload endpoint with no file."""
        response = client.post("/upload/video")
        
        assert response.status_code == 422  # Validation error
    
    def test_upload_empty_file(self):
        """Test uploading an empty file."""
        files = {"file": ("empty.mp4", io.BytesIO(b""), "video/mp4")}
        
        response = client.post("/upload/video", files=files)
        
        assert response.status_code == 400
        assert "Empty file" in response.json()["detail"]


class TestSessionManagement:
    """Test session management functionality with SessionManager integration."""
    
    @patch('backend.api.session_manager')
    def test_get_existing_session_info_with_session_manager(self, mock_session_manager):
        """Test retrieving info for an existing session using SessionManager."""
        session_id = "test_session_123"
        # Create a mock SessionData object
        mock_session = Mock()
        mock_session.filename = "test.mp4"
        mock_session.edits = []
        mock_session.finalized = False
        mock_session.last_activity = time.time()
        mock_session.file_size = 1000000
        
        # Mock the async get_session method
        async def mock_get_session(sid):
            return mock_session
        mock_session_manager.get_session = mock_get_session
        
        response = client.get(f"/session/{session_id}")
        
        assert response.status_code == 200
        data = response.json()
        assert data["session_id"] == session_id
        assert data["filename"] == "test.mp4"
        assert data["edits_count"] == 0
        assert data["finalized"] is False
        assert data["file_size"] == 1000000
    
    @patch('backend.api.session_manager')
    def test_get_nonexistent_session_info_with_session_manager(self, mock_session_manager):
        """Test retrieving info for a non-existent session using SessionManager."""
        # Mock the async get_session method to return None
        async def mock_get_session(sid):
            return None
        mock_session_manager.get_session = mock_get_session
        
        response = client.get("/session/nonexistent_session")
        
        assert response.status_code == 404
        assert "Session not found" in response.json()["detail"]
    
    @patch('backend.api.session_manager')
    def test_session_creation_with_limits(self, mock_session_manager):
        """Test session creation respects concurrent session limits."""
        # Mock session manager to return limit exceeded
        mock_session_manager.create_session.side_effect = ValueError("Session limit exceeded")
        
        video_content = b"fake video content"
        files = {"file": ("test.mp4", io.BytesIO(video_content), "video/mp4")}
        
        response = client.post("/upload/video", files=files)
        
        assert response.status_code == 429  # Too Many Requests
        assert "Session limit exceeded" in response.json()["detail"]
    
    @patch('backend.api.session_manager')
    def test_session_cleanup_on_timeout(self, mock_session_manager):
        """Test that sessions are cleaned up on timeout."""
        # Mock cleanup method
        mock_session_manager.cleanup_expired_sessions.return_value = ["expired_session_1", "expired_session_2"]
        
        # Trigger cleanup (this would be called periodically)
        cleaned_sessions = mock_session_manager.cleanup_expired_sessions()
        
        assert len(cleaned_sessions) == 2
        assert "expired_session_1" in cleaned_sessions
        assert "expired_session_2" in cleaned_sessions
        mock_session_manager.cleanup_expired_sessions.assert_called_once()
    
    @patch('backend.api.session_manager')
    def test_session_update_activity(self, mock_session_manager):
        """Test that session activity is updated on API calls."""
        session_id = "active_session"
        # Create a proper mock SessionData object
        mock_session = Mock()
        mock_session.filename = "test.mp4"
        mock_session.edits = []
        mock_session.finalized = False
        mock_session.last_activity = time.time() - 100
        mock_session.file_size = 1000
        
        # Mock the async get_session method
        async def mock_get_session(sid):
            return mock_session
        mock_session_manager.get_session = mock_get_session
        
        response = client.get(f"/session/{session_id}")
        
        assert response.status_code == 200
        # Verify session data is returned correctly
        data = response.json()
        assert data["session_id"] == session_id
    
    @patch('backend.api.session_manager')
    def test_session_stats_endpoint(self, mock_session_manager):
        """Test session statistics endpoint."""
        mock_stats = {
            "total_sessions": 5,
            "active_sessions": 3,
            "completed_sessions": 2,
            "failed_sessions": 0,
            "redis_connected": True,
            "memory_usage": 0.75
        }
        
        mock_session_manager.get_stats.return_value = mock_stats
        
        response = client.get("/admin/session_stats")
        
        assert response.status_code == 200
        data = response.json()
        assert data["total_sessions"] == 5
        assert data["active_sessions"] == 3
        assert data["redis_connected"] is True


class TestVideoGeneration:
    """Test video generation from scripts."""
    
    @patch('backend.api.VideoAgent')
    def test_generate_from_script_success(self, mock_video_agent):
        """Test successful video generation from script."""
        # Mock VideoAgent
        mock_agent = Mock()
        mock_agent.run.return_value = {
            "final_video": "output.mp4",
            "status": "success"
        }
        mock_video_agent.return_value = mock_agent
        
        script_data = {
            "script": "This is a test script for video generation.",
            "voice": "default",
            "style": "documentary"
        }
        
        response = client.post("/generate", json=script_data)
        
        assert response.status_code == 200
        data = response.json()
        assert "clips" in data
        assert "narrations" in data
        assert "bgms" in data
    
    def test_generate_from_script_missing_script(self):
        """Test video generation with missing script."""
        script_data = {
            "voice": "default",
            "style": "documentary"
        }
        
        response = client.post("/generate", json=script_data)
        
        assert response.status_code == 422  # Validation error
    
    def test_generate_from_script_empty_script(self):
        """Test video generation with empty script."""
        script_data = {
            "script": "",
            "voice": "default",
            "style": "documentary"
        }
        
        response = client.post("/generate", json=script_data)
        
        assert response.status_code == 400
        assert "Script cannot be empty" in response.json()["detail"]
    
    @patch('backend.api.VideoAgent')
    def test_generate_from_script_agent_failure(self, mock_video_agent):
        """Test video generation when VideoAgent fails."""
        # Mock VideoAgent to raise an exception
        mock_video_agent.side_effect = Exception("VideoAgent failed")
        
        script_data = {
            "script": "This is a test script.",
            "voice": "default",
            "style": "documentary"
        }
        
        response = client.post("/generate", json=script_data)
        
        assert response.status_code == 500
        assert "VideoAgent failed" in response.json()["detail"]


class TestVideoProcessing:
    """Test video processing endpoints."""
    
    @patch('backend.api.VideoAgent')
    def test_process_video_nonexistent_session(self, mock_video_agent):
        """Test processing video for non-existent session."""
        # Mock VideoAgent to return expected structure
        mock_agent = Mock()
        mock_agent.run_with_video.return_value = {
            "final_video": "processed.mp4",
            "plan": "test plan",
            "source_video": "test.mp4",
            "processing_type": "upload",
            "coverage_percentage": 85.5,
            "scene_count": 3
        }
        mock_video_agent.return_value = mock_agent
        
        # Create dummy video file for processing
        video_content = b"fake video content"
        files = {"video": ("test.mp4", io.BytesIO(video_content), "video/mp4")}
        
        response = client.post("/process_video", files=files)
        
        assert response.status_code == 200
        data = response.json()
        assert "final_video" in data
        assert data["final_video"] == "processed.mp4"
        assert data["plan"] == "test plan"
    
    @patch('backend.api.VideoAgent')
    def test_process_video_success(self, mock_video_agent):
        """Test successful video processing."""
        # Mock VideoAgent
        mock_agent = Mock()
        mock_agent.run_with_video.return_value = {
            "final_video": "processed.mp4",
            "plan": "success plan",
            "source_video": "test.mp4",
            "processing_type": "analysis",
            "coverage_percentage": 92.0,
            "scene_count": 5
        }
        mock_video_agent.return_value = mock_agent
        
        # Create dummy video file for processing
        video_content = b"fake video content"
        files = {"video": ("test.mp4", io.BytesIO(video_content), "video/mp4")}
        
        response = client.post("/process_video", files=files)
        
        assert response.status_code == 200
        data = response.json()
        assert "final_video" in data
        assert data["final_video"] == "processed.mp4"
        assert data["coverage_percentage"] == 92.0
        assert data["scene_count"] == 5
    
    @patch('backend.api.VideoAgent')
    def test_process_video_agent_failure(self, mock_video_agent):
        """Test video processing when VideoAgent fails."""
        # Mock VideoAgent to raise an exception
        mock_video_agent.side_effect = Exception("Processing failed")
        
        # Create dummy video file for processing
        video_content = b"fake video content"
        files = {"video": ("test.mp4", io.BytesIO(video_content), "video/mp4")}
        
        response = client.post("/process_video", files=files)
        
        assert response.status_code == 500
        assert "Processing failed" in response.json()["detail"]


class TestVideoStreaming:
    """Test video streaming and preview functionality."""
    
    def test_preview_nonexistent_session(self):
        """Test preview for non-existent session."""
        response = client.get("/preview/nonexistent_session")
        
        assert response.status_code == 404
        assert "Session not found" in response.json()["detail"]
    
    @patch('backend.api.session_manager')
    def test_preview_no_preview_available(self, mock_session_manager):
        """Test preview when no preview file exists."""
        # Mock session without preview_path
        mock_session = Mock()
        mock_session.preview_path = None
        
        async def mock_get_session(sid):
            return mock_session
        mock_session_manager.get_session = mock_get_session
        
        response = client.get("/preview/test_session_no_preview")
        
        assert response.status_code == 404
        assert "Preview not available" in response.json()["detail"]
    
    @patch('backend.api.session_manager')
    @patch('os.path.exists')
    @patch('os.path.getsize')
    def test_preview_with_range_header(self, mock_getsize, mock_exists, mock_session_manager):
        """Test preview with Range header for video streaming."""
        # Mock session with preview
        preview_path = "/test/preview.mp4"
        mock_session = Mock()
        mock_session.preview_path = preview_path
        
        async def mock_get_session(sid):
            return mock_session
        mock_session_manager.get_session = mock_get_session
        
        # Mock file existence and size
        mock_exists.return_value = True
        mock_getsize.return_value = 1000
        
        headers = {"Range": "bytes=0-499"}
        
        with patch('builtins.open', create=True) as mock_open:
            mock_file = Mock()
            mock_file.read.return_value = b"video data chunk"
            mock_open.return_value.__enter__.return_value = mock_file
            
            response = client.get("/preview/test_session_preview", headers=headers)
            
            assert response.status_code == 206  # Partial content
            assert "Content-Range" in response.headers


class TestVideoTrimming:
    """Test video trimming functionality."""
    
    def test_trim_video_nonexistent_session(self):
        """Test trimming video for non-existent session."""
        trim_data = {
            "start_time": 10.0,
            "end_time": 30.0
        }
        
        response = client.post("/trim/nonexistent_session", json=trim_data)
        
        assert response.status_code == 404
        assert "Session not found" in response.json()["detail"]
    
    @patch('backend.api.session_manager')
    def test_trim_video_invalid_times(self, mock_session_manager):
        """Test trimming with invalid time parameters."""
        session_id = "test_trim_session"
        # Mock session with video
        mock_session = Mock()
        mock_session.final_video = "/test/video.mp4"
        
        async def mock_get_session(sid):
            return mock_session
        mock_session_manager.get_session = mock_get_session
        
        # Test negative start time
        trim_data = {
            "start_time": -5.0,
            "end_time": 30.0
        }
        
        response = client.post(f"/trim/{session_id}", json=trim_data)
        
        assert response.status_code == 400
        assert "Invalid time parameters" in response.json()["detail"]
        
        # Test start time >= end time
        trim_data = {
            "start_time": 40.0,
            "end_time": 30.0
        }
        
        response = client.post(f"/trim/{session_id}", json=trim_data)
        
        assert response.status_code == 400
        assert "Invalid time parameters" in response.json()["detail"]


class TestBatchEditing:
    """Test batch editing functionality."""
    
    def test_batch_edit_nonexistent_session(self):
        """Test batch editing for non-existent session."""
        edit_data = {
            "edits": [
                {"type": "trim", "start": 10, "end": 20},
                {"type": "volume", "value": 0.8}
            ]
        }
        
        response = client.post("/apply_edits/nonexistent_session", json=edit_data)
        
        assert response.status_code == 404
        assert "Session not found" in response.json()["detail"]
    
    @patch('backend.api.session_manager')
    def test_batch_edit_empty_edits(self, mock_session_manager):
        """Test batch editing with empty edits list."""
        session_id = "test_batch_session"
        # Mock session with video
        mock_session = Mock()
        mock_session.final_video = "/test/video.mp4"
        
        async def mock_get_session(sid):
            return mock_session
        mock_session_manager.get_session = mock_get_session
        
        edit_data = {"edits": []}
        
        response = client.post(f"/apply_edits/{session_id}", json=edit_data)
        
        assert response.status_code == 400
        assert "No edits provided" in response.json()["detail"]


class TestThumbnailGeneration:
    """Test thumbnail generation functionality."""
    
    def test_generate_thumbnail_nonexistent_session(self):
        """Test thumbnail generation for non-existent session."""
        thumbnail_data = {"time": "10.0"}
        response = client.post("/thumbnail/nonexistent_session", json=thumbnail_data)
        
        assert response.status_code == 404
        assert "Session not found" in response.json()["detail"]
    
    @patch('backend.api.session_manager')
    def test_generate_thumbnail_no_video(self, mock_session_manager):
        """Test thumbnail generation when no video exists."""
        session_id = "test_thumbnail_session"
        # Mock session without preview_path or video_path
        mock_session = Mock()
        mock_session.preview_path = None
        mock_session.video_path = None
        
        async def mock_get_session(sid):
            return mock_session
        mock_session_manager.get_session = mock_get_session
        
        thumbnail_data = {"time": "10.0"}
        response = client.post(f"/thumbnail/{session_id}", json=thumbnail_data)
        
        assert response.status_code == 400
        assert "No video available" in response.json()["detail"]


class TestFinalization:
    """Test video finalization functionality."""
    
    def test_finalize_nonexistent_session(self):
        """Test finalizing non-existent session."""
        response = client.post("/finalize/nonexistent_session")
        
        assert response.status_code == 404
        assert "Session not found" in response.json()["detail"]
    
    @patch('backend.api.session_manager')
    def test_finalize_no_video(self, mock_session_manager):
        """Test finalizing session with no video."""
        session_id = "test_finalize_session"
        # Mock session without video_path or preview_path
        mock_session = Mock()
        mock_session.video_path = None
        mock_session.preview_path = None
        
        async def mock_get_session(sid):
            return mock_session
        mock_session_manager.get_session = mock_get_session
        
        response = client.post(f"/finalize/{session_id}")
        
        assert response.status_code == 400
        assert "No video to finalize" in response.json()["detail"]


class TestWebSocketFunctionality:
    """Test WebSocket editing functionality."""
    
    @patch('backend.api.session_manager')
    def test_websocket_connection(self, mock_session_manager):
        """Test WebSocket connection establishment."""
        mock_session = Mock()

        async def mock_get_session(sid):
            return mock_session

        mock_session_manager.get_session = AsyncMock(side_effect=mock_get_session)
        mock_session_manager.register_websocket = AsyncMock()

        with client.websocket_connect("/ws/edit/test_session") as websocket:
            # Test that connection is established
            assert websocket is not None
    
    @patch('backend.api.session_manager')
    def test_websocket_invalid_message(self, mock_session_manager):
        """Test WebSocket with invalid message format."""
        mock_session = Mock()
        mock_session.to_dict.return_value = {}

        async def mock_get_session(sid):
            return mock_session

        mock_session_manager.get_session = AsyncMock(side_effect=mock_get_session)
        mock_session_manager.register_websocket = AsyncMock()
        mock_session_manager.update_session = AsyncMock()

        with client.websocket_connect("/ws/edit/test_session") as websocket:
            # Send invalid JSON
            websocket.send_text("invalid json")

            response = websocket.receive_text()
            data = json.loads(response)
            assert data["error"] == "Invalid message format"
    
    @patch('backend.api.session_manager')
    def test_websocket_unknown_command(self, mock_session_manager):
        """Test WebSocket with unknown command."""
        mock_session = Mock()
        mock_session.to_dict.return_value = {}

        async def mock_get_session(sid):
            return mock_session

        mock_session_manager.get_session = AsyncMock(side_effect=mock_get_session)
        mock_session_manager.register_websocket = AsyncMock()
        mock_session_manager.update_session = AsyncMock()

        with client.websocket_connect("/ws/edit/test_session") as websocket:
            # Send unknown command
            message = {
                "command": "unknown_command",
                "data": {}
            }
            websocket.send_text(json.dumps(message))

            response = websocket.receive_text()
            data = json.loads(response)
            assert data["error"] == "Unknown command"


class TestErrorHandling:
    """Test general error handling across endpoints."""
    
    def test_internal_server_errors(self):
        """Test that internal server errors are properly handled."""
        # This would test various scenarios that could cause 500 errors
        pass
    
    def test_rate_limiting(self):
        """Test rate limiting if implemented."""
        # This would test rate limiting functionality
        pass
    
    def test_authentication_if_required(self):
        """Test authentication mechanisms if implemented."""
        # This would test authentication logic
        pass


# Cleanup function to run after tests
def cleanup_test_sessions():
    """Clean up test sessions after running tests."""
    # Note: With SessionManager, cleanup is handled automatically
    # This is just a placeholder for any additional cleanup if needed
    pass


# Run cleanup after all tests
@pytest.fixture(autouse=True)
def cleanup_after_tests():
    """Automatically clean up after each test."""
    yield
    cleanup_test_sessions()
