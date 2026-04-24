import hashlib
import json
import logging
import threading
import time
from typing import Any, Dict, Optional
from collections import OrderedDict
from server_core import config_core
logger = logging.getLogger(__name__)

COMMAND_TIMEOUT = config_core.get("COMMAND_TIMEOUT", 300)  # 5 minutes default timeout
CACHE_SIZE = config_core.get("CACHE_SIZE", 1000)
CACHE_TTL = config_core.get("CACHE_TTL", 3600)  # 1 hour default TTL

class CommandResultCache:
    """Advanced caching system for command results"""

    def __init__(self, max_size: int = CACHE_SIZE, ttl: int = CACHE_TTL):
        self.cache = OrderedDict()
        self.max_size = max_size
        self.ttl = ttl
        self.stats = {"hits": 0, "misses": 0, "evictions": 0}
        self._lock = threading.RLock()

    def _generate_key(self, command: str, params: Dict[str, Any]) -> str:
        """Generate cache key from command and parameters"""
        key_data = f"{command}:{json.dumps(params, sort_keys=True)}"
        return hashlib.sha256(key_data.encode()).hexdigest()

    def _is_expired(self, timestamp: float) -> bool:
        """Check if cache entry is expired"""
        return time.time() - timestamp > self.ttl

    def get(self, command: str, params: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Get cached result if available and not expired"""
        key = self._generate_key(command, params)

        with self._lock:
            if key in self.cache:
                timestamp, data = self.cache[key]
                if not self._is_expired(timestamp):
                    # Move to end (most recently used)
                    self.cache.move_to_end(key)
                    self.stats["hits"] += 1
                    logger.info(f"💾 Cache HIT for command: {command}")
                    return data
                else:
                    # Remove expired entry
                    del self.cache[key]

            self.stats["misses"] += 1
            logger.info(f"🔍 Cache MISS for command: {command}")
            return None

    def set(self, command: str, params: Dict[str, Any], result: Dict[str, Any]):
        """Store result in cache"""
        key = self._generate_key(command, params)

        with self._lock:
            # Remove oldest entries if cache is full
            while len(self.cache) >= self.max_size:
                oldest_key = next(iter(self.cache))
                del self.cache[oldest_key]
                self.stats["evictions"] += 1

            self.cache[key] = (time.time(), result)
            logger.info(f"💾 Cached result for command: {command}")

    def clear(self):
        """Clear all cached entries and reset statistics"""
        with self._lock:
            self.cache.clear()
            self.stats = {"hits": 0, "misses": 0, "evictions": 0}

    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        with self._lock:
            total_requests = self.stats["hits"] + self.stats["misses"]
            hit_rate = (self.stats["hits"] / total_requests * 100) if total_requests > 0 else 0

            return {
                "size": len(self.cache),
                "max_size": self.max_size,
                "hit_rate": f"{hit_rate:.1f}%",
                "hits": self.stats["hits"],
                "misses": self.stats["misses"],
                "evictions": self.stats["evictions"]
            }
