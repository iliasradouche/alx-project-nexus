from rest_framework import generics, status, permissions
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.pagination import PageNumberPagination
from django.db.models import Q, Avg
from django.core.cache import cache
from .models import Movie, Genre, UserMovieRating, UserMovieWatchlist
from .serializers import (
    MovieListSerializer, MovieDetailSerializer, GenreSerializer,
    UserMovieRatingSerializer, UserMovieWatchlistSerializer,
    MovieSearchSerializer
)
from .services import TMDbAPIService, MovieDataService
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
        queryset = Movie.objects.select_related().prefetch_related('genres')
        
        # Filter by genre
        genre = self.request.query_params.get('genre')
        if genre:
            queryset = queryset.filter(genres__name__icontains=genre)
        
        # Filter by year
        year = self.request.query_params.get('year')
        if year:
            queryset = queryset.filter(release_date__year=year)
        
        # Filter by minimum rating
        min_rating = self.request.query_params.get('min_rating')
        if min_rating:
            try:
                min_rating = float(min_rating)
                queryset = queryset.filter(vote_average__gte=min_rating)
            except ValueError:
                pass
        
        # Search by title
        search = self.request.query_params.get('search')
        if search:
            queryset = queryset.filter(
                Q(title__icontains=search) | 
                Q(original_title__icontains=search)
            )
        
        # Ordering
        ordering = self.request.query_params.get('ordering', '-popularity')
        valid_orderings = [
            'popularity', '-popularity', 'vote_average', '-vote_average',
            'release_date', '-release_date', 'title', '-title'
        ]
        if ordering in valid_orderings:
            queryset = queryset.order_by(ordering)
        
        return queryset.distinct()


class MovieDetailView(generics.RetrieveAPIView):
    """Get movie details"""
    queryset = Movie.objects.select_related().prefetch_related('genres')
    serializer_class = MovieDetailSerializer
    permission_classes = [permissions.AllowAny]
    lookup_field = 'tmdb_id'


class GenreListView(generics.ListAPIView):
    """List all genres"""
    queryset = Genre.objects.all()
    serializer_class = GenreSerializer
    permission_classes = [permissions.AllowAny]


@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def search_movies(request):
    """Search movies using TMDb API"""
    serializer = MovieSearchSerializer(data=request.data)
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    query = serializer.validated_data['query']
    page = serializer.validated_data['page']
    
    tmdb_service = TMDbAPIService()
    movie_service = MovieDataService()
    
    # Search TMDb API
    search_results = tmdb_service.search_movies(query, page)
    
    if not search_results:
        return Response(
            {'error': 'Failed to search movies'},
            status=status.HTTP_503_SERVICE_UNAVAILABLE
        )
    
    # Save movies to database
    movies_data = []
    for movie_data in search_results.get('results', []):
        movie = movie_service.create_or_update_movie(movie_data)
        if movie:
            movies_data.append(MovieListSerializer(movie).data)
    
    return Response({
        'results': movies_data,
        'total_results': search_results.get('total_results', 0),
        'total_pages': search_results.get('total_pages', 0),
        'page': page
    })


@api_view(['GET'])
@permission_classes([permissions.AllowAny])
def popular_movies(request):
    """Get popular movies from TMDb"""
    page = int(request.query_params.get('page', 1))
    
    cache_key = f"popular_movies_db_{page}"
    cached_movies = cache.get(cache_key)
    
    if cached_movies:
        return Response(cached_movies)
    
    tmdb_service = TMDbAPIService()
    movie_service = MovieDataService()
    
    # Get popular movies from TMDb
    popular_data = tmdb_service.get_popular_movies(page)
    
    if not popular_data:
        return Response(
            {'error': 'Failed to fetch popular movies'},
            status=status.HTTP_503_SERVICE_UNAVAILABLE
        )
    
    # Save movies to database and serialize
    movies_data = []
    for movie_data in popular_data.get('results', []):
        movie = movie_service.create_or_update_movie(movie_data)
        if movie:
            movies_data.append(MovieListSerializer(movie).data)
    
    response_data = {
        'results': movies_data,
        'total_results': popular_data.get('total_results', 0),
        'total_pages': popular_data.get('total_pages', 0),
        'page': page
    }
    
    # Cache for 1 hour
    cache.set(cache_key, response_data, 3600)
    
    return Response(response_data)


