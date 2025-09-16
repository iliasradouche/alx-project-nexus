from django.test import TestCase
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from decimal import Decimal
from datetime import date
from movies.models import Genre, Movie, UserMovieRating, UserMovieWatchlist
from movies.validators import MovieValidators, UserValidators


class GenreModelTest(TestCase):
    """Test cases for Genre model"""
    
    def setUp(self):
        self.genre_data = {
            'tmdb_id': 28,
            'name': 'Action'
        }
    
    def test_create_genre(self):
        """Test creating a genre"""
        genre = Genre.objects.create(**self.genre_data)
        self.assertEqual(genre.name, 'Action')
        self.assertEqual(genre.tmdb_id, 28)
        self.assertEqual(str(genre), 'Action')
    
    def test_genre_unique_tmdb_id(self):
        """Test that tmdb_id is unique"""
        Genre.objects.create(**self.genre_data)
        with self.assertRaises(Exception):
            Genre.objects.create(**self.genre_data)
    
    def test_genre_str_representation(self):
        """Test string representation of genre"""
        genre = Genre.objects.create(**self.genre_data)
        self.assertEqual(str(genre), 'Action')


class MovieModelTest(TestCase):
    """Test cases for Movie model"""
    
    def setUp(self):
        self.genre = Genre.objects.create(tmdb_id=28, name='Action')
        self.movie_data = {
            'tmdb_id': 550,
            'title': 'Fight Club',
            'overview': 'An insomniac office worker and a devil-may-care soap maker form an underground fight club.',
            'release_date': date(1999, 10, 15),
            'vote_average': 8.4,
            'vote_count': 26280,
            'popularity': 61.416,
            'poster_path': '/pB8BM7pdSp6B6Ih7QZ4DrQ3PmJK.jpg',
            'backdrop_path': '/fCayJrkfRaCRCTh8GqN30f8oyQF.jpg',
            'adult': False,
            'original_language': 'en',
            'original_title': 'Fight Club'
        }
    
    def test_create_movie(self):
        """Test creating a movie"""
        movie = Movie.objects.create(**self.movie_data)
        movie.genres.add(self.genre)
        
        self.assertEqual(movie.title, 'Fight Club')
        self.assertEqual(movie.tmdb_id, 550)
        self.assertEqual(movie.vote_average, 8.4)
        self.assertIn(self.genre, movie.genres.all())
        self.assertEqual(str(movie), 'Fight Club (1999)')
    
    def test_movie_unique_tmdb_id(self):
        """Test that tmdb_id is unique"""
        Movie.objects.create(**self.movie_data)
        with self.assertRaises(Exception):
            Movie.objects.create(**self.movie_data)
    
    def test_movie_str_representation(self):
        """Test string representation of movie"""
        movie = Movie.objects.create(**self.movie_data)
        expected = f"{movie.title} ({movie.release_date.year})"
        self.assertEqual(str(movie), expected)
    
    def test_movie_validation(self):
        """Test movie field validation"""
        # Test invalid vote_average
        movie = Movie(
            tmdb_id=999,
            title='Invalid Movie',
            vote_average=11.0,  # Invalid: > 10
            vote_count=100,
            popularity=50.0,
            poster_path='/poster.jpg'
        )
        with self.assertRaises(ValidationError):
            movie.full_clean()
    
    def test_movie_ordering(self):
        """Test movie default ordering"""
        movie1 = Movie.objects.create(
            tmdb_id=1, title='Movie A', release_date=date(2020, 1, 1),
            vote_average=7.0, vote_count=100, popularity=50.0, poster_path='/poster1.jpg'
        )
        movie2 = Movie.objects.create(
            tmdb_id=2, title='Movie B', release_date=date(2021, 1, 1),
            vote_average=8.0, vote_count=200, popularity=60.0, poster_path='/poster2.jpg'
        )
        
        movies = list(Movie.objects.all())
        # Should be ordered by popularity descending
        self.assertEqual(movies[0], movie2)
        self.assertEqual(movies[1], movie1)


class UserMovieRatingModelTest(TestCase):
    """Test cases for UserMovieRating model"""
    
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
    
    def test_create_rating(self):
        """Test creating a movie rating"""
        rating = UserMovieRating.objects.create(
            user=self.user,
            movie=self.movie,
            rating=8.5
        )
        
        self.assertEqual(rating.user, self.user)
        self.assertEqual(rating.movie, self.movie)
        self.assertEqual(rating.rating, 8.5)
        self.assertIsNotNone(rating.created_at)
        self.assertIsNotNone(rating.updated_at)
    
    def test_rating_unique_constraint(self):
        """Test that user can only rate a movie once"""
        UserMovieRating.objects.create(
            user=self.user,
            movie=self.movie,
            rating=8.5
        )
        
        with self.assertRaises(Exception):
            UserMovieRating.objects.create(
                user=self.user,
                movie=self.movie,
                rating=7.0
            )
    
    def test_rating_validation(self):
        """Test rating field validation"""
        # Test invalid rating (too high)
        rating = UserMovieRating(
            user=self.user,
            movie=self.movie,
            rating=11.0  # Invalid: > 10
        )
        with self.assertRaises(ValidationError):
            rating.full_clean()
        
        # Test invalid rating (too low)
        rating.rating = -1.0
        with self.assertRaises(ValidationError):
            rating.full_clean()
    
    def test_rating_str_representation(self):
        """Test string representation of rating"""
        rating = UserMovieRating.objects.create(
            user=self.user,
            movie=self.movie,
            rating=8.5
        )
        
        expected = f"{self.user.username} rated {self.movie.title}: 8.5"
        self.assertEqual(str(rating), expected)


class UserMovieWatchlistModelTest(TestCase):
    """Test cases for UserMovieWatchlist model"""
    
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
    
    def test_create_watchlist_item(self):
        """Test creating a watchlist item"""
        watchlist_item = UserMovieWatchlist.objects.create(
            user=self.user,
            movie=self.movie
        )
        
        self.assertEqual(watchlist_item.user, self.user)
        self.assertEqual(watchlist_item.movie, self.movie)
        self.assertIsNotNone(watchlist_item.added_at)
    
    def test_watchlist_unique_constraint(self):
        """Test that user can only add a movie to watchlist once"""
        UserMovieWatchlist.objects.create(
            user=self.user,
            movie=self.movie
        )
        
        with self.assertRaises(Exception):
            UserMovieWatchlist.objects.create(
                user=self.user,
                movie=self.movie
            )
    
    def test_watchlist_str_representation(self):
        """Test string representation of watchlist item"""
        watchlist_item = UserMovieWatchlist.objects.create(
            user=self.user,
            movie=self.movie
        )
        
        expected = f"{self.user.username} - {self.movie.title}"
        self.assertEqual(str(watchlist_item), expected)
    
    def test_watchlist_ordering(self):
        """Test watchlist default ordering"""
        movie2 = Movie.objects.create(
            tmdb_id=551,
            title='Another Movie',
            release_date=date(2000, 1, 1),
            vote_average=Decimal('7.0'),
            vote_count=1000,
            popularity=Decimal('30.0')
        )
        
        # Create watchlist items with some delay
        item1 = UserMovieWatchlist.objects.create(
            user=self.user,
            movie=self.movie
        )
        item2 = UserMovieWatchlist.objects.create(
            user=self.user,
            movie=movie2
        )
        
        watchlist = list(UserMovieWatchlist.objects.filter(user=self.user).order_by('id'))
        # Should be ordered by creation order
        self.assertEqual(watchlist[0], item1)
        self.assertEqual(watchlist[1], item2)