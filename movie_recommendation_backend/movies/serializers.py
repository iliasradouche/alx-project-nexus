from rest_framework import serializers
from .models import Movie, Genre, UserMovieRating, UserMovieWatchlist


class GenreSerializer(serializers.ModelSerializer):
    """Serializer for Genre model"""
    
    class Meta:
        model = Genre
        fields = ['id', 'tmdb_id', 'name']
        read_only_fields = ['id']


class MovieListSerializer(serializers.ModelSerializer):
    """Serializer for Movie model in list views"""
    genres = GenreSerializer(many=True, read_only=True)
    poster_url = serializers.ReadOnlyField()
    
    class Meta:
        model = Movie
        fields = [
            'id', 'tmdb_id', 'title', 'overview', 'release_date',
            'vote_average', 'vote_count', 'popularity', 'poster_path',
            'poster_url', 'genres', 'adult', 'original_language'
        ]
        read_only_fields = ['id']


class MovieDetailSerializer(serializers.ModelSerializer):
    """Serializer for Movie model in detail views"""
    genres = GenreSerializer(many=True, read_only=True)
    poster_url = serializers.ReadOnlyField()
    backdrop_url = serializers.ReadOnlyField()
    
    class Meta:
        model = Movie
        fields = [
            'id', 'tmdb_id', 'title', 'original_title', 'overview',
            'release_date', 'runtime', 'vote_average', 'vote_count',
            'popularity', 'poster_path', 'backdrop_path', 'poster_url',
            'backdrop_url', 'adult', 'original_language', 'genres',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class UserMovieRatingSerializer(serializers.ModelSerializer):
    """Serializer for UserMovieRating model"""
    movie = MovieListSerializer(read_only=True)
    movie_id = serializers.IntegerField(write_only=True)
    
    class Meta:
        model = UserMovieRating
        fields = [
            'id', 'movie', 'movie_id', 'rating', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']
    
    def validate_rating(self, value):
        """Validate rating is between 1 and 10"""
        if not 1 <= value <= 10:
            raise serializers.ValidationError(
                "Rating must be between 1 and 10."
            )
        return value
    
    def create(self, validated_data):
        """Create a new rating"""
        movie_id = validated_data.pop('movie_id')
        try:
            movie = Movie.objects.get(id=movie_id)
        except Movie.DoesNotExist:
            raise serializers.ValidationError(
                {"movie_id": "Movie not found."}
            )
        
        validated_data['movie'] = movie
        validated_data['user'] = self.context['request'].user
        
        # Update existing rating or create new one
        rating, created = UserMovieRating.objects.update_or_create(
            user=validated_data['user'],
            movie=movie,
            defaults={'rating': validated_data['rating']}
        )
        
        return rating


class UserMovieWatchlistSerializer(serializers.ModelSerializer):
    """Serializer for UserMovieWatchlist model"""
    movie = MovieListSerializer(read_only=True)
    movie_id = serializers.IntegerField(write_only=True)
    
    class Meta:
        model = UserMovieWatchlist
        fields = ['id', 'movie', 'movie_id', 'added_at']
        read_only_fields = ['id', 'added_at']
    
    def create(self, validated_data):
        """Add movie to watchlist"""
        movie_id = validated_data.pop('movie_id')
        try:
            movie = Movie.objects.get(id=movie_id)
        except Movie.DoesNotExist:
            raise serializers.ValidationError(
                {"movie_id": "Movie not found."}
            )
        
        validated_data['movie'] = movie
        validated_data['user'] = self.context['request'].user
        
        # Create watchlist entry if it doesn't exist
        watchlist_item, created = UserMovieWatchlist.objects.get_or_create(
            user=validated_data['user'],
            movie=movie
        )
        
        if not created:
            raise serializers.ValidationError(
                "Movie is already in your watchlist."
            )
        
        return watchlist_item


class MovieSearchSerializer(serializers.Serializer):
    """Serializer for movie search parameters"""
    query = serializers.CharField(max_length=255, required=True)
    page = serializers.IntegerField(min_value=1, default=1)
    
    def validate_query(self, value):
        """Validate search query"""
        if len(value.strip()) < 2:
            raise serializers.ValidationError(
                "Search query must be at least 2 characters long."
            )
        return value.strip()