"""Stream proxy API endpoints."""
from typing import Annotated, Any, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, Request, Response
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from app.api.dependencies import CurrentUser, DBSession
from app.services.streaming.token_generator import generate_stream_token, verify_stream_token
from app.services.streaming.subscription_validator import validate_subscription
from app.services.streaming.stream_limiter import start_stream, end_stream, get_active_streams
from app.services.streaming.analytics import record_stream_start, record_stream_end, stream_analytics
from app.services.streaming.traffic_router import get_stream_url, traffic_router

router = APIRouter()


# ================== Request/Response Models ==================


class StreamStartRequest(BaseModel):
    """Request to start a stream."""
    item_id: str
    source: str  # jellyfin or navidrome
    quality: str = "auto"


class StreamStartResponse(BaseModel):
    """Response for stream start."""
    session_id: str
    stream_token: str
    stream_url: str
    expires_in: int
    current_streams: int
    max_streams: int


class StreamEndRequest(BaseModel):
    """Request to end a stream."""
    session_id: str
    watch_time_seconds: int


class StreamTokenVerifyResponse(BaseModel):
    """Response for token verification."""
    valid: bool
    user_id: Optional[int] = None
    item_id: Optional[str] = None
    source: Optional[str] = None


# ================== Stream Endpoints ==================


@router.post("/start", response_model=StreamStartResponse)
async def start_streaming(
    request: StreamStartRequest,
    current_user: CurrentUser,
    db: DBSession
):
    """Start a new stream session.
    
    Validates subscription, checks concurrent stream limits, and generates
    a short-lived stream token.
    """
    # Validate subscription
    validation = validate_subscription(db, current_user.id, "movie")
    
    if not validation.get("allowed"):
        raise HTTPException(
            status_code=403,
            detail=validation
        )
    
    # Get max streams from validation
    max_streams = validation.get("max_streams", 1)
    
    # Check concurrent stream limit
    stream_result = start_stream(
        user_id=current_user.id,
        max_streams=max_streams,
        item_id=request.item_id,
        source=request.source
    )
    
    if not stream_result.get("allowed"):
        raise HTTPException(
            status_code=429,
            detail=stream_result
        )
    
    # Generate stream token
    stream_token = generate_stream_token(
        user_id=current_user.id,
        item_id=request.item_id,
        media_source=request.source
    )
    
    # Get stream URL
    try:
        stream_info = await get_stream_url(
            item_id=request.item_id,
            source=request.source,
            user_id=current_user.id,
            quality=request.quality
        )
    except ValueError as e:
        # Clean up the stream session
        end_stream(stream_result["session_id"])
        raise HTTPException(
            status_code=404,
            detail=str(e)
        )
    
    # Record analytics
    record_stream_start(
        user_id=current_user.id,
        item_id=request.item_id,
        source=request.source,
        session_id=stream_result["session_id"],
        quality=request.quality
    )
    
    return StreamStartResponse(
        session_id=stream_result["session_id"],
        stream_token=stream_token,
        stream_url=stream_info["stream_url"],
        expires_in=60,  # Token expires in 60 seconds
        current_streams=stream_result["current_streams"],
        max_streams=stream_result["max_streams"]
    )


@router.post("/end")
async def end_streaming(
    request: StreamEndRequest,
    current_user: CurrentUser
):
    """End a stream session."""
    # End the stream session
    success = end_stream(request.session_id)
    
    if not success:
        raise HTTPException(
            status_code=404,
            detail="Session not found"
        )
    
    # Record analytics
    record_stream_end(
        session_id=request.session_id,
        user_id=current_user.id,
        watch_time_seconds=request.watch_time_seconds,
        item_id=""  # Would need to track this
    )
    
    return {"message": "Stream ended successfully"}


@router.get("/active")
async def get_active_stream_sessions(
    current_user: CurrentUser
):
    """Get active stream sessions for the current user."""
    sessions = get_active_streams(current_user.id)
    
    return {
        "sessions": sessions,
        "count": len(sessions)
    }


# ================== Token Validation ==================


@router.get("/verify-token", response_model=StreamTokenVerifyResponse)
async def verify_stream_token_endpoint(
    token: str = Query(..., description="Stream token to verify")
):
    """Verify a stream token."""
    payload = verify_stream_token(token)
    
    if payload is None:
        return StreamTokenVerifyResponse(valid=False)
    
    return StreamTokenVerifyResponse(
        valid=True,
        user_id=int(payload.get("sub", 0)),
        item_id=payload.get("item_id"),
        source=payload.get("source")
    )


# ================== Stream Proxy ==================


@router.get("/proxy/{source}/{item_id}")
async def proxy_stream(
    source: str,
    item_id: str,
    request: Request,
    token: str = Query(..., description="Stream token")
):
    """Proxy stream requests to media servers.
    
    Validates the stream token before proxying.
    """
    # Verify token
    payload = verify_stream_token(token)
    
    if payload is None:
        raise HTTPException(
            status_code=401,
            detail="Invalid or expired stream token"
        )
    
    # Verify the item matches
    if payload.get("item_id") != item_id:
        raise HTTPException(
            status_code=403,
            detail="Token item mismatch"
        )
    
    # Verify the source matches
    if payload.get("source") != source:
        raise HTTPException(
            status_code=403,
            detail="Token source mismatch"
        )
    
    # Get range header if present
    range_header = request.headers.get("Range")
    
    # Proxy the stream
    try:
        response = await traffic_router.proxy_stream(
            item_id=item_id,
            source=source,
            range_header=range_header
        )
        
        return StreamingResponse(
            content=response.aiter_bytes(),
            status_code=response.status_code,
            headers=dict(response.headers),
            media_type=response.headers.get("Content-Type", "video/mp4")
        )
    
    except Exception as e:
        raise HTTPException(
            status_code=502,
            detail=f"Failed to proxy stream: {str(e)}"
        )


# ================== Analytics ==================


@router.get("/analytics/user")
async def get_user_stream_analytics(
    current_user: CurrentUser
):
    """Get streaming analytics for the current user."""
    stats = stream_analytics.get_user_stats(current_user.id)
    recent = stream_analytics.get_recent_streams(limit=50, user_id=current_user.id)
    
    return {
        "stats": stats,
        "recent_streams": recent
    }


@router.get("/analytics/popular")
async def get_popular_items(
    limit: int = Query(10, ge=1, le=100),
    days: int = Query(7, ge=1, le=90)
):
    """Get popular media items."""
    popular = stream_analytics.get_popular_items(limit=limit, days=days)
    
    return {"popular": popular}


@router.get("/analytics/daily")
async def get_daily_analytics(
    date: Optional[str] = Query(None, description="Date in YYYY-MM-DD format")
):
    """Get daily streaming analytics."""
    stats = stream_analytics.get_daily_stats(date)
    active_sessions = stream_analytics.get_active_sessions_count()
    
    return {
        "date": date or "today",
        "stats": stats,
        "active_sessions": active_sessions
    }