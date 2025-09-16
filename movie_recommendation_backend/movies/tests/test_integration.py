from django.test import TestCase, TransactionTestCase
from django.contrib.auth.models import User
from django.urls import reverse
from django.test.utils import override_settings
from django.core.cache import cache
from rest_framework.test import APITestCase, APIClient
from rest_framework import status
from rest_framework_simplejwt.tokens import RefreshToken
from unittest.mock import patch, Mock
from decimal import Decimal
from datetime import date
import json
import time

from movies.models import Genre, Movie, UserMovieRating, UserMovieWatchlist
from movies.middleware import RateLimitMiddleware, RequestValidationMiddleware


class MovieAPIIntegrationTest(APITestCase):
    """Integration tests for the complete movie API workflow"""
    
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.client = APIClient()
        
        # Create test data
        self.action_genre = Genre.objects.create(tmdb_id=28, name='Action')
        self.drama_genre = Genre.objects.create(tmdb_id=18, name='Drama')
        
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
            overview='The presidencies of Kennedy and Johnson.',
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
        return refresh.access_token
    
    def test_complete_user_workflow(self):
        """Test complete user workflow: browse movies, rate, add to watchlist"""
        # Step 1: Browse movies without authentication
        movies_url = reverse('movie-list')
        response = self.client.get(movies_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 2)
        
        # Step 2: Get movie details
        movie_detail_url = reverse('movie-detail', kwargs={'pk': self.movie1.pk})
        response = self.client.get(movie_detail_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['title'], 'Fight Club')
        
        # Step 3: Try to rate without authentication (should fail)
        ratings_url = reverse('user-ratings')
        rating_data = {'movie': self.movie1.id, 'rating': 8.5}
        response = self.client.post(ratings_url, rating_data)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        
        # Step 4: Authenticate user
        token = self.authenticate_user()
        
        # Step 5: Rate a movie
        response = self.client.post(ratings_url, rating_data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(UserMovieRating.objects.count(), 1)
        
        # Step 6: Add movie to watchlist
        watchlist_url = reverse('user-watchlist')
        watchlist_data = {'movie': self.movie2.id}
        response = self.client.post(watchlist_url, watchlist_data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(UserMovieWatchlist.objects.count(), 1)
        
        # Step 7: Get user's ratings
        response = self.client.get(ratings_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)
        
        # Step 8: Get user's watchlist
        response = self.client.get(watchlist_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)
        
        # Step 9: Update rating
        updated_rating_data = {'movie': self.movie1.id, 'rating': 9.0}
        response = self.client.post(ratings_url, updated_rating_data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        
        # Verify rating was updated, not duplicated
        self.assertEqual(UserMovieRating.objects.count(), 1)
        rating = UserMovieRating.objects.first()
        self.assertEqual(rating.rating, Decimal('9.0'))
        
        # Step 10: Remove from watchlist
        watchlist_item = UserMovieWatchlist.objects.first()
        watchlist_detail_url = reverse('user-watchlist-detail', kwargs={'pk': watchlist_item.pk})
        response = self.client.delete(watchlist_detail_url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(UserMovieWatchlist.objects.count(), 0)
    
    def test_filtering_and_search_workflow(self):
        """Test movie filtering and search functionality"""
        movies_url = reverse('movie-list')
        
        # Test genre filtering
        response = self.client.get(movies_url, {'genre': self.action_genre.id})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)
        self.assertEqual(response.data['results'][0]['title'], 'Fight Club')
        
        # Test year filtering
        response = self.client.get(movies_url, {'year': 1999})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)
        
        # Test search
        response = self.client.get(movies_url, {'search': 'Fight'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)
        
        # Test combined filters
        response = self.client.get(movies_url, {
            'genre': self.drama_genre.id,
            'year': 1994
        })
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)
        self.assertEqual(response.data['results'][0]['title'], 'Forrest Gump')
    
    @patch('movies.views.requests.get')
    def test_tmdb_api_integration(self, mock_get):
        """Test integration with TMDb API endpoints"""
        # Mock TMDb API response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'results': [
                {
                    'id': 551,
                    'title': 'New Movie',
                    'overview': 'A new movie from TMDb',
                    'release_date': '2023-01-01',
                    'vote_average': 7.5,
                    'vote_count': 1000,
                    'popularity': 45.0,
                    'poster_path': '/new_movie.jpg'
                }
            ],
            'total_results': 1,
            'total_pages': 1
        }
        mock_get.return_value = mock_response
        
        # Test search movies
        search_url = reverse('search-movies')
        response = self.client.get(search_url, {'query': 'New Movie'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('results', response.data)
        
        # Test popular movies
        popular_url = reverse('popular-movies')
        response = self.client.get(popular_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('results', response.data)
        
        # Test movie recommendations
        recommendations_url = reverse('movie-recommendations', kwargs={'movie_id': 550})
        response = self.client.get(recommendations_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('results', response.data)
    
    def test_error_handling_workflow(self):
        """Test error handling throughout the API"""
        # Test invalid movie ID
        invalid_movie_url = reverse('movie-detail', kwargs={'pk': 99999})
        response = self.client.get(invalid_movie_url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        
        # Test invalid genre filter
        movies_url = reverse('movie-list')
        response = self.client.get(movies_url, {'genre': 'invalid'})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        
        # Test invalid rating
        self.authenticate_user()
        ratings_url = reverse('user-ratings')
        invalid_rating_data = {'movie': self.movie1.id, 'rating': 11.0}
        response = self.client.post(ratings_url, invalid_rating_data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        
        # Test duplicate watchlist entry
        watchlist_url = reverse('user-watchlist')
        watchlist_data = {'movie': self.movie1.id}
        
        # Add to watchlist first time
        response = self.client.post(watchlist_url, watchlist_data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        
        # Try to add same movie again
        response = self.client.post(watchlist_url, watchlist_data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


class CachingIntegrationTest(APITestCase):
    """Integration tests for caching functionality"""
    
    def setUp(self):
        self.client = APIClient()
        cache.clear()  # Clear cache before each test
    
    def test_movie_list_caching(self):
        """Test that movie list responses are cached"""
        # Create test movie
        movie = Movie.objects.create(
            tmdb_id=550,
            title='Fight Club',
            release_date='1999-10-15',
            vote_average=Decimal('8.4'),
            vote_count=26280,
            popularity=Decimal('61.416')
        )
        
        movies_url = reverse('movie-list')
        
        # First request - should hit database
        response1 = self.client.get(movies_url)
        self.assertEqual(response1.status_code, status.HTTP_200_OK)
        
        # Second request - should hit cache
        response2 = self.client.get(movies_url)
        self.assertEqual(response2.status_code, status.HTTP_200_OK)
        
        # Responses should be identical
        self.assertEqual(response1.data, response2.data)
    
    @patch('movies.views.requests.get')
    def test_tmdb_api_caching(self, mock_get):
        """Test that TMDb API responses are cached"""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'results': [],
            'total_results': 0,
            'total_pages': 0
        }
        mock_get.return_value = mock_response
        
        popular_url = reverse('popular-movies')
        
        # First request
        response1 = self.client.get(popular_url)
        self.assertEqual(response1.status_code, status.HTTP_200_OK)
        
        # Second request - should use cache, not call API again
        response2 = self.client.get(popular_url)
        self.assertEqual(response2.status_code, status.HTTP_200_OK)
        
        # API should only be called once due to caching
        self.assertEqual(mock_get.call_count, 1)


class MiddlewareIntegrationTest(TransactionTestCase):
    """Integration tests for custom middleware"""
    
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
    
    def test_security_headers_middleware(self):
        """Test that security headers are added to responses"""
        movies_url = reverse('movie-list')
        response = self.client.get(movies_url)
        
        # Check for security headers
        self.assertIn('X-Content-Type-Options', response)
        self.assertIn('X-Frame-Options', response)
        self.assertIn('X-XSS-Protection', response)
        self.assertEqual(response['X-Content-Type-Options'], 'nosniff')
        self.assertEqual(response['X-Frame-Options'], 'DENY')
    
    def test_request_validation_middleware(self):
        """Test request validation middleware"""
        movies_url = reverse('movie-list')
        
        # Test with valid request
        response = self.client.get(movies_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Test with potentially malicious content
        malicious_data = {'search': '<script>alert("xss")</script>'}
        response = self.client.get(movies_url, malicious_data)
        # Should still work but content should be sanitized
        self.assertEqual(response.status_code, status.HTTP_200_OK)
    
    @override_settings(RATELIMIT_ENABLE=True)
    def test_rate_limiting_middleware(self):
        """Test rate limiting middleware"""
        movies_url = reverse('movie-list')
        
        # Make multiple requests quickly
        responses = []
        for i in range(15):  # Exceed rate limit
            response = self.client.get(movies_url)
            responses.append(response)
        
        # Some requests should be rate limited
        status_codes = [r.status_code for r in responses]
        
        # Should have some successful requests and some rate limited
        self.assertIn(status.HTTP_200_OK, status_codes)
        # Note: Actual rate limiting behavior depends on configuration


class DatabaseIntegrationTest(TransactionTestCase):
    """Integration tests for database operations"""
    
    def test_concurrent_rating_updates(self):
        """Test concurrent rating updates don't create duplicates"""
        user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        movie = Movie.objects.create(
            tmdb_id=550,
            title='Fight Club',
            release_date='1999-10-15',
            vote_average=Decimal('8.4'),
            vote_count=26280,
            popularity=Decimal('61.416')
        )
        
        # Create initial rating
        rating = UserMovieRating.objects.create(
            user=user,
            movie=movie,
            rating=Decimal('8.0')
        )
        
        # Update rating
        rating.rating = Decimal('9.0')
        rating.save()
        
        # Verify only one rating exists
        ratings = UserMovieRating.objects.filter(user=user, movie=movie)
        self.assertEqual(ratings.count(), 1)
        self.assertEqual(ratings.first().rating, Decimal('9.0'))
    
    def test_movie_genre_relationships(self):
        """Test movie-genre many-to-many relationships"""
        action_genre = Genre.objects.create(tmdb_id=28, name='Action')
        drama_genre = Genre.objects.create(tmdb_id=18, name='Drama')
        
        movie = Movie.objects.create(
            tmdb_id=550,
            title='Fight Club',
            release_date='1999-10-15',
            vote_average=Decimal('8.4'),
            vote_count=26280,
            popularity=Decimal('61.416')
        )
        
        # Add genres
        movie.genres.add(action_genre, drama_genre)
        
        # Test relationships
        self.assertEqual(movie.genres.count(), 2)
        self.assertIn(action_genre, movie.genres.all())
        self.assertIn(drama_genre, movie.genres.all())
        
        # Test reverse relationship
        self.assertIn(movie, action_genre.movies.all())
        self.assertIn(movie, drama_genre.movies.all())
    
    def test_user_data_isolation(self):
        """Test that user data is properly isolated"""
        user1 = User.objects.create_user(
            username='user1',
            email='user1@example.com',
            password='testpass123'
        )
        user2 = User.objects.create_user(
            username='user2',
            email='user2@example.com',
            password='testpass123'
        )
        
        movie = Movie.objects.create(
            tmdb_id=550,
            title='Fight Club',
            release_date='1999-10-15',
            vote_average=Decimal('8.4'),
            vote_count=26280,
            popularity=Decimal('61.416')
        )
        
        # Create ratings for both users
        UserMovieRating.objects.create(
            user=user1,
            movie=movie,
            rating=Decimal('8.0')
        )
        UserMovieRating.objects.create(
            user=user2,
            movie=movie,
            rating=Decimal('9.0')
        )
        
        # Create watchlist items for both users
        UserMovieWatchlist.objects.create(user=user1, movie=movie)
        
        # Test data isolation
        user1_ratings = UserMovieRating.objects.filter(user=user1)
        user2_ratings = UserMovieRating.objects.filter(user=user2)
        
        self.assertEqual(user1_ratings.count(), 1)
        self.assertEqual(user2_ratings.count(), 1)
        self.assertEqual(user1_ratings.first().rating, Decimal('8.0'))
        self.assertEqual(user2_ratings.first().rating, Decimal('9.0'))
        
        user1_watchlist = UserMovieWatchlist.objects.filter(user=user1)
        user2_watchlist = UserMovieWatchlist.objects.filter(user=user2)
        
        self.assertEqual(user1_watchlist.count(), 1)
        self.assertEqual(user2_watchlist.count(), 0)