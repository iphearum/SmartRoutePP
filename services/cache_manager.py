# services/cache_manager.py
import asyncio
import json
import time
from typing import Optional, Dict, Any
import logging

logger = logging.getLogger(__name__)

class CacheManager:
    def __init__(self):
        self.memory_cache: Dict[str, Dict] = {}
        self.cache_stats = {"hits": 0, "misses": 0}
    
    async def get(self, key: str) -> Optional[Dict]:
        """Get from cache with stats"""
        if key in self.memory_cache:
            entry = self.memory_cache[key]
            if entry["expires_at"] > time.time():
                self.cache_stats["hits"] += 1
                return entry["data"]
            else:
                del self.memory_cache[key]
        
        self.cache_stats["misses"] += 1
        return None
    
    async def set(self, key: str, data: Dict, ttl: int = 3600):
        """Set cache with TTL"""
        self.memory_cache[key] = {
            "data": data,
            "expires_at": time.time() + ttl
        }
        
        # Cleanup old entries periodically
        if len(self.memory_cache) > 1000:
            await self._cleanup_expired()
    
    async def _cleanup_expired(self):
        """Remove expired entries"""
        current_time = time.time()
        expired_keys = [
            key for key, entry in self.memory_cache.items()
            if entry["expires_at"] <= current_time
        ]
        
        for key in expired_keys:
            del self.memory_cache[key]
        
        logger.info(f"Cleaned up {len(expired_keys)} expired cache entries")
    
    async def warm_popular_routes(self):
        """Warm cache with popular routes"""
        # Implement popular route precomputation
        logger.info("Starting cache warming for popular routes")
        # Add your popular route coordinates here
        popular_routes = [
            (11.5449, 104.8922, 11.5564, 104.9282),  # Example coordinates
            # Add more popular routes
        ]
        
        for s_lat, s_lon, d_lat, d_lon in popular_routes:
            try:
                # Precompute and cache these routes
                pass
            except Exception as e:
                logger.warning(f"Failed to precompute route: {e}")