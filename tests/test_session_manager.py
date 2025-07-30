"""
Comprehensive unit tests for session manager to close testing gaps.
Rule 4.1: Close Testing Gaps
"""

import pytest
import asyncio
import time
from unittest.mock import Mock, patch, AsyncMock
from backend.session_manager import (
    SessionManager, SessionData, InMemorySessionStore, 
    RedisSessionStore, session_manager
)
import config

class TestSessionData:
    """Test SessionData dataclass functionality."""
    
    def test_session_data_creation(self):
        """Test creating session data with default values."""
        session = SessionData(session_id="test_123")
        
        assert session.session_id == "test_123"
        assert session.edits == []
        assert session.created_at > 0
        assert session.last_activity > 0
        assert not session.finalized
    
    def test_session_data_to_dict(self):
        """Test converting session data to dictionary."""
        session = SessionData(
            session_id="test_456",
            filename="video.mp4",
            file_size=1000000
        )
        
        data_dict = session.to_dict()
        assert isinstance(data_dict, dict)
        assert data_dict["session_id"] == "test_456"
        assert data_dict["filename"] == "video.mp4"
        assert data_dict["file_size"] == 1000000
    
    def test_session_data_from_dict(self):
        """Test creating session data from dictionary."""
        data = {
            "session_id": "test_789",
            "filename": "test.mp4",
            "file_size": 500000,
            "video_duration": 120.0,
            "edits": [{"type": "trim", "start": 10, "end": 20}]
        }
        
        session = SessionData.from_dict(data)
        assert session.session_id == "test_789"
        assert session.filename == "test.mp4"
        assert session.file_size == 500000
        assert session.video_duration == 120.0
        assert len(session.edits) == 1
    
    def test_update_activity(self):
        """Test updating last activity timestamp."""
        session = SessionData(session_id="test_activity")
        original_time = session.last_activity
        
        time.sleep(0.01)  # Small delay to ensure time difference
        session.update_activity()
        
        assert session.last_activity > original_time


class TestInMemorySessionStore:
    """Test in-memory session store functionality."""
    
    @pytest.fixture
    def store(self):
        """Create a fresh in-memory store for each test."""
        return InMemorySessionStore()
    
    @pytest.mark.asyncio
    async def test_set_and_get_session(self, store):
        """Test setting and getting session data."""
        session = SessionData(session_id="mem_test_1", filename="test.mp4")
        
        result = await store.set("mem_test_1", session)
        assert result is True
        
        retrieved = await store.get("mem_test_1")
        assert retrieved is not None
        assert retrieved.session_id == "mem_test_1"
        assert retrieved.filename == "test.mp4"
    
    @pytest.mark.asyncio
    async def test_delete_session(self, store):
        """Test deleting session data."""
        session = SessionData(session_id="mem_test_2")
        await store.set("mem_test_2", session)
        
        # Verify session exists
        retrieved = await store.get("mem_test_2")
        assert retrieved is not None
        
        # Delete session
        result = await store.delete("mem_test_2")
        assert result is True
        
        # Verify session is gone
        retrieved = await store.get("mem_test_2")
        assert retrieved is None
    
    @pytest.mark.asyncio
    async def test_count_sessions(self, store):
        """Test counting sessions."""
        initial_count = await store.count()
        
        # Add sessions
        for i in range(3):
            session = SessionData(session_id=f"count_test_{i}")
            await store.set(f"count_test_{i}", session)
        
        final_count = await store.count()
        assert final_count == initial_count + 3
    
    @pytest.mark.asyncio
    async def test_list_expired_sessions(self, store):
        """Test listing expired sessions."""
        # Create sessions with different activity times
        current_time = time.time()
        
        # Fresh session
        fresh_session = SessionData(session_id="fresh")
        fresh_session.last_activity = current_time
        await store.set("fresh", fresh_session)
        
        # Expired session
        expired_session = SessionData(session_id="expired")
        expired_session.last_activity = current_time - 3600  # 1 hour ago
        await store.set("expired", expired_session)
        
        # List expired with 30 minute timeout
        expired_list = await store.list_expired(1800)
        
        assert "expired" in expired_list
        assert "fresh" not in expired_list


