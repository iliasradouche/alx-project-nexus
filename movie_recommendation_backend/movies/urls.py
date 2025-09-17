from django.urls import path
from . import views, auth_views, user_views

app_name = 'movies'

urlpatterns = [
    # Movie endpoints
    path('', views.MovieListView.as_view(), name='movie-list'),
    path('<int:tmdb_id>/', views.MovieDetailView.as_view(), name='movie-detail'),
    path('<int:tmdb_id>/recommendations/', views.movie_recommendations, name='movie-recommendations'),
    
    # Genre endpoints
    path('genres/', views.GenreListView.as_view(), name='genre-list'),
    
    # TMDb API endpoints
    path('search/', views.search_movies, name='movie-search'),
    path('popular/', views.popular_movies, name='popular-movies'),
    path('top-rated/', views.top_rated_movies, name='top-rated-movies'),
    
    # User movie interactions
    path('ratings/', views.UserMovieRatingListCreateView.as_view(), name='user-ratings'),
    path('ratings/<int:pk>/', views.UserMovieRatingDetailView.as_view(), name='user-rating-detail'),
    path('watchlist/', views.UserMovieWatchlistListCreateView.as_view(), name='user-watchlist'),
    path('watchlist/<int:pk>/', views.UserMovieWatchlistDetailView.as_view(), name='user-watchlist-detail'),
    
    # Authentication endpoints moved to auth_urls.py
    
    # User-specific endpoints
    path('user/stats/', user_views.user_stats, name='user-stats'),
    path('user/recommendations/', user_views.recommended_for_user, name='user-recommendations'),
    path('user/movie/<int:movie_id>/status/', user_views.check_movie_status, name='check-movie-status'),
    path('user/watchlist/bulk-add/', user_views.bulk_add_to_watchlist, name='bulk-add-watchlist'),
]