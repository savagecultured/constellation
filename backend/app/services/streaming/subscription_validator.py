"""Subscription tier validation for stream access."""
from typing import Any, Optional
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.user import User
from app.models.subscription import Subscription, SubscriptionTier, SubscriptionStatus


class SubscriptionValidator:
    """Validates user subscription tiers and stream access."""
    
    # Tier hierarchy (higher = more access)
    TIER_HIERARCHY = {
        SubscriptionTier.FREE: 0,
        SubscriptionTier.BASIC: 1,
        SubscriptionTier.PREMIUM: 2,
        SubscriptionTier.FAMILY: 3
    }
    
    # Max streams per tier
    TIER_MAX_STREAMS = {
        SubscriptionTier.FREE: settings.FREE_MAX_STREAMS,
        SubscriptionTier.BASIC: settings.BASIC_MAX_STREAMS,
        SubscriptionTier.PREMIUM: settings.PREMIUM_MAX_STREAMS,
        SubscriptionTier.FAMILY: settings.FAMILY_MAX_STREAMS
    }
    
    def __init__(self, db: Session):
        """Initialize the validator with a database session."""
        self.db = db
    
    def get_user_subscription(self, user_id: int) -> Optional[Subscription]:
        """Get the user's subscription.
        
        Args:
            user_id: The user ID
            
        Returns:
            Subscription object if found, None otherwise
        """
        return self.db.query(Subscription).filter(
            Subscription.user_id == user_id
        ).first()
    
    def is_subscription_active(self, subscription: Optional[Subscription]) -> bool:
        """Check if subscription is active.
        
        Args:
            subscription: The subscription to check
            
        Returns:
            True if active, False otherwise
        """
        if subscription is None:
            return False
        
        return subscription.status in [
            SubscriptionStatus.ACTIVE,
            SubscriptionStatus.TRIALING
        ]
    
    def get_tier_max_streams(self, tier: SubscriptionTier) -> int:
        """Get the maximum concurrent streams for a tier.
        
        Args:
            tier: The subscription tier
            
        Returns:
            Maximum number of concurrent streams
        """
        return self.TIER_MAX_STREAMS.get(tier, 1)
    
    def can_access_media_type(
        self,
        subscription: Optional[Subscription],
        media_type: str
    ) -> bool:
        """Check if subscription allows access to a media type.
        
        Args:
            subscription: The user's subscription
            media_type: The media type (movie, music, series)
            
        Returns:
            True if access is allowed
        """
        # If no subscription, check if it's a free tier
        if subscription is None:
            return True  # Free users can access basic content
        
        tier = subscription.tier
        
        # Define tier access levels
        # FREE: basic access (some movies, music)
        # BASIC: + series
        # PREMIUM: + new releases
        # FAMILY: + all content
        
        if tier == SubscriptionTier.FREE:
            # Free tier can access music and some movies
            return media_type in ["music", "movie"]
        
        elif tier == SubscriptionTier.BASIC:
            # Basic tier adds series
            return media_type in ["music", "movie", "series"]
        
        elif tier == SubscriptionTier.PREMIUM:
            # Premium adds everything
            return True
        
        elif tier == SubscriptionTier.FAMILY:
            # Family has full access
            return True
        
        return False
    
    def validate_stream_access(
        self,
        user_id: int,
        media_type: str = "movie"
    ) -> dict[str, Any]:
        """Validate if user can access streaming.
        
        Args:
            user_id: The user ID
            media_type: The type of media being accessed
            
        Returns:
            Dictionary with validation result
        """
        # Get user and subscription
        user = self.db.query(User).filter(User.id == user_id).first()
        
        if user is None:
            return {
                "allowed": False,
                "reason": "user_not_found",
                "message": "User not found"
            }
        
        if not user.is_active:
            return {
                "allowed": False,
                "reason": "user_inactive",
                "message": "User account is inactive"
            }
        
        subscription = self.get_user_subscription(user_id)
        
        # Check if subscription is active
        if not self.is_subscription_active(subscription):
            return {
                "allowed": False,
                "reason": "subscription_inactive",
                "message": "Subscription is not active",
                "tier": subscription.tier.value if subscription else "none"
            }
        
        # Check media type access
        if not self.can_access_media_type(subscription, media_type):
            tier_name = subscription.tier.value if subscription else "free"
            return {
                "allowed": False,
                "reason": "tier_restriction",
                "message": f"Media type '{media_type}' requires a higher subscription tier",
                "current_tier": tier_name
            }
        
        # Get max streams for tier
        max_streams = self.get_tier_max_streams(
            subscription.tier if subscription else SubscriptionTier.FREE
        )
        
        return {
            "allowed": True,
            "tier": subscription.tier.value if subscription else "free",
            "max_streams": max_streams,
            "is_trial": subscription.is_in_trial_period if subscription else False
        }
    
    def get_tier_info(self, tier: SubscriptionTier) -> dict[str, Any]:
        """Get information about a subscription tier.
        
        Args:
            tier: The subscription tier
            
        Returns:
            Dictionary with tier information
        """
        return {
            "tier": tier.value,
            "max_streams": self.get_tier_max_streams(tier),
            "level": self.TIER_HIERARCHY.get(tier, 0)
        }


def validate_subscription(
    db: Session,
    user_id: int,
    media_type: str = "movie"
) -> dict[str, Any]:
    """Validate user subscription for streaming."""
    validator = SubscriptionValidator(db)
    return validator.validate_stream_access(user_id, media_type)