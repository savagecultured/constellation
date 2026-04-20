"""Jellyfin API client wrapper."""
from typing import Any, Optional
import httpx

from app.services.base_media import MediaServerClient


class JellyfinClient(MediaServerClient):
    """Jellyfin media server API client."""
    
    def __init__(
        self,
        base_url: str,
        api_key: str,
        device_id: str = "constellation-streaming",
        timeout: float = 30.0
    ):
        """Initialize the Jellyfin client.
        
        Args:
            base_url: The base URL of the Jellyfin server
            api_key: Jellyfin API key
            device_id: Device ID for authentication
            timeout: Request timeout in seconds
        """
        super().__init__(base_url, api_key, timeout)
        self.device_id = device_id
    
    async def _get_client(self) -> httpx.AsyncClient:
        """Get or create the HTTP client with Jellyfin authentication."""
        if self._client is None:
            self._client = httpx.AsyncClient(
                base_url=self.base_url,
                headers={
                    "X-Api-Key": self.api_key,
                    "X-Emby-Authorization": f"MediaBrowser Client=\"Constellation Streaming\", Device=\"Python\", DeviceId=\"{self.device_id}\", Version=\"1.0.0\""
                },
                timeout=self.timeout
            )
        return self._client
    
    async def authenticate(self, username: str, password: str) -> dict[str, Any]:
        """Authenticate with Jellyfin.
        
        Args:
            username: Jellyfin username
            password: Jellyfin password
            
        Returns:
            Authentication response with access token
        """
        data = {
            "Username": username,
            "Pw": password
        }
        client = await self._get_client()
        response = await client.post("/Users/AuthenticateByName", json=data)
        response.raise_for_status()
        return response.json()
    
    async def get_user(self, user_id: str) -> dict[str, Any]:
        """Get user information."""
        return await self._get(f"/Users/{user_id}")
    
    async def get_libraries(self) -> list[dict[str, Any]]:
        """Get all media libraries from Jellyfin."""
        data = await self._get("/Library/MediaFolders")
        return data.get("Items", [])
    
    async def get_library_items(
        self,
        library_id: str,
        start_index: int = 0,
        limit: int = 100
    ) -> list[dict[str, Any]]:
        """Get items from a specific library.
        
        Args:
            library_id: The library ID
            start_index: Starting index for pagination
            limit: Maximum number of items to return
            
        Returns:
            List of items in the library
        """
        params = {
            "recursive": "true",
            "startIndex": start_index,
            "limit": limit,
            "includeMedia": "true",
            "fields": "PrimaryImageAspectRatio,BasicSyncInfo,MediaSourceCount"
        }
        data = await self._get(f"/Items?parentId={library_id}", params=params)
        return data.get("Items", [])
    
    async def get_item(self, item_id: str) -> dict[str, Any]:
        """Get a specific item by ID."""
        params = {
            "fields": "Chapters,MediaSources,MediaStreams"
        }
        return await self._get(f"/Items/{item_id}", params=params)
    
    async def get_items_by_type(
        self,
        item_type: str,
        start_index: int = 0,
        limit: int = 100
    ) -> list[dict[str, Any]]:
        """Get items by type (Movie, Series, Music, etc.).
        
        Args:
            item_type: The type of items to fetch (Movie, Series, MusicArtist, etc.)
            start_index: Starting index for pagination
            limit: Maximum number of items to return
            
        Returns:
            List of items matching the type
        """
        params = {
            "includeItemTypes": item_type,
            "startIndex": start_index,
            "limit": limit,
            "recursive": "true",
            "sortOrder": "Descending",
            "sortBy": "DateCreated"
        }
        data = await self._get("/Items", params=params)
        return data.get("Items", [])
    
    async def search_items(
        self,
        query: str,
        limit: int = 20
    ) -> list[dict[str, Any]]:
        """Search for items.
        
        Args:
            query: Search query string
            limit: Maximum number of results
            
        Returns:
            List of matching items
        """
        params = {
            "searchTerm": query,
            "limit": limit,
            "includeItemTypes": "Movie,Series,MusicAlbum,MusicArtist,Audio,Video"
        }
        data = await self._get("/Items", params=params)
        return data.get("Items", [])
    
    async def get_itemPlaybackInfo(self, item_id: str) -> dict[str, Any]:
        """Get playback information for an item.
        
        Args:
            item_id: The item ID
            
        Returns:
            Playback information including stream URLs
        """
        params = {
            "userId": "",  # Empty for non-authenticated access
            "maxStreamingBitrate": 140000000,
            "audioBitrate": 384000
        }
        data = await self._post(f"/Items/{item_id}/PlaybackInfo", json=params)
        return data
    
    async def get_stream_url(
        self,
        item_id: str,
        media_source_id: Optional[str] = None
    ) -> dict[str, Any]:
        """Get stream URL for an item.
        
        Args:
            item_id: The item ID
            media_source_id: Optional specific media source ID
            
        Returns:
            Stream URL information
        """
        item = await self.get_item(item_id)
        media_sources = item.get("MediaSources", [])
        
        if not media_sources:
            raise ValueError(f"No media sources found for item {item_id}")
        
        # Select the appropriate media source
        media_source = None
        if media_source_id:
            for source in media_sources:
                if source.get("Id") == media_source_id:
                    media_source = source
                    break
        else:
            media_source = media_sources[0]
        
        if not media_source:
            raise ValueError(f"Media source {media_source_id} not found")
        
        return {
            "item_id": item_id,
            "media_source": media_source,
            "stream_url": f"/Audio/{item_id}/universal.mp3"
        }
    
    async def get_similar_items(
        self,
        item_id: str,
        limit: int = 10
    ) -> list[dict[str, Any]]:
        """Get similar items.
        
        Args:
            item_id: The reference item ID
            limit: Maximum number of similar items
            
        Returns:
            List of similar items
        """
        params = {"limit": limit}
        data = await self._get(f"/Movies/{item_id}/Similar", params=params)
        return data.get("Items", [])
    
    async def get_item_images(self, item_id: str) -> dict[str, Any]:
        """Get image URLs for an item.
        
        Args:
            item_id: The item ID
            
        Returns:
            Dictionary of image types and their URLs
        """
        return await self._get(f"/Items/{item_id}/Images")
    
    async def health_check(self) -> bool:
        """Check if Jellyfin server is healthy."""
        try:
            await self._get("/System/Info")
            return True
        except Exception:
            return False
    
    async def get_system_info(self) -> dict[str, Any]:
        """Get system information."""
        return await self._get("/System/Info")
    
    async def get_activity_log(self, limit: int = 50) -> list[dict[str, Any]]:
        """Get recent activity log entries.
        
        Args:
            limit: Maximum number of entries
            
        Returns:
            List of activity log entries
        """
        params = {"limit": limit}
        data = await self._get("/System/ActivityLog/Entries", params=params)
        return data.get("Items", [])