@api_view(['GET'])
@permission_classes([permissions.AllowAny])
def top_rated_movies(request):
    """Get top rated movies from TMDb"""
    page = int(request.query_params.get('page', 1))
    
    cache_key = f"top_rated_movies_db_{page}"
    cached_movies = cache.get(cache_key)
    
    if cached_movies:
        return Response(cached_movies)
    
    tmdb_service = TMDbAPIService()
    movie_service = MovieDataService()
    
    # Get top rated movies from TMDb
    top_rated_data = tmdb_service.get_top_rated_movies(page)
    
    if not top_rated_data:
        return Response(
            {'error': 'Failed to fetch top rated movies'},
            status=status.HTTP_503_SERVICE_UNAVAILABLE
        )
    
    # Save movies to database and serialize
    movies_data = []
    for movie_data in top_rated_data.get('results', []):
        movie = movie_service.create_or_update_movie(movie_data)
        if movie:
            movies_data.append(MovieListSerializer(movie).data)
    
    response_data = {
        'results': movies_data,
        'total_results': top_rated_data.get('total_results', 0),
        'total_pages': top_rated_data.get('total_pages', 0),
        'page': page
    }
    
    # Cache for 1 hour
    cache.set(cache_key, response_data, 3600)
    
    return Response(response_data)


@api_view(['GET'])
@permission_classes([permissions.AllowAny])
def movie_recommendations(request, tmdb_id):
    """Get movie recommendations based on a specific movie"""
    page = int(request.query_params.get('page', 1))
    
    cache_key = f"movie_recommendations_{tmdb_id}_{page}"
    cached_recommendations = cache.get(cache_key)
    
    if cached_recommendations:
        return Response(cached_recommendations)
    
    tmdb_service = TMDbAPIService()
    movie_service = MovieDataService()
    
    # Get recommendations from TMDb
    recommendations_data = tmdb_service.get_movie_recommendations(tmdb_id, page)
    
    if not recommendations_data:
        return Response(
            {'error': 'Failed to fetch movie recommendations'},
            status=status.HTTP_503_SERVICE_UNAVAILABLE
        )
    
    # Save movies to database and serialize
    movies_data = []
    for movie_data in recommendations_data.get('results', []):
        movie = movie_service.create_or_update_movie(movie_data)
        if movie:
            movies_data.append(MovieListSerializer(movie).data)
    
    response_data = {
        'results': movies_data,
        'total_results': recommendations_data.get('total_results', 0),
        'total_pages': recommendations_data.get('total_pages', 0),
        'page': page
    }
    
    # Cache for 6 hours
    cache.set(cache_key, response_data, 21600)
    
    return Response(response_data)


class UserMovieRatingListCreateView(generics.ListCreateAPIView):
    """List user's movie ratings and create new ratings"""
    serializer_class = UserMovieRatingSerializer
    permission_classes = [permissions.IsAuthenticated]
    pagination_class = MoviePagination
    
    def get_queryset(self):
        return UserMovieRating.objects.filter(
            user=self.request.user
        ).select_related('movie').prefetch_related('movie__genres')


class UserMovieRatingDetailView(generics.RetrieveUpdateDestroyAPIView):
    """Retrieve, update, or delete a user's movie rating"""
    serializer_class = UserMovieRatingSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        return UserMovieRating.objects.filter(user=self.request.user)


class UserMovieWatchlistListCreateView(generics.ListCreateAPIView):
    """List user's watchlist and add movies to watchlist"""
    serializer_class = UserMovieWatchlistSerializer
    permission_classes = [permissions.IsAuthenticated]
    pagination_class = MoviePagination
    
    def get_queryset(self):
        return UserMovieWatchlist.objects.filter(
            user=self.request.user
        ).select_related('movie').prefetch_related('movie__genres')


class UserMovieWatchlistDetailView(generics.RetrieveDestroyAPIView):
    """Remove movie from watchlist"""
    serializer_class = UserMovieWatchlistSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        return UserMovieWatchlist.objects.filter(user=self.request.user)
