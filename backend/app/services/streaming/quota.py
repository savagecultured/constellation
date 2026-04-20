"""Redis quota enforcement service."""
import redis.asyncio as redis
from typing import Any, Optional
from datetime import datetime, timedelta
import calendar

from app.core.config import settings
from app.models.subscription import SubscriptionTier, Subscription


class QuotaManager:
    """Manages monthly streaming quotas using Redis."""
    
    # Key structure: stream:{user_id}:{year}-{month}
    KEY_PREFIX = "stream"
    
    # Default quotas in bytes (GB to bytes)
    TIER_QUOTAS = {
        SubscriptionTier.FREE: settings.FREE_MONTHLY_QUOTA_GB * 1024 * 1024 * 1024,
        SubscriptionTier.BASIC: settings.BASIC_MONTHLY_QUOTA_GB * 1024 * 1024 * 1024,
        SubscriptionTier.PREMIUM: settings.PREMIUM_MONTHLY_QUOTA_GB * 1024 * 1024 * 1024,
        SubscriptionTier.FAMILY: settings.FAMILY_MONTHLY_QUOTA_GB * 1024 * 1024 * 1024
    }
    
    def __init__(self):
        """Initialize the quota manager."""
        self._redis: Optional[redis.Redis] = None
    
    async def _get_redis(self) -> redis.Redis:
        """Get or create Redis connection."""
        if self._redis is None:
            self._redis = redis.from_url(
                settings.REDIS_URL,
                max_connections=settings.REDIS_MAX_CONNECTIONS,
                socket_timeout=settings.REDIS_SOCKET_TIMEOUT,
                decode_responses=True
            )
        return self._redis
    
    async def close(self):
        """Close Redis connection."""
        if self._redis:
            await self._redis.close()
            self._redis = None
    
    def _get_month_key(self, user_id: int, year: int, month: int) -> str:
        """Generate the Redis key for a user's monthly quota.
        
        Args:
            user_id: The user ID
            year: The year
            month: The month (1-12)
            
        Returns:
            Redis key string
        """
        return f"{self.KEY_PREFIX}:{user_id}:{year}-{month:02d}"
    
    def _get_month_bounds(self, year: int, month: int) -> tuple[datetime, datetime]:
        """Get the start and end of a month.
        
        Args:
            year: The year
            month: The month (1-12)
            
        Returns:
            Tuple of (start_datetime, end_datetime)
        """
        start = datetime(year, month, 1)
        if month == 12:
            end = datetime(year + 1, 1, 1)
        else:
            end = datetime(year, month + 1, 1)
        return start, end
    
    def _get_ttl_seconds(self, year: int, month: int) -> int:
        """Calculate TTL in seconds until end of month.
        
        Args:
            year: The year
            month: The month
            
        Returns:
            TTL in seconds
        """
        _, end = self._get_month_bounds(year, month)
        now = datetime.utcnow()
        
        if end <= now:
            return 0  # Already expired
        
        return int((end - now).total_seconds())
    
    async def get_quota(self, user_id: int) -> dict[str, Any]:
        """Get user's current quota usage.
        
        Args:
            user_id: The user ID
            
        Returns:
            Dictionary with quota information
        """
        now = datetime.utcnow()
        
        # Get current month key
        key = self._get_month_key(user_id, now.year, now.month)
        
        r = await self._get_redis()
        
        # Get current usage
        usage = await r.get(key)
        usage_bytes = int(usage) if usage else 0
        
        return {
            "user_id": user_id,
            "year": now.year,
            "month": now.month,
            "usage_bytes": usage_bytes,
            "usage_gb": round(usage_bytes / (1024 * 1024 * 1024), 2)
        }
    
    async def check_quota(
        self,
        user_id: int,
        tier: SubscriptionTier,
        bytes_needed: int = 0
    ) -> dict[str, Any]:
        """Check if user has quota available.
        
        Args:
            user_id: The user ID
            tier: The user's subscription tier
            bytes_needed: Additional bytes needed (optional)
            
        Returns:
            Dictionary with quota check result
        """
        now = datetime.utcnow()
        key = self._get_month_key(user_id, now.year, now.month)
        
        r = await self._get_redis()
        
        # Get current usage
        usage = await r.get(key)
        current_usage = int(usage) if usage else 0
        
        # Get quota limit for tier
        quota_limit = self.TIER_QUOTAS.get(tier, self.TIER_QUOTAS[SubscriptionTier.FREE])
        
        # Calculate available
        available = max(0, quota_limit - current_usage)
        has_quota = available >= bytes_needed
        
        return {
            "allowed": has_quota,
            "user_id": user_id,
            "tier": tier.value,
            "quota_bytes": quota_limit,
            "quota_gb": round(quota_limit / (1024 * 1024 * 1024), 2),
            "used_bytes": current_usage,
            "used_gb": round(current_usage / (1024 * 1024 * 1024), 2),
            "available_bytes": available,
            "available_gb": round(available / (1024 * 1024 * 1024), 2),
            "year": now.year,
            "month": now.month
        }
    
    async def consume_quota(
        self,
        user_id: int,
        bytes_consumed: int,
        year: Optional[int] = None,
        month: Optional[int] = None
    ) -> dict[str, Any]:
        """Consume quota bytes.
        
        Args:
            user_id: The user ID
            bytes_consumed: Number of bytes to consume
            year: Optional year (defaults to current)
            month: Optional month (defaults to current)
            
        Returns:
            Dictionary with consumption result
        """
        now = datetime.utcnow()
        year = year or now.year
        month = month or now.month
        
        key = self._get_month_key(user_id, year, month)
        
        r = await self._get_redis()
        
        # Calculate TTL for key expiration
        ttl = self._get_ttl_seconds(year, month)
        
        # Increment the counter
        new_value = await r.incrby(key, bytes_consumed)
        
        # Set expiry if not already set
        if ttl > 0:
            await r.expire(key, ttl)
        
        return {
            "user_id": user_id,
            "bytes_consumed": bytes_consumed,
            "new_total_bytes": new_value,
            "new_total_gb": round(new_value / (1024 * 1024 * 1024), 2),
            "year": year,
            "month": month
        }
    
    async def reset_quota(self, user_id: int) -> bool:
        """Reset a user's quota for the current month.
        
        Args:
            user_id: The user ID
            
        Returns:
            True if reset successfully
        """
        now = datetime.utcnow()
        key = self._get_month_key(user_id, now.year, now.month)
        
        r = await self._get_redis()
        
        await r.set(key, 0)
        await r.expire(key, self._get_ttl_seconds(now.year, now.month))
        
        return True
    
    async def get_all_quotas(
        self,
        limit: int = 100
    ) -> list[dict[str, Any]]:
        """Get quota info for all users.
        
        Note: This is expensive and should be used with caution.
        
        Args:
            limit: Maximum number of users
            
        Returns:
            List of quota information
        """
        r = await self._get_redis()
        
        # Find all stream keys
        keys = []
        async for key in r.scan_iter(match=f"{self.KEY_PREFIX}:*"):
            keys.append(key)
            if len(keys) >= limit * 10:  # Safety limit
                break
        
        quotas = []
        for key in keys[:limit]:
            usage = await r.get(key)
            if usage:
                # Parse key to get user_id
                parts = key.split(":")
                if len(parts) >= 2:
                    user_id = int(parts[1])
                    quotas.append({
                        "user_id": user_id,
                        "used_bytes": int(usage),
                        "used_gb": round(int(usage) / (1024 * 1024 * 1024), 2)
                    })
        
        return quotas
    
    async def cleanup_expired(self) -> int:
        """Clean up expired quota keys.
        
        Returns:
            Number of keys cleaned up
        """
        r = await self._get_redis()
        
        cleaned = 0
        async for key in r.scan_iter(match=f"{self.KEY_PREFIX}:*"):
            ttl = await r.ttl(key)
            if ttl <= 0:
                await r.delete(key)
                cleaned += 1
        
        return cleaned


# Global instance
quota_manager = QuotaManager()


async def get_quota(user_id: int) -> dict[str, Any]:
    """Get user quota."""
    return await quota_manager.get_quota(user_id)


async def check_quota(
    user_id: int,
    tier: SubscriptionTier,
    bytes_needed: int = 0
) -> dict[str, Any]:
    """Check user quota."""
    return await quota_manager.check_quota(user_id, tier, bytes_needed)


async def consume_quota(
    user_id: int,
    bytes_consumed: int
) -> dict[str, Any]:
    """Consume quota."""
    return await quota_manager.consume_quota(user_id, bytes_consumed)