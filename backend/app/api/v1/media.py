"""Media library API endpoints."""
from typing import Annotated, Any, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel

from app.api.dependencies import CurrentUser
from app.services.media_factory import MediaClientFactory
from app.services.jellyfin import JellyfinClient
from app.services.navidrome import NavidromeClient

router = APIRouter()


# ================== Response Models ==================


class MediaLibraryResponse(BaseModel):
    """Response model for media library."""
    libraries: list[dict[str, Any]]
    source: str


class MediaSearchResponse(BaseModel):
    """Response model for media search."""
    query: str
    results: list[dict[str, Any]]
    total: int
    source: str


class PlaybackInfoResponse(BaseModel):
    """Response model for playback info."""
    item_id: str
    stream_url: str
    source: str


class HealthCheckResponse(BaseModel):
    """Response model for media server health check."""
    jellyfin: bool
    navidrome: bool


# ================== Health & Info Endpoints ==================


@router.get("/health", response_model=HealthCheckResponse)
async def check_media_health(
    current_user: CurrentUser
):
    """
    Check health status of all configured media servers.
    """
    health = await MediaClientFactory.health_check_all()
    return HealthCheckResponse(**health)


# ================== Jellyfin Endpoints ==================


@router.get("/jellyfin/libraries", response_model=MediaLibraryResponse)
async def get_jellyfin_libraries(
    current_user: CurrentUser
):
    """
    Get all libraries from Jellyfin server.
    """
    try:
        client = MediaClientFactory.get_jellyfin_client()
        libraries = await client.get_libraries()
        return MediaLibraryResponse(
            libraries=libraries,
            source="jellyfin"
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch Jellyfin libraries: {str(e)}"
        )


@router.get("/jellyfin/libraries/{library_id}/items")
async def get_jellyfin_library_items(
    library_id: str,
    current_user: CurrentUser,
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100)
):
    """
    Get items from a specific Jellyfin library.
    """
    try:
        client = MediaClientFactory.get_jellyfin_client()
        items = await client.get_library_items(library_id, skip, limit)
        return {"items": items, "source": "jellyfin", "library_id": library_id}
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch library items: {str(e)}"
        )


@router.get("/jellyfin/items/{item_id}")
async def get_jellyfin_item(
    item_id: str,
    current_user: CurrentUser
):
    """
    Get a specific item from Jellyfin.
    """
    try:
        client = MediaClientFactory.get_jellyfin_client()
        item = await client.get_item(item_id)
        return {"item": item, "source": "jellyfin"}
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch item: {str(e)}"
        )


@router.get("/jellyfin/items/{item_id}/playback")
async def get_jellyfin_playback_info(
    item_id: str,
    current_user: CurrentUser
):
    """
    Get playback information for a Jellyfin item.
    """
    try:
        client = MediaClientFactory.get_jellyfin_client()
        playback_info = await client.get_itemPlaybackInfo(item_id)
        return {
            "item_id": item_id,
            "playback_info": playback_info,
            "source": "jellyfin"
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get playback info: {str(e)}"
        )


# ================== Navidrome Endpoints ==================


@router.get("/navidrome/libraries", response_model=MediaLibraryResponse)
async def get_navidrome_libraries(
    current_user: CurrentUser
):
    """
    Get all libraries/categories from Navidrome server.
    """
    try:
        client = MediaClientFactory.get_navidrome_client()
        libraries = await client.get_libraries()
        return MediaLibraryResponse(
            libraries=libraries,
            source="navidrome"
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch Navidrome libraries: {str(e)}"
        )


@router.get("/navidrome/libraries/{library_id}/items")
async def get_navidrome_library_items(
    library_id: str,
    current_user: CurrentUser,
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100)
):
    """
    Get items from a specific Navidrome library/category.
    """
    try:
        client = MediaClientFactory.get_navidrome_client()
        items = await client.get_library_items(library_id, skip, limit)
        return {"items": items, "source": "navidrome", "library_id": library_id}
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch library items: {str(e)}"
        )


@router.get("/navidrome/albums")
async def get_navidrome_albums(
    current_user: CurrentUser,
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100)
):
    """
    Get all albums from Navidrome.
    """
    try:
        client = MediaClientFactory.get_navidrome_client()
        albums = await client.get_albums(skip, limit)
        return {"albums": albums, "source": "navidrome"}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch albums: {str(e)}"
        )


@router.get("/navidrome/artists")
async def get_navidrome_artists(
    current_user: CurrentUser,
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100)
):
    """
    Get all artists from Navidrome.
    """
    try:
        client = MediaClientFactory.get_navidrome_client()
        artists = await client.get_artists(skip, limit)
        return {"artists": artists, "source": "navidrome"}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch artists: {str(e)}"
        )


@router.get("/navidrome/albums/{album_id}/songs")
async def get_navidrome_album_songs(
    album_id: str,
    current_user: CurrentUser
):
    """
    Get songs from a specific Navidrome album.
    """
    try:
        client = MediaClientFactory.get_navidrome_client()
        songs = await client.get_album_songs(album_id)
        return {"album_id": album_id, "songs": songs, "source": "navidrome"}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch album songs: {str(e)}"
        )


@router.get("/navidrome/items/{item_id}")
async def get_navidrome_item(
    item_id: str,
    current_user: CurrentUser
):
    """
    Get a specific item from Navidrome (album, artist, or song).
    """
    try:
        client = MediaClientFactory.get_navidrome_client()
        item = await client.get_item(item_id)
        return {"item": item, "source": "navidrome"}
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch item: {str(e)}"
        )


# ================== Unified Search Endpoint ==================


@router.get("/search", response_model=MediaSearchResponse)
async def search_media(
    current_user: CurrentUser,
    query: str = Query(..., min_length=1, description="Search query"),
    source: Optional[str] = Query(None, description="Specific source to search (jellyfin/navidrome)"),
    limit: int = Query(20, ge=1, le=100)
):
    """
    Search for media across all configured media servers.
    """
    results = []
    
    sources_to_search = []
    if source == "jellyfin" or source is None:
        if MediaClientFactory._jellyfin_client is not None:
            sources_to_search.append("jellyfin")
    
    if source == "navidrome" or source is None:
        if MediaClientFactory._navidrome_client is not None:
            sources_to_search.append("navidrome")
    
    if not sources_to_search:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="No media servers configured"
        )
    
    for src in sources_to_search:
        try:
            if src == "jellyfin":
                client = MediaClientFactory.get_jellyfin_client()
                search_results = await client.search_items(query, limit)
                for item in search_results:
                    item["_source"] = "jellyfin"
                results.extend(search_results)
            elif src == "navidrome":
                client = MediaClientFactory.get_navidrome_client()
                search_results = await client.search_items(query, limit)
                # Handle the different response format from Navidrome
                if isinstance(search_results, dict):
                    for category, items in search_results.items():
                        for item in items:
                            item["_source"] = "navidrome"
                            item["_category"] = category
                        results.extend(items if isinstance(items, list) else [])
                else:
                    for item in search_results:
                        item["_source"] = "navidrome"
                    results.extend(search_results)
        except Exception as e:
            # Continue searching other sources if one fails
            continue
    
    return MediaSearchResponse(
        query=query,
        results=results[:limit],
        total=len(results),
        source=",".join(sources_to_search) if source is None else source
    )