from django.test import TestCase
from django.core.exceptions import ValidationError
from decimal import Decimal

from movies.validators import (
    MovieValidators,
    UserValidators,
    APIValidators,
    validate_rating,
    validate_year,
    validate_tmdb_id
)


class MovieValidatorsTest(TestCase):
    """Test cases for MovieValidators"""
    
    def test_validate_rating_valid(self):
        """Test validating valid ratings"""
        valid_ratings = [0.0, 5.0, 10.0, 7.5, 8.25]
        
        for rating in valid_ratings:
            with self.subTest(rating=rating):
                # Should not raise exception
                MovieValidators.validate_rating(Decimal(str(rating)))
    
    def test_validate_rating_invalid_high(self):
        """Test validating ratings that are too high"""
        invalid_ratings = [10.1, 15.0, 100.0]
        
        for rating in invalid_ratings:
            with self.subTest(rating=rating):
                with self.assertRaises(ValidationError):
                    MovieValidators.validate_rating(Decimal(str(rating)))
    
    def test_validate_rating_invalid_low(self):
        """Test validating ratings that are too low"""
        invalid_ratings = [-0.1, -1.0, -10.0]
        
        for rating in invalid_ratings:
            with self.subTest(rating=rating):
                with self.assertRaises(ValidationError):
                    MovieValidators.validate_rating(Decimal(str(rating)))
    
    def test_validate_year_valid(self):
        """Test validating valid years"""
        valid_years = [1900, 1950, 2000, 2023, 2030]
        
        for year in valid_years:
            with self.subTest(year=year):
                # Should not raise exception
                MovieValidators.validate_year(year)
    
    def test_validate_year_invalid_early(self):
        """Test validating years that are too early"""
        invalid_years = [1800, 1850, 1899]
        
        for year in invalid_years:
            with self.subTest(year=year):
                with self.assertRaises(ValidationError):
                    MovieValidators.validate_year(year)
    
    def test_validate_year_invalid_late(self):
        """Test validating years that are too late"""
        invalid_years = [2051, 2100, 3000]
        
        for year in invalid_years:
            with self.subTest(year=year):
                with self.assertRaises(ValidationError):
                    MovieValidators.validate_year(year)
    
    def test_validate_tmdb_id_valid(self):
        """Test validating valid TMDb IDs"""
        valid_ids = [1, 100, 550, 12345, 999999]
        
        for tmdb_id in valid_ids:
            with self.subTest(tmdb_id=tmdb_id):
                # Should not raise exception
                MovieValidators.validate_tmdb_id(tmdb_id)
    
    def test_validate_tmdb_id_invalid(self):
        """Test validating invalid TMDb IDs"""
        invalid_ids = [0, -1, -100]
        
        for tmdb_id in invalid_ids:
            with self.subTest(tmdb_id=tmdb_id):
                with self.assertRaises(ValidationError):
                    MovieValidators.validate_tmdb_id(tmdb_id)
    
    def test_validate_vote_count_valid(self):
        """Test validating valid vote counts"""
        valid_counts = [0, 1, 100, 1000, 50000]
        
        for count in valid_counts:
            with self.subTest(count=count):
                # Should not raise exception
                MovieValidators.validate_vote_count(count)
    
    def test_validate_vote_count_invalid(self):
        """Test validating invalid vote counts"""
        invalid_counts = [-1, -10, -100]
        
        for count in invalid_counts:
            with self.subTest(count=count):
                with self.assertRaises(ValidationError):
                    MovieValidators.validate_vote_count(count)
    
    def test_validate_popularity_valid(self):
        """Test validating valid popularity scores"""
        valid_scores = [0.0, 1.5, 50.0, 100.0, 999.99]
        
        for score in valid_scores:
            with self.subTest(score=score):
                # Should not raise exception
                MovieValidators.validate_popularity(Decimal(str(score)))
    
    def test_validate_popularity_invalid(self):
        """Test validating invalid popularity scores"""
        invalid_scores = [-0.1, -1.0, -10.0]
        
        for score in invalid_scores:
            with self.subTest(score=score):
                with self.assertRaises(ValidationError):
                    MovieValidators.validate_popularity(Decimal(str(score)))


