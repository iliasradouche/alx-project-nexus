from django.urls import path
from . import views

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
]