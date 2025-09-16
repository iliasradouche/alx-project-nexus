from rest_framework import generics, status, permissions
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.pagination import PageNumberPagination
from django.db.models import Q, Avg
from django.core.cache import cache
from django.core.exceptions import ValidationError
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


class MovieListView(generics.ListAPIView):
    """List movies with filtering and search"""
    serializer_class = MovieListSerializer
    pagination_class = MoviePagination
    permission_classes = [permissions.AllowAny]
    
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
            # Check if rating already exists
            movie = serializer.validated_data['movie']
            existing_rating = UserMovieRating.objects.filter(
                user=self.request.user,
                movie=movie
            ).first()
            
            if existing_rating:
                # Update existing rating
                existing_rating.rating = serializer.validated_data['rating']
                existing_rating.save()
                return existing_rating
            else:
                # Create new rating
                return serializer.save(user=self.request.user)
                
        except Exception as e:
            logger.error(f"Error creating movie rating: {str(e)}")
            raise InvalidRatingException("Failed to create movie rating")


class UserMovieRatingDetailView(generics.RetrieveUpdateDestroyAPIView):
    """Retrieve, update, or delete a user's movie rating"""
    serializer_class = UserMovieRatingSerializer
    permission_classes = [permissions.IsAuthenticated]
    
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
            # Check if movie is already in watchlist
            movie = serializer.validated_data['movie']
            existing_watchlist = UserMovieWatchlist.objects.filter(
                user=self.request.user,
                movie=movie
            ).first()
            
            if existing_watchlist:
                raise DuplicateWatchlistException("Movie is already in your watchlist")
            
            return serializer.save(user=self.request.user)
            
        except DuplicateWatchlistException:
            raise
        except Exception as e:
            logger.error(f"Error adding movie to watchlist: {str(e)}")
            raise MovieNotFoundException("Failed to add movie to watchlist")


class UserMovieWatchlistDetailView(generics.RetrieveDestroyAPIView):
    """Remove movie from watchlist"""
    serializer_class = UserMovieWatchlistSerializer
    permission_classes = [permissions.IsAuthenticated]
    
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
