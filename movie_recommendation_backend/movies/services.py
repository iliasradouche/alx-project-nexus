import requests
import logging
from datetime import datetime
from typing import Dict, List, Optional
from django.conf import settings
from django.core.cache import cache
from .models import Movie, Genre

logger = logging.getLogger(__name__)


class TMDbAPIService:
    """Service class for interacting with TMDb API"""
    
    def __init__(self):
        self.api_key = settings.TMDB_API_KEY
        self.base_url = settings.TMDB_BASE_URL
        self.session = requests.Session()
        self.session.params = {'api_key': self.api_key}
    
    def _make_request(self, endpoint: str, params: Dict = None) -> Optional[Dict]:
        """Make a request to TMDb API with error handling"""
        try:
            url = f"{self.base_url}/{endpoint}"
            response = self.session.get(url, params=params, timeout=10)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"TMDb API request failed: {e}")
            return None
    
    def search_movies(self, query: str, page: int = 1) -> Optional[Dict]:
        """Search for movies by title"""
        cache_key = f"tmdb_search_{query}_{page}"
        cached_result = cache.get(cache_key)
        
        if cached_result:
            return cached_result
        
        params = {
            'query': query,
            'page': page,
            'include_adult': False
        }
        
        result = self._make_request('search/movie', params)
        if result:
            # Cache for 1 hour
            cache.set(cache_key, result, 3600)
        
        return result
    
    def get_movie_details(self, movie_id: int) -> Optional[Dict]:
        """Get detailed information about a specific movie"""
        cache_key = f"tmdb_movie_{movie_id}"
        cached_result = cache.get(cache_key)
        
        if cached_result:
            return cached_result
        
        result = self._make_request(f'movie/{movie_id}')
        if result:
            # Cache for 24 hours
            cache.set(cache_key, result, 86400)
        
        return result
    
    def get_popular_movies(self, page: int = 1) -> Optional[Dict]:
        """Get popular movies"""
        cache_key = f"tmdb_popular_{page}"
        cached_result = cache.get(cache_key)
        
        if cached_result:
            return cached_result
        
        params = {'page': page}
        result = self._make_request('movie/popular', params)
        
        if result:
            # Cache for 6 hours
            cache.set(cache_key, result, 21600)
        
        return result
    
    def get_top_rated_movies(self, page: int = 1) -> Optional[Dict]:
        """Get top rated movies"""
        cache_key = f"tmdb_top_rated_{page}"
        cached_result = cache.get(cache_key)
        
        if cached_result:
            return cached_result
        
        params = {'page': page}
        result = self._make_request('movie/top_rated', params)
        
        if result:
            # Cache for 6 hours
            cache.set(cache_key, result, 21600)
        
        return result
    
    def get_now_playing_movies(self, page: int = 1) -> Optional[Dict]:
        """Get now playing movies"""
        cache_key = f"tmdb_now_playing_{page}"
        cached_result = cache.get(cache_key)
        
        if cached_result:
            return cached_result
        
        params = {'page': page}
        result = self._make_request('movie/now_playing', params)
        
        if result:
            # Cache for 6 hours
            cache.set(cache_key, result, 21600)
        
        return result
    
    def get_upcoming_movies(self, page: int = 1) -> Optional[Dict]:
        """Get upcoming movies"""
        cache_key = f"tmdb_upcoming_{page}"
        cached_result = cache.get(cache_key)
        
        if cached_result:
            return cached_result
        
        params = {'page': page}
        result = self._make_request('movie/upcoming', params)
        
        if result:
            # Cache for 6 hours
            cache.set(cache_key, result, 21600)
        
        return result
    
    def get_movie_recommendations(self, movie_id: int, page: int = 1) -> Optional[Dict]:
        """Get movie recommendations based on a specific movie"""
        cache_key = f"tmdb_recommendations_{movie_id}_{page}"
        cached_result = cache.get(cache_key)
        
        if cached_result:
            return cached_result
        
        params = {'page': page}
        result = self._make_request(f'movie/{movie_id}/recommendations', params)
        
        if result:
            # Cache for 12 hours
            cache.set(cache_key, result, 43200)
        
        return result
    
    def get_genres(self) -> Optional[Dict]:
        """Get list of movie genres"""
        cache_key = "tmdb_genres"
        cached_result = cache.get(cache_key)
        
        if cached_result:
            return cached_result
        
        result = self._make_request('genre/movie/list')
        
        if result:
            # Cache for 7 days
            cache.set(cache_key, result, 604800)
        
        return result


