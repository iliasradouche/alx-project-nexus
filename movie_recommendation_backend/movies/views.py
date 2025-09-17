from rest_framework import generics, status, permissions
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.pagination import PageNumberPagination
from django.db.models import Q, Avg
from django.core.cache import cache
from django.core.exceptions import ValidationError
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from .models import Movie, Genre, UserMovieRating, UserMovieWatchlist
from .serializers import (
    MovieListSerializer, MovieDetailSerializer, GenreSerializer,
    UserMovieRatingSerializer, UserMovieWatchlistSerializer,
    MovieSearchSerializer
)
from .services import TMDbAPIService, MovieDataService
from .cache_utils import cache_result, get_cached_movie_data
from .exceptions import (
    MovieNotFoundException, TMDbAPIException, InvalidRatingException,
    DuplicateWatchlistException, AuthenticationRequiredException
)
from .validators import APIValidators, MovieValidators
import logging

logger = logging.getLogger(__name__)


class MoviePagination(PageNumberPagination):
    """Custom pagination for movies"""
    page_size = 20
    page_size_query_param = 'page_size'
    max_page_size = 100
    
    def get_paginated_response(self, data):
        """Enhanced pagination response with performance metrics"""
        response = super().get_paginated_response(data)
        
        # Add pagination metadata for better client-side handling
        response.data.update({
            'page_info': {
                'current_page': self.page.number,
                'total_pages': self.page.paginator.num_pages,
                'page_size': self.page_size,
                'has_previous': self.page.has_previous(),
                'has_next': self.page.has_next(),
                'start_index': self.page.start_index(),
                'end_index': self.page.end_index(),
            }
        })
        
        return response


class OptimizedMoviePagination(PageNumberPagination):
    """Optimized pagination for large datasets with cursor-based pagination fallback"""
    page_size = 50
    page_size_query_param = 'page_size'
    max_page_size = 200
    
    def paginate_queryset(self, queryset, request, view=None):
        """Optimize pagination for large datasets"""
        # Use cursor pagination for very large datasets
        total_count = queryset.count()
        
        if total_count > 10000:  # Switch to cursor-based for large datasets
            return self._cursor_paginate(queryset, request)
        
        return super().paginate_queryset(queryset, request, view)
    
    def _cursor_paginate(self, queryset, request):
        """Simple cursor-based pagination for large datasets"""
        cursor = request.GET.get('cursor')
        page_size = self.get_page_size(request)
        
        if cursor:
            try:
                cursor_id = int(cursor)
                queryset = queryset.filter(id__gt=cursor_id)
            except (ValueError, TypeError):
                pass
        
        # Get one extra item to determine if there's a next page
        items = list(queryset[:page_size + 1])
        has_next = len(items) > page_size
        
        if has_next:
            items = items[:-1]
        
        # Set pagination metadata
        self.cursor_data = {
            'has_next': has_next,
            'next_cursor': items[-1].id if items and has_next else None,
            'page_size': page_size,
            'is_cursor_paginated': True
        }
        
        return items
    
    def get_paginated_response(self, data):
        """Return appropriate response based on pagination type"""
        if hasattr(self, 'cursor_data'):
            return Response({
                'results': data,
                'pagination': self.cursor_data
            })
        
        return super().get_paginated_response(data)


