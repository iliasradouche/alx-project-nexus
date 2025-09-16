from django.core.exceptions import ValidationError
from django.core.validators import RegexValidator
from rest_framework import serializers
import re
from datetime import datetime, date


class MovieValidators:
    """
    Collection of validators for movie-related data
    """
    
    @staticmethod
    def validate_rating(value):
        """
        Validate movie rating (1-10)
        """
        if not isinstance(value, (int, float)):
            raise ValidationError("Rating must be a number")
        
        if value < 1 or value > 10:
            raise ValidationError("Rating must be between 1 and 10")
        
        return value
    
    @staticmethod
    def validate_year(value):
        """
        Validate movie release year
        """
        if not isinstance(value, int):
            raise ValidationError("Year must be an integer")
        
        current_year = datetime.now().year
        if value < 1888 or value > current_year + 5:  # First movie was made in 1888
            raise ValidationError(f"Year must be between 1888 and {current_year + 5}")
        
        return value
    
    @staticmethod
    def validate_tmdb_id(value):
        """
        Validate TMDb ID format
        """
        if not isinstance(value, int) or value <= 0:
            raise ValidationError("TMDb ID must be a positive integer")
        
        return value
    
    @staticmethod
    def validate_genre_name(value):
        """
        Validate genre name
        """
        if not isinstance(value, str):
            raise ValidationError("Genre name must be a string")
        
        if len(value.strip()) < 2:
            raise ValidationError("Genre name must be at least 2 characters long")
        
        if len(value) > 50:
            raise ValidationError("Genre name cannot exceed 50 characters")
        
        # Only allow letters, spaces, hyphens, and apostrophes
        if not re.match(r"^[a-zA-Z\s\-']+$", value):
            raise ValidationError("Genre name can only contain letters, spaces, hyphens, and apostrophes")
        
        return value.strip().title()
    
    @staticmethod
    def validate_movie_title(value):
        """
        Validate movie title
        """
        if not isinstance(value, str):
            raise ValidationError("Movie title must be a string")
        
        if len(value.strip()) < 1:
            raise ValidationError("Movie title cannot be empty")
        
        if len(value) > 200:
            raise ValidationError("Movie title cannot exceed 200 characters")
        
        return value.strip()
    
    @staticmethod
    def validate_overview(value):
        """
        Validate movie overview/description
        """
        if value is None:
            return value
        
        if not isinstance(value, str):
            raise ValidationError("Overview must be a string")
        
        if len(value) > 2000:
            raise ValidationError("Overview cannot exceed 2000 characters")
        
        return value.strip()
    
    @staticmethod
    def validate_poster_path(value):
        """
        Validate poster path format
        """
        if value is None:
            return value
        
        if not isinstance(value, str):
            raise ValidationError("Poster path must be a string")
        
        # TMDb poster paths start with '/'
        if not value.startswith('/'):
            raise ValidationError("Poster path must start with '/'")
        
        # Check for valid image extensions
        valid_extensions = ['.jpg', '.jpeg', '.png', '.webp']
        if not any(value.lower().endswith(ext) for ext in valid_extensions):
            raise ValidationError("Poster path must end with a valid image extension (.jpg, .jpeg, .png, .webp)")
        
        return value
    
    @staticmethod
    def validate_backdrop_path(value):
        """
        Validate backdrop path format
        """
        if value is None:
            return value
        
        return MovieValidators.validate_poster_path(value)  # Same validation as poster
    
    @staticmethod
    def validate_runtime(value):
        """
        Validate movie runtime in minutes
        """
        if value is None:
            return value
        
        if not isinstance(value, int) or value <= 0:
            raise ValidationError("Runtime must be a positive integer (minutes)")
        
        if value > 600:  # 10 hours seems reasonable as max
            raise ValidationError("Runtime cannot exceed 600 minutes (10 hours)")
        
        return value
    
    @staticmethod
    def validate_popularity(value):
        """
        Validate popularity score
        """
        if value is None:
            return value
        
        if not isinstance(value, (int, float)) or value < 0:
            raise ValidationError("Popularity must be a non-negative number")
        
        return value
    
    @staticmethod
    def validate_vote_average(value):
        """
        Validate vote average (0-10)
        """
        if value is None:
            return value
        
        if not isinstance(value, (int, float)):
            raise ValidationError("Vote average must be a number")
        
        if value < 0 or value > 10:
            raise ValidationError("Vote average must be between 0 and 10")
        
        return value
    
    @staticmethod
    def validate_vote_count(value):
        """
        Validate vote count
        """
        if value is None:
            return value
        
        if not isinstance(value, int) or value < 0:
            raise ValidationError("Vote count must be a non-negative integer")
        
        return value


