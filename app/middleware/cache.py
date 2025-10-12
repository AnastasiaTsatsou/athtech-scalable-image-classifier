"""
Response caching middleware for image classification
"""

import hashlib
from typing import Dict, Any, Optional

import logging
from cachetools import TTLCache

logger = logging.getLogger(__name__)

# In-memory cache with TTL (Redis in production)
cache = TTLCache(maxsize=1000, ttl=3600)  # 1 hour TTL, max 1000 entries


def image_cache_key(image_bytes: bytes, top_k: int = 5) -> str:
    """Generate cache key for image classification request"""
    # Create hash of image + parameters
    # Use SHA256 for better distribution
    content = image_bytes + str(top_k).encode()
    return hashlib.sha256(content).hexdigest()


def get_cached_result(cache_key: str) -> Optional[Dict[str, Any]]:
    """Get cached classification result"""
    try:
        result = cache.get(cache_key)
        if result:
            logger.info(f"Cache hit for key: {cache_key[:8]}...")
        else:
            logger.info(f"Cache miss for key: {cache_key[:8]}...")
        return result
    except Exception as e:
        logger.warning(f"Cache get failed: {e}")
        return None


def set_cached_result(cache_key: str, result: Dict[str, Any]) -> None:
    """Cache classification result"""
    try:
        cache[cache_key] = result
        logger.info(
            f"Cached result for key: {cache_key[:8]}... "
            f"(cache size: {len(cache)})"
        )
    except Exception as e:
        logger.warning(f"Cache set failed: {e}")


def clear_cache() -> None:
    """Clear all cached results"""
    cache.clear()
    logger.info("Cache cleared")


def get_cache_stats() -> Dict[str, Any]:
    """Get cache statistics"""
    return {
        "cache_size": len(cache),
        "max_size": cache.maxsize,
        "ttl": cache.ttl,
    }