class MovieListView(generics.ListAPIView):
    """List movies with filtering and search"""
    serializer_class = MovieListSerializer
    pagination_class = MoviePagination
    permission_classes = [permissions.AllowAny]
    
    @swagger_auto_schema(
        operation_description="Retrieve a paginated list of movies with optional filtering",
        operation_summary="List Movies",
        manual_parameters=[
            openapi.Parameter(
                'genre', openapi.IN_QUERY,
                description="Filter movies by genre name (case-insensitive)",
                type=openapi.TYPE_STRING
            ),
            openapi.Parameter(
                'year', openapi.IN_QUERY,
                description="Filter movies by release year",
                type=openapi.TYPE_INTEGER
            ),
            openapi.Parameter(
                'min_rating', openapi.IN_QUERY,
                description="Filter movies with minimum rating (0.0-10.0)",
                type=openapi.TYPE_NUMBER
            ),
            openapi.Parameter(
                'search', openapi.IN_QUERY,
                description="Search movies by title or overview",
                type=openapi.TYPE_STRING
            ),
            openapi.Parameter(
                'page', openapi.IN_QUERY,
                description="Page number for pagination",
                type=openapi.TYPE_INTEGER
            ),
            openapi.Parameter(
                'page_size', openapi.IN_QUERY,
                description="Number of results per page (max 100)",
                type=openapi.TYPE_INTEGER
            ),
        ],
        responses={
            200: MovieListSerializer(many=True),
            400: "Bad Request - Invalid parameters"
        },
        tags=['Movies']
    )
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)
    
    def get_queryset(self):
        try:
            queryset = Movie.objects.select_related().prefetch_related('genres')
            
            # Filter by genre
            genre = self.request.query_params.get('genre')
            if genre:
                genre = MovieValidators.validate_genre_name(genre)
                queryset = queryset.filter(genres__name__icontains=genre)
            
            # Filter by year
            year = self.request.query_params.get('year')
            if year:
                try:
                    year = int(year)
                    MovieValidators.validate_year(year)
                    queryset = queryset.filter(release_date__year=year)
                except (ValueError, ValidationError) as e:
                    logger.warning(f"Invalid year parameter: {year}")
            
            # Filter by minimum rating
            min_rating = self.request.query_params.get('min_rating')
            if min_rating:
                try:
                    min_rating = float(min_rating)
                    MovieValidators.validate_rating(min_rating)
                    queryset = queryset.filter(vote_average__gte=min_rating)
                except (ValueError, ValidationError) as e:
                    logger.warning(f"Invalid min_rating parameter: {min_rating}")
            
            # Search by title
            search = self.request.query_params.get('search')
            if search:
                try:
                    search = APIValidators.validate_search_query(search)
                    queryset = queryset.filter(
                        Q(title__icontains=search) | 
                        Q(original_title__icontains=search)
                    )
                except ValidationError as e:
                    logger.warning(f"Invalid search query: {search}")
            
            # Ordering
            ordering = self.request.query_params.get('ordering', '-popularity')
            valid_orderings = [
                'popularity', '-popularity', 'vote_average', '-vote_average',
                'release_date', '-release_date', 'title', '-title'
            ]
            try:
                ordering = APIValidators.validate_sort_field(ordering, valid_orderings)
                queryset = queryset.order_by(ordering)
            except ValidationError as e:
                logger.warning(f"Invalid ordering parameter: {ordering}")
                queryset = queryset.order_by('-popularity')  # Default ordering
            
            return queryset.distinct()
            
        except Exception as e:
            logger.error(f"Error in MovieListView.get_queryset: {str(e)}")
            return Movie.objects.none()


class MovieDetailView(generics.RetrieveAPIView):
    """Get movie details"""
    queryset = Movie.objects.select_related().prefetch_related('genres')
    serializer_class = MovieDetailSerializer
    permission_classes = [permissions.AllowAny]
    lookup_field = 'tmdb_id'
    
    @swagger_auto_schema(
        operation_description="Retrieve detailed information about a specific movie",
        operation_summary="Get Movie Details",
        responses={
            200: MovieDetailSerializer(),
            404: "Movie not found",
            400: "Invalid TMDb ID"
        },
        tags=['Movies']
    )
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)
    
    def get_object(self):
        try:
            tmdb_id = self.kwargs['tmdb_id']
            
            # Validate TMDb ID
            MovieValidators.validate_tmdb_id(tmdb_id)
            
            # Check cache first
            cached_movie = get_cached_movie_data(tmdb_id)
            if cached_movie:
                return cached_movie
            
            try:
                movie = super().get_object()
            except Movie.DoesNotExist:
                logger.warning(f"Movie with TMDb ID {tmdb_id} not found")
                raise MovieNotFoundException(f"Movie with ID {tmdb_id} not found")
            
            # Cache movie details for 2 hours
            cache.set(f"movie_details:{tmdb_id}", movie, 7200)
            
            return movie
            
        except ValidationError as e:
            logger.error(f"Validation error in MovieDetailView: {str(e)}")
            raise InvalidRatingException(str(e))
        except Exception as e:
            logger.error(f"Unexpected error in MovieDetailView: {str(e)}")
            raise MovieNotFoundException("Movie not found")


