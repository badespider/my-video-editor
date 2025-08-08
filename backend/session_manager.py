"""
Enhanced Session Manager with Redis support and scalability optimizations.
Rule 3.2: Address Scalability Edges
"""

import asyncio
import json
import time
import uuid
import os
import logging
from typing import Dict, Optional, List, Any
from dataclasses import dataclass, asdict
from abc import ABC, abstractmethod

import config

# Try to import Redis, fallback to in-memory if not available
try:
    import redis.asyncio as redis
    from redis.asyncio import ConnectionPool
    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False
    redis = None
    ConnectionPool = None

logger = logging.getLogger(__name__)

@dataclass
class SessionData:
    """Structured session data with serialization support."""
    session_id: str
    user_id: str = 'guest'
    video_path: Optional[str] = None
    preview_path: Optional[str] = None
    edits: List[Dict] = None
    last_activity: float = 0
    filename: Optional[str] = None
    file_size: int = 0
    video_duration: float = 0
    finalized: bool = False
    analysis: Optional[Dict] = None
    suggestions: Optional[Dict] = None
    optimization_recommendations: Optional[Dict] = None
    created_at: float = 0
    ws_token: Optional[str] = None  # Token for WebSocket authentication
    ws_token_expires_at: Optional[float] = None  # Expiration for WebSocket token
    final_video_path: Optional[str] = None  # Path to finalized video
    
    def __post_init__(self):
        if self.edits is None:
            self.edits = []
        if self.created_at == 0:
            self.created_at = time.time()
        if self.last_activity == 0:
            self.last_activity = time.time()
    
    def to_dict(self) -> Dict:
        """Convert to dictionary for storage."""
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'SessionData':
        """Create from dictionary."""
        return cls(**data)
    
    def update_activity(self):
        """Update last activity timestamp."""
        self.last_activity = time.time()

    def set_ws_token(self, token: str):
        """Set WebSocket token and its expiration."""
        self.ws_token = token
        self.ws_token_expires_at = time.time() + config.WS_TOKEN_VALIDATION_TTL

    def is_ws_token_valid(self, token: str) -> bool:
        """Validate WebSocket token."""
        if not self.ws_token or not self.ws_token_expires_at:
            return False
        
        if time.time() > self.ws_token_expires_at:
            return False
            
        return self.ws_token == token


class SessionStore(ABC):
    """Abstract base class for session storage backends."""
    
    @abstractmethod
    async def get(self, session_id: str) -> Optional[SessionData]:
        """Get session data by ID."""
        pass
    
    @abstractmethod
    async def set(self, session_id: str, session_data: SessionData) -> bool:
        """Set session data."""
        pass
    
    @abstractmethod
    async def delete(self, session_id: str) -> bool:
        """Delete session data."""
        pass
    
    @abstractmethod
    async def list_expired(self, timeout: int) -> List[str]:
        """List expired session IDs."""
        pass
    
    @abstractmethod
    async def count(self) -> int:
        """Count total sessions."""
        pass
    
    @abstractmethod
    async def cleanup(self):
        """Cleanup resources."""
        pass


class InMemorySessionStore(SessionStore):
    """In-memory session store for development and testing."""
    
    def __init__(self):
        self._sessions: Dict[str, SessionData] = {}
        self._lock = asyncio.Lock()
    
    async def get(self, session_id: str) -> Optional[SessionData]:
        async with self._lock:
            session = self._sessions.get(session_id)
            if session:
                session.update_activity()
            return session
    
    async def set(self, session_id: str, session_data: SessionData) -> bool:
        async with self._lock:
            session_data.update_activity()
            self._sessions[session_id] = session_data
            return True
    
    async def delete(self, session_id: str) -> bool:
        async with self._lock:
            if session_id in self._sessions:
                del self._sessions[session_id]
                return True
            return False
    
    async def list_expired(self, timeout: int) -> List[str]:
        current_time = time.time()
        expired = []
        
        async with self._lock:
            for session_id, session_data in self._sessions.items():
                if current_time - session_data.last_activity > timeout:
                    expired.append(session_id)
        
        return expired
    
    async def count(self) -> int:
        async with self._lock:
            return len(self._sessions)
    
    async def cleanup(self):
        async with self._lock:
            self._sessions.clear()


