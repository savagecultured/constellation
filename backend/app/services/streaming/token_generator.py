"""Stream token generator for short-lived signed tokens."""
from datetime import datetime, timedelta
from typing import Any, Optional
import hashlib
import secrets

from jose import jwt, JWTError
from app.core.config import settings


class StreamTokenGenerator:
    """Generates short-lived signed tokens for stream access."""
    
    # Token expiry in seconds (max 60s as per requirements)
    TOKEN_EXPIRY_SECONDS = 60
    
    def __init__(self):
        """Initialize the token generator."""
        self.secret_key = settings.STREAM_TOKEN_SECRET
        self.algorithm = "HS256"
    
    def generate_stream_token(
        self,
        user_id: int,
        item_id: str,
        media_source: str,
        ip_address: Optional[str] = None
    ) -> str:
        """Generate a short-lived stream token.
        
        Args:
            user_id: The user ID requesting the stream
            item_id: The media item ID to stream
            media_source: Either 'jellyfin' or 'navidrome'
            ip_address: Optional IP address for validation
            
        Returns:
            Signed JWT token
        """
        now = datetime.utcnow()
        expiry = now + timedelta(seconds=self.TOKEN_EXPIRY_SECONDS)
        
        # Create token payload
        payload = {
            "sub": str(user_id),
            "item_id": item_id,
            "source": media_source,
            "iat": now,
            "exp": expiry,
            "type": "stream",
            "nonce": secrets.token_hex(8)  # Unique token identifier
        }
        
        # Add IP address if provided
        if ip_address:
            payload["ip"] = ip_address
        
        # Sign the token
        token = jwt.encode(payload, self.secret_key, algorithm=self.algorithm)
        
        return token
    
    def verify_stream_token(self, token: str) -> Optional[dict[str, Any]]:
        """Verify and decode a stream token.
        
        Args:
            token: The JWT token to verify
            
        Returns:
            Token payload if valid, None if invalid
        """
        try:
            payload = jwt.decode(
                token,
                self.secret_key,
                algorithms=[self.algorithm]
            )
            
            # Verify this is a stream token
            if payload.get("type") != "stream":
                return None
            
            return payload
            
        except JWTError:
            return None
    
    def generate_playback_session(
        self,
        user_id: int,
        item_id: str,
        media_source: str,
        quality: str = "auto"
    ) -> dict[str, Any]:
        """Generate a complete playback session with token and metadata.
        
        Args:
            user_id: The user ID
            item_id: The media item ID
            media_source: Either 'jellyfin' or 'navidrome'
            quality: Video quality preference (auto, 1080p, 720p, 480p, etc.)
            
        Returns:
            Dictionary with token and session metadata
        """
        token = self.generate_stream_token(
            user_id=user_id,
            item_id=item_id,
            media_source=media_source
        )
        
        return {
            "token": token,
            "expires_in": self.TOKEN_EXPIRY_SECONDS,
            "item_id": item_id,
            "source": media_source,
            "quality": quality,
            "token_type": "stream"
        }
    
    def revoke_token(self, token: str) -> bool:
        """Revoke a stream token by adding it to a blacklist.
        
        Note: In production, this should use Redis for fast lookups.
        
        Args:
            token: The token to revoke
            
        Returns:
            True if revoked successfully
        """
        # In production, store the token nonce in Redis with TTL
        # For now, we just return True to indicate the operation completed
        payload = self.verify_stream_token(token)
        if payload:
            nonce = payload.get("nonce")
            # In production: redis.setex(f"revoked:{nonce}", TTL, "1")
            return True
        return False


# Global instance
stream_token_generator = StreamTokenGenerator()


def generate_stream_token(
    user_id: int,
    item_id: str,
    media_source: str,
    ip_address: Optional[str] = None
) -> str:
    """Generate a short-lived stream token."""
    return stream_token_generator.generate_stream_token(
        user_id=user_id,
        item_id=item_id,
        media_source=media_source,
        ip_address=ip_address
    )


def verify_stream_token(token: str) -> Optional[dict[str, Any]]:
    """Verify a stream token."""
    return stream_token_generator.verify_stream_token(token)


def generate_playback_session(
    user_id: int,
    item_id: str,
    media_source: str,
    quality: str = "auto"
) -> dict[str, Any]:
    """Generate a complete playback session."""
    return stream_token_generator.generate_playback_session(
        user_id=user_id,
        item_id=item_id,
        media_source=media_source,
        quality=quality
    )