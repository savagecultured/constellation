"""Media server client factory."""
from typing import Optional
from app.core.config import settings
from app.services.base_media import MediaServerClient
from app.services.jellyfin import JellyfinClient
from app.services.navidrome import NavidromeClient


class MediaClientFactory:
    """Factory for creating media server clients."""
    
    _jellyfin_client: Optional[JellyfinClient] = None
    _navidrome_client: Optional[NavidromeClient] = None
    
    @classmethod
    def get_jellyfin_client(cls) -> JellyfinClient:
        """Get the Jellyfin client singleton."""
        if cls._jellyfin_client is None:
            if not settings.JELLYFIN_URL or not settings.JELLYFIN_API_KEY:
                raise ValueError("Jellyfin is not configured")
            cls._jellyfin_client = JellyfinClient(
                base_url=settings.JELLYFIN_URL,
                api_key=settings.JELLYFIN_API_KEY,
                timeout=settings.MEDIA_SERVER_TIMEOUT
            )
        return cls._jellyfin_client
    
    @classmethod
    def get_navidrome_client(cls) -> NavidromeClient:
        """Get the Navidrome client singleton."""
        if cls._navidrome_client is None:
            if not settings.NAVIDROME_URL or not settings.NAVIDROME_API_KEY:
                raise ValueError("Navidrome is not configured")
            cls._navidrome_client = NavidromeClient(
                base_url=settings.NAVIDROME_URL,
                api_key=settings.NAVIDROME_API_KEY,
                timeout=settings.MEDIA_SERVER_TIMEOUT
            )
        return cls._navidrome_client
    
    @classmethod
    async def close_all(cls):
        """Close all media server clients."""
        if cls._jellyfin_client:
            await cls._jellyfin_client.close()
            cls._jellyfin_client = None
        if cls._navidrome_client:
            await cls._navidrome_client.close()
            cls._navidrome_client = None
    
    @classmethod
    async def health_check_all(cls) -> dict[str, bool]:
        """Check health of all media servers."""
        results = {"jellyfin": False, "navidrome": False}
        
        if settings.JELLYFIN_URL and settings.JELLYFIN_API_KEY:
            try:
                client = cls.get_jellyfin_client()
                results["jellyfin"] = await client.health_check()
            except Exception:
                results["jellyfin"] = False
        
        if settings.NAVIDROME_URL and settings.NAVIDROME_API_KEY:
            try:
                client = cls.get_navidrome_client()
                results["navidrome"] = await client.health_check()
            except Exception:
                results["navidrome"] = False
        
        return results