class GenreListView(generics.ListAPIView):
    """List all genres"""
    queryset = Genre.objects.all()
    serializer_class = GenreSerializer
    permission_classes = [permissions.AllowAny]
    
    @swagger_auto_schema(
        operation_description="Retrieve a list of all available movie genres",
        operation_summary="List Genres",
        responses={
            200: GenreSerializer(many=True)
        },
        tags=['Genres']
    )
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)


@swagger_auto_schema(
    method='post',
    operation_description="Search for movies using the TMDb API",
    operation_summary="Search Movies",
    request_body=MovieSearchSerializer,
    responses={
        200: openapi.Response(
            description="Search results",
            schema=openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={
                    'results': openapi.Schema(
                        type=openapi.TYPE_ARRAY,
                        items=openapi.Schema(type=openapi.TYPE_OBJECT)
                    ),
                    'total_results': openapi.Schema(type=openapi.TYPE_INTEGER),
                    'total_pages': openapi.Schema(type=openapi.TYPE_INTEGER)
                }
            )
        ),
        400: "Bad Request - Invalid search parameters",
        401: "Authentication required"
    },
    tags=['Movies']
)
@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def search_movies(request):
    """Search movies using TMDb API"""
    try:
        serializer = MovieSearchSerializer(data=request.data)
        if not serializer.is_valid():
            logger.warning(f"Invalid search request: {serializer.errors}")
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        query = serializer.validated_data['query']
        page = serializer.validated_data['page']
        
        # Additional validation
        query = APIValidators.validate_search_query(query)
        page = APIValidators.validate_page_number(page)
        
        tmdb_service = TMDbAPIService()
        movie_service = MovieDataService()
        
        # Search TMDb API
        try:
            search_results = tmdb_service.search_movies(query, page)
        except Exception as e:
            logger.error(f"TMDb API error in search_movies: {str(e)}")
            raise TMDbAPIException("Failed to search movies from TMDb API")
        
        if not search_results:
            raise TMDbAPIException("No results returned from TMDb API")
        
        # Save movies to database
        movies_data = []
        for movie_data in search_results.get('results', []):
            try:
                movie = movie_service.create_or_update_movie(movie_data)
                if movie:
                    movies_data.append(MovieListSerializer(movie).data)
            except Exception as e:
                logger.warning(f"Failed to process movie data: {str(e)}")
                continue
        
        return Response({
            'results': movies_data,
            'total_results': search_results.get('total_results', 0),
            'total_pages': search_results.get('total_pages', 0),
            'page': page
        })
        
    except ValidationError as e:
        logger.error(f"Validation error in search_movies: {str(e)}")
        raise InvalidRatingException(str(e))
    except TMDbAPIException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error in search_movies: {str(e)}")
        raise TMDbAPIException("An unexpected error occurred while searching movies")


@swagger_auto_schema(
    method='get',
    operation_description="Get popular movies from TMDb API",
    operation_summary="Get Popular Movies",
    manual_parameters=[
        openapi.Parameter(
            'page', openapi.IN_QUERY,
            description="Page number for pagination",
            type=openapi.TYPE_INTEGER
        ),
    ],
    responses={
        200: openapi.Response(
            description="Popular movies",
            schema=openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={
                    'results': openapi.Schema(
                        type=openapi.TYPE_ARRAY,
                        items=openapi.Schema(type=openapi.TYPE_OBJECT)
                    ),
                    'total_results': openapi.Schema(type=openapi.TYPE_INTEGER),
                    'total_pages': openapi.Schema(type=openapi.TYPE_INTEGER),
                    'page': openapi.Schema(type=openapi.TYPE_INTEGER)
                }
            )
        ),
        400: "Bad Request - Invalid parameters"
    },
    tags=['Movies']
)
@api_view(['GET'])
@permission_classes([permissions.AllowAny])
@cache_result('popular_movies', timeout=3600)
def popular_movies(request):
    """Get popular movies from TMDb"""
    try:
        page_param = request.query_params.get('page', 1)
        page = APIValidators.validate_page_number(page_param)
        
        cache_key = f"popular_movies_db_{page}"
        cached_movies = cache.get(cache_key)
        
        if cached_movies:
            return Response(cached_movies)
        
        tmdb_service = TMDbAPIService()
        movie_service = MovieDataService()
        
        # Get popular movies from TMDb
        try:
            popular_data = tmdb_service.get_popular_movies(page)
        except Exception as e:
            logger.error(f"TMDb API error in popular_movies: {str(e)}")
            raise TMDbAPIException("Failed to fetch popular movies from TMDb API")
        
        if not popular_data:
            raise TMDbAPIException("No popular movies data returned from TMDb API")
        
        # Save movies to database and serialize
        movies_data = []
        for movie_data in popular_data.get('results', []):
            try:
                movie = movie_service.create_or_update_movie(movie_data)
                if movie:
                    movies_data.append(MovieListSerializer(movie).data)
            except Exception as e:
                logger.warning(f"Failed to process popular movie data: {str(e)}")
                continue
        
        response_data = {
            'results': movies_data,
            'total_results': popular_data.get('total_results', 0),
            'total_pages': popular_data.get('total_pages', 0),
            'page': page
        }
        
        # Cache for 1 hour
        cache.set(cache_key, response_data, 3600)
        
        return Response(response_data)
        
    except ValidationError as e:
        logger.error(f"Validation error in popular_movies: {str(e)}")
        raise InvalidRatingException(str(e))
    except TMDbAPIException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error in popular_movies: {str(e)}")
        raise TMDbAPIException("An unexpected error occurred while fetching popular movies")


