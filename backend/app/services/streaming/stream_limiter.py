"""Concurrent stream limit enforcement."""
import time
from typing import Any, Optional
from datetime import datetime, timedelta


class StreamLimiter:
    """Enforces concurrent stream limits per user/subscription.
    
    In production, this would use Redis for distributed locking.
    For now, it uses an in-memory store.
    """
    
    # Active streams storage (in production, use Redis)
    _active_streams: dict[str, dict[str, Any]] = {}
    
    # Stream session timeout (seconds)
    SESSION_TIMEOUT = 3600  # 1 hour
    
    def __init__(self):
        """Initialize the stream limiter."""
        self._cleanup_old_sessions()
    
    def _cleanup_old_sessions(self):
        """Remove expired stream sessions."""
        now = time.time()
        expired_keys = []
        
        for session_id, session_data in self._active_streams.items():
            if now - session_data.get("started_at", 0) > self.SESSION_TIMEOUT:
                expired_keys.append(session_id)
        
        for key in expired_keys:
            del self._active_streams[key]
    
    def start_stream(
        self,
        user_id: int,
        max_streams: int,
        item_id: str,
        source: str
    ) -> dict[str, Any]:
        """Start a new stream session.
        
        Args:
            user_id: The user ID
            max_streams: Maximum concurrent streams allowed
            item_id: The media item ID
            source: The media source (jellyfin/navidrome)
            
        Returns:
            Dictionary with session info or error
        """
        self._cleanup_old_sessions()
        
        # Count current active streams for this user
        user_streams = self.get_active_streams(user_id)
        current_count = len(user_streams)
        
        if current_count >= max_streams:
            return {
                "allowed": False,
                "reason": "max_streams_reached",
                "message": f"Maximum concurrent streams ({max_streams}) reached",
                "current_streams": current_count,
                "max_streams": max_streams
            }
        
        # Create new session
        session_id = f"{user_id}:{item_id}:{int(time.time())}"
        session_data = {
            "session_id": session_id,
            "user_id": user_id,
            "item_id": item_id,
            "source": source,
            "started_at": time.time(),
            "last_activity": time.time()
        }
        
        self._active_streams[session_id] = session_data
        
        return {
            "allowed": True,
            "session_id": session_id,
            "current_streams": current_count + 1,
            "max_streams": max_streams
        }
    
    def end_stream(self, session_id: str) -> bool:
        """End a stream session.
        
        Args:
            session_id: The session ID to end
            
        Returns:
            True if session was found and ended
        """
        if session_id in self._active_streams:
            del self._active_streams[session_id]
            return True
        return False
    
    def get_active_streams(self, user_id: int) -> list[dict[str, Any]]:
        """Get all active streams for a user.
        
        Args:
            user_id: The user ID
            
        Returns:
            List of active stream sessions
        """
        self._cleanup_old_sessions()
        
        return [
            session for session in self._active_streams.values()
            if session.get("user_id") == user_id
        ]
    
    def update_activity(self, session_id: str) -> bool:
        """Update last activity time for a session.
        
        Args:
            session_id: The session ID
            
        Returns:
            True if updated successfully
        """
        if session_id in self._active_streams:
            self._active_streams[session_id]["last_activity"] = time.time()
            return True
        return False
    
    def get_stream_count(self, user_id: int) -> int:
        """Get the number of active streams for a user.
        
        Args:
            user_id: The user ID
            
        Returns:
            Number of active streams
        """
        return len(self.get_active_streams(user_id))
    
    def is_stream_active(self, session_id: str) -> bool:
        """Check if a session is still active.
        
        Args:
            session_id: The session ID
            
        Returns:
            True if active
        """
        return session_id in self._active_streams
    
    def get_all_active_sessions(self) -> list[dict[str, Any]]:
        """Get all active stream sessions.
        
        Returns:
            List of all active sessions
        """
        self._cleanup_old_sessions()
        return list(self._active_streams.values())


# Global instance
stream_limiter = StreamLimiter()


def start_stream(
    user_id: int,
    max_streams: int,
    item_id: str,
    source: str
) -> dict[str, Any]:
    """Start a new stream session."""
    return stream_limiter.start_stream(user_id, max_streams, item_id, source)


def end_stream(session_id: str) -> bool:
    """End a stream session."""
    return stream_limiter.end_stream(session_id)


def get_active_streams(user_id: int) -> list[dict[str, Any]]:
    """Get active streams for a user."""
    return stream_limiter.get_active_streams(user_id)