class MovieDataService:
    """Service class for managing movie data in the database"""
    
    def __init__(self):
        self.tmdb_service = TMDbAPIService()
    
    def sync_genres(self) -> bool:
        """Sync genres from TMDb API to database"""
        try:
            genres_data = self.tmdb_service.get_genres()
            if not genres_data or 'genres' not in genres_data:
                return False
            
            for genre_data in genres_data['genres']:
                Genre.objects.get_or_create(
                    tmdb_id=genre_data['id'],
                    defaults={'name': genre_data['name']}
                )
            
            logger.info(f"Synced {len(genres_data['genres'])} genres")
            return True
        
        except Exception as e:
            logger.error(f"Failed to sync genres: {e}")
            return False
    
    def _parse_date(self, date_string: str) -> Optional[datetime.date]:
        """Parse date string to date object"""
        if not date_string:
            return None
        try:
            return datetime.strptime(date_string, '%Y-%m-%d').date()
        except ValueError:
            return None
    
    def create_or_update_movie(self, movie_data: Dict, return_created: bool = False):
        """Create or update a movie from TMDb data"""
        try:
            # Parse release date
            release_date = self._parse_date(movie_data.get('release_date'))
            
            # Create or update movie
            movie, created = Movie.objects.get_or_create(
                tmdb_id=movie_data['id'],
                defaults={
                    'title': movie_data.get('title', ''),
                    'original_title': movie_data.get('original_title', ''),
                    'overview': movie_data.get('overview', ''),
                    'release_date': release_date,
                    'runtime': movie_data.get('runtime'),
                    'vote_average': movie_data.get('vote_average', 0.0),
                    'vote_count': movie_data.get('vote_count', 0),
                    'popularity': movie_data.get('popularity', 0.0),
                    'poster_path': movie_data.get('poster_path', ''),
                    'backdrop_path': movie_data.get('backdrop_path', ''),
                    'adult': movie_data.get('adult', False),
                    'original_language': movie_data.get('original_language', ''),
                }
            )
            
            # Update existing movie if not created
            if not created:
                movie.title = movie_data.get('title', movie.title)
                movie.original_title = movie_data.get('original_title', movie.original_title)
                movie.overview = movie_data.get('overview', movie.overview)
                movie.release_date = release_date or movie.release_date
                movie.runtime = movie_data.get('runtime', movie.runtime)
                movie.vote_average = movie_data.get('vote_average', movie.vote_average)
                movie.vote_count = movie_data.get('vote_count', movie.vote_count)
                movie.popularity = movie_data.get('popularity', movie.popularity)
                movie.poster_path = movie_data.get('poster_path', movie.poster_path)
                movie.backdrop_path = movie_data.get('backdrop_path', movie.backdrop_path)
                movie.adult = movie_data.get('adult', movie.adult)
                movie.original_language = movie_data.get('original_language', movie.original_language)
                movie.save()
            
            # Handle genres
            if 'genres' in movie_data:
                genre_ids = [genre['id'] for genre in movie_data['genres']]
                genres = Genre.objects.filter(tmdb_id__in=genre_ids)
                movie.genres.set(genres)
            elif 'genre_ids' in movie_data:
                genres = Genre.objects.filter(tmdb_id__in=movie_data['genre_ids'])
                movie.genres.set(genres)
            
            if return_created:
                return movie, created
            return movie
        
        except Exception as e:
            logger.error(f"Failed to create/update movie {movie_data.get('id')}: {e}")
            if return_created:
                return None, False
            return None
    
    def sync_popular_movies(self, pages: int = 5) -> int:
        """Sync popular movies from TMDb API"""
        synced_count = 0
        
        for page in range(1, pages + 1):
            try:
                data = self.tmdb_service.get_popular_movies(page)
                if not data or 'results' not in data:
                    continue
                
                for movie_data in data['results']:
                    movie = self.create_or_update_movie(movie_data)
                    if movie:
                        synced_count += 1
                
                logger.info(f"Synced page {page} of popular movies")
            
            except Exception as e:
                logger.error(f"Failed to sync popular movies page {page}: {e}")
        
        return synced_count