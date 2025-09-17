import json
import time
import logging
import hashlib
from django.http import JsonResponse
from django.utils.deprecation import MiddlewareMixin
from django.core.exceptions import ValidationError
from django.core.cache import cache
from rest_framework import status
from .exceptions import RateLimitExceededException

logger = logging.getLogger(__name__)


class RequestValidationMiddleware(MiddlewareMixin):
    """
    Middleware for request validation and preprocessing
    """
    
    def process_request(self, request):
        # Add timestamp to request for error tracking
        request.META['HTTP_X_TIMESTAMP'] = str(int(time.time()))
        
        # Validate JSON content for POST/PUT requests
        if request.method in ['POST', 'PUT', 'PATCH'] and request.content_type == 'application/json':
            try:
                if request.body:
                    json.loads(request.body)
            except json.JSONDecodeError:
                return JsonResponse({
                    'error': {
                        'code': 'invalid_json',
                        'message': 'Invalid JSON format in request body',
                        'timestamp': request.META.get('HTTP_X_TIMESTAMP'),
                        'path': request.path
                    }
                }, status=status.HTTP_400_BAD_REQUEST)
        
        return None


class ErrorLoggingMiddleware(MiddlewareMixin):
    """
    Middleware for comprehensive error logging
    """
    
    def process_exception(self, request, exception):
        # Log all exceptions with context
        logger.error(
            f"Exception in {request.method} {request.path}: {str(exception)}",
            extra={
                'request_method': request.method,
                'request_path': request.path,
                'user': getattr(request, 'user', None),
                'timestamp': request.META.get('HTTP_X_TIMESTAMP'),
                'user_agent': request.META.get('HTTP_USER_AGENT', ''),
                'remote_addr': request.META.get('REMOTE_ADDR', ''),
            },
            exc_info=True
        )
        return None


class RateLimitMiddleware(MiddlewareMixin):
    """
    Simple rate limiting middleware
    """
    
    def __init__(self, get_response):
        self.get_response = get_response
        self.request_counts = {}  # In production, use Redis or database
        self.rate_limit = 100  # requests per minute
        self.time_window = 60  # seconds
        super().__init__(get_response)
    
    def process_request(self, request):
        # Skip rate limiting for authenticated users (optional)
        if hasattr(request, 'user') and request.user.is_authenticated:
            return None
        
        # Get client IP
        client_ip = self.get_client_ip(request)
        current_time = time.time()
        
        # Clean old entries
        self.cleanup_old_entries(current_time)
        
        # Check rate limit
        if client_ip in self.request_counts:
            request_times = self.request_counts[client_ip]
            recent_requests = [t for t in request_times if current_time - t < self.time_window]
            
            if len(recent_requests) >= self.rate_limit:
                return JsonResponse({
                    'error': {
                        'code': 'rate_limit_exceeded',
                        'message': f'Rate limit exceeded. Maximum {self.rate_limit} requests per minute.',
                        'timestamp': request.META.get('HTTP_X_TIMESTAMP'),
                        'path': request.path
                    }
                }, status=status.HTTP_429_TOO_MANY_REQUESTS)
            
            self.request_counts[client_ip] = recent_requests + [current_time]
        else:
            self.request_counts[client_ip] = [current_time]
        
        return None
    
    def get_client_ip(self, request):
        """Get client IP address"""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip
    
    def cleanup_old_entries(self, current_time):
        """Remove old entries to prevent memory leaks"""
        for ip in list(self.request_counts.keys()):
            self.request_counts[ip] = [
                t for t in self.request_counts[ip] 
                if current_time - t < self.time_window
            ]
            if not self.request_counts[ip]:
                del self.request_counts[ip]


class SecurityHeadersMiddleware(MiddlewareMixin):
    """
    Middleware to add security headers
    """
    
    def process_response(self, request, response):
        # Add security headers
        response['X-Content-Type-Options'] = 'nosniff'
        response['X-Frame-Options'] = 'DENY'
        response['X-XSS-Protection'] = '1; mode=block'
        response['Referrer-Policy'] = 'strict-origin-when-cross-origin'
        
        # Add API version header
        response['X-API-Version'] = '1.0'
        
        return response


class RequestResponseLoggingMiddleware(MiddlewareMixin):
    """
    Middleware for logging requests and responses (for debugging)
    """
    
    def process_request(self, request):
        # Log incoming requests (be careful with sensitive data)
        if request.path.startswith('/api/'):
            logger.info(
                f"Incoming request: {request.method} {request.path}",
                extra={
                    'request_method': request.method,
                    'request_path': request.path,
                    'user': str(getattr(request, 'user', 'Anonymous')),
                    'timestamp': request.META.get('HTTP_X_TIMESTAMP'),
                }
            )
        return None
    
    def process_response(self, request, response):
        # Log API responses
        if request.path.startswith('/api/'):
            logger.info(
                f"Response: {request.method} {request.path} - {response.status_code}",
                extra={
                    'request_method': request.method,
                    'request_path': request.path,
                    'response_status': response.status_code,
                    'user': str(getattr(request, 'user', 'Anonymous')),
                    'timestamp': request.META.get('HTTP_X_TIMESTAMP'),
                }
            )
        return response


