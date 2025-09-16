import json
import time
import logging
from django.http import JsonResponse
from django.utils.deprecation import MiddlewareMixin
from django.core.exceptions import ValidationError
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