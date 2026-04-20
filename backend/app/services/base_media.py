"""Base media server client."""
from abc import ABC, abstractmethod
from typing import Any, Optional
import httpx
from app.core.config import settings


class MediaServerClient(ABC):
    """Base class for media server API clients."""
    
    def __init__(
        self,
        base_url: str,
        api_key: Optional[str] = None,
        timeout: float = 30.0
    ):
        """Initialize the media server client.
        
        Args:
            base_url: The base URL of the media server API
            api_key: Optional API key for authentication
            timeout: Request timeout in seconds
        """
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        self.timeout = timeout
        self._client: Optional[httpx.AsyncClient] = None
    
    async def _get_client(self) -> httpx.AsyncClient:
        """Get or create the HTTP client."""
        if self._client is None:
            headers: dict[str, str] = {}
            if self.api_key:
                headers["X-Api-Key"] = self.api_key
            
            self._client = httpx.AsyncClient(
                base_url=self.base_url,
                headers=headers,
                timeout=self.timeout
            )
        return self._client
    
    async def close(self):
        """Close the HTTP client."""
        if self._client is not None:
            await self._client.aclose()
            self._client = None
    
    async def _get(self, endpoint: str, params: Optional[dict] = None) -> Any:
        """Make a GET request to the media server API."""
        client = await self._get_client()
        response = await client.get(endpoint, params=params)
        response.raise_for_status()
        return response.json()
    
    async def _post(
        self,
        endpoint: str,
        data: Optional[dict] = None,
        json: Optional[dict] = None
    ) -> Any:
        """Make a POST request to the media server API."""
        client = await self._get_client()
        response = await client.post(endpoint, data=data, json=json)
        response.raise_for_status()
        return response.json()
    
    # Abstract methods that must be implemented by subclasses
    
    @abstractmethod
    async def get_libraries(self) -> list[dict[str, Any]]:
        """Get all libraries from the media server."""
        pass
    
    @abstractmethod
    async def get_library_items(
        self,
        library_id: str,
        start_index: int = 0,
        limit: int = 100
    ) -> Any:
        """Get items from a specific library."""
        pass
    
    @abstractmethod
    async def get_item(self, item_id: str) -> dict[str, Any]:
        """Get a specific item by ID."""
        pass
    
    @abstractmethod
    async def search_items(
        self,
        query: str,
        limit: int = 20
    ) -> Any:
        """Search for items."""
        pass
    
    @abstractmethod
    async def get_itemPlaybackInfo(self, item_id: str) -> dict[str, Any]:
        """Get playback information for an item."""
        pass
    
    @abstractmethod
    async def health_check(self) -> bool:
        """Check if the media server is healthy."""
        pass