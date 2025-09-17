from drf_yasg import openapi
from rest_framework import serializers

# Common response schemas
ERROR_RESPONSE_SCHEMA = openapi.Schema(
    type=openapi.TYPE_OBJECT,
    properties={
        'error': openapi.Schema(type=openapi.TYPE_STRING, description='Error message'),
        'details': openapi.Schema(type=openapi.TYPE_STRING, description='Detailed error information')
    }
)

VALIDATION_ERROR_SCHEMA = openapi.Schema(
    type=openapi.TYPE_OBJECT,
    properties={
        'field_name': openapi.Schema(
            type=openapi.TYPE_ARRAY,
            items=openapi.Schema(type=openapi.TYPE_STRING),
            description='List of validation errors for this field'
        )
    }
)

# Authentication schemas
JWT_TOKEN_RESPONSE_SCHEMA = openapi.Schema(
    type=openapi.TYPE_OBJECT,
    properties={
        'access': openapi.Schema(type=openapi.TYPE_STRING, description='JWT access token'),
        'refresh': openapi.Schema(type=openapi.TYPE_STRING, description='JWT refresh token'),
        'user': openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'id': openapi.Schema(type=openapi.TYPE_INTEGER),
                'username': openapi.Schema(type=openapi.TYPE_STRING),
                'email': openapi.Schema(type=openapi.TYPE_STRING, format=openapi.FORMAT_EMAIL),
                'first_name': openapi.Schema(type=openapi.TYPE_STRING),
                'last_name': openapi.Schema(type=openapi.TYPE_STRING)
            }
        )
    }
)

REGISTER_REQUEST_SCHEMA = openapi.Schema(
    type=openapi.TYPE_OBJECT,
    required=['username', 'email', 'password'],
    properties={
        'username': openapi.Schema(
            type=openapi.TYPE_STRING,
            description='Unique username (3-150 characters)',
            min_length=3,
            max_length=150
        ),
        'email': openapi.Schema(
            type=openapi.TYPE_STRING,
            format=openapi.FORMAT_EMAIL,
            description='Valid email address'
        ),
        'password': openapi.Schema(
            type=openapi.TYPE_STRING,
            description='Password (minimum 8 characters)',
            min_length=8
        ),
        'first_name': openapi.Schema(
            type=openapi.TYPE_STRING,
            description='First name (optional)',
            max_length=30
        ),
        'last_name': openapi.Schema(
            type=openapi.TYPE_STRING,
            description='Last name (optional)',
            max_length=30
        )
    }
)

LOGIN_REQUEST_SCHEMA = openapi.Schema(
    type=openapi.TYPE_OBJECT,
    required=['username', 'password'],
    properties={
        'username': openapi.Schema(type=openapi.TYPE_STRING, description='Username'),
        'password': openapi.Schema(type=openapi.TYPE_STRING, description='Password')
    }
)

# Movie schemas
MOVIE_SEARCH_REQUEST_SCHEMA = openapi.Schema(
    type=openapi.TYPE_OBJECT,
    required=['query'],
    properties={
        'query': openapi.Schema(
            type=openapi.TYPE_STRING,
            description='Search query (minimum 2 characters)',
            min_length=2,
            max_length=100
        ),
        'page': openapi.Schema(
            type=openapi.TYPE_INTEGER,
            description='Page number (default: 1)',
            minimum=1,
            default=1
        )
    }
)

MOVIE_LIST_RESPONSE_SCHEMA = openapi.Schema(
    type=openapi.TYPE_OBJECT,
    properties={
        'count': openapi.Schema(type=openapi.TYPE_INTEGER, description='Total number of movies'),
        'next': openapi.Schema(type=openapi.TYPE_STRING, format=openapi.FORMAT_URI, description='Next page URL'),
        'previous': openapi.Schema(type=openapi.TYPE_STRING, format=openapi.FORMAT_URI, description='Previous page URL'),
        'results': openapi.Schema(
            type=openapi.TYPE_ARRAY,
            items=openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={
                    'id': openapi.Schema(type=openapi.TYPE_INTEGER),
                    'tmdb_id': openapi.Schema(type=openapi.TYPE_INTEGER),
                    'title': openapi.Schema(type=openapi.TYPE_STRING),
                    'overview': openapi.Schema(type=openapi.TYPE_STRING),
                    'release_date': openapi.Schema(type=openapi.TYPE_STRING, format=openapi.FORMAT_DATE),
                    'vote_average': openapi.Schema(type=openapi.TYPE_NUMBER, format=openapi.FORMAT_FLOAT),
                    'vote_count': openapi.Schema(type=openapi.TYPE_INTEGER),
                    'popularity': openapi.Schema(type=openapi.TYPE_NUMBER, format=openapi.FORMAT_FLOAT),
                    'poster_path': openapi.Schema(type=openapi.TYPE_STRING),
                    'backdrop_path': openapi.Schema(type=openapi.TYPE_STRING),
                    'genres': openapi.Schema(
                        type=openapi.TYPE_ARRAY,
                        items=openapi.Schema(
                            type=openapi.TYPE_OBJECT,
                            properties={
                                'id': openapi.Schema(type=openapi.TYPE_INTEGER),
                                'name': openapi.Schema(type=openapi.TYPE_STRING)
                            }
                        )
                    )
                }
            )
        ),
        'page_info': openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'current_page': openapi.Schema(type=openapi.TYPE_INTEGER),
                'total_pages': openapi.Schema(type=openapi.TYPE_INTEGER),
                'page_size': openapi.Schema(type=openapi.TYPE_INTEGER),
                'has_previous': openapi.Schema(type=openapi.TYPE_BOOLEAN),
                'has_next': openapi.Schema(type=openapi.TYPE_BOOLEAN)
            }
        )
    }
)

