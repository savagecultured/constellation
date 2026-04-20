"""Stream analytics tracking."""
import time
from typing import Any, Optional
from datetime import datetime, timedelta
from collections import defaultdict


class StreamAnalytics:
    """Tracks streaming analytics and statistics.
    
    In production, this would use Redis with TTL for time-series data
    and PostgreSQL for persistent storage.
    """
    
    # In-memory storage (replace with Redis in production)
    _stream_history: list[dict[str, Any]] = []
    _user_stats: dict[int, dict[str, Any]] = defaultdict(dict)
    _daily_stats: dict[str, dict[str, Any]] = defaultdict(dict)
    
    # Max history to keep in memory
    MAX_HISTORY = 10000
    
    def __init__(self):
        """Initialize the analytics tracker."""
        pass
    
    def record_stream_start(
        self,
        user_id: int,
        item_id: str,
        source: str,
        session_id: str,
        quality: str = "auto"
    ):
        """Record the start of a stream.
        
        Args:
            user_id: The user ID
            item_id: The media item ID
            source: The media source
            session_id: The stream session ID
            quality: The video quality
        """
        now = datetime.utcnow()
        date_key = now.strftime("%Y-%m-%d")
        
        event = {
            "event_type": "stream_start",
            "user_id": user_id,
            "item_id": item_id,
            "source": source,
            "session_id": session_id,
            "quality": quality,
            "timestamp": now.isoformat(),
            "date": date_key
        }
        
        self._stream_history.append(event)
        
        # Trim history if needed
        if len(self._stream_history) > self.MAX_HISTORY:
            self._stream_history = self._stream_history[-self.MAX_HISTORY:]
        
        # Update user stats
        if user_id not in self._user_stats:
            self._user_stats[user_id] = {
                "total_streams": 0,
                "total_watch_time": 0,
                "last_stream": None
            }
        
        self._user_stats[user_id]["total_streams"] += 1
        self._user_stats[user_id]["last_stream"] = now.isoformat()
        
        # Update daily stats
        if date_key not in self._daily_stats:
            self._daily_stats[date_key] = {
                "total_streams": 0,
                "unique_users": set(),
                "total_watch_time": 0
            }
        
        self._daily_stats[date_key]["total_streams"] += 1
        self._daily_stats[date_key]["unique_users"].add(user_id)
    
    def record_stream_end(
        self,
        session_id: str,
        user_id: int,
        watch_time_seconds: int,
        item_id: str
    ):
        """Record the end of a stream.
        
        Args:
            session_id: The stream session ID
            user_id: The user ID
            watch_time_seconds: How long the stream was watched
            item_id: The media item ID
        """
        now = datetime.utcnow()
        date_key = now.strftime("%Y-%m-%d")
        
        event = {
            "event_type": "stream_end",
            "user_id": user_id,
            "item_id": item_id,
            "session_id": session_id,
            "watch_time_seconds": watch_time_seconds,
            "timestamp": now.isoformat(),
            "date": date_key
        }
        
        self._stream_history.append(event)
        
        # Trim history if needed
        if len(self._stream_history) > self.MAX_HISTORY:
            self._stream_history = self._stream_history[-self.MAX_HISTORY:]
        
        # Update user stats
        if user_id in self._user_stats:
            self._user_stats[user_id]["total_watch_time"] += watch_time_seconds
        
        # Update daily stats
        if date_key in self._daily_stats:
            self._daily_stats[date_key]["total_watch_time"] += watch_time_seconds
    
    def record_stream_pause(self, session_id: str):
        """Record when a stream is paused."""
        now = datetime.utcnow()
        
        event = {
            "event_type": "stream_pause",
            "session_id": session_id,
            "timestamp": now.isoformat()
        }
        
        self._stream_history.append(event)
    
    def record_stream_resume(self, session_id: str):
        """Record when a stream is resumed."""
        now = datetime.utcnow()
        
        event = {
            "event_type": "stream_resume",
            "session_id": session_id,
            "timestamp": now.isoformat()
        }
        
        self._stream_history.append(event)
    
    def get_user_stats(self, user_id: int) -> dict[str, Any]:
        """Get streaming statistics for a user.
        
        Args:
            user_id: The user ID
            
        Returns:
            Dictionary with user statistics
        """
        stats = self._user_stats.get(user_id, {
            "total_streams": 0,
            "total_watch_time": 0,
            "last_stream": None
        })
        
        # Convert set to count for unique users in daily stats
        for date_key, data in self._daily_stats.items():
            data["unique_users"] = len(data.get("unique_users", set()))
        
        return stats
    
    def get_daily_stats(self, date: Optional[str] = None) -> dict[str, Any]:
        """Get streaming statistics for a specific date.
        
        Args:
            date: Date in YYYY-MM-DD format, defaults to today
            
        Returns:
            Dictionary with daily statistics
        """
        if date is None:
            date = datetime.utcnow().strftime("%Y-%m-%d")
        
        stats = self._daily_stats.get(date, {
            "total_streams": 0,
            "unique_users": 0,
            "total_watch_time": 0
        })
        
        # Convert set to count
        if isinstance(stats.get("unique_users"), set):
            stats["unique_users"] = len(stats["unique_users"])
        
        return stats
    
    def get_recent_streams(
        self,
        limit: int = 100,
        user_id: Optional[int] = None
    ) -> list[dict[str, Any]]:
        """Get recent stream events.
        
        Args:
            limit: Maximum number of events to return
            user_id: Optional filter by user
            
        Returns:
            List of stream events
        """
        events = self._stream_history[-limit:]
        
        if user_id is not None:
            events = [e for e in events if e.get("user_id") == user_id]
        
        return events
    
    def get_popular_items(
        self,
        limit: int = 10,
        days: int = 7
    ) -> list[dict[str, Any]]:
        """Get most popular items.
        
        Args:
            limit: Number of items to return
            days: Number of days to look back
            
        Returns:
            List of popular items with view counts
        """
        cutoff = datetime.utcnow() - timedelta(days=days)
        
        # Count item views
        item_counts: dict[str, int] = defaultdict(int)
        
        for event in self._stream_history:
            if event.get("event_type") == "stream_start":
                event_time = datetime.fromisoformat(event["timestamp"])
                if event_time >= cutoff:
                    item_id = event.get("item_id")
                    if item_id:
                        item_counts[item_id] += 1
        
        # Sort by count
        sorted_items = sorted(
            item_counts.items(),
            key=lambda x: x[1],
            reverse=True
        )[:limit]
        
        return [
            {"item_id": item_id, "view_count": count}
            for item_id, count in sorted_items
        ]
    
    def get_active_sessions_count(self) -> int:
        """Get the number of currently active sessions."""
        active_sessions = set()
        
        for event in self._stream_history:
            if event.get("event_type") == "stream_start":
                active_sessions.add(event.get("session_id"))
            elif event.get("event_type") == "stream_end":
                active_sessions.discard(event.get("session_id"))
        
        return len(active_sessions)


# Global instance
stream_analytics = StreamAnalytics()


def record_stream_start(
    user_id: int,
    item_id: str,
    source: str,
    session_id: str,
    quality: str = "auto"
):
    """Record stream start."""
    stream_analytics.record_stream_start(
        user_id, item_id, source, session_id, quality
    )


def record_stream_end(
    session_id: str,
    user_id: int,
    watch_time_seconds: int,
    item_id: str
):
    """Record stream end."""
    stream_analytics.record_stream_end(
        session_id, user_id, watch_time_seconds, item_id
    )


def get_user_stats(user_id: int) -> dict[str, Any]:
    """Get user streaming stats."""
    return stream_analytics.get_user_stats(user_id)