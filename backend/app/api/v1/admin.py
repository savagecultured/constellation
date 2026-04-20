from typing import Annotated, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from sqlalchemy import func, or_

from app.api.dependencies import get_db, CurrentAdminUser, DBSession
from app.core.security import get_password_hash, create_user
from app.models.user import User
from app.models.subscription import Subscription, SubscriptionTier, SubscriptionStatus
from app.schemas.user import UserResponse, UserCreate, UserUpdate, UserListResponse

router = APIRouter()


# ================== User CRUD Operations ==================


@router.post("/users", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def create_user_endpoint(
    user_data: UserCreate,
    db: DBSession,
    current_admin: CurrentAdminUser
):
    """
    Create a new user. Admin only.
    """
    # Check if username already exists
    existing_user = db.query(User).filter(User.username == user_data.username).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already registered"
        )
    
    # Check if email already exists
    existing_email = db.query(User).filter(User.email == user_data.email).first()
    if existing_email:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    
    # Create new user
    hashed_password = get_password_hash(user_data.password)
    new_user = User(
        username=user_data.username,
        email=user_data.email,
        full_name=user_data.full_name,
        hashed_password=hashed_password,
        is_active=True,
        is_admin=False
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return new_user


@router.get("/users", response_model=UserListResponse)
def list_users(
    db: DBSession,
    current_admin: CurrentAdminUser,
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(50, ge=1, le=100, description="Maximum records to return"),
    search: Optional[str] = Query(None, description="Search by username or email"),
    is_active: Optional[bool] = Query(None, description="Filter by active status"),
    is_admin: Optional[bool] = Query(None, description="Filter by admin status")
):
    """
    List all users with pagination and filters. Admin only.
    """
    query = db.query(User)
    
    # Apply search filter
    if search:
        query = query.filter(
            or_(
                User.username.ilike(f"%{search}%"),
                User.email.ilike(f"%{search}%")
            )
        )
    
    # Apply active status filter
    if is_active is not None:
        query = query.filter(User.is_active == is_active)
    
    # Apply admin status filter
    if is_admin is not None:
        query = query.filter(User.is_admin == is_admin)
    
    # Get total count
    total = query.count()
    
    # Apply pagination
    users = query.order_by(User.created_at.desc()).offset(skip).limit(limit).all()
    
    return UserListResponse(users=users, total=total)


@router.get("/users/{user_id}", response_model=UserResponse)
def get_user(
    user_id: int,
    db: DBSession,
    current_admin: CurrentAdminUser
):
    """
    Get a specific user by ID. Admin only.
    """
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    return user


@router.put("/users/{user_id}", response_model=UserResponse)
def update_user(
    user_id: int,
    user_data: UserUpdate,
    db: DBSession,
    current_admin: CurrentAdminUser
):
    """
    Update a user. Admin only.
    """
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # Update fields if provided
    if user_data.email is not None:
        # Check if email is already taken by another user
        existing = db.query(User).filter(
            User.email == user_data.email,
            User.id != user_id
        ).first()
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered to another user"
            )
        user.email = user_data.email
    
    if user_data.full_name is not None:
        user.full_name = user_data.full_name
    
    if user_data.password is not None:
        user.hashed_password = get_password_hash(user_data.password)
    
    db.commit()
    db.refresh(user)
    return user


@router.delete("/users/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_user(
    user_id: int,
    db: DBSession,
    current_admin: CurrentAdminUser
):
    """
    Delete a user. Admin only.
    """
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # Prevent deleting yourself
    if user.id == current_admin.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot delete your own account"
        )
    
    db.delete(user)
    db.commit()
    return None


# ================== User Status Management ==================


@router.post("/users/{user_id}/activate", response_model=UserResponse)
def activate_user(
    user_id: int,
    db: DBSession,
    current_admin: CurrentAdminUser
):
    """
    Activate a user account. Admin only.
    """
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    user.is_active = True
    db.commit()
    db.refresh(user)
    return user


@router.post("/users/{user_id}/deactivate", response_model=UserResponse)
def deactivate_user(
    user_id: int,
    db: DBSession,
    current_admin: CurrentAdminUser
):
    """
    Deactivate a user account. Admin only.
    """
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # Prevent deactivating yourself
    if user.id == current_admin.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot deactivate your own account"
        )
    
    user.is_active = False
    db.commit()
    db.refresh(user)
    return user