class UserValidatorsTest(TestCase):
    """Test cases for UserValidators"""
    
    def test_validate_username_valid(self):
        """Test validating valid usernames"""
        valid_usernames = [
            'user123',
            'test_user',
            'john.doe',
            'a' * 30,  # Max length
            'user-name'
        ]
        
        for username in valid_usernames:
            with self.subTest(username=username):
                # Should not raise exception
                UserValidators.validate_username(username)
    
    def test_validate_username_invalid_length(self):
        """Test validating usernames with invalid length"""
        invalid_usernames = [
            'ab',  # Too short
            'a' * 151,  # Too long
            ''  # Empty
        ]
        
        for username in invalid_usernames:
            with self.subTest(username=username):
                with self.assertRaises(ValidationError):
                    UserValidators.validate_username(username)
    
    def test_validate_username_invalid_characters(self):
        """Test validating usernames with invalid characters"""
        invalid_usernames = [
            'user@name',
            'user name',  # Space
            'user#name',
            'user$name'
        ]
        
        for username in invalid_usernames:
            with self.subTest(username=username):
                with self.assertRaises(ValidationError):
                    UserValidators.validate_username(username)
    
    def test_validate_email_valid(self):
        """Test validating valid email addresses"""
        valid_emails = [
            'test@example.com',
            'user.name@domain.co.uk',
            'user+tag@example.org',
            'firstname.lastname@company.com'
        ]
        
        for email in valid_emails:
            with self.subTest(email=email):
                # Should not raise exception
                UserValidators.validate_email(email)
    
    def test_validate_email_invalid(self):
        """Test validating invalid email addresses"""
        invalid_emails = [
            'invalid-email',
            '@example.com',
            'user@',
            'user..name@example.com',
            'user@.com',
            ''
        ]
        
        for email in invalid_emails:
            with self.subTest(email=email):
                with self.assertRaises(ValidationError):
                    UserValidators.validate_email(email)


class APIValidatorsTest(TestCase):
    """Test cases for APIValidators"""
    
    def test_validate_page_number_valid(self):
        """Test validating valid page numbers"""
        valid_pages = [1, 5, 10, 100, 1000, '1', '5', '10']
        
        for page in valid_pages:
            with self.subTest(page=page):
                result = APIValidators.validate_page_number(page)
                self.assertIsInstance(result, int)
                self.assertGreaterEqual(result, 1)
    
    def test_validate_page_number_invalid(self):
        """Test validating invalid page numbers"""
        invalid_pages = [0, -1, -10, '0', '-1', 'invalid', '', None]
        
        for page in invalid_pages:
            with self.subTest(page=page):
                with self.assertRaises(ValidationError):
                    APIValidators.validate_page_number(page)
    
    def test_validate_search_query_valid(self):
        """Test validating valid search queries"""
        valid_queries = [
            'Fight Club',
            'action movie',
            'The Matrix',
            'a' * 100,  # Long but valid
            'movie 2023'
        ]
        
        for query in valid_queries:
            with self.subTest(query=query):
                # Should not raise exception
                APIValidators.validate_search_query(query)
    
    def test_validate_search_query_invalid(self):
        """Test validating invalid search queries"""
        invalid_queries = [
            '',  # Empty
            '  ',  # Only whitespace
            'ab',  # Too short
            'a' * 201  # Too long
        ]
        
        for query in invalid_queries:
            with self.subTest(query=query):
                with self.assertRaises(ValidationError):
                    APIValidators.validate_search_query(query)
    
    def test_validate_movie_id_valid(self):
        """Test validating valid movie IDs"""
        valid_ids = [1, 100, 550, 12345, '1', '100', '550']
        
        for movie_id in valid_ids:
            with self.subTest(movie_id=movie_id):
                result = APIValidators.validate_movie_id(movie_id)
                self.assertIsInstance(result, int)
                self.assertGreater(result, 0)
    
    def test_validate_movie_id_invalid(self):
        """Test validating invalid movie IDs"""
        invalid_ids = [0, -1, 'invalid', '', None, '0', '-1']
        
        for movie_id in invalid_ids:
            with self.subTest(movie_id=movie_id):
                with self.assertRaises(ValidationError):
                    APIValidators.validate_movie_id(movie_id)