class RedisSessionStore(SessionStore):
    """Redis-based session store for production scalability."""
    
    def __init__(self, connection_pool: ConnectionPool):
        self.pool = connection_pool
        self.redis = redis.Redis(connection_pool=connection_pool)
        self.key_prefix = "video_session:"
        
    def _make_key(self, session_id: str) -> str:
        """Generate Redis key for session."""
        return f"{self.key_prefix}{session_id}"
    
    async def get(self, session_id: str) -> Optional[SessionData]:
        try:
            key = self._make_key(session_id)
            data = await self.redis.get(key)
            if data:
                session_dict = json.loads(data)
                session = SessionData.from_dict(session_dict)
                
                # Update activity and extend TTL
                session.update_activity()
                await self.redis.expire(key, config.REDIS_SESSION_TTL)
                await self.redis.set(key, json.dumps(session.to_dict()))
                
                return session
            return None
        except Exception as e:
            logger.error(f"Redis get error for session {session_id}: {e}")
            return None
    
    async def set(self, session_id: str, session_data: SessionData) -> bool:
        try:
            key = self._make_key(session_id)
            session_data.update_activity()
            data = json.dumps(session_data.to_dict())
            await self.redis.setex(key, config.REDIS_SESSION_TTL, data)
            return True
        except Exception as e:
            logger.error(f"Redis set error for session {session_id}: {e}")
            return False
    
    async def delete(self, session_id: str) -> bool:
        try:
            key = self._make_key(session_id)
            result = await self.redis.delete(key)
            return result > 0
        except Exception as e:
            logger.error(f"Redis delete error for session {session_id}: {e}")
            return False
    
    async def list_expired(self, timeout: int) -> List[str]:
        # Redis TTL handles expiration automatically, return empty list
        return []
    
    async def count(self) -> int:
        try:
            pattern = f"{self.key_prefix}*"
            keys = await self.redis.keys(pattern)
            return len(keys)
        except Exception as e:
            logger.error(f"Redis count error: {e}")
            return 0
    
    async def cleanup(self):
        try:
            await self.redis.close()
        except Exception as e:
            logger.error(f"Redis cleanup error: {e}")