# Rating schemas
RATING_REQUEST_SCHEMA = openapi.Schema(
    type=openapi.TYPE_OBJECT,
    required=['movie', 'rating'],
    properties={
        'movie': openapi.Schema(
            type=openapi.TYPE_INTEGER,
            description='Movie ID (TMDb ID)'
        ),
        'rating': openapi.Schema(
            type=openapi.TYPE_NUMBER,
            format=openapi.FORMAT_FLOAT,
            description='Rating value (0.5 - 5.0)',
            minimum=0.5,
            maximum=5.0
        ),
        'review': openapi.Schema(
            type=openapi.TYPE_STRING,
            description='Optional review text',
            max_length=1000
        )
    }
)

# Watchlist schemas
WATCHLIST_REQUEST_SCHEMA = openapi.Schema(
    type=openapi.TYPE_OBJECT,
    required=['movie'],
    properties={
        'movie': openapi.Schema(
            type=openapi.TYPE_INTEGER,
            description='Movie ID (TMDb ID)'
        )
    }
)

# User statistics schema
USER_STATS_RESPONSE_SCHEMA = openapi.Schema(
    type=openapi.TYPE_OBJECT,
    properties={
        'total_ratings': openapi.Schema(type=openapi.TYPE_INTEGER, description='Total number of movies rated'),
        'watchlist_count': openapi.Schema(type=openapi.TYPE_INTEGER, description='Number of movies in watchlist'),
        'average_rating': openapi.Schema(
            type=openapi.TYPE_NUMBER,
            format=openapi.FORMAT_FLOAT,
            description='User\'s average rating'
        ),
        'favorite_genres': openapi.Schema(
            type=openapi.TYPE_ARRAY,
            items=openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={
                    'genre': openapi.Schema(type=openapi.TYPE_STRING),
                    'count': openapi.Schema(type=openapi.TYPE_INTEGER)
                }
            ),
            description='Top genres by rating count'
        )
    }
)

# Common parameter schemas
PAGE_PARAMETER = openapi.Parameter(
    'page',
    openapi.IN_QUERY,
    description='Page number for pagination',
    type=openapi.TYPE_INTEGER,
    minimum=1,
    default=1
)

PAGE_SIZE_PARAMETER = openapi.Parameter(
    'page_size',
    openapi.IN_QUERY,
    description='Number of results per page (max 100)',
    type=openapi.TYPE_INTEGER,
    minimum=1,
    maximum=100,
    default=20
)

SEARCH_PARAMETER = openapi.Parameter(
    'search',
    openapi.IN_QUERY,
    description='Search query for filtering results',
    type=openapi.TYPE_STRING,
    min_length=2
)

ORDERING_PARAMETER = openapi.Parameter(
    'ordering',
    openapi.IN_QUERY,
    description='Field to order results by. Prefix with "-" for descending order.',
    type=openapi.TYPE_STRING,
    enum=['popularity', '-popularity', 'vote_average', '-vote_average', 
          'release_date', '-release_date', 'title', '-title']
)

# Security definitions
JWT_AUTH_HEADER = openapi.Parameter(
    'Authorization',
    openapi.IN_HEADER,
    description='JWT token in format: Bearer <token>',
    type=openapi.TYPE_STRING,
    required=True
)

# Response status codes with descriptions
STATUS_RESPONSES = {
    200: 'Success',
    201: 'Created successfully',
    204: 'No content - operation successful',
    400: 'Bad Request - Invalid input data',
    401: 'Unauthorized - Authentication required',
    403: 'Forbidden - Insufficient permissions',
    404: 'Not Found - Resource does not exist',
    409: 'Conflict - Resource already exists',
    422: 'Unprocessable Entity - Validation failed',
    429: 'Too Many Requests - Rate limit exceeded',
    500: 'Internal Server Error'
}