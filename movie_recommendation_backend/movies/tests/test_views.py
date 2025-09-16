from django.test import TestCase
from django.contrib.auth.models import User
from django.urls import reverse
from rest_framework.test import APITestCase, APIClient
from rest_framework import status
from rest_framework_simplejwt.tokens import RefreshToken
from unittest.mock import patch, Mock
from decimal import Decimal
from datetime import date
import json

from movies.models import Genre, Movie, UserMovieRating, UserMovieWatchlist
from movies.exceptions import MovieNotFoundException, TMDbAPIException


class MovieViewTestCase(APITestCase):
    """Base test case for movie views"""
    
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.client = APIClient()
        
        # Create test genres
        self.action_genre = Genre.objects.create(tmdb_id=28, name='Action')
        self.drama_genre = Genre.objects.create(tmdb_id=18, name='Drama')
        
        # Create test movies
        self.movie1 = Movie.objects.create(
            tmdb_id=550,
            title='Fight Club',
            overview='An insomniac office worker forms an underground fight club.',
            release_date=date(1999, 10, 15),
            vote_average=8.4,
            vote_count=26280,
            popularity=61.416,
            poster_path='/pB8BM7pdSp6B6Ih7QZ4DrQ3PmJK.jpg',
            adult=False,
            original_language='en',
            original_title='Fight Club'
        )
        self.movie1.genres.add(self.action_genre, self.drama_genre)
        
        self.movie2 = Movie.objects.create(
            tmdb_id=13,
            title='Forrest Gump',
            overview='The presidencies of Kennedy and Johnson through the eyes of Alabama man.',
            release_date=date(1994, 6, 23),
            vote_average=8.5,
            vote_count=24000,
            popularity=55.0,
            poster_path='/arw2vcBveWOVZr6pxd9XTd1TdQa.jpg',
            adult=False,
            original_language='en',
            original_title='Forrest Gump'
        )
        self.movie2.genres.add(self.drama_genre)
    
    def authenticate_user(self):
        """Helper method to authenticate user"""
        refresh = RefreshToken.for_user(self.user)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {refresh.access_token}')


class MovieListViewTest(MovieViewTestCase):
    """Test cases for MovieListView"""
    
    def test_get_movies_list(self):
        """Test getting list of movies"""
        url = reverse('movie-list')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('results', response.data)
        self.assertEqual(len(response.data['results']), 2)
    
    def test_filter_movies_by_genre(self):
        """Test filtering movies by genre"""
        url = reverse('movie-list')
        response = self.client.get(url, {'genre': self.action_genre.id})
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)
        self.assertEqual(response.data['results'][0]['title'], 'Fight Club')
    
    def test_search_movies_by_title(self):
        """Test searching movies by title"""
        url = reverse('movie-list')
        response = self.client.get(url, {'search': 'Fight'})
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)
        self.assertEqual(response.data['results'][0]['title'], 'Fight Club')
    
    def test_filter_movies_by_year(self):
        """Test filtering movies by release year"""
        url = reverse('movie-list')
        response = self.client.get(url, {'year': 1999})
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)
        self.assertEqual(response.data['results'][0]['title'], 'Fight Club')
    
    def test_invalid_genre_filter(self):
        """Test filtering with invalid genre ID"""
        url = reverse('movie-list')
        response = self.client.get(url, {'genre': 'invalid'})
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
    
    def test_pagination(self):
        """Test pagination of movie list"""
        # Create more movies to test pagination
        for i in range(15):
            Movie.objects.create(
                tmdb_id=1000 + i,
                title=f'Test Movie {i}',
                release_date='2020-01-01',
                vote_average=Decimal('7.0'),
                vote_count=1000,
                popularity=Decimal('30.0')
            )
        
        url = reverse('movie-list')
        response = self.client.get(url, {'page': 1})
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('next', response.data)
        self.assertIn('previous', response.data)
        self.assertIn('count', response.data)