@swagger_auto_schema(
    method='get',
    operation_description="Get top rated movies from TMDb API",
    operation_summary="Get Top Rated Movies",
    manual_parameters=[
        openapi.Parameter(
            'page', openapi.IN_QUERY,
            description="Page number for pagination",
            type=openapi.TYPE_INTEGER
        ),
    ],
    responses={
        200: openapi.Response(
            description="Top rated movies",
            schema=openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={
                    'results': openapi.Schema(
                        type=openapi.TYPE_ARRAY,
                        items=openapi.Schema(type=openapi.TYPE_OBJECT)
                    ),
                    'total_results': openapi.Schema(type=openapi.TYPE_INTEGER),
                    'total_pages': openapi.Schema(type=openapi.TYPE_INTEGER),
                    'page': openapi.Schema(type=openapi.TYPE_INTEGER)
                }
            )
        ),
        400: "Bad Request - Invalid parameters"
    },
    tags=['Movies']
)
@api_view(['GET'])
@permission_classes([permissions.AllowAny])
@cache_result('top_rated_movies', timeout=3600)
def top_rated_movies(request):
    """Get top rated movies from TMDb"""
    try:
        page_param = request.query_params.get('page', 1)
        page = APIValidators.validate_page_number(page_param)
        
        cache_key = f"top_rated_movies_db_{page}"
        cached_movies = cache.get(cache_key)
        
        if cached_movies:
            return Response(cached_movies)
        
        tmdb_service = TMDbAPIService()
        movie_service = MovieDataService()
        
        # Get top rated movies from TMDb
        try:
            top_rated_data = tmdb_service.get_top_rated_movies(page)
        except Exception as e:
            logger.error(f"TMDb API error in top_rated_movies: {str(e)}")
            raise TMDbAPIException("Failed to fetch top rated movies from TMDb API")
        
        if not top_rated_data:
            raise TMDbAPIException("No top rated movies data returned from TMDb API")
        
        # Save movies to database and serialize
        movies_data = []
        for movie_data in top_rated_data.get('results', []):
            try:
                movie = movie_service.create_or_update_movie(movie_data)
                if movie:
                    movies_data.append(MovieListSerializer(movie).data)
            except Exception as e:
                logger.warning(f"Failed to process top rated movie data: {str(e)}")
                continue
        
        response_data = {
            'results': movies_data,
            'total_results': top_rated_data.get('total_results', 0),
            'total_pages': top_rated_data.get('total_pages', 0),
            'page': page
        }
        
        # Cache for 1 hour
        cache.set(cache_key, response_data, 3600)
        
        return Response(response_data)
        
    except ValidationError as e:
        logger.error(f"Validation error in top_rated_movies: {str(e)}")
        raise InvalidRatingException(str(e))
    except TMDbAPIException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error in top_rated_movies: {str(e)}")
        raise TMDbAPIException("An unexpected error occurred while fetching top rated movies")


