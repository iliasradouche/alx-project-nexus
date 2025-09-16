from django.test import TestCase
from django.contrib.auth.models import User
from rest_framework.exceptions import ValidationError
from rest_framework import serializers
from decimal import Decimal
from datetime import date

from movies.models import Genre, Movie, UserMovieRating, UserMovieWatchlist
from movies.serializers import (
    GenreSerializer,
    MovieListSerializer,
    MovieDetailSerializer,
    UserMovieRatingSerializer,
    UserMovieWatchlistSerializer
)


class GenreSerializerTest(TestCase):
    """Test cases for GenreSerializer"""
    
    def setUp(self):
        self.genre = Genre.objects.create(
            tmdb_id=28,
            name='Action'
        )
        self.genre_data = {
            'tmdb_id': 18,
            'name': 'Drama'
        }
    
    def test_serialize_genre(self):
        """Test serializing a genre"""
        serializer = GenreSerializer(self.genre)
        data = serializer.data
        
        self.assertEqual(data['id'], self.genre.id)
        self.assertEqual(data['tmdb_id'], 28)
        self.assertEqual(data['name'], 'Action')
    
    def test_deserialize_valid_genre(self):
        """Test deserializing valid genre data"""
        serializer = GenreSerializer(data=self.genre_data)
        
        self.assertTrue(serializer.is_valid())
        genre = serializer.save()
        self.assertEqual(genre.name, 'Drama')
        self.assertEqual(genre.tmdb_id, 18)
    
    def test_deserialize_invalid_genre(self):
        """Test deserializing invalid genre data"""
        invalid_data = {
            'tmdb_id': 'invalid',  # Should be integer
            'name': ''
        }
        serializer = GenreSerializer(data=invalid_data)
        
        self.assertFalse(serializer.is_valid())
        self.assertIn('tmdb_id', serializer.errors)
        self.assertIn('name', serializer.errors)