@router.post("/users/{user_id}/make-admin", response_model=UserResponse)
def make_user_admin(
    user_id: int,
    db: DBSession,
    current_admin: CurrentAdminUser
):
    """
    Grant admin privileges to a user. Admin only.
    """
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    user.is_admin = True
    db.commit()
    db.refresh(user)
    return user


@router.post("/users/{user_id}/remove-admin", response_model=UserResponse)
def remove_admin_privileges(
    user_id: int,
    db: DBSession,
    current_admin: CurrentAdminUser
):
    """
    Remove admin privileges from a user. Admin only.
    """
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # Prevent removing your own admin privileges
    if user.id == current_admin.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot remove your own admin privileges"
        )
    
    user.is_admin = False
    db.commit()
    db.refresh(user)
    return user


# ================== Admin Dashboard Data ==================


class DashboardStatsResponse(status.HTTP_200_OK):
    """Response model for dashboard statistics."""
    def __init__(self, **data):
        self.total_users = data.get("total_users", 0)
        self.active_users = data.get("active_users", 0)
        self.inactive_users = data.get("inactive_users", 0)
        self.admin_users = data.get("admin_users", 0)
        self.total_subscriptions = data.get("total_subscriptions", 0)
        self.free_subscriptions = data.get("free_subscriptions", 0)
        self.basic_subscriptions = data.get("basic_subscriptions", 0)
        self.premium_subscriptions = data.get("premium_subscriptions", 0)
        self.family_subscriptions = data.get("family_subscriptions", 0)
        self.active_subscriptions = data.get("active_subscriptions", 0)
        self.trial_subscriptions = data.get("trial_subscriptions", 0)
        super().__init__()


@router.get("/dashboard/stats")
def get_dashboard_stats(
    db: DBSession,
    current_admin: CurrentAdminUser
):
    """
    Get dashboard statistics. Admin only.
    """
    # User statistics
    total_users = db.query(User).count()
    active_users = db.query(User).filter(User.is_active == True).count()
    inactive_users = db.query(User).filter(User.is_active == False).count()
    admin_users = db.query(User).filter(User.is_admin == True).count()
    
    # Subscription statistics
    total_subscriptions = db.query(Subscription).count()
    free_subscriptions = db.query(Subscription).filter(Subscription.tier == SubscriptionTier.FREE).count()
    basic_subscriptions = db.query(Subscription).filter(Subscription.tier == SubscriptionTier.BASIC).count()
    premium_subscriptions = db.query(Subscription).filter(Subscription.tier == SubscriptionTier.PREMIUM).count()
    family_subscriptions = db.query(Subscription).filter(Subscription.tier == SubscriptionTier.FAMILY).count()
    active_subscriptions = db.query(Subscription).filter(Subscription.status == SubscriptionStatus.ACTIVE).count()
    trial_subscriptions = db.query(Subscription).filter(Subscription.is_in_trial_period == True).count()
    
    return {
        "total_users": total_users,
        "active_users": active_users,
        "inactive_users": inactive_users,
        "admin_users": admin_users,
        "total_subscriptions": total_subscriptions,
        "free_subscriptions": free_subscriptions,
        "basic_subscriptions": basic_subscriptions,
        "premium_subscriptions": premium_subscriptions,
        "family_subscriptions": family_subscriptions,
        "active_subscriptions": active_subscriptions,
        "trial_subscriptions": trial_subscriptions
    }


@router.get("/dashboard/users/recent", response_model=UserListResponse)
def get_recent_users(
    db: DBSession,
    current_admin: CurrentAdminUser,
    limit: int = Query(10, ge=1, le=50, description="Number of recent users to return")
):
    """
    Get recently registered users. Admin only.
    """
    users = db.query(User).order_by(User.created_at.desc()).limit(limit).all()
    total = db.query(User).count()
    return UserListResponse(users=users, total=total)


@router.get("/dashboard/users/active", response_model=UserListResponse)
def get_active_users_list(
    db: DBSession,
    current_admin: CurrentAdminUser,
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100)
):
    """
    Get list of active users. Admin only.
    """
    query = db.query(User).filter(User.is_active == True)
    total = query.count()
    users = query.order_by(User.created_at.desc()).offset(skip).limit(limit).all()
    return UserListResponse(users=users, total=total)