"""Media metadata synchronization job."""
import asyncio
import logging
from datetime import datetime, timedelta
from typing import Optional

from app.services.media_factory import MediaClientFactory
from app.services.jellyfin import JellyfinClient
from app.services.navidrome import NavidromeClient

logger = logging.getLogger(__name__)


class MediaSyncJob:
    """Background job for synchronizing media metadata."""
    
    def __init__(
        self,
        sync_interval: int = 3600,  # Default: sync every hour
        batch_size: int = 100
    ):
        """Initialize the sync job.
        
        Args:
            sync_interval: Interval between syncs in seconds
            batch_size: Number of items to process per batch
        """
        self.sync_interval = sync_interval
        self.batch_size = batch_size
        self._running = False
        self._task: Optional[asyncio.Task] = None
    
    async def start(self):
        """Start the background sync job."""
        if self._running:
            logger.warning("Sync job is already running")
            return
        
        self._running = True
        self._task = asyncio.create_task(self._run_sync_loop())
        logger.info("Media sync job started")
    
    async def stop(self):
        """Stop the background sync job."""
        self._running = False
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
        logger.info("Media sync job stopped")
    
    async def _run_sync_loop(self):
        """Main sync loop."""
        while self._running:
            try:
                await self.sync_all()
            except Exception as e:
                logger.error(f"Sync job failed: {str(e)}")
            
            # Wait for the next sync interval
            await asyncio.sleep(self.sync_interval)
    
    async def sync_all(self):
        """Synchronize metadata from all configured media servers."""
        logger.info("Starting media metadata sync...")
        start_time = datetime.utcnow()
        
        results = {
            "jellyfin": {"success": False, "items_synced": 0, "error": None},
            "navidrome": {"success": False, "items_synced": 0, "error": None}
        }
        
        # Sync Jellyfin
        try:
            results["jellyfin"]["items_synced"] = await self._sync_jellyfin()
            results["jellyfin"]["success"] = True
        except Exception as e:
            results["jellyfin"]["error"] = str(e)
            logger.error(f"Jellyfin sync failed: {str(e)}")
        
        # Sync Navidrome
        try:
            results["navidrome"]["items_synced"] = await self._sync_navidrome()
            results["navidrome"]["success"] = True
        except Exception as e:
            results["navidrome"]["error"] = str(e)
            logger.error(f"Navidrome sync failed: {str(e)}")
        
        duration = (datetime.utcnow() - start_time).total_seconds()
        logger.info(
            f"Media sync completed in {duration:.2f}s: "
            f"Jellyfin={results['jellyfin']['items_synced']} items, "
            f"Navidrome={results['navidrome']['items_synced']} items"
        )
        
        return results
    
    async def _sync_jellyfin(self) -> int:
        """Sync metadata from Jellyfin.
        
        Returns:
            Number of items synchronized
        """
        try:
            client = MediaClientFactory.get_jellyfin_client()
        except ValueError:
            logger.warning("Jellyfin not configured, skipping sync")
            return 0
        
        total_synced = 0
        
        # Get all libraries
        libraries = await client.get_libraries()
        logger.info(f"Found {len(libraries)} Jellyfin libraries")
        
        for library in libraries:
            library_id = library.get("Id")
            library_name = library.get("Name", "Unknown")
            
            if not library_id:
                continue
            
            logger.info(f"Syncing library: {library_name}")
            
            # Process items in batches
            offset = 0
            while True:
                items = await client.get_library_items(
                    library_id,
                    start_index=offset,
                    limit=self.batch_size
                )
                
                if not items:
                    break
                
                # Here you would typically:
                # 1. Store/update item metadata in your database
                # 2. Update search indexes
                # 3. Generate thumbnails
                
                total_synced += len(items)
                offset += len(items)
                
                if len(items) < self.batch_size:
                    break
        
        return total_synced
    
    async def _sync_navidrome(self) -> int:
        """Sync metadata from Navidrome.
        
        Returns:
            Number of items synchronized
        """
        try:
            client = MediaClientFactory.get_navidrome_client()
        except ValueError:
            logger.warning("Navidrome not configured, skipping sync")
            return 0
        
        total_synced = 0
        
        # Get all albums
        offset = 0
        while True:
            albums = await client.get_albums(offset, self.batch_size)
            
            if not albums:
                break
            
            total_synced += len(albums)
            offset += len(albums)
            
            if len(albums) < self.batch_size:
                break
        
        # Get all artists
        offset = 0
        while True:
            artists = await client.get_artists(offset, self.batch_size)
            
            if not artists:
                break
            
            total_synced += len(artists)
            offset += len(artists)
            
            if len(artists) < self.batch_size:
                break
        
        logger.info(f"Synced {total_synced} Navidrome items")
        return total_synced
    
    async def sync_library(self, library_id: str, source: str):
        """Sync a specific library.
        
        Args:
            library_id: The library ID to sync
            source: Either 'jellyfin' or 'navidrome'
        """
        if source == "jellyfin":
            try:
                client = MediaClientFactory.get_jellyfin_client()
            except ValueError:
                raise ValueError("Jellyfin not configured")
            
            items = await client.get_library_items(library_id, 0, self.batch_size)
            return len(items)
        
        elif source == "navidrome":
            try:
                client = MediaClientFactory.get_navidrome_client()
            except ValueError:
                raise ValueError("Navidrome not configured")
            
            items = await client.get_library_items(library_id, 0, self.batch_size)
            return len(items)
        
        else:
            raise ValueError(f"Unknown source: {source}")


# Global sync job instance
media_sync_job = MediaSyncJob()


async def start_media_sync():
    """Start the media sync background job."""
    await media_sync_job.start()


async def stop_media_sync():
    """Stop the media sync background job."""
    await media_sync_job.stop()


async def trigger_sync():
    """Trigger an immediate sync."""
    return await media_sync_job.sync_all()