"""Player UI Backend service."""
from typing import Any, Optional
from datetime import datetime
import time


class PlayerSessionManager:
    """Manages player UI sessions including playback state."""
    
    # In production, use Redis for distributed sessions
    _sessions: dict[str, dict[str, Any]] = {}
    
    def __init__(self):
        """Initialize the session manager."""
        pass
    
    def create_session(
        self,
        user_id: int,
        item_id: str,
        source: str,
        session_id: str
    ) -> dict[str, Any]:
        """Create a new player session.
        
        Args:
            user_id: The user ID
            item_id: The media item ID
            source: The media source (jellyfin/navidrome)
            session_id: The stream session ID
            
        Returns:
            Session information
        """
        player_session = {
            "player_session_id": f"player_{int(time.time() * 1000)}",
            "user_id": user_id,
            "item_id": item_id,
            "source": source,
            "stream_session_id": session_id,
            "playback_state": "idle",
            "position": 0,  # in seconds
            "duration": 0,
            "volume": 1.0,
            "muted": False,
            "playback_rate": 1.0,
            "quality": "auto",
            "available_qualities": [],
            "created_at": datetime.utcnow().isoformat(),
            "updated_at": datetime.utcnow().isoformat(),
            "last_activity": datetime.utcnow().isoformat()
        }
        
        self._sessions[player_session["player_session_id"]] = player_session
        
        return player_session
    
    def get_session(self, player_session_id: str) -> Optional[dict[str, Any]]:
        """Get a player session.
        
        Args:
            player_session_id: The player session ID
            
        Returns:
            Session information or None
        """
        return self._sessions.get(player_session_id)
    
    def update_position(
        self,
        player_session_id: str,
        position: int
    ) -> dict[str, Any]:
        """Update playback position.
        
        Args:
            player_session_id: The player session ID
            position: Position in seconds
            
        Returns:
            Updated session
        """
        if player_session_id not in self._sessions:
            return {"error": "Session not found"}
        
        session = self._sessions[player_session_id]
        session["position"] = position
        session["updated_at"] = datetime.utcnow().isoformat()
        session["last_activity"] = datetime.utcnow().isoformat()
        
        return session
    
    def update_state(
        self,
        player_session_id: str,
        state: str
    ) -> dict[str, Any]:
        """Update playback state (play, pause, stopped).
        
        Args:
            player_session_id: The player session ID
            state: New playback state
            
        Returns:
            Updated session
        """
        if player_session_id not in self._sessions:
            return {"error": "Session not found"}
        
        session = self._sessions[player_session_id]
        session["playback_state"] = state
        session["updated_at"] = datetime.utcnow().isoformat()
        session["last_activity"] = datetime.utcnow().isoformat()
        
        return session
    
    def set_quality(
        self,
        player_session_id: str,
        quality: str
    ) -> dict[str, Any]:
        """Set playback quality.
        
        Args:
            player_session_id: The player session ID
            quality: Quality setting
            
        Returns:
            Updated session
        """
        if player_session_id not in self._sessions:
            return {"error": "Session not found"}
        
        session = self._sessions[player_session_id]
        session["quality"] = quality
        session["updated_at"] = datetime.utcnow().isoformat()
        
        return session
    
    def set_volume(
        self,
        player_session_id: str,
        volume: float,
        muted: bool = False
    ) -> dict[str, Any]:
        """Set volume and mute state.
        
        Args:
            player_session_id: The player session ID
            volume: Volume level (0.0 to 1.0)
            muted: Whether muted
            
        Returns:
            Updated session
        """
        if player_session_id not in self._sessions:
            return {"error": "Session not found"}
        
        session = self._sessions[player_session_id]
        session["volume"] = max(0.0, min(1.0, volume))
        session["muted"] = muted
        session["updated_at"] = datetime.utcnow().isoformat()
        
        return session
    
    def set_playback_rate(
        self,
        player_session_id: str,
        rate: float
    ) -> dict[str, Any]:
        """Set playback speed.
        
        Args:
            player_session_id: The player session ID
            rate: Playback rate (0.5, 1.0, 1.5, 2.0, etc.)
            
        Returns:
            Updated session
        """
        if player_session_id not in self._sessions:
            return {"error": "Session not found"}
        
        session = self._sessions[player_session_id]
        session["playback_rate"] = rate
        session["updated_at"] = datetime.utcnow().isoformat()
        
        return session
    
    def end_session(self, player_session_id: str) -> bool:
        """End a player session.
        
        Args:
            player_session_id: The player session ID
            
        Returns:
            True if session was ended
        """
        if player_session_id in self._sessions:
            session = self._sessions[player_session_id]
            session["playback_state"] = "ended"
            session["updated_at"] = datetime.utcnow().isoformat()
            return True
        return False
    
    def get_user_sessions(self, user_id: int) -> list[dict[str, Any]]:
        """Get all sessions for a user.
        
        Args:
            user_id: The user ID
            
        Returns:
            List of user sessions
        """
        return [
            session for session in self._sessions.values()
            if session.get("user_id") == user_id
        ]


# Global instance
player_session_manager = PlayerSessionManager()


