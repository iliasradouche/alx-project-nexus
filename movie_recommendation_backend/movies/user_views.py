from rest_framework import status, permissions
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from django.db.models import Avg, Count
from django.core.cache import cache
from .models import Movie, UserMovieRating, UserMovieWatchlist
from .serializers import MovieListSerializer
from .cache_utils import (
    cache_user_recommendations, 
    get_cached_user_recommendations,
    invalidate_user_cache,
    cache_result
)
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi


@swagger_auto_schema(
    method='get',
    operation_description="Get user statistics including total ratings, watchlist count, and average rating",
    responses={
        200: openapi.Response('User statistics', openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'total_ratings': openapi.Schema(type=openapi.TYPE_INTEGER),
                'watchlist_count': openapi.Schema(type=openapi.TYPE_INTEGER),
                'average_rating': openapi.Schema(type=openapi.TYPE_NUMBER, format=openapi.FORMAT_FLOAT),
            }
        )),
        401: 'Unauthorized'
    }
)
@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def user_stats(request):
    """
    Get user statistics (ratings count, watchlist count, average rating)
    """
    try:
        user = request.user
        
        # Check cache first
        cache_key = f"user_stats:{user.id}"
        cached_stats = cache.get(cache_key)
        if cached_stats:
            return Response(cached_stats, status=status.HTTP_200_OK)
        
        # Get user statistics
        ratings_count = UserMovieRating.objects.filter(user=user).count()
        watchlist_count = UserMovieWatchlist.objects.filter(user=user).count()
        
        # Calculate average rating
        avg_rating = UserMovieRating.objects.filter(user=user).aggregate(
            avg_rating=Avg('rating')
        )['avg_rating']
        
        # Get rating distribution
        rating_distribution = {}
        for i in range(1, 11):
            count = UserMovieRating.objects.filter(user=user, rating=i).count()
            rating_distribution[str(i)] = count
        
        stats = {
            'ratings_count': ratings_count,
            'watchlist_count': watchlist_count,
            'average_rating': round(avg_rating, 2) if avg_rating else None,
            'rating_distribution': rating_distribution
        }
        
        # Cache for 10 minutes
        cache.set(cache_key, stats, 600)
        
        return Response(stats, status=status.HTTP_200_OK)
        
    except Exception as e:
        return Response({
            'error': f'Failed to get user stats: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@swagger_auto_schema(
    method='get',
    operation_description="Check if a movie is in user's watchlist and get user's rating",
    manual_parameters=[
        openapi.Parameter('movie_id', openapi.IN_PATH, description="Movie ID", type=openapi.TYPE_INTEGER)
    ],
    responses={
        200: openapi.Response('Movie status', openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'in_watchlist': openapi.Schema(type=openapi.TYPE_BOOLEAN),
                'user_rating': openapi.Schema(type=openapi.TYPE_NUMBER, format=openapi.FORMAT_FLOAT, nullable=True),
            }
        )),
        401: 'Unauthorized'
    }
)
@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def check_movie_status(request, movie_id):
    """
    Check if a movie is rated or in watchlist for the current user
    """
    try:
        user = request.user
        
        # Check if movie exists
        try:
            movie = Movie.objects.get(id=movie_id)
        except Movie.DoesNotExist:
            return Response({
                'error': 'Movie not found'
            }, status=status.HTTP_404_NOT_FOUND)
        
        # Check rating
        user_rating = None
        try:
            rating_obj = UserMovieRating.objects.get(user=user, movie=movie)
            user_rating = rating_obj.rating
        except UserMovieRating.DoesNotExist:
            pass
        
        # Check watchlist
        in_watchlist = UserMovieWatchlist.objects.filter(
            user=user, movie=movie
        ).exists()
        
        return Response({
            'movie_id': movie_id,
            'user_rating': user_rating,
            'in_watchlist': in_watchlist,
            'movie': MovieListSerializer(movie).data
        }, status=status.HTTP_200_OK)
        
    except Exception as e:
        return Response({
            'error': f'Failed to check movie status: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@swagger_auto_schema(
    method='get',
    operation_description="Get personalized movie recommendations based on user's ratings and preferences",
    manual_parameters=[
        openapi.Parameter('limit', openapi.IN_QUERY, description="Number of recommendations (default: 10)", type=openapi.TYPE_INTEGER)
    ],
    responses={
        200: openapi.Response('Recommended movies', openapi.Schema(
            type=openapi.TYPE_ARRAY,
            items=openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={
                    'id': openapi.Schema(type=openapi.TYPE_INTEGER),
                    'title': openapi.Schema(type=openapi.TYPE_STRING),
                    'overview': openapi.Schema(type=openapi.TYPE_STRING),
                    'release_date': openapi.Schema(type=openapi.TYPE_STRING, format=openapi.FORMAT_DATE),
                    'vote_average': openapi.Schema(type=openapi.TYPE_NUMBER, format=openapi.FORMAT_FLOAT),
                    'poster_path': openapi.Schema(type=openapi.TYPE_STRING, nullable=True),
                }
            )
        )),
        401: 'Unauthorized'
    }
)
@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def recommended_for_user(request):
    """
    Get personalized movie recommendations based on user's ratings
    """
    try:
        user = request.user
        
        # Check cache first
        cached_recommendations = get_cached_user_recommendations(user.id)
        if cached_recommendations:
            return Response(cached_recommendations, status=status.HTTP_200_OK)
        
        # Get user's highly rated movies (rating >= 7)
        highly_rated = UserMovieRating.objects.filter(
            user=user, rating__gte=7
        ).select_related('movie').prefetch_related('movie__genres')
        
        if not highly_rated.exists():
            result = {
                'message': 'No ratings found. Rate some movies to get personalized recommendations.',
                'recommendations': []
            }
            # Cache empty result for 5 minutes
            cache_user_recommendations(user.id, result, timeout=300)
            return Response(result, status=status.HTTP_200_OK)
        
        # Get genres from highly rated movies
        favorite_genres = set()
        for rating in highly_rated:
            for genre in rating.movie.genres.all():
                favorite_genres.add(genre.id)
        
        # Get movies from favorite genres that user hasn't rated
        rated_movie_ids = UserMovieRating.objects.filter(user=user).values_list('movie_id', flat=True)
        watchlist_movie_ids = UserMovieWatchlist.objects.filter(user=user).values_list('movie_id', flat=True)
        
        recommendations = Movie.objects.filter(
            genres__id__in=favorite_genres,
            vote_average__gte=6.0  # Only recommend well-rated movies
        ).exclude(
            id__in=list(rated_movie_ids) + list(watchlist_movie_ids)
        ).distinct().order_by('-vote_average', '-popularity')[:20]
        
        result = {
            'recommendations': MovieListSerializer(recommendations, many=True).data,
            'based_on_genres': len(favorite_genres),
            'total_recommendations': recommendations.count()
        }
        
        # Cache recommendations for 30 minutes
        cache_user_recommendations(user.id, result, timeout=1800)
        
        return Response(result, status=status.HTTP_200_OK)
        
    except Exception as e:
        return Response({
            'error': f'Failed to get recommendations: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@swagger_auto_schema(
    method='post',
    operation_description="Add multiple movies to user's watchlist",
    request_body=openapi.Schema(
        type=openapi.TYPE_OBJECT,
        required=['movie_ids'],
        properties={
            'movie_ids': openapi.Schema(
                type=openapi.TYPE_ARRAY,
                items=openapi.Schema(type=openapi.TYPE_INTEGER),
                description='List of movie IDs to add to watchlist'
            ),
        }
    ),
    responses={
        200: openapi.Response('Bulk add result', openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'added': openapi.Schema(type=openapi.TYPE_INTEGER, description='Number of movies added'),
                'skipped': openapi.Schema(type=openapi.TYPE_INTEGER, description='Number of movies already in watchlist'),
                'not_found': openapi.Schema(type=openapi.TYPE_INTEGER, description='Number of movies not found'),
            }
        )),
        400: 'Bad request - invalid movie_ids',
        401: 'Unauthorized'
    }
)
@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def bulk_add_to_watchlist(request):
    """
    Add multiple movies to watchlist at once
    """
    try:
        user = request.user
        movie_ids = request.data.get('movie_ids', [])
        
        if not movie_ids or not isinstance(movie_ids, list):
            return Response({
                'error': 'movie_ids must be a non-empty list'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Validate movies exist
        existing_movies = Movie.objects.filter(id__in=movie_ids)
        existing_movie_ids = list(existing_movies.values_list('id', flat=True))
        
        # Check which movies are already in watchlist
        already_in_watchlist = UserMovieWatchlist.objects.filter(
            user=user, movie_id__in=existing_movie_ids
        ).values_list('movie_id', flat=True)
        
        # Add movies to watchlist
        new_watchlist_items = []
        for movie_id in existing_movie_ids:
            if movie_id not in already_in_watchlist:
                new_watchlist_items.append(
                    UserMovieWatchlist(user=user, movie_id=movie_id)
                )
        
        # Bulk create
        created_items = UserMovieWatchlist.objects.bulk_create(new_watchlist_items)
        
        return Response({
            'message': f'Added {len(created_items)} movies to watchlist',
            'added_count': len(created_items),
            'already_in_watchlist': len(already_in_watchlist),
            'invalid_movie_ids': list(set(movie_ids) - set(existing_movie_ids))
        }, status=status.HTTP_201_CREATED)
        
    except Exception as e:
        return Response({
            'error': f'Failed to add movies to watchlist: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)