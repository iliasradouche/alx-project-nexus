from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from movies.services import TMDbAPIService, MovieDataService
import time


class Command(BaseCommand):
    help = 'Populate database with initial movie data from TMDb API'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--pages',
            type=int,
            default=5,
            help='Number of pages to fetch for each category (default: 5)'
        )
        parser.add_argument(
            '--delay',
            type=float,
            default=0.25,
            help='Delay between API calls in seconds (default: 0.25)'
        )
        parser.add_argument(
            '--categories',
            nargs='+',
            default=['popular', 'top_rated'],
            choices=['popular', 'top_rated', 'now_playing', 'upcoming'],
            help='Categories to fetch (default: popular top_rated)'
        )
    
    def handle(self, *args, **options):
        pages = options['pages']
        delay = options['delay']
        categories = options['categories']
        
        self.stdout.write(
            self.style.SUCCESS(
                f'Starting to populate movies from TMDb API...\n'
                f'Pages per category: {pages}\n'
                f'Delay between calls: {delay}s\n'
                f'Categories: {", ".join(categories)}\n'
            )
        )
        
        tmdb_service = TMDbAPIService()
        movie_service = MovieDataService()
        
        # First, populate genres
        self.stdout.write('Fetching genres...')
        try:
            genres_data = tmdb_service.get_genres()
            if genres_data and 'genres' in genres_data:
                for genre_data in genres_data['genres']:
                    movie_service.create_or_update_genre(genre_data)
                self.stdout.write(
                    self.style.SUCCESS(
                        f'✓ Populated {len(genres_data["genres"])} genres'
                    )
                )
            else:
                self.stdout.write(
                    self.style.WARNING('⚠ Failed to fetch genres')
                )
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'✗ Error fetching genres: {str(e)}')
            )
        
        # Track statistics
        total_movies = 0
        total_new_movies = 0
        total_updated_movies = 0
        
        # Populate movies by category
        for category in categories:
            self.stdout.write(f'\nFetching {category} movies...')
            
            category_movies = 0
            category_new = 0
            category_updated = 0
            
            for page in range(1, pages + 1):
                try:
                    # Get movies based on category
                    if category == 'popular':
                        movies_data = tmdb_service.get_popular_movies(page)
                    elif category == 'top_rated':
                        movies_data = tmdb_service.get_top_rated_movies(page)
                    elif category == 'now_playing':
                        movies_data = tmdb_service.get_now_playing_movies(page)
                    elif category == 'upcoming':
                        movies_data = tmdb_service.get_upcoming_movies(page)
                    else:
                        continue
                    
                    if not movies_data or 'results' not in movies_data:
                        self.stdout.write(
                            self.style.WARNING(
                                f'⚠ No data for {category} page {page}'
                            )
                        )
                        continue
                    
                    # Process movies in batch
                    with transaction.atomic():
                        for movie_data in movies_data['results']:
                            try:
                                movie, created = movie_service.create_or_update_movie(
                                    movie_data, return_created=True
                                )
                                if movie:
                                    category_movies += 1
                                    if created:
                                        category_new += 1
                                    else:
                                        category_updated += 1
                            except Exception as e:
                                self.stdout.write(
                                    self.style.WARNING(
                                        f'⚠ Error processing movie {movie_data.get("title", "Unknown")}: {str(e)}'
                                    )
                                )
                    
                    self.stdout.write(
                        f'  Page {page}/{pages}: {len(movies_data["results"])} movies processed'
                    )
                    
                    # Rate limiting
                    if delay > 0:
                        time.sleep(delay)
                        
                except Exception as e:
                    self.stdout.write(
                        self.style.ERROR(
                            f'✗ Error fetching {category} page {page}: {str(e)}'
                        )
                    )
                    continue
            
            # Category summary
            self.stdout.write(
                self.style.SUCCESS(
                    f'✓ {category.title()}: {category_movies} movies '
                    f'({category_new} new, {category_updated} updated)'
                )
            )
            
            total_movies += category_movies
            total_new_movies += category_new
            total_updated_movies += category_updated
        
        # Final summary
        self.stdout.write(
            self.style.SUCCESS(
                f'\n🎬 Population complete!\n'
                f'Total movies processed: {total_movies}\n'
                f'New movies added: {total_new_movies}\n'
                f'Movies updated: {total_updated_movies}\n'
            )
        )
        
        # Additional recommendations
        self.stdout.write(
            self.style.WARNING(
                '\n💡 Recommendations:\n'
                '• Run migrations if you haven\'t: python manage.py migrate\n'
                '• Create a superuser: python manage.py createsuperuser\n'
                '• Start the server: python manage.py runserver\n'
                '• Test the API at: http://localhost:8000/api/movies/\n'
            )
        )