class UserValidators:
    """
    Collection of validators for user-related data
    """
    
    @staticmethod
    def validate_username(value):
        """
        Validate username format
        """
        if not isinstance(value, str):
            raise ValidationError("Username must be a string")
        
        if len(value) < 3:
            raise ValidationError("Username must be at least 3 characters long")
        
        if len(value) > 30:
            raise ValidationError("Username cannot exceed 30 characters")
        
        # Allow letters, numbers, underscores, and hyphens
        if not re.match(r"^[a-zA-Z0-9_-]+$", value):
            raise ValidationError("Username can only contain letters, numbers, underscores, and hyphens")
        
        return value.lower()
    
    @staticmethod
    def validate_email(value):
        """
        Validate email format
        """
        if not isinstance(value, str):
            raise ValidationError("Email must be a string")
        
        email_regex = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        if not re.match(email_regex, value):
            raise ValidationError("Invalid email format")
        
        return value.lower()


class APIValidators:
    """
    Collection of validators for API-specific data
    """
    
    @staticmethod
    def validate_page_number(value):
        """
        Validate pagination page number
        """
        try:
            page = int(value)
        except (ValueError, TypeError):
            raise ValidationError("Page number must be an integer")
        
        if page < 1:
            raise ValidationError("Page number must be greater than 0")
        
        if page > 1000:  # Reasonable limit
            raise ValidationError("Page number cannot exceed 1000")
        
        return page
    
    @staticmethod
    def validate_page_size(value):
        """
        Validate pagination page size
        """
        try:
            size = int(value)
        except (ValueError, TypeError):
            raise ValidationError("Page size must be an integer")
        
        if size < 1:
            raise ValidationError("Page size must be greater than 0")
        
        if size > 100:  # Reasonable limit
            raise ValidationError("Page size cannot exceed 100")
        
        return size
    
    @staticmethod
    def validate_search_query(value):
        """
        Validate search query
        """
        if not isinstance(value, str):
            raise ValidationError("Search query must be a string")
        
        if len(value.strip()) < 2:
            raise ValidationError("Search query must be at least 2 characters long")
        
        if len(value) > 100:
            raise ValidationError("Search query cannot exceed 100 characters")
        
        return value.strip()
    
    @staticmethod
    def validate_sort_field(value, allowed_fields):
        """
        Validate sort field
        """
        if not isinstance(value, str):
            raise ValidationError("Sort field must be a string")
        
        # Handle descending order prefix
        field = value.lstrip('-')
        
        if field not in allowed_fields:
            raise ValidationError(f"Invalid sort field. Allowed fields: {', '.join(allowed_fields)}")
        
        return value
    
    @staticmethod
    def validate_date_range(start_date, end_date):
        """
        Validate date range
        """
        if start_date and end_date:
            if start_date > end_date:
                raise ValidationError("Start date cannot be after end date")
        
        return start_date, end_date


# Custom DRF field validators
class RatingField(serializers.FloatField):
    """
    Custom serializer field for movie ratings
    """
    def validate(self, value):
        return MovieValidators.validate_rating(value)


class YearField(serializers.IntegerField):
    """
    Custom serializer field for years
    """
    def validate(self, value):
        return MovieValidators.validate_year(value)


class TMDbIDField(serializers.IntegerField):
    """
    Custom serializer field for TMDb IDs
    """
    def validate(self, value):
        return MovieValidators.validate_tmdb_id(value)