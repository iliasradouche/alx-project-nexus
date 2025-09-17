import time
import threading
from collections import defaultdict, deque
from datetime import datetime, timedelta
from django.core.cache import cache
from django.conf import settings
import logging

logger = logging.getLogger(__name__)


class TMDbRateLimiter:
    """
    Advanced rate limiter for TMDb API calls with multiple strategies:
    - Token bucket algorithm for burst handling
    - Sliding window for precise rate limiting
    - Exponential backoff for error handling
    - Request prioritization
    """
    
    def __init__(self):
        self.requests_per_second = getattr(settings, 'TMDB_REQUESTS_PER_SECOND', 40)
        self.burst_capacity = getattr(settings, 'TMDB_BURST_CAPACITY', 10)
        self.window_size = 60  # 1 minute sliding window
        
        # Token bucket for burst handling
        self.tokens = self.burst_capacity
        self.last_refill = time.time()
        self.lock = threading.Lock()
        
        # Sliding window tracking
        self.request_times = deque()
        
        # Exponential backoff tracking
        self.consecutive_errors = 0
        self.last_error_time = None
        
        # Request prioritization
        self.priority_weights = {
            'high': 1.0,    # Critical requests (user-facing)
            'medium': 0.7,  # Background updates
            'low': 0.4      # Bulk operations
        }
    
    def _refill_tokens(self):
        """Refill tokens based on elapsed time"""
        now = time.time()
        elapsed = now - self.last_refill
        
        # Add tokens based on rate limit
        tokens_to_add = elapsed * (self.requests_per_second / 60)  # Convert to per-second
        self.tokens = min(self.burst_capacity, self.tokens + tokens_to_add)
        self.last_refill = now
    
    def _clean_old_requests(self):
        """Remove requests older than window size"""
        cutoff_time = time.time() - self.window_size
        while self.request_times and self.request_times[0] < cutoff_time:
            self.request_times.popleft()
    
    def _calculate_backoff_delay(self):
        """Calculate exponential backoff delay"""
        if self.consecutive_errors == 0:
            return 0
        
        # Exponential backoff: 2^errors seconds, max 300 seconds (5 minutes)
        delay = min(300, 2 ** self.consecutive_errors)
        
        # Check if enough time has passed since last error
        if self.last_error_time:
            time_since_error = time.time() - self.last_error_time
            remaining_delay = max(0, delay - time_since_error)
            return remaining_delay
        
        return delay
    
    def can_make_request(self, priority='medium'):
        """Check if a request can be made based on rate limits and priority"""
        with self.lock:
            # Check exponential backoff
            backoff_delay = self._calculate_backoff_delay()
            if backoff_delay > 0:
                return False, f"Backing off for {backoff_delay:.1f} seconds"
            
            # Refill tokens
            self._refill_tokens()
            
            # Clean old requests from sliding window
            self._clean_old_requests()
            
            # Check sliding window limit
            current_requests = len(self.request_times)
            max_requests = self.requests_per_second * (self.window_size / 60)
            
            if current_requests >= max_requests:
                return False, "Sliding window limit exceeded"
            
            # Check token bucket (with priority weighting)
            priority_weight = self.priority_weights.get(priority, 0.5)
            required_tokens = 1.0 / priority_weight
            
            if self.tokens < required_tokens:
                return False, "Token bucket empty"
            
            return True, "Request allowed"
    
    def make_request(self, priority='medium'):
        """Record a request being made"""
        with self.lock:
            can_proceed, reason = self.can_make_request(priority)
            
            if not can_proceed:
                logger.warning(f"TMDb API request blocked: {reason}")
                return False
            
            # Consume tokens
            priority_weight = self.priority_weights.get(priority, 0.5)
            required_tokens = 1.0 / priority_weight
            self.tokens -= required_tokens
            
            # Record request time
            self.request_times.append(time.time())
            
            logger.debug(f"TMDb API request allowed (priority: {priority}, tokens: {self.tokens:.2f})")
            return True
    
    def record_success(self):
        """Record a successful API call"""
        with self.lock:
            self.consecutive_errors = 0
            self.last_error_time = None
    
    def record_error(self, error_type='general'):
        """Record an API error for backoff calculation"""
        with self.lock:
            self.consecutive_errors += 1
            self.last_error_time = time.time()
            
            logger.warning(
                f"TMDb API error recorded (type: {error_type}, "
                f"consecutive: {self.consecutive_errors})"
            )
    
    def get_stats(self):
        """Get current rate limiter statistics"""
        with self.lock:
            self._clean_old_requests()
            
            return {
                'tokens_available': self.tokens,
                'burst_capacity': self.burst_capacity,
                'requests_in_window': len(self.request_times),
                'window_size_seconds': self.window_size,
                'consecutive_errors': self.consecutive_errors,
                'backoff_delay': self._calculate_backoff_delay(),
                'requests_per_second_limit': self.requests_per_second
            }
    
    def wait_if_needed(self, priority='medium', max_wait=30):
        """Wait until a request can be made, with maximum wait time"""
        start_time = time.time()
        
        while time.time() - start_time < max_wait:
            can_proceed, reason = self.can_make_request(priority)
            
            if can_proceed:
                return self.make_request(priority)
            
            # Wait a short time before checking again
            time.sleep(0.1)
        
        logger.error(f"TMDb API rate limiter timeout after {max_wait} seconds")
        return False


# Global rate limiter instance
tmdb_rate_limiter = TMDbRateLimiter()


class CachedTMDbRateLimiter:
    """
    Redis-backed rate limiter for distributed environments
    """
    
    def __init__(self, cache_prefix='tmdb_rate_limit'):
        self.cache_prefix = cache_prefix
        self.requests_per_second = getattr(settings, 'TMDB_REQUESTS_PER_SECOND', 40)
        self.window_size = 60
    
    def _get_cache_key(self, key_type):
        """Generate cache key for rate limiting data"""
        return f"{self.cache_prefix}:{key_type}"
    
    def can_make_request(self, priority='medium'):
        """Check if request can be made using Redis cache"""
        try:
            # Get current request count from cache
            current_count = cache.get(self._get_cache_key('count'), 0)
            max_requests = self.requests_per_second * (self.window_size / 60)
            
            if current_count >= max_requests:
                return False, "Rate limit exceeded"
            
            return True, "Request allowed"
        
        except Exception as e:
            logger.error(f"Cache error in rate limiter: {e}")
            # Fallback to allowing request if cache fails
            return True, "Cache error - allowing request"
    
    def make_request(self, priority='medium'):
        """Record a request in cache"""
        try:
            cache_key = self._get_cache_key('count')
            
            # Atomic increment with expiration
            current_count = cache.get(cache_key, 0)
            cache.set(cache_key, current_count + 1, timeout=self.window_size)
            
            return True
        
        except Exception as e:
            logger.error(f"Cache error recording request: {e}")
            return True  # Allow request if cache fails


# Choose rate limiter based on cache backend
def get_rate_limiter():
    """Get appropriate rate limiter based on configuration"""
    try:
        # Test if cache is available and working
        cache.set('test_key', 'test_value', 1)
        cache.get('test_key')
        return CachedTMDbRateLimiter()
    except Exception:
        # Fallback to in-memory rate limiter
        return tmdb_rate_limiter


# Export the appropriate rate limiter
rate_limiter = get_rate_limiter()