@api_view(['GET'])
@permission_classes([permissions.AllowAny])
def movie_recommendations(request, tmdb_id):
    """Get movie recommendations based on a specific movie"""
    try:
        # Validate tmdb_id parameter
        MovieValidators.validate_tmdb_id(tmdb_id)
        
        page_param = request.query_params.get('page', 1)
        page = APIValidators.validate_page_number(page_param)
        
        cache_key = f"movie_recommendations_{tmdb_id}_{page}"
        cached_recommendations = cache.get(cache_key)
        
        if cached_recommendations:
            return Response(cached_recommendations)
        
        tmdb_service = TMDbAPIService()
        movie_service = MovieDataService()
        
        # Get recommendations from TMDb
        try:
            recommendations_data = tmdb_service.get_movie_recommendations(tmdb_id, page)
        except Exception as e:
            logger.error(f"TMDb API error in movie_recommendations: {str(e)}")
            raise TMDbAPIException("Failed to fetch movie recommendations from TMDb API")
        
        if not recommendations_data:
            raise TMDbAPIException("No recommendations data returned from TMDb API")
        
        # Save movies to database and serialize
        movies_data = []
        for movie_data in recommendations_data.get('results', []):
            try:
                movie = movie_service.create_or_update_movie(movie_data)
                if movie:
                    movies_data.append(MovieListSerializer(movie).data)
            except Exception as e:
                logger.warning(f"Failed to process recommendation movie data: {str(e)}")
                continue
        
        response_data = {
            'results': movies_data,
            'total_results': recommendations_data.get('total_results', 0),
            'total_pages': recommendations_data.get('total_pages', 0),
            'page': page
        }
        
        # Cache for 6 hours
        cache.set(cache_key, response_data, 21600)
        
        return Response(response_data)
        
    except ValidationError as e:
        logger.error(f"Validation error in movie_recommendations: {str(e)}")
        raise InvalidRatingException(str(e))
    except TMDbAPIException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error in movie_recommendations: {str(e)}")
        raise TMDbAPIException("An unexpected error occurred while fetching movie recommendations")


class UserMovieRatingListCreateView(generics.ListCreateAPIView):
    """List user's movie ratings and create new ratings"""
    serializer_class = UserMovieRatingSerializer
    permission_classes = [permissions.IsAuthenticated]
    pagination_class = MoviePagination
    
    @swagger_auto_schema(
        operation_description="Retrieve a paginated list of user's movie ratings",
        operation_summary="List User Ratings",
        responses={
            200: UserMovieRatingSerializer(many=True),
            401: "Authentication required"
        },
        tags=['User Ratings']
    )
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)
    
    @swagger_auto_schema(
        operation_description="Create a new movie rating or update existing rating",
        operation_summary="Rate Movie",
        request_body=UserMovieRatingSerializer,
        responses={
            201: UserMovieRatingSerializer(),
            400: "Bad Request - Invalid rating data",
            401: "Authentication required"
        },
        tags=['User Ratings']
    )
    def post(self, request, *args, **kwargs):
        return super().post(request, *args, **kwargs)
    
    def get_queryset(self):
        try:
            return UserMovieRating.objects.filter(
                user=self.request.user
            ).select_related('movie').prefetch_related('movie__genres')
        except Exception as e:
            logger.error(f"Error in UserMovieRatingListCreateView.get_queryset: {str(e)}")
            return UserMovieRating.objects.none()
    
    def perform_create(self, serializer):
        try:
            # The serializer handles movie validation and duplicate checking internally
            return serializer.save(user=self.request.user)
                
        except Exception as e:
            logger.error(f"Error creating movie rating: {str(e)}")
            raise InvalidRatingException("Failed to create movie rating")