class PlaylistGenerator:
    """Generates HLS/DASH playlists for streaming."""
    
    @staticmethod
    def generate_hls_master(
        base_url: str,
        qualities: list[dict[str, Any]],
        item_id: str
    ) -> str:
        """Generate HLS master playlist.
        
        Args:
            base_url: Base URL for stream
            qualities: List of quality options
            item_id: Media item ID
            
        Returns:
            HLS master playlist content
        """
        lines = [
            "#EXTM3U",
            "#EXT-X-VERSION:3",
            "#EXT-X-INDEPENDENT-SEGMENTS"
        ]
        
        for quality in qualities:
            bandwidth = quality.get("bandwidth", 0)
            resolution = quality.get("resolution", "auto")
            name = quality.get("name", "auto")
            
            lines.append(f"#EXT-X-STREAM-INF:BANDWIDTH={bandwidth},RESOLUTION={resolution},NAME=\"{name}\"")
            lines.append(f"{base_url}/hls/{item_id}/{quality.get('id', 'auto')}/playlist.m3u8")
        
        return "\n".join(lines)
    
    @staticmethod
    def generate_hls_media(
        segments: list[dict[str, Any]],
        target_duration: int = 10
    ) -> str:
        """Generate HLS media playlist.
        
        Args:
            segments: List of segments
            target_duration: Target segment duration
            
        Returns:
            HLS media playlist content
        """
        lines = [
            "#EXTM3U",
            f"#EXT-X-TARGETDURATION:{target_duration}",
            "#EXT-X-VERSION:3",
            "#EXT-X-PLAYLIST-TYPE:VOD"
        ]
        
        for segment in segments:
            duration = segment.get("duration", target_duration)
            uri = segment.get("uri", "")
            
            lines.append(f"#EXTINF:{duration},")
            lines.append(uri)
        
        lines.append("#EXT-X-ENDLIST")
        
        return "\n".join(lines)
    
    @staticmethod
    def generate_dash_manifest(
        base_url: str,
        qualities: list[dict[str, Any]],
        item_id: str,
        duration: int
    ) -> str:
        """Generate DASH manifest.
        
        Args:
            base_url: Base URL for stream
            qualities: List of quality options
            item_id: Media item ID
            duration: Total duration in seconds
            
        Returns:
            DASH MPD manifest content
        """
        # Generate AdaptationSets for each quality
        adaptation_sets = []
        
        for idx, quality in enumerate(qualities):
            bandwidth = quality.get("bandwidth", 0)
            width = quality.get("width", 1920)
            height = quality.get("height", 1080)
            codecs = quality.get("codecs", "avc1.42001E,mp4a.40.2")
            
            adaptation_sets.append(f'''
        <AdaptationSet id="{idx}" mimeType="video/mp4" codecs="{codecs}" bandwidth="{bandwidth}">
            <Representation id="r{idx}" width="{width}" height="{height}">
                <BaseURL>{base_url}/dash/{item_id}/{quality.get('id', 'auto')}/</BaseURL>
                <SegmentBase indexRange="0-100"/>
            </Representation>
        </AdaptationSet>''')
        
        manifest = f'''<?xml version="1.0" encoding="UTF-8"?>
<MPD xmlns="urn:mpeg:dash:schema:mpd:2011" type="static" mediaPresentationDuration="PT{duration}S" minBufferTime="PT1S" profiles="urn:mpeg:dash:profile:isoff-on-demand:2011">
    <Period>
        {''.join(adaptation_sets)}
    </Period>
</MPD>'''
        
        return manifest
    
    @staticmethod
    def generate_quality_options(
        max_bitrate: int = 140000000
    ) -> list[dict[str, Any]]:
        """Generate standard quality options.
        
        Args:
            max_bitrate: Maximum bitrate
            
        Returns:
            List of quality options
        """
        return [
            {
                "id": "auto",
                "name": "Auto",
                "bandwidth": 0,
                "resolution": "auto",
                "width": 0,
                "height": 0
            },
            {
                "id": "4k",
                "name": "4K",
                "bandwidth": 20000000,
                "resolution": "3840x2160",
                "width": 3840,
                "height": 2160,
                "codecs": "avc1.640028,mp4a.40.2"
            },
            {
                "id": "1080p",
                "name": "1080p",
                "bandwidth": 8000000,
                "resolution": "1920x1080",
                "width": 1920,
                "height": 1080,
                "codecs": "avc1.64001f,mp4a.40.2"
            },
            {
                "id": "720p",
                "name": "720p",
                "bandwidth": 4000000,
                "resolution": "1280x720",
                "width": 1280,
                "height": 720,
                "codecs": "avc1.64001f,mp4a.40.2"
            },
            {
                "id": "480p",
                "name": "480p",
                "bandwidth": 2000000,
                "resolution": "854x480",
                "width": 854,
                "height": 480,
                "codecs": "avc1.64001e,mp4a.40.2"
            },
            {
                "id": "360p",
                "name": "360p",
                "bandwidth": 1000000,
                "resolution": "640x360",
                "width": 640,
                "height": 360,
                "codecs": "avc1.64001e,mp4a.40.2"
            }
        ]


# Global instances
playlist_generator = PlaylistGenerator()