class APIResponseCacheMiddleware(MiddlewareMixin):
    """
    Middleware to cache API responses for improved performance.
    Caches GET requests to API endpoints with configurable timeouts.
    """
    
    def __init__(self, get_response):
        self.get_response = get_response
        # Cache timeout in seconds (default: 5 minutes)
        self.cache_timeout = 300
        # Cacheable endpoints patterns
        self.cacheable_patterns = [
            '/api/movies/',
            '/api/genres/',
            '/api/search/',
        ]
        # Skip caching for these patterns
        self.skip_patterns = [
            '/api/auth/',
            '/api/ratings/',
            '/api/watchlist/',
        ]
        super().__init__(get_response)
    
    def process_request(self, request):
        """Check if we have a cached response for this request"""
        if not self._should_cache_request(request):
            return None
            
        cache_key = self._generate_cache_key(request)
        cached_response = cache.get(cache_key)
        
        if cached_response:
            # Return cached response
            response_data, content_type, status_code = cached_response
            response = JsonResponse(response_data, safe=False)
            response['Content-Type'] = content_type
            response.status_code = status_code
            response['X-Cache-Hit'] = 'True'
            return response
            
        return None
    
    def process_response(self, request, response):
        """Cache the response if it's cacheable"""
        if not self._should_cache_request(request):
            return response
            
        if not self._should_cache_response(response):
            return response
            
        cache_key = self._generate_cache_key(request)
        
        try:
            # Parse JSON response
            if hasattr(response, 'content'):
                response_data = json.loads(response.content.decode('utf-8'))
                cache_data = (
                    response_data,
                    response.get('Content-Type', 'application/json'),
                    response.status_code
                )
                
                # Determine cache timeout based on endpoint
                timeout = self._get_cache_timeout(request.path)
                cache.set(cache_key, cache_data, timeout)
                
                # Add cache headers
                response['X-Cache-Hit'] = 'False'
                response['X-Cache-Timeout'] = str(timeout)
                
        except (json.JSONDecodeError, AttributeError):
            # Skip caching if response is not valid JSON
            pass
            
        return response
    
    def _should_cache_request(self, request):
        """Determine if the request should be cached"""
        # Only cache GET requests
        if request.method != 'GET':
            return False
            
        # Skip if path matches skip patterns
        for pattern in self.skip_patterns:
            if pattern in request.path:
                return False
                
        # Check if path matches cacheable patterns
        for pattern in self.cacheable_patterns:
            if pattern in request.path:
                return True
                
        return False
    
    def _should_cache_response(self, response):
        """Determine if the response should be cached"""
        # Only cache successful responses
        if response.status_code != 200:
            return False
            
        # Check if response is JSON
        content_type = response.get('Content-Type', '')
        if 'application/json' not in content_type:
            return False
            
        return True
    
    def _generate_cache_key(self, request):
        """Generate a unique cache key for the request"""
        # Include path, query parameters, and user ID (if authenticated)
        key_parts = [
            request.path,
            request.GET.urlencode(),
        ]
        
        # Include user ID for personalized responses
        if hasattr(request, 'user') and request.user.is_authenticated:
            key_parts.append(f'user_{request.user.id}')
            
        key_string = '|'.join(key_parts)
        return f'api_cache_{hashlib.md5(key_string.encode()).hexdigest()}'
    
    def _get_cache_timeout(self, path):
        """Get cache timeout based on the endpoint"""
        # Different timeouts for different endpoints
        timeout_map = {
            '/api/movies/': 600,      # 10 minutes for movie lists
            '/api/genres/': 3600,     # 1 hour for genres (rarely change)
            '/api/search/': 300,      # 5 minutes for search results
        }
        
        for pattern, timeout in timeout_map.items():
            if pattern in path:
                return timeout
                
        return self.cache_timeout  # Default timeout


class PerformanceMonitoringMiddleware(MiddlewareMixin):
    """
    Middleware to monitor API performance and log slow requests.
    """
    
    def __init__(self, get_response):
        self.get_response = get_response
        # Threshold for slow requests (in seconds)
        self.slow_request_threshold = 1.0
        super().__init__(get_response)
    
    def process_request(self, request):
        """Record request start time"""
        request._start_time = time.time()
        return None
    
    def process_response(self, request, response):
        """Log performance metrics"""
        if hasattr(request, '_start_time'):
            duration = time.time() - request._start_time
            
            # Add performance headers
            response['X-Response-Time'] = f'{duration:.3f}s'
            
            # Log slow requests
            if duration > self.slow_request_threshold:
                logger.warning(
                    f'Slow request: {request.method} {request.path} '
                    f'took {duration:.3f}s (User: {getattr(request.user, "id", "anonymous")})'
                )
        
        return response