class UserMovieRatingDetailView(generics.RetrieveUpdateDestroyAPIView):
    """Retrieve, update, or delete a user's movie rating"""
    serializer_class = UserMovieRatingSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    @swagger_auto_schema(
        operation_description="Retrieve a specific movie rating",
        operation_summary="Get Rating Details",
        responses={
            200: UserMovieRatingSerializer(),
            404: "Rating not found",
            401: "Authentication required"
        },
        tags=['User Ratings']
    )
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)
    
    @swagger_auto_schema(
        operation_description="Update a movie rating",
        operation_summary="Update Rating",
        request_body=UserMovieRatingSerializer,
        responses={
            200: UserMovieRatingSerializer(),
            404: "Rating not found",
            400: "Bad Request - Invalid rating data",
            401: "Authentication required"
        },
        tags=['User Ratings']
    )
    def put(self, request, *args, **kwargs):
        return super().put(request, *args, **kwargs)
    
    @swagger_auto_schema(
        operation_description="Delete a movie rating",
        operation_summary="Delete Rating",
        responses={
            204: "Rating deleted successfully",
            404: "Rating not found",
            401: "Authentication required"
        },
        tags=['User Ratings']
    )
    def delete(self, request, *args, **kwargs):
        return super().delete(request, *args, **kwargs)
    
    def get_queryset(self):
        try:
            return UserMovieRating.objects.filter(user=self.request.user)
        except Exception as e:
            logger.error(f"Error in UserMovieRatingDetailView.get_queryset: {str(e)}")
            return UserMovieRating.objects.none()
    
    def get_object(self):
        try:
            return super().get_object()
        except UserMovieRating.DoesNotExist:
            logger.warning(f"Rating not found for user {self.request.user.id}")
            raise MovieNotFoundException("Rating not found")
        except Exception as e:
            logger.error(f"Error retrieving rating: {str(e)}")
            raise MovieNotFoundException("Rating not found")


class UserMovieWatchlistListCreateView(generics.ListCreateAPIView):
    """List user's watchlist and add movies to watchlist"""
    serializer_class = UserMovieWatchlistSerializer
    permission_classes = [permissions.IsAuthenticated]
    pagination_class = MoviePagination
    
    @swagger_auto_schema(
        operation_description="Retrieve a paginated list of user's watchlist movies",
        operation_summary="List User Watchlist",
        responses={
            200: UserMovieWatchlistSerializer(many=True),
            401: "Authentication required"
        },
        tags=['User Watchlist']
    )
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)
    
    @swagger_auto_schema(
        operation_description="Add a movie to user's watchlist",
        operation_summary="Add to Watchlist",
        request_body=UserMovieWatchlistSerializer,
        responses={
            201: UserMovieWatchlistSerializer(),
            400: "Bad Request - Movie already in watchlist or invalid data",
            401: "Authentication required"
        },
        tags=['User Watchlist']
    )
    def post(self, request, *args, **kwargs):
        return super().post(request, *args, **kwargs)
    
    def get_queryset(self):
        try:
            return UserMovieWatchlist.objects.filter(
                user=self.request.user
            ).select_related('movie').prefetch_related('movie__genres')
        except Exception as e:
            logger.error(f"Error in UserMovieWatchlistListCreateView.get_queryset: {str(e)}")
            return UserMovieWatchlist.objects.none()
    
    def perform_create(self, serializer):
        try:
            # The serializer handles movie validation and creation internally
            return serializer.save(user=self.request.user)
            
        except Exception as e:
            logger.error(f"Error adding movie to watchlist: {str(e)}")
            raise MovieNotFoundException("Failed to add movie to watchlist")


class UserMovieWatchlistDetailView(generics.RetrieveDestroyAPIView):
    """Remove movie from watchlist"""
    serializer_class = UserMovieWatchlistSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    @swagger_auto_schema(
        operation_description="Retrieve a specific watchlist entry",
        operation_summary="Get Watchlist Entry",
        responses={
            200: UserMovieWatchlistSerializer(),
            404: "Watchlist entry not found",
            401: "Authentication required"
        },
        tags=['User Watchlist']
    )
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)
    
    @swagger_auto_schema(
        operation_description="Remove a movie from user's watchlist",
        operation_summary="Remove from Watchlist",
        responses={
            204: "Movie removed from watchlist successfully",
            404: "Watchlist entry not found",
            401: "Authentication required"
        },
        tags=['User Watchlist']
    )
    def delete(self, request, *args, **kwargs):
        return super().delete(request, *args, **kwargs)
    
    def get_queryset(self):
        try:
            return UserMovieWatchlist.objects.filter(user=self.request.user)
        except Exception as e:
            logger.error(f"Error in UserMovieWatchlistDetailView.get_queryset: {str(e)}")
            return UserMovieWatchlist.objects.none()
    
    def get_object(self):
        try:
            return super().get_object()
        except UserMovieWatchlist.DoesNotExist:
            logger.warning(f"Watchlist item not found for user {self.request.user.id}")
            raise MovieNotFoundException("Watchlist item not found")
        except Exception as e:
            logger.error(f"Error retrieving watchlist item: {str(e)}")
            raise MovieNotFoundException("Watchlist item not found")