class StandaloneValidatorTest(TestCase):
    """Test cases for standalone validator functions"""
    
    def test_validate_rating_function(self):
        """Test standalone validate_rating function"""
        # Valid ratings
        valid_ratings = [Decimal('0.0'), Decimal('5.0'), Decimal('10.0')]
        for rating in valid_ratings:
            with self.subTest(rating=rating):
                # Should not raise exception
                validate_rating(rating)
        
        # Invalid ratings
        invalid_ratings = [Decimal('-1.0'), Decimal('11.0')]
        for rating in invalid_ratings:
            with self.subTest(rating=rating):
                with self.assertRaises(ValidationError):
                    validate_rating(rating)
    
    def test_validate_year_function(self):
        """Test standalone validate_year function"""
        # Valid years
        valid_years = [1900, 2000, 2023, 2050]
        for year in valid_years:
            with self.subTest(year=year):
                # Should not raise exception
                validate_year(year)
        
        # Invalid years
        invalid_years = [1800, 2051]
        for year in invalid_years:
            with self.subTest(year=year):
                with self.assertRaises(ValidationError):
                    validate_year(year)
    
    def test_validate_tmdb_id_function(self):
        """Test standalone validate_tmdb_id function"""
        # Valid IDs
        valid_ids = [1, 100, 550, 12345]
        for tmdb_id in valid_ids:
            with self.subTest(tmdb_id=tmdb_id):
                # Should not raise exception
                validate_tmdb_id(tmdb_id)
        
        # Invalid IDs
        invalid_ids = [0, -1, -100]
        for tmdb_id in invalid_ids:
            with self.subTest(tmdb_id=tmdb_id):
                with self.assertRaises(ValidationError):
                    validate_tmdb_id(tmdb_id)


class ValidatorEdgeCasesTest(TestCase):
    """Test cases for validator edge cases"""
    
    def test_rating_precision(self):
        """Test rating validation with different decimal precisions"""
        # Test various decimal precisions
        ratings = [
            Decimal('8.1'),
            Decimal('8.12'),
            Decimal('8.123'),
            Decimal('8.1234')
        ]
        
        for rating in ratings:
            with self.subTest(rating=rating):
                # Should not raise exception
                MovieValidators.validate_rating(rating)
    
    def test_boundary_values(self):
        """Test validation at boundary values"""
        # Test exact boundary values
        boundary_tests = [
            (MovieValidators.validate_rating, Decimal('0.0')),
            (MovieValidators.validate_rating, Decimal('10.0')),
            (MovieValidators.validate_year, 1900),
            (MovieValidators.validate_year, 2050),
            (MovieValidators.validate_tmdb_id, 1),
            (MovieValidators.validate_vote_count, 0),
            (MovieValidators.validate_popularity, Decimal('0.0'))
        ]
        
        for validator, value in boundary_tests:
            with self.subTest(validator=validator.__name__, value=value):
                # Should not raise exception
                validator(value)
    
    def test_type_conversion(self):
        """Test validators with different input types"""
        # Test that validators handle type conversion appropriately
        test_cases = [
            (APIValidators.validate_page_number, '5', int),
            (APIValidators.validate_movie_id, '550', int)
        ]
        
        for validator, input_value, expected_type in test_cases:
            with self.subTest(validator=validator.__name__, input_value=input_value):
                result = validator(input_value)
                self.assertIsInstance(result, expected_type)
    
    def test_whitespace_handling(self):
        """Test how validators handle whitespace"""
        # Test search query with leading/trailing whitespace
        query_with_whitespace = '  Fight Club  '
        # Should handle whitespace appropriately
        APIValidators.validate_search_query(query_with_whitespace.strip())
        
        # Test username with whitespace (should be invalid)
        username_with_space = 'user name'
        with self.assertRaises(ValidationError):
            UserValidators.validate_username(username_with_space)