class MovieDetailViewTest(MovieViewTestCase):
    """Test cases for MovieDetailView"""
    
    def test_get_movie_detail(self):
        """Test getting movie detail"""
        url = reverse('movie-detail', kwargs={'pk': self.movie1.pk})
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['title'], 'Fight Club')
        self.assertEqual(response.data['tmdb_id'], 550)
    
    def test_get_nonexistent_movie(self):
        """Test getting detail of nonexistent movie"""
        url = reverse('movie-detail', kwargs={'pk': 99999})
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)


class GenreListViewTest(MovieViewTestCase):
    """Test cases for GenreListView"""
    
    def test_get_genres_list(self):
        """Test getting list of genres"""
        url = reverse('genre-list')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 2)
        genre_names = [genre['name'] for genre in response.data]
        self.assertIn('Action', genre_names)
        self.assertIn('Drama', genre_names)


class UserMovieRatingViewTest(MovieViewTestCase):
    """Test cases for UserMovieRating views"""
    
    def test_create_rating_authenticated(self):
        """Test creating a movie rating when authenticated"""
        self.authenticate_user()
        url = reverse('user-ratings')
        data = {
            'movie': self.movie1.id,
            'rating': 8.5
        }
        
        response = self.client.post(url, data)
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(UserMovieRating.objects.count(), 1)
        rating = UserMovieRating.objects.first()
        self.assertEqual(rating.user, self.user)
        self.assertEqual(rating.movie, self.movie1)
        self.assertEqual(rating.rating, Decimal('8.5'))
    
    def test_create_rating_unauthenticated(self):
        """Test creating a movie rating when not authenticated"""
        url = reverse('user-ratings')
        data = {
            'movie': self.movie1.id,
            'rating': 8.5
        }
        
        response = self.client.post(url, data)
        
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
    
    def test_update_existing_rating(self):
        """Test updating an existing rating"""
        self.authenticate_user()
        
        # Create initial rating
        UserMovieRating.objects.create(
            user=self.user,
            movie=self.movie1,
            rating=7.0
        )
        
        url = reverse('user-ratings')
        data = {
            'movie': self.movie1.id,
            'rating': 9.0
        }
        
        response = self.client.post(url, data)
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(UserMovieRating.objects.count(), 1)
        rating = UserMovieRating.objects.first()
        self.assertEqual(rating.rating, 9.0)
    
    def test_get_user_ratings(self):
        """Test getting user's movie ratings"""
        self.authenticate_user()
        
        # Create some ratings
        UserMovieRating.objects.create(
            user=self.user,
            movie=self.movie1,
            rating=8.5
        )
        UserMovieRating.objects.create(
            user=self.user,
            movie=self.movie2,
            rating=9.0
        )
        
        url = reverse('user-ratings')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 2)
    
    def test_invalid_rating_value(self):
        """Test creating rating with invalid value"""
        self.authenticate_user()
        url = reverse('user-ratings')
        data = {
            'movie': self.movie1.id,
            'rating': 11.0  # Invalid: should be <= 10
        }
        
        response = self.client.post(url, data)
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


