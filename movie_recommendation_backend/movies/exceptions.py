from rest_framework.views import exception_handler
from rest_framework.response import Response
from rest_framework import status
from django.core.exceptions import ValidationError
from django.http import Http404
import logging

logger = logging.getLogger(__name__)


class MovieAPIException(Exception):
    """
    Base exception class for Movie API
    """
    default_message = "An error occurred"
    default_code = "api_error"
    status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
    
    def __init__(self, message=None, code=None, status_code=None):
        self.message = message or self.default_message
        self.code = code or self.default_code
        self.status_code = status_code or self.status_code
        super().__init__(self.message)


class TMDbAPIException(MovieAPIException):
    """
    Exception for TMDb API related errors
    """
    default_message = "TMDb API error occurred"
    default_code = "tmdb_api_error"
    status_code = status.HTTP_503_SERVICE_UNAVAILABLE


class MovieNotFoundException(MovieAPIException):
    """
    Exception when a movie is not found
    """
    default_message = "Movie not found"
    default_code = "movie_not_found"
    status_code = status.HTTP_404_NOT_FOUND


class InvalidRatingException(MovieAPIException):
    """
    Exception for invalid movie ratings
    """
    default_message = "Invalid rating value. Rating must be between 1 and 10"
    default_code = "invalid_rating"
    status_code = status.HTTP_400_BAD_REQUEST


class DuplicateWatchlistException(MovieAPIException):
    """
    Exception when trying to add a movie that's already in watchlist
    """
    default_message = "Movie is already in your watchlist"
    default_code = "duplicate_watchlist"
    status_code = status.HTTP_409_CONFLICT


class AuthenticationRequiredException(MovieAPIException):
    """
    Exception when authentication is required
    """
    default_message = "Authentication required"
    default_code = "authentication_required"
    status_code = status.HTTP_401_UNAUTHORIZED


class RateLimitExceededException(MovieAPIException):
    """
    Exception when rate limit is exceeded
    """
    default_message = "Rate limit exceeded. Please try again later"
    default_code = "rate_limit_exceeded"
    status_code = status.HTTP_429_TOO_MANY_REQUESTS


def custom_exception_handler(exc, context):
    """
    Custom exception handler for the API
    """
    # Call REST framework's default exception handler first
    response = exception_handler(exc, context)
    
    # Log the exception
    logger.error(f"API Exception: {exc}", exc_info=True)
    
    # Handle custom exceptions
    if isinstance(exc, MovieAPIException):
        custom_response_data = {
            'error': {
                'code': exc.code,
                'message': exc.message,
                'timestamp': context['request'].META.get('HTTP_X_TIMESTAMP'),
                'path': context['request'].path
            }
        }
        return Response(custom_response_data, status=exc.status_code)
    
    # Handle Django validation errors
    if isinstance(exc, ValidationError):
        custom_response_data = {
            'error': {
                'code': 'validation_error',
                'message': 'Validation failed',
                'details': exc.message_dict if hasattr(exc, 'message_dict') else str(exc),
                'timestamp': context['request'].META.get('HTTP_X_TIMESTAMP'),
                'path': context['request'].path
            }
        }
        return Response(custom_response_data, status=status.HTTP_400_BAD_REQUEST)
    
    # Handle 404 errors
    if isinstance(exc, Http404):
        custom_response_data = {
            'error': {
                'code': 'not_found',
                'message': 'The requested resource was not found',
                'timestamp': context['request'].META.get('HTTP_X_TIMESTAMP'),
                'path': context['request'].path
            }
        }
        return Response(custom_response_data, status=status.HTTP_404_NOT_FOUND)
    
    # If response is None, it means the exception wasn't handled by DRF
    if response is None:
        custom_response_data = {
            'error': {
                'code': 'internal_server_error',
                'message': 'An unexpected error occurred',
                'timestamp': context['request'].META.get('HTTP_X_TIMESTAMP'),
                'path': context['request'].path
            }
        }
        return Response(custom_response_data, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    # Customize the response format for DRF exceptions
    if response is not None:
        custom_response_data = {
            'error': {
                'code': getattr(exc, 'default_code', 'api_error'),
                'message': response.data.get('detail', str(exc)) if isinstance(response.data, dict) else str(response.data),
                'timestamp': context['request'].META.get('HTTP_X_TIMESTAMP'),
                'path': context['request'].path
            }
        }
        response.data = custom_response_data
    
    return response