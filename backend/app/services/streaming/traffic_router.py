"""Traffic routing to media servers."""
from typing import Any, Optional
import httpx

from app.core.config import settings
from app.services.jellyfin import JellyfinClient
from app.services.navidrome import NavidromeClient
from app.services.media_factory import MediaClientFactory


class TrafficRouter:
    """Routes traffic to Jellyfin or Navidrome media servers."""
    
    def __init__(self):
        """Initialize the traffic router."""
        self.timeout = settings.MEDIA_SERVER_TIMEOUT
    
    async def get_stream_url(
        self,
        item_id: str,
        source: str,
        user_id: int,
        quality: str = "auto"
    ) -> dict[str, Any]:
        """Get the stream URL for a media item.
        
        Args:
            item_id: The media item ID
            source: Either 'jellyfin' or 'navidrome'
            user_id: The user ID
            quality: Video quality preference
            
        Returns:
            Dictionary with stream URL and metadata
        """
        if source == "jellyfin":
            return await self._get_jellyfin_stream_url(item_id, user_id, quality)
        elif source == "navidrome":
            return await self._get_navidrome_stream_url(item_id, user_id, quality)
        else:
            raise ValueError(f"Unknown media source: {source}")
    
    async def _get_jellyfin_stream_url(
        self,
        item_id: str,
        user_id: int,
        quality: str
    ) -> dict[str, Any]:
        """Get stream URL from Jellyfin."""
        try:
            client = MediaClientFactory.get_jellyfin_client()
        except ValueError:
            raise ValueError("Jellyfin is not configured")
        
        # Get playback info
        playback_info = await client.get_itemPlaybackInfo(item_id)
        
        # Get the media source
        media_sources = playback_info.get("MediaSources", [])
        if not media_sources:
            raise ValueError(f"No media sources found for item {item_id}")
        
        media_source = media_sources[0]
        stream_container = media_source.get("Container", "mp4")
        
        # Build the stream URL
        # In production, this would go through our proxy
        base_url = settings.JELLYFIN_URL.rstrip("/")
        
        return {
            "stream_url": f"{base_url}/Videos/{item_id}/stream",
            "source": "jellyfin",
            "item_id": item_id,
            "container": stream_container,
            "quality": quality,
            "direct": False  # Goes through proxy
        }
    
    async def _get_navidrome_stream_url(
        self,
        item_id: str,
        user_id: int,
        quality: str
    ) -> dict[str, Any]:
        """Get stream URL from Navidrome."""
        try:
            client = MediaClientFactory.get_navidrome_client()
        except ValueError:
            raise ValueError("Navidrome is not configured")
        
        # Get stream URL
        stream_info = await client.get_stream_url(item_id)
        
        base_url = settings.NAVIDROME_URL.rstrip("/")
        
        return {
            "stream_url": f"{base_url}{stream_info['stream_url']}",
            "source": "navidrome",
            "item_id": item_id,
            "container": "mp3",
            "quality": quality,
            "direct": False
        }
    
    async def proxy_stream(
        self,
        item_id: str,
        source: str,
        range_header: Optional[str] = None
    ) -> httpx.Response:
        """Proxy a stream request to the media server.
        
        Args:
            item_id: The media item ID
            source: Either 'jellyfin' or 'navidrome'
            range_header: Optional HTTP Range header
            
        Returns:
            The proxied response
        """
        if source == "jellyfin":
            return await self._proxy_jellyfin_stream(item_id, range_header)
        elif source == "navidrome":
            return await self._proxy_navidrome_stream(item_id, range_header)
        else:
            raise ValueError(f"Unknown media source: {source}")
    
    async def _proxy_jellyfin_stream(
        self,
        item_id: str,
        range_header: Optional[str] = None
    ) -> httpx.Response:
        """Proxy a Jellyfin stream."""
        client = await self._get_proxy_client("jellyfin")
        
        headers = {}
        if range_header:
            headers["Range"] = range_header
        
        base_url = settings.JELLYFIN_URL.rstrip("/")
        response = await client.get(
            f"{base_url}/Videos/{item_id}/stream",
            headers=headers,
            follow_redirects=True
        )
        
        return response
    
    async def _proxy_navidrome_stream(
        self,
        item_id: str,
        range_header: Optional[str] = None
    ) -> httpx.Response:
        """Proxy a Navidrome stream."""
        client = await self._get_proxy_client("navidrome")
        
        headers = {}
        if range_header:
            headers["Range"] = range_header
        
        base_url = settings.NAVIDROME_URL.rstrip("/")
        response = await client.get(
            f"{base_url}/rest/song/{item_id}/download",
            headers=headers
        )
        
        return response
    
    async def _get_proxy_client(self, source: str) -> httpx.AsyncClient:
        """Get an HTTP client for proxying."""
        if source == "jellyfin":
            api_key = settings.JELLYFIN_API_KEY
        else:
            api_key = settings.NAVIDROME_API_KEY
        
        headers = {"X-Api-Key": api_key} if api_key else {}
        
        return httpx.AsyncClient(
            headers=headers,
            timeout=self.timeout,
            follow_redirects=True
        )


# Global instance
traffic_router = TrafficRouter()


async def get_stream_url(
    item_id: str,
    source: str,
    user_id: int,
    quality: str = "auto"
) -> dict[str, Any]:
    """Get stream URL for a media item."""
    return await traffic_router.get_stream_url(item_id, source, user_id, quality)