class SessionManager:
    """Enhanced session manager with scalability optimizations."""
    
    def __init__(self):
        self.store: SessionStore = self._create_store()
        self.active_connections: Dict[str, Any] = {}  # WebSocket connections
        self.cleanup_task: Optional[asyncio.Task] = None
        self.connection_pool = None
        
    def _create_store(self) -> SessionStore:
        """Create appropriate session store based on configuration."""
        if config.USE_REDIS and REDIS_AVAILABLE:
            try:
                # Create Redis connection pool
                self.connection_pool = ConnectionPool(
                    host=config.REDIS_HOST,
                    port=config.REDIS_PORT,
                    db=config.REDIS_DB,
                    password=config.REDIS_PASSWORD,
                    decode_responses=False,
                    max_connections=20,
                    retry_on_timeout=True,
                    health_check_interval=30
                )
                logger.info("Using Redis session store")
                return RedisSessionStore(self.connection_pool)
            except Exception as e:
                logger.warning(f"Failed to initialize Redis: {e}. Falling back to in-memory store.")
        
        logger.info("Using in-memory session store")
        return InMemorySessionStore()
    
    async def start(self):
        """Start the session manager and cleanup task."""
        self.cleanup_task = asyncio.create_task(self._cleanup_loop())
        logger.info("Session manager started")
    
    async def stop(self):
        """Stop the session manager and cleanup resources."""
        if self.cleanup_task:
            self.cleanup_task.cancel()
            try:
                await self.cleanup_task
            except asyncio.CancelledError:
                pass
        
        await self.store.cleanup()
        if self.connection_pool:
            await self.connection_pool.disconnect()
        
        logger.info("Session manager stopped")
    
    async def create_session(self, filename: str = None, file_size: int = 0, user_id: str = 'guest') -> str:
        """Create a new session."""
        # Check session limit
        current_count = await self.store.count()
        if current_count >= config.MAX_SESSIONS:
            raise ValueError("Maximum sessions reached")
        
        session_id = str(uuid.uuid4())
        session_data = SessionData(
            session_id=session_id,
            user_id=user_id,
            filename=filename,
            file_size=file_size
        )
        
        await self.store.set(session_id, session_data)
        logger.info(f"Created session: {session_id}")
        return session_id
    
    async def get_session(self, session_id: str) -> Optional[SessionData]:
        """Get session data by ID."""
        return await self.store.get(session_id)
    
    async def update_session(self, session_id: str, **updates) -> bool:
        """Update session data."""
        session = await self.store.get(session_id)
        if not session:
            return False
        
        # Update fields
        for key, value in updates.items():
            if hasattr(session, key):
                setattr(session, key, value)
        
        await self.store.set(session_id, session)
        return True
    
    async def delete_session(self, session_id: str) -> bool:
        """Delete a session and cleanup files."""
        session = await self.store.get(session_id)
        if session:
            # Clean up files
            await self._cleanup_session_files(session)
            
            # Close WebSocket if active
            if session_id in self.active_connections:
                try:
                    await self.active_connections[session_id].close()
                except:
                    pass
                del self.active_connections[session_id]
        
        return await self.store.delete(session_id)
    
    async def register_websocket(self, session_id: str, websocket):
        """Register WebSocket connection for session."""
        self.active_connections[session_id] = websocket
        logger.info(f"WebSocket registered for session: {session_id}")
    
    async def unregister_websocket(self, session_id: str):
        """Unregister WebSocket connection."""
        if session_id in self.active_connections:
            del self.active_connections[session_id]
            logger.info(f"WebSocket unregistered for session: {session_id}")
    
    async def get_session_stats(self) -> Dict[str, Any]:
        """Get session statistics."""
        total_sessions = await self.store.count()
        active_websockets = len(self.active_connections)
        
        return {
            "total_sessions": total_sessions,
            "active_websockets": active_websockets,
            "max_sessions": config.MAX_SESSIONS,
            "session_timeout": config.SESSION_TIMEOUT,
            "storage_backend": "redis" if isinstance(self.store, RedisSessionStore) else "memory"
        }
    
    async def _cleanup_loop(self):
        """Periodic cleanup of expired sessions."""
        while True:
            try:
                await asyncio.sleep(60)  # Run every minute
                
                expired_sessions = await self.store.list_expired(config.SESSION_TIMEOUT)
                
                for session_id in expired_sessions:
                    try:
                        await self.delete_session(session_id)
                        logger.info(f"Cleaned up expired session: {session_id}")
                    except Exception as e:
                        logger.error(f"Failed to cleanup session {session_id}: {e}")
                
                if expired_sessions:
                    logger.info(f"Cleaned up {len(expired_sessions)} expired sessions")
                    
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in cleanup loop: {e}")
    
    async def _cleanup_session_files(self, session: SessionData):
        """Clean up files associated with a session."""
        files_to_remove = []
        
        if session.video_path:
            files_to_remove.append(session.video_path)
        if session.preview_path and session.preview_path != session.video_path:
            files_to_remove.append(session.preview_path)
        
        for file_path in files_to_remove:
            if file_path and os.path.exists(file_path):
                try:
                    os.remove(file_path)
                    logger.debug(f"Removed file: {file_path}")
                except Exception as e:
                    logger.warning(f"Failed to remove file {file_path}: {e}")


# Global session manager instance
session_manager = SessionManager()