@pytest.mark.skipif(not hasattr(config, 'USE_REDIS') or not config.USE_REDIS, 
                   reason="Redis not configured")
class TestRedisSessionStore:
    """Test Redis session store functionality."""
    
    @pytest.fixture
    def mock_redis_pool(self):
        """Mock Redis connection pool."""
        return Mock()
    
    @pytest.fixture
    def store(self, mock_redis_pool):
        """Create Redis store with mocked connection."""
        with patch('backend.session_manager.redis') as mock_redis:
            mock_redis_instance = Mock()
            mock_redis.Redis.return_value = mock_redis_instance
            
            store = RedisSessionStore(mock_redis_pool)
            store.redis = mock_redis_instance
            return store
    
    @pytest.mark.asyncio
    async def test_redis_set_and_get(self, store):
        """Test Redis set and get operations."""
        session = SessionData(session_id="redis_test_1", filename="video.mp4")
        
        # Mock Redis operations
        store.redis.setex = AsyncMock(return_value=True)
        store.redis.get = AsyncMock(return_value='{"session_id": "redis_test_1", "filename": "video.mp4", "edits": [], "last_activity": 1234567890, "created_at": 1234567890, "file_size": 0, "video_duration": 0, "finalized": false, "video_path": null, "preview_path": null, "analysis": null, "suggestions": null, "optimization_recommendations": null}')
        store.redis.expire = AsyncMock(return_value=True)
        store.redis.set = AsyncMock(return_value=True)
        
        # Test set
        result = await store.set("redis_test_1", session)
        assert result is True
        
        # Test get
        retrieved = await store.get("redis_test_1")
        assert retrieved is not None
        assert retrieved.session_id == "redis_test_1"
    
    @pytest.mark.asyncio
    async def test_redis_delete(self, store):
        """Test Redis delete operation."""
        store.redis.delete = AsyncMock(return_value=1)
        
        result = await store.delete("redis_test_2")
        assert result is True
        
        # Test deleting non-existent key
        store.redis.delete = AsyncMock(return_value=0)
        result = await store.delete("non_existent")
        assert result is False
    
    @pytest.mark.asyncio
    async def test_redis_count(self, store):
        """Test Redis count operation."""
        store.redis.keys = AsyncMock(return_value=[b'key1', b'key2', b'key3'])
        
        count = await store.count()
        assert count == 3
    
    @pytest.mark.asyncio
    async def test_redis_error_handling(self, store):
        """Test Redis error handling."""
        # Mock Redis to raise an exception
        store.redis.get = AsyncMock(side_effect=Exception("Redis connection failed"))
        
        result = await store.get("error_test")
        assert result is None  # Should return None on error