class UserMovieWatchlistViewTest(MovieViewTestCase):
    """Test cases for UserMovieWatchlist views"""
    
    def test_add_to_watchlist_authenticated(self):
        """Test adding movie to watchlist when authenticated"""
        self.authenticate_user()
        url = reverse('user-watchlist')
        data = {'movie': self.movie1.id}
        
        response = self.client.post(url, data)
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(UserMovieWatchlist.objects.count(), 1)
        watchlist_item = UserMovieWatchlist.objects.first()
        self.assertEqual(watchlist_item.user, self.user)
        self.assertEqual(watchlist_item.movie, self.movie1)
    
    def test_add_to_watchlist_unauthenticated(self):
        """Test adding movie to watchlist when not authenticated"""
        url = reverse('user-watchlist')
        data = {'movie': self.movie1.id}
        
        response = self.client.post(url, data)
        
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
    
    def test_add_duplicate_to_watchlist(self):
        """Test adding duplicate movie to watchlist"""
        self.authenticate_user()
        
        # Add movie to watchlist first
        UserMovieWatchlist.objects.create(
            user=self.user,
            movie=self.movie1
        )
        
        url = reverse('user-watchlist')
        data = {'movie': self.movie1.id}
        
        response = self.client.post(url, data)
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(UserMovieWatchlist.objects.count(), 1)
    
    def test_get_user_watchlist(self):
        """Test getting user's watchlist"""
        self.authenticate_user()
        
        # Add movies to watchlist
        UserMovieWatchlist.objects.create(
            user=self.user,
            movie=self.movie1
        )
        UserMovieWatchlist.objects.create(
            user=self.user,
            movie=self.movie2
        )
        
        url = reverse('user-watchlist')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 2)
    
    def test_remove_from_watchlist(self):
        """Test removing movie from watchlist"""
        self.authenticate_user()
        
        # Add movie to watchlist
        watchlist_item = UserMovieWatchlist.objects.create(
            user=self.user,
            movie=self.movie1
        )
        
        url = reverse('user-watchlist-detail', kwargs={'pk': watchlist_item.pk})
        response = self.client.delete(url)
        
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(UserMovieWatchlist.objects.count(), 0)


class TMDbAPIViewTest(MovieViewTestCase):
    """Test cases for TMDb API views"""
    
    @patch('movies.views.requests.get')
    def test_search_movies_success(self, mock_get):
        """Test successful movie search"""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'results': [
                {
                    'id': 550,
                    'title': 'Fight Club',
                    'overview': 'Test overview',
                    'release_date': '1999-10-15',
                    'vote_average': 8.4,
                    'vote_count': 26280,
                    'popularity': 61.416,
                    'poster_path': '/test.jpg'
                }
            ],
            'total_results': 1,
            'total_pages': 1
        }
        mock_get.return_value = mock_response
        
        url = reverse('search-movies')
        response = self.client.get(url, {'query': 'Fight Club'})
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('results', response.data)
        self.assertEqual(len(response.data['results']), 1)
    
    @patch('movies.views.requests.get')
    def test_search_movies_api_error(self, mock_get):
        """Test movie search with API error"""
        mock_response = Mock()
        mock_response.status_code = 500
        mock_get.return_value = mock_response
        
        url = reverse('search-movies')
        response = self.client.get(url, {'query': 'Fight Club'})
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
    
    def test_search_movies_missing_query(self):
        """Test movie search without query parameter"""
        url = reverse('search-movies')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
    
    @patch('movies.views.requests.get')
    def test_popular_movies_success(self, mock_get):
        """Test successful popular movies fetch"""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'results': [
                {
                    'id': 550,
                    'title': 'Fight Club',
                    'overview': 'Test overview',
                    'release_date': '1999-10-15',
                    'vote_average': 8.4,
                    'vote_count': 26280,
                    'popularity': 61.416,
                    'poster_path': '/test.jpg'
                }
            ],
            'total_results': 1,
            'total_pages': 1
        }
        mock_get.return_value = mock_response
        
        url = reverse('popular-movies')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('results', response.data)
    
    @patch('movies.views.requests.get')
    def test_movie_recommendations_success(self, mock_get):
        """Test successful movie recommendations fetch"""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'results': [
                {
                    'id': 551,
                    'title': 'Recommended Movie',
                    'overview': 'Test overview',
                    'release_date': '2000-01-01',
                    'vote_average': 7.5,
                    'vote_count': 1000,
                    'popularity': 40.0,
                    'poster_path': '/test2.jpg'
                }
            ],
            'total_results': 1,
            'total_pages': 1
        }
        mock_get.return_value = mock_response
        
        url = reverse('movie-recommendations', kwargs={'movie_id': 550})
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('results', response.data)
    
    def test_movie_recommendations_invalid_id(self):
        """Test movie recommendations with invalid movie ID"""
        url = reverse('movie-recommendations', kwargs={'movie_id': 'invalid'})
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)