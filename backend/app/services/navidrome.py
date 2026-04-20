"""Navidrome API client wrapper."""
from typing import Any, Optional
import httpx

from app.services.base_media import MediaServerClient


class NavidromeClient(MediaServerClient):
    """Navidrome music server API client."""
    
    def __init__(
        self,
        base_url: str,
        api_key: str,
        timeout: float = 30.0
    ):
        """Initialize the Navidrome client.
        
        Args:
            base_url: The base URL of the Navidrome server
            api_key: Navidrome API key
            timeout: Request timeout in seconds
        """
        super().__init__(base_url, api_key, timeout)
    
    async def _get_client(self) -> httpx.AsyncClient:
        """Get or create the HTTP client with Navidrome authentication."""
        if self._client is None:
            self._client = httpx.AsyncClient(
                base_url=self.base_url,
                headers={"X-Api-Key": self.api_key},
                timeout=self.timeout
            )
        return self._client
    
    async def get_libraries(self) -> list[dict[str, Any]]:
        """Get all music libraries from Navidrome."""
        # Navidrome doesn't have traditional libraries like Jellyfin
        # Instead, it has music folders and categories
        albums = await self._get("/album", params={"size": 1})
        
        # Return folder-like structures
        return [
            {"id": "all", "name": "All Music", "type": "music"},
            {"id": "recently_added", "name": "Recently Added", "type": "music"},
            {"id": "recently_played", "name": "Recently Played", "type": "music"},
            {"id": "most_played", "name": "Most Played", "type": "music"}
        ]
    
    async def get_library_items(
        self,
        library_id: str,
        start_index: int = 0,
        limit: int = 100
    ) -> list[dict[str, Any]]:
        """Get items from a specific library/category.
        
        Args:
            library_id: The library ID (or special category)
            start_index: Starting index for pagination
            limit: Maximum number of items to return
            
        Returns:
            List of items in the library
        """
        params = {
            "offset": start_index,
            "max": limit
        }
        
        # Handle special categories
        if library_id == "all":
            return await self._get("/album", params=params)
        elif library_id == "recently_added":
            params["sort"] = "recentlyAdded"
            params["order"] = "desc"
            return await self._get("/album", params=params)
        elif library_id == "recently_played":
            params["sort"] = "lastPlayed"
            params["order"] = "desc"
            return await self._get("/album", params=params)
        elif library_id == "most_played":
            params["sort"] = "playCount"
            params["order"] = "desc"
            return await self._get("/album", params=params)
        else:
            # Assume it's a specific album ID
            return await self._get(f"/album/{library_id}", params=params)
    
    async def get_item(self, item_id: str) -> dict[str, Any]:
        """Get a specific item by ID."""
        # Check if it's an album or artist
        try:
            album = await self._get(f"/album/{item_id}")
            if album:
                return album
        except Exception:
            pass
        
        try:
            artist = await self._get(f"/artist/{item_id}")
            if artist:
                return artist
        except Exception:
            pass
        
        try:
            song = await self._get(f"/song/{item_id}")
            if song:
                return song
        except Exception:
            pass
        
        raise ValueError(f"Item {item_id} not found")
    
    async def get_albums(
        self,
        start_index: int = 0,
        limit: int = 100
    ) -> list[dict[str, Any]]:
        """Get all albums.
        
        Args:
            start_index: Starting index for pagination
            limit: Maximum number of albums
            
        Returns:
            List of albums
        """
        params = {
            "offset": start_index,
            "max": limit
        }
        data = await self._get("/album", params=params)
        return data if isinstance(data, list) else []
    
    async def get_artists(
        self,
        start_index: int = 0,
        limit: int = 100
    ) -> list[dict[str, Any]]:
        """Get all artists.
        
        Args:
            start_index: Starting index for pagination
            limit: Maximum number of artists
            
        Returns:
            List of artists
        """
        params = {
            "offset": start_index,
            "max": limit
        }
        data = await self._get("/artist", params=params)
        return data if isinstance(data, list) else []
    
    async def get_artist_albums(self, artist_id: str) -> list[dict[str, Any]]:
        """Get albums by a specific artist.
        
        Args:
            artist_id: The artist ID
            
        Returns:
            List of albums by the artist
        """
        return await self._get(f"/artist/{artist_id}/albums")
    
    async def get_album_songs(self, album_id: str) -> list[dict[str, Any]]:
        """Get songs from a specific album.
        
        Args:
            album_id: The album ID
            
        Returns:
            List of songs in the album
        """
        return await self._get(f"/album/{album_id}/songs")
    
    async def get_playlists(self) -> list[dict[str, Any]]:
        """Get all playlists.
        
        Returns:
            List of playlists
        """
        return await self._get("/playlist")
    
    async def get_playlist_items(self, playlist_id: str) -> list[dict[str, Any]]:
        """Get items in a specific playlist.
        
        Args:
            playlist_id: The playlist ID
            
        Returns:
            List of items in the playlist
        """
        return await self._get(f"/playlist/{playlist_id}")
    
    async def search_items(
        self,
        query: str,
        limit: int = 20
    ) -> dict[str, list[dict[str, Any]]]:
        """Search for items.
        
        Args:
            query: Search query string
            limit: Maximum number of results per category
            
        Returns:
            Dictionary with search results organized by type
        """
        params = {
            "q": query,
            "max": limit
        }
        
        # Navidrome has a unified search endpoint
        data = await self._get("/search", params=params)
        
        return {
            "artists": data.get("artists", [])[:limit],
            "albums": data.get("albums", [])[:limit],
            "songs": data.get("songs", [])[:limit]
        }
    
    async def search_albums(self, query: str, limit: int = 20) -> list[dict[str, Any]]:
        """Search for albums.
        
        Args:
            query: Search query string
            limit: Maximum number of results
            
        Returns:
            List of matching albums
        """
        params = {
            "q": query,
            "max": limit
        }
        data = await self._get("/album", params=params)
        return data if isinstance(data, list) else []
    
    async def search_artists(self, query: str, limit: int = 20) -> list[dict[str, Any]]:
        """Search for artists.
        
        Args:
            query: Search query string
            limit: Maximum number of results
            
        Returns:
            List of matching artists
        """
        params = {
            "q": query,
            "max": limit
        }
        data = await self._get("/artist", params=params)
        return data if isinstance(data, list) else []
    
    async def search_songs(self, query: str, limit: int = 20) -> list[dict[str, Any]]:
        """Search for songs.
        
        Args:
            query: Search query string
            limit: Maximum number of results
            
        Returns:
            List of matching songs
        """
        params = {
            "q": query,
            "max": limit
        }
        data = await self._get("/song", params=params)
        return data if isinstance(data, list) else []
    
    async def get_itemPlaybackInfo(self, item_id: str) -> dict[str, Any]:
        """Get playback information for an item.
        
        For Navidrome, this returns the stream URL.
        
        Args:
            item_id: The item ID
            
        Returns:
            Playback information including stream URL
        """
        return {
            "id": item_id,
            "stream_url": f"/rest/song/{item_id}/download",
            "format": "audio"
        }
    
    async def get_stream_url(
        self,
        item_id: str,
        max_bitrate: Optional[int] = None
    ) -> dict[str, Any]:
        """Get stream URL for a song.
        
        Args:
            item_id: The song ID
            max_bitrate: Optional maximum bitrate
            
        Returns:
            Stream URL information
        """
        params = {}
        if max_bitrate:
            params["maxBitRate"] = max_bitrate
        
        return {
            "id": item_id,
            "stream_url": f"/rest/song/{item_id}/download",
            "params": params
        }
    
    async def get_album_art(self, album_id: str) -> dict[str, Any]:
        """Get album artwork information.
        
        Args:
            album_id: The album ID
            
        Returns:
            Artwork information including URL
        """
        return {
            "album_id": album_id,
            "art_url": f"/rest/getCoverArt.view?id={album_id}&size=500"
        }
    
    async def get_artist_image(self, artist_id: str) -> dict[str, Any]:
        """Get artist image information.
        
        Args:
            artist_id: The artist ID
            
        Returns:
            Image information including URL
        """
        return {
            "artist_id": artist_id,
            "image_url": f"/rest/getCoverArt.view?id={artist_id}&size=500"
        }
    
    async def health_check(self) -> bool:
        """Check if Navidrome server is healthy."""
        try:
            await self._get("/health")
            return True
        except Exception:
            try:
                await self._get("/")
                return True
            except Exception:
                return False
    
    async def get_server_info(self) -> dict[str, Any]:
        """Get server information."""
        return await self._get("/")
    
    async def get_genres(self) -> list[dict[str, Any]]:
        """Get all music genres.
        
        Returns:
            List of genres
        """
        return await self._get("/genre")
    
    async def get_genre_albums(self, genre: str) -> list[dict[str, Any]]:
        """Get albums by genre.
        
        Args:
            genre: The genre name
            
        Returns:
            List of albums in the genre
        """
        return await self._get(f"/genre/{genre}/albums")