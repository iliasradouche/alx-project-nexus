from django.core.cache import cache
from django.conf import settings
from functools import wraps
import hashlib
import json
from typing import Any, Optional


def generate_cache_key(prefix: str, *args, **kwargs) -> str:
    """
    Generate a consistent cache key from arguments
    """
    # Create a string representation of all arguments
    key_data = {
        'args': args,
        'kwargs': sorted(kwargs.items()) if kwargs else {}
    }
    
    # Create hash of the arguments for consistent key generation
    key_string = json.dumps(key_data, sort_keys=True, default=str)
    key_hash = hashlib.md5(key_string.encode()).hexdigest()[:16]
    
    return f"{prefix}:{key_hash}"


def cache_result(prefix: str, timeout: Optional[int] = None):
    """
    Decorator to cache function results
    
    Args:
        prefix: Cache key prefix
        timeout: Cache timeout in seconds (uses default if None)
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Generate cache key
            cache_key = generate_cache_key(prefix, *args, **kwargs)
            
            # Try to get from cache
            result = cache.get(cache_key)
            if result is not None:
                return result
            
            # Execute function and cache result
            result = func(*args, **kwargs)
            cache_timeout = timeout or getattr(settings, 'CACHE_MIDDLEWARE_SECONDS', 300)
            cache.set(cache_key, result, cache_timeout)
            
            return result
        return wrapper
    return decorator


def cache_movie_data(movie_id: int, data: dict, timeout: int = 3600):
    """
    Cache movie data by ID
    
    Args:
        movie_id: Movie ID
        data: Movie data to cache
        timeout: Cache timeout in seconds (default: 1 hour)
    """
    cache_key = f"movie_data:{movie_id}"
    cache.set(cache_key, data, timeout)


def get_cached_movie_data(movie_id: int) -> Optional[dict]:
    """
    Get cached movie data by ID
    
    Args:
        movie_id: Movie ID
        
    Returns:
        Cached movie data or None if not found
    """
    cache_key = f"movie_data:{movie_id}"
    return cache.get(cache_key)


def cache_user_recommendations(user_id: int, recommendations: list, timeout: int = 1800):
    """
    Cache user recommendations
    
    Args:
        user_id: User ID
        recommendations: List of recommended movies
        timeout: Cache timeout in seconds (default: 30 minutes)
    """
    cache_key = f"user_recommendations:{user_id}"
    cache.set(cache_key, recommendations, timeout)


def get_cached_user_recommendations(user_id: int) -> Optional[list]:
    """
    Get cached user recommendations
    
    Args:
        user_id: User ID
        
    Returns:
        Cached recommendations or None if not found
    """
    cache_key = f"user_recommendations:{user_id}"
    return cache.get(cache_key)


def invalidate_user_cache(user_id: int):
    """
    Invalidate all cache entries for a specific user
    
    Args:
        user_id: User ID
    """
    # List of cache patterns to invalidate for user
    patterns = [
        f"user_recommendations:{user_id}",
        f"user_stats:{user_id}",
        f"user_watchlist:{user_id}",
        f"user_ratings:{user_id}"
    ]
    
    for pattern in patterns:
        cache.delete(pattern)


def cache_tmdb_response(endpoint: str, params: dict, data: dict, timeout: int = 3600):
    """
    Cache TMDb API responses
    
    Args:
        endpoint: API endpoint
        params: Request parameters
        data: Response data
        timeout: Cache timeout in seconds (default: 1 hour)
    """
    cache_key = generate_cache_key(f"tmdb:{endpoint}", **params)
    cache.set(cache_key, data, timeout)


def get_cached_tmdb_response(endpoint: str, params: dict) -> Optional[dict]:
    """
    Get cached TMDb API response
    
    Args:
        endpoint: API endpoint
        params: Request parameters
        
    Returns:
        Cached response data or None if not found
    """
    cache_key = generate_cache_key(f"tmdb:{endpoint}", **params)
    return cache.get(cache_key)


def warm_cache_for_popular_movies(movie_ids: list):
    """
    Pre-warm cache for popular movies
    
    Args:
        movie_ids: List of movie IDs to pre-cache
    """
    from .services import TMDbService
    
    tmdb_service = TMDbService()
    
    for movie_id in movie_ids:
        try:
            # Check if already cached
            if not get_cached_movie_data(movie_id):
                # Fetch and cache movie data
                movie_data = tmdb_service.get_movie_details(movie_id)
                if movie_data:
                    cache_movie_data(movie_id, movie_data)
        except Exception as e:
            # Log error but continue with other movies
            print(f"Error warming cache for movie {movie_id}: {e}")
            continue


class CacheStats:
    """
    Utility class for cache statistics and monitoring
    """
    
    @staticmethod
    def get_cache_info() -> dict:
        """
        Get basic cache information
        
        Returns:
            Dictionary with cache statistics
        """
        try:
            from django_redis import get_redis_connection
            redis_conn = get_redis_connection("default")
            
            info = redis_conn.info()
            return {
                'connected_clients': info.get('connected_clients', 0),
                'used_memory_human': info.get('used_memory_human', '0B'),
                'keyspace_hits': info.get('keyspace_hits', 0),
                'keyspace_misses': info.get('keyspace_misses', 0),
                'total_commands_processed': info.get('total_commands_processed', 0)
            }
        except Exception as e:
            return {'error': str(e)}
    
    @staticmethod
    def clear_all_cache():
        """
        Clear all cache entries (use with caution)
        """
        cache.clear()
    
    @staticmethod
    def get_cache_keys_by_pattern(pattern: str) -> list:
        """
        Get cache keys matching a pattern
        
        Args:
            pattern: Pattern to match (e.g., 'movie_data:*')
            
        Returns:
            List of matching cache keys
        """
        try:
            from django_redis import get_redis_connection
            redis_conn = get_redis_connection("default")
            return [key.decode() for key in redis_conn.keys(f"movie_rec:{pattern}")]
        except Exception as e:
            return []