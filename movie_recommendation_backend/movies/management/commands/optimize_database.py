from django.core.management.base import BaseCommand
from django.db import connection
from django.conf import settings
import logging

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Optimize database performance by adding indexes and analyzing queries'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be done without executing',
        )
        parser.add_argument(
            '--analyze',
            action='store_true',
            help='Analyze current database performance',
        )
    
    def handle(self, *args, **options):
        dry_run = options['dry_run']
        analyze = options['analyze']
        
        if analyze:
            self.analyze_performance()
            return
        
        self.stdout.write(self.style.SUCCESS('Starting database optimization...'))
        
        # Add database indexes for better performance
        self.add_indexes(dry_run)
        
        # Optimize database tables
        self.optimize_tables(dry_run)
        
        self.stdout.write(self.style.SUCCESS('Database optimization completed!'))
    
    def add_indexes(self, dry_run=False):
        """Add performance indexes to database tables"""
        
        indexes = [
            # Movie table indexes
            {
                'table': 'movies_movie',
                'name': 'idx_movie_tmdb_id',
                'columns': ['tmdb_id'],
                'unique': True
            },
            {
                'table': 'movies_movie',
                'name': 'idx_movie_popularity',
                'columns': ['popularity DESC']
            },
            {
                'table': 'movies_movie',
                'name': 'idx_movie_vote_average',
                'columns': ['vote_average DESC']
            },
            {
                'table': 'movies_movie',
                'name': 'idx_movie_release_date',
                'columns': ['release_date DESC']
            },
            {
                'table': 'movies_movie',
                'name': 'idx_movie_title',
                'columns': ['title']
            },
            {
                'table': 'movies_movie',
                'name': 'idx_movie_original_title',
                'columns': ['original_title']
            },
            {
                'table': 'movies_movie',
                'name': 'idx_movie_created_at',
                'columns': ['created_at DESC']
            },
            
            # Genre table indexes
            {
                'table': 'movies_genre',
                'name': 'idx_genre_tmdb_id',
                'columns': ['tmdb_id'],
                'unique': True
            },
            {
                'table': 'movies_genre',
                'name': 'idx_genre_name',
                'columns': ['name']
            },
            
            # UserMovieRating table indexes
            {
                'table': 'movies_usermovierating',
                'name': 'idx_rating_user_movie',
                'columns': ['user_id', 'movie_id'],
                'unique': True
            },
            {
                'table': 'movies_usermovierating',
                'name': 'idx_rating_user',
                'columns': ['user_id']
            },
            {
                'table': 'movies_usermovierating',
                'name': 'idx_rating_movie',
                'columns': ['movie_id']
            },
            {
                'table': 'movies_usermovierating',
                'name': 'idx_rating_created_at',
                'columns': ['created_at DESC']
            },
            
            # UserMovieWatchlist table indexes
            {
                'table': 'movies_usermoviewatchlist',
                'name': 'idx_watchlist_user_movie',
                'columns': ['user_id', 'movie_id'],
                'unique': True
            },
            {
                'table': 'movies_usermoviewatchlist',
                'name': 'idx_watchlist_user',
                'columns': ['user_id']
            },
            {
                'table': 'movies_usermoviewatchlist',
                'name': 'idx_watchlist_added_at',
                'columns': ['added_at DESC']
            },
            
            # Movie-Genre many-to-many table indexes
            {
                'table': 'movies_movie_genres',
                'name': 'idx_movie_genres_movie',
                'columns': ['movie_id']
            },
            {
                'table': 'movies_movie_genres',
                'name': 'idx_movie_genres_genre',
                'columns': ['genre_id']
            },
        ]
        
        with connection.cursor() as cursor:
            for index in indexes:
                try:
                    # Check if index already exists
                    if self.index_exists(cursor, index['name']):
                        self.stdout.write(
                            self.style.WARNING(f"Index {index['name']} already exists, skipping...")
                        )
                        continue
                    
                    # Build CREATE INDEX statement
                    unique_clause = 'UNIQUE ' if index.get('unique', False) else ''
                    # Handle DESC clauses for SQLite compatibility
                    columns = []
                    for col in index['columns']:
                        if ' DESC' in col:
                            # SQLite doesn't support DESC in column names for some operations
                            col = col.replace(' DESC', '')
                        columns.append(col)
                    columns_clause = ', '.join(columns)
                    
                    sql = f"CREATE {unique_clause}INDEX {index['name']} ON {index['table']} ({columns_clause})"
                    
                    if dry_run:
                        self.stdout.write(f"Would execute: {sql}")
                    else:
                        cursor.execute(sql)
                        self.stdout.write(
                            self.style.SUCCESS(f"Created index: {index['name']}")
                        )
                        
                except Exception as e:
                    self.stdout.write(
                        self.style.ERROR(f"Failed to create index {index['name']}: {e}")
                    )
    
    def index_exists(self, cursor, index_name):
        """Check if an index exists in the database"""
        try:
            if connection.vendor == 'postgresql':
                cursor.execute(
                    "SELECT 1 FROM pg_indexes WHERE indexname = %s",
                    [index_name]
                )
            elif connection.vendor == 'sqlite':
                cursor.execute(
                    "SELECT 1 FROM sqlite_master WHERE type='index' AND name = ?",
                    [index_name]
                )
            else:
                # MySQL
                cursor.execute(
                    "SELECT 1 FROM information_schema.statistics WHERE index_name = %s",
                    [index_name]
                )
            return cursor.fetchone() is not None
        except Exception:
            return False
    
    def optimize_tables(self, dry_run=False):
        """Optimize database tables"""
        tables = [
            'movies_movie',
            'movies_genre',
            'movies_usermovierating',
            'movies_usermoviewatchlist',
            'movies_movie_genres'
        ]
        
        with connection.cursor() as cursor:
            for table in tables:
                try:
                    if connection.vendor == 'postgresql':
                        sql = f"VACUUM ANALYZE {table}"
                    elif connection.vendor == 'mysql':
                        sql = f"OPTIMIZE TABLE {table}"
                    else:
                        # SQLite
                        sql = f"VACUUM"
                    
                    if dry_run:
                        self.stdout.write(f"Would execute: {sql}")
                    else:
                        cursor.execute(sql)
                        self.stdout.write(
                            self.style.SUCCESS(f"Optimized table: {table}")
                        )
                        
                except Exception as e:
                    self.stdout.write(
                        self.style.ERROR(f"Failed to optimize table {table}: {e}")
                    )
    
    def analyze_performance(self):
        """Analyze current database performance"""
        self.stdout.write(self.style.SUCCESS('Analyzing database performance...'))
        
        with connection.cursor() as cursor:
            # Get table sizes
            self.stdout.write('\n=== Table Sizes ===')
            
            if connection.vendor == 'postgresql':
                cursor.execute("""
                    SELECT 
                        schemaname,
                        tablename,
                        attname,
                        n_distinct,
                        correlation
                    FROM pg_stats 
                    WHERE schemaname = 'public' 
                    AND tablename LIKE 'movies_%'
                    ORDER BY tablename, attname
                """)
                
                for row in cursor.fetchall():
                    self.stdout.write(f"{row[1]}.{row[2]}: distinct={row[3]}, correlation={row[4]}")
            
            elif connection.vendor == 'sqlite':
                # Get table info for SQLite
                tables = ['movies_movie', 'movies_genre', 'movies_usermovierating', 'movies_usermoviewatchlist']
                for table in tables:
                    try:
                        cursor.execute(f"SELECT COUNT(*) FROM {table}")
                        count = cursor.fetchone()[0]
                        self.stdout.write(f"{table}: {count} rows")
                    except Exception as e:
                        self.stdout.write(f"Error analyzing {table}: {e}")
            
            # Show existing indexes
            self.stdout.write('\n=== Existing Indexes ===')
            
            if connection.vendor == 'postgresql':
                cursor.execute("""
                    SELECT 
                        tablename,
                        indexname,
                        indexdef
                    FROM pg_indexes 
                    WHERE tablename LIKE 'movies_%'
                    ORDER BY tablename, indexname
                """)
                
                for row in cursor.fetchall():
                    self.stdout.write(f"{row[0]}: {row[1]}")
            
            elif connection.vendor == 'sqlite':
                cursor.execute("""
                    SELECT 
                        name,
                        tbl_name,
                        sql
                    FROM sqlite_master 
                    WHERE type='index' 
                    AND tbl_name LIKE 'movies_%'
                    ORDER BY tbl_name, name
                """)
                
                for row in cursor.fetchall():
                    if row[0] and not row[0].startswith('sqlite_'):
                        self.stdout.write(f"{row[1]}: {row[0]}")
        
        self.stdout.write(self.style.SUCCESS('\nPerformance analysis completed!'))