class TestSessionManager:
    """Test session manager functionality."""
    
    @pytest.fixture
    def manager(self):
        """Create a fresh session manager for testing."""
        with patch('backend.session_manager.config.USE_REDIS', False):
            manager = SessionManager()
            return manager
    
    @pytest.mark.asyncio
    async def test_create_session(self, manager):
        """Test creating a new session."""
        session_id = await manager.create_session("test.mp4", 1000)
        
        assert session_id is not None
        assert len(session_id) > 0
        
        # Verify session exists
        session = await manager.get_session(session_id)
        assert session is not None
        assert session.filename == "test.mp4"
        assert session.file_size == 1000
    
    @pytest.mark.asyncio
    async def test_update_session(self, manager):
        """Test updating session data."""
        session_id = await manager.create_session("original.mp4", 500)
        
        result = await manager.update_session(
            session_id, 
            filename="updated.mp4",
            video_duration=120.0
        )
        assert result is True
        
        # Verify updates
        session = await manager.get_session(session_id)
        assert session.filename == "updated.mp4"
        assert session.video_duration == 120.0
    
    @pytest.mark.asyncio
    async def test_delete_session(self, manager):
        """Test deleting a session."""
        session_id = await manager.create_session("delete_test.mp4", 100)
        
        # Verify session exists
        session = await manager.get_session(session_id)
        assert session is not None
        
        # Delete session
        result = await manager.delete_session(session_id)
        assert result is True
        
        # Verify session is gone
        session = await manager.get_session(session_id)
        assert session is None
    
    @pytest.mark.asyncio
    async def test_websocket_registration(self, manager):
        """Test WebSocket registration and unregistration."""
        mock_websocket = Mock()
        session_id = "ws_test_session"
        
        # Register WebSocket
        await manager.register_websocket(session_id, mock_websocket)
        assert session_id in manager.active_connections
        assert manager.active_connections[session_id] == mock_websocket
        
        # Unregister WebSocket
        await manager.unregister_websocket(session_id)
        assert session_id not in manager.active_connections
    
    @pytest.mark.asyncio
    async def test_session_limit_enforcement(self, manager):
        """Test session limit enforcement."""
        original_max = config.MAX_SESSIONS
        config.MAX_SESSIONS = 2
        
        try:
            # Create sessions up to limit
            session1 = await manager.create_session("file1.mp4", 100)
            session2 = await manager.create_session("file2.mp4", 200)
            
            # Try to create one more
            with pytest.raises(ValueError, match="Maximum sessions reached"):
                await manager.create_session("file3.mp4", 300)
        
        finally:
            config.MAX_SESSIONS = original_max
    
    @pytest.mark.asyncio
    async def test_get_session_stats(self, manager):
        """Test getting session statistics."""
        # Create some sessions and WebSocket connections
        session1 = await manager.create_session("stats1.mp4", 100)
        session2 = await manager.create_session("stats2.mp4", 200)
        
        await manager.register_websocket(session1, Mock())
        await manager.register_websocket(session2, Mock())
        
        stats = await manager.get_session_stats()
        
        assert stats["total_sessions"] >= 2
        assert stats["active_websockets"] >= 2
        assert "max_sessions" in stats
        assert "session_timeout" in stats
        assert "storage_backend" in stats
    
    @pytest.mark.asyncio
    async def test_cleanup_session_files(self, manager):
        """Test cleanup of session files."""
        import tempfile
        import os
        
        # Create temporary files to simulate video and preview files
        temp_dir = tempfile.mkdtemp()
        video_file = os.path.join(temp_dir, "video.mp4")
        preview_file = os.path.join(temp_dir, "preview.mp4")
        
        # Create dummy files
        with open(video_file, 'w') as f:
            f.write("dummy video")
        with open(preview_file, 'w') as f:
            f.write("dummy preview")
        
        # Create session with file paths
        session = SessionData(
            session_id="cleanup_test",
            video_path=video_file,
            preview_path=preview_file
        )
        
        # Test cleanup
        await manager._cleanup_session_files(session)
        
        # Verify files are removed
        assert not os.path.exists(video_file)
        assert not os.path.exists(preview_file)
        
        # Cleanup temp dir
        os.rmdir(temp_dir)


class TestSessionManagerIntegration:
    """Integration tests for session manager with API."""
    
    @pytest.mark.asyncio
    async def test_manager_startup_shutdown(self):
        """Test session manager startup and shutdown."""
        manager = SessionManager()
        
        await manager.start()
        assert manager.cleanup_task is not None
        
        await manager.stop()
        assert manager.cleanup_task.cancelled()
    
    @pytest.mark.asyncio
    async def test_concurrent_session_operations(self):
        """Test concurrent session operations."""
        manager = SessionManager()
        
        # Create multiple sessions concurrently
        tasks = []
        for i in range(10):
            task = manager.create_session(f"concurrent_{i}.mp4", i * 100)
            tasks.append(task)
        
        session_ids = await asyncio.gather(*tasks)
        
        # Verify all sessions were created
        assert len(session_ids) == 10
        assert len(set(session_ids)) == 10  # All unique
        
        # Verify all sessions exist
        for session_id in session_ids:
            session = await manager.get_session(session_id)
            assert session is not None


@pytest.mark.asyncio
async def test_global_session_manager():
    """Test the global session manager instance."""
    # Ensure global instance is properly initialized
    assert session_manager is not None
    assert hasattr(session_manager, 'store')
    
    # Test basic operations
    session_id = await session_manager.create_session("global_test.mp4", 1000)
    session = await session_manager.get_session(session_id)
    
    assert session is not None
    assert session.filename == "global_test.mp4"
    
    # Cleanup
    await session_manager.delete_session(session_id)
