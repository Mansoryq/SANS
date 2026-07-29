import os
import json
import logging
import redis
from functools import wraps
from typing import Callable, Any, Optional
from redis import Redis
from app.core.config import settings

logger = logging.getLogger(__name__)

# Initialize Redis connection
redis_client: Optional[Redis] = None
REDIS_URL = settings.REDIS_URL

def get_redis_client() -> Redis:
    global redis_client
    if redis_client is None:
        try:
            redis_client = redis.Redis.from_url(REDIS_URL, decode_responses=True)
        except Exception as e:
            logger.error(f"Failed to connect to Redis: {e}")
            redis_client = None
    return redis_client

def cache_response(ttl_seconds: int = 60):
    """
    Simple Redis cache decorator for synchronous functions returning Pydantic models or dicts.
    """
    def decorator(func: Callable):
        @wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            if not redis_client:
                return func(*args, **kwargs)
                
            # Create a cache key based on function name and arguments
            key_parts = [func.__name__]
            key_parts.extend([str(a) for a in args[1:]]) # skip self if method
            key_parts.extend([f"{k}:{v}" for k, v in sorted(kwargs.items())])
            cache_key = "cache:" + ":".join(key_parts)
            
            try:
                cached_value = redis_client.get(cache_key)
                if cached_value:
                    logger.debug(f"Cache hit for {cache_key}")
                    # Note: In a real app, we need to deserialize back to the ORM/Pydantic models.
                    # For simplicity, if we hit the cache, we return raw dicts which FastAPI handles.
                    return json.loads(cached_value)
            except Exception as e:
                logger.warning(f"Redis get error: {e}")
                
            # Execute function
            result = func(*args, **kwargs)
            
            # Cache the result
            try:
                if result is not None:
                    # Convert ORM objects to dicts for JSON serialization
                    if isinstance(result, list):
                        # Pydantic v2 support via model_dump if it's a schema, else handle ORM
                        serializable = []
                        for item in result:
                            if hasattr(item, "__dict__"):
                                d = {k: (str(v) if v is not None else None) for k, v in item.__dict__.items() if not k.startswith("_")}
                                serializable.append(d)
                            else:
                                serializable.append(item)
                        redis_client.setex(cache_key, ttl_seconds, json.dumps(serializable))
            except Exception as e:
                logger.warning(f"Redis set error: {e}")
                
            return result
        return wrapper
    return decorator

def invalidate_cache(prefix: str):
    """Invalidate all keys matching a prefix."""
    if not redis_client:
        return
    try:
        keys = redis_client.keys(f"cache:{prefix}*")
        if keys:
            redis_client.delete(*keys)
    except Exception as e:
        logger.warning(f"Redis delete error: {e}")
