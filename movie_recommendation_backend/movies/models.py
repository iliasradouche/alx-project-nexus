from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator, MaxValueValidator


class Genre(models.Model):
    """Model for movie genres"""
    tmdb_id = models.IntegerField(unique=True)
    name = models.CharField(max_length=100)

    def __str__(self):
        return self.name

    class Meta:
        ordering = ['name']


class Movie(models.Model):
    """Model for movies from TMDb API"""
    tmdb_id = models.IntegerField(unique=True)
    title = models.CharField(max_length=255)
    original_title = models.CharField(max_length=255, blank=True)
    overview = models.TextField(blank=True)
    release_date = models.DateField(null=True, blank=True)
    runtime = models.IntegerField(null=True, blank=True)  # in minutes
    vote_average = models.FloatField(
        default=0.0,
        validators=[MinValueValidator(0.0), MaxValueValidator(10.0)]
    )
    vote_count = models.IntegerField(
        default=0,
        validators=[MinValueValidator(0)]
    )
    popularity = models.FloatField(
        default=0.0,
        validators=[MinValueValidator(0.0)]
    )
    poster_path = models.CharField(max_length=255, blank=True)
    backdrop_path = models.CharField(max_length=255, blank=True)
    adult = models.BooleanField(default=False)
    original_language = models.CharField(max_length=10, blank=True)
    genres = models.ManyToManyField(Genre, blank=True)

    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        year = self.release_date.year if self.release_date else 'Unknown'
        return f"{self.title} ({year})"

    @property
    def poster_url(self):
        """Get full poster URL"""
        if self.poster_path:
            return f"https://image.tmdb.org/t/p/w500{self.poster_path}"
        return None

    @property
    def backdrop_url(self):
        """Get full backdrop URL"""
        if self.backdrop_path:
            return f"https://image.tmdb.org/t/p/w1280{self.backdrop_path}"
        return None

    class Meta:
        ordering = ['-popularity', '-vote_average']
        indexes = [
            models.Index(fields=['tmdb_id']),
            models.Index(fields=['title']),
            models.Index(fields=['release_date']),
            models.Index(fields=['vote_average']),
            models.Index(fields=['popularity']),
        ]


class UserMovieRating(models.Model):
    """Model for user movie ratings"""
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    movie = models.ForeignKey(Movie, on_delete=models.CASCADE)
    rating = models.FloatField(
        validators=[MinValueValidator(0.0), MaxValueValidator(10.0)]
    )  # 0-10 scale
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ['user', 'movie']
        indexes = [
            models.Index(fields=['user', 'rating']),
            models.Index(fields=['movie', 'rating']),
        ]

    def __str__(self):
        return f"{self.user.username} rated {self.movie.title}: {self.rating}"


class UserMovieWatchlist(models.Model):
    """Model for user movie watchlists"""
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    movie = models.ForeignKey(Movie, on_delete=models.CASCADE)
    added_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ['user', 'movie']
        indexes = [
            models.Index(fields=['user', 'added_at']),
        ]

    def __str__(self):
        return f"{self.user.username} - {self.movie.title}"