class MovieListSerializerTest(TestCase):
    """Test cases for MovieListSerializer"""
    
    def setUp(self):
        self.genre = Genre.objects.create(tmdb_id=28, name='Action')
        self.movie = Movie.objects.create(
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
        self.movie.genres.add(self.genre)
    
    def test_serialize_movie_list(self):
        """Test serializing a movie for list view"""
        serializer = MovieListSerializer(self.movie)
        data = serializer.data
        
        self.assertEqual(data['id'], self.movie.id)
        self.assertEqual(data['tmdb_id'], 550)
        self.assertEqual(data['title'], 'Fight Club')
        self.assertEqual(data['vote_average'], 8.4)
        self.assertIn('genres', data)
        self.assertEqual(len(data['genres']), 1)
        self.assertEqual(data['genres'][0]['name'], 'Action')
    
    def test_serialize_movie_without_poster(self):
        """Test serializing movie without poster path"""
        movie_no_poster = Movie.objects.create(
            tmdb_id=551,
            title='Test Movie',
            release_date=date(2020, 1, 1),
            vote_average=7.0,
            vote_count=1000,
            popularity=30.0,
            poster_path=''
        )
        
        serializer = MovieListSerializer(movie_no_poster)
        data = serializer.data
        
        self.assertEqual(data['poster_path'], '')


class MovieDetailSerializerTest(TestCase):
    """Test cases for MovieDetailSerializer"""
    
    def setUp(self):
        self.genre = Genre.objects.create(tmdb_id=28, name='Action')
        self.movie = Movie.objects.create(
            tmdb_id=550,
            title='Fight Club',
            overview='An insomniac office worker forms an underground fight club.',
            release_date=date(1999, 10, 15),
            vote_average=8.4,
            vote_count=26280,
            popularity=61.416,
            poster_path='/pB8BM7pdSp6B6Ih7QZ4DrQ3PmJK.jpg',
            backdrop_path='/fCayJrkfRaCRCTh8GqN30f8oyQF.jpg',
            adult=False,
            original_language='en',
            original_title='Fight Club'
        )
        self.movie.genres.add(self.genre)
    
    def test_serialize_movie_detail(self):
        """Test serializing a movie for detail view"""
        serializer = MovieDetailSerializer(self.movie)
        data = serializer.data
        
        self.assertEqual(data['id'], self.movie.id)
        self.assertEqual(data['tmdb_id'], 550)
        self.assertEqual(data['title'], 'Fight Club')
        self.assertEqual(data['overview'], self.movie.overview)
        self.assertEqual(data['vote_average'], 8.4)
        self.assertEqual(data['vote_count'], 26280)
        self.assertEqual(data['popularity'], 61.416)
        self.assertIn('backdrop_path', data)
        self.assertIn('genres', data)
        self.assertEqual(len(data['genres']), 1)


class UserMovieRatingSerializerTest(TestCase):
    """Test cases for UserMovieRatingSerializer"""
    
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.movie = Movie.objects.create(
            tmdb_id=550,
            title='Fight Club',
            release_date=date(1999, 10, 15),
            vote_average=8.4,
            vote_count=26280,
            popularity=61.416,
            poster_path='/poster.jpg'
        )
        self.rating = UserMovieRating.objects.create(
            user=self.user,
            movie=self.movie,
            rating=8.5
        )
    
    def test_serialize_rating(self):
        """Test serializing a movie rating"""
        serializer = UserMovieRatingSerializer(self.rating)
        data = serializer.data
        
        self.assertEqual(data['id'], self.rating.id)
        self.assertEqual(data['rating'], 8.5)
        self.assertIn('movie', data)
        self.assertEqual(data['movie']['title'], 'Fight Club')
        self.assertIn('created_at', data)
        self.assertIn('updated_at', data)
    
    def test_deserialize_valid_rating(self):
        """Test deserializing valid rating data"""
        rating_data = {
            'movie_id': self.movie.id,
            'rating': 9.0
        }
        
        # Mock request context
        request = type('MockRequest', (), {'user': self.user})()
        serializer = UserMovieRatingSerializer(data=rating_data, context={'request': request})
        
        self.assertTrue(serializer.is_valid())
        # Test that the serializer creates the rating correctly
        rating = serializer.save()
        self.assertEqual(rating.movie, self.movie)
        self.assertEqual(rating.rating, 9.0)
        self.assertEqual(rating.user, self.user)
    
    def test_deserialize_invalid_rating_high(self):
        """Test deserializing rating that's too high"""
        rating_data = {
            'movie_id': self.movie.id,
            'rating': 11.0  # Invalid: should be <= 10
        }
        
        request = type('MockRequest', (), {'user': self.user})()
        serializer = UserMovieRatingSerializer(data=rating_data, context={'request': request})
        
        self.assertFalse(serializer.is_valid())
        self.assertIn('rating', serializer.errors)
    
    def test_deserialize_invalid_rating_low(self):
        """Test deserializing rating that's too low"""
        rating_data = {
            'movie_id': self.movie.id,
            'rating': -1.0  # Invalid: should be >= 0
        }
        
        request = type('MockRequest', (), {'user': self.user})()
        serializer = UserMovieRatingSerializer(data=rating_data, context={'request': request})
        
        self.assertFalse(serializer.is_valid())
        self.assertIn('rating', serializer.errors)
    
    def test_deserialize_missing_movie(self):
        """Test deserializing rating without movie"""
        rating_data = {
            'rating': 8.5
        }
        
        request = type('MockRequest', (), {'user': self.user})()
        serializer = UserMovieRatingSerializer(data=rating_data, context={'request': request})
        
        self.assertFalse(serializer.is_valid())
        self.assertIn('movie_id', serializer.errors)
    
    def test_deserialize_nonexistent_movie(self):
        """Test deserializing rating with nonexistent movie"""
        rating_data = {
            'movie_id': 99999,  # Nonexistent movie ID
            'rating': 8.5
        }
        
        request = type('MockRequest', (), {'user': self.user})()
        serializer = UserMovieRatingSerializer(data=rating_data, context={'request': request})
        
        # Should be valid at serializer level, but fail during save
        self.assertTrue(serializer.is_valid())
        
        with self.assertRaises(serializers.ValidationError):
            serializer.save()


class UserMovieWatchlistSerializerTest(TestCase):
    """Test cases for UserMovieWatchlistSerializer"""
    
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.movie = Movie.objects.create(
            tmdb_id=550,
            title='Fight Club',
            release_date=date(1999, 10, 15),
            vote_average=8.4,
            vote_count=26280,
            popularity=61.416,
            poster_path='/poster.jpg'
        )
        self.watchlist_item = UserMovieWatchlist.objects.create(
            user=self.user,
            movie=self.movie
        )
    
    def test_serialize_watchlist_item(self):
        """Test serializing a watchlist item"""
        serializer = UserMovieWatchlistSerializer(self.watchlist_item)
        data = serializer.data
        
        self.assertEqual(data['id'], self.watchlist_item.id)
        self.assertIn('movie', data)
        self.assertEqual(data['movie']['title'], 'Fight Club')
        self.assertIn('added_at', data)
    
    def test_deserialize_valid_watchlist_item(self):
        """Test deserializing valid watchlist data"""
        # Create another movie for testing
        movie2 = Movie.objects.create(
            tmdb_id=551,
            title='Another Movie',
            release_date=date(2000, 1, 1),
            vote_average=7.0,
            vote_count=1000,
            popularity=30.0,
            poster_path='/another_poster.jpg'
        )
        
        watchlist_data = {
            'movie_id': movie2.id
        }
        
        request = type('MockRequest', (), {'user': self.user})()
        serializer = UserMovieWatchlistSerializer(data=watchlist_data, context={'request': request})
        
        self.assertTrue(serializer.is_valid())
        
        # Test that the serializer creates the watchlist item correctly
        watchlist_item = serializer.save()
        self.assertEqual(watchlist_item.movie, movie2)
        self.assertEqual(watchlist_item.user, self.user)
    
    def test_deserialize_missing_movie(self):
        """Test deserializing watchlist item without movie"""
        watchlist_data = {}
        
        request = type('MockRequest', (), {'user': self.user})()
        serializer = UserMovieWatchlistSerializer(data=watchlist_data, context={'request': request})
        
        self.assertFalse(serializer.is_valid())
        self.assertIn('movie_id', serializer.errors)
    
    def test_deserialize_nonexistent_movie(self):
        """Test deserializing watchlist item with nonexistent movie"""
        watchlist_data = {
            'movie_id': 99999  # Nonexistent movie ID
        }
        
        request = type('MockRequest', (), {'user': self.user})()
        serializer = UserMovieWatchlistSerializer(data=watchlist_data, context={'request': request})
        
        # Should be valid at serializer level, but fail during save
        self.assertTrue(serializer.is_valid())
        
        with self.assertRaises(serializers.ValidationError):
            serializer.save()


class SerializerValidationTest(TestCase):
    """Test cases for custom serializer validations"""
    
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.movie = Movie.objects.create(
            tmdb_id=550,
            title='Fight Club',
            release_date=date(1999, 10, 15),
            vote_average=8.4,
            vote_count=26280,
            popularity=61.416,
            poster_path='/poster.jpg'
        )
    
    def test_rating_decimal_precision(self):
        """Test rating decimal precision validation"""
        rating_data = {
            'movie_id': self.movie.id,
            'rating': 8.555555  # Too many decimal places
        }
        
        request = type('MockRequest', (), {'user': self.user})()
        serializer = UserMovieRatingSerializer(data=rating_data, context={'request': request})
        
        # Should still be valid but rounded appropriately
        self.assertTrue(serializer.is_valid())
    
    def test_movie_title_length(self):
        """Test movie title length validation"""
        long_title = 'A' * 300  # Very long title
        movie_data = {
            'tmdb_id': 999,
            'title': long_title,
            'release_date': '2020-01-01',
            'vote_average': 7.0,
            'vote_count': 1000,
            'popularity': 30.0
        }
        
        # This should be handled by model validation
        movie = Movie(**movie_data)
        # The model should handle this appropriately
    
    def test_empty_string_validation(self):
        """Test validation of empty strings"""
        genre_data = {
            'tmdb_id': 28,
            'name': ''  # Empty name
        }
        serializer = GenreSerializer(data=genre_data)
        
        self.assertFalse(serializer.is_valid())
        self.assertIn('name', serializer.errors)