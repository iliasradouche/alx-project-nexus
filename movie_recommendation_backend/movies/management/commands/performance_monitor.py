from django.core.management.base import BaseCommand
from django.core.cache import cache
from django.db import connection
from django.conf import settings
import time
import psutil
import json
from datetime import datetime, timedelta
from movies.models import Movie, Genre, UserMovieRating
from movies.cache_utils import CacheStats


class Command(BaseCommand):
    help = 'Monitor system performance and generate reports'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--report-type',
            type=str,
            choices=['cache', 'database', 'system', 'all'],
            default='all',
            help='Type of performance report to generate'
        )
        parser.add_argument(
            '--output-format',
            type=str,
            choices=['json', 'table'],
            default='table',
            help='Output format for the report'
        )
        parser.add_argument(
            '--save-to-file',
            type=str,
            help='Save report to specified file path'
        )
    
    def handle(self, *args, **options):
        report_type = options['report_type']
        output_format = options['output_format']
        save_to_file = options.get('save_to_file')
        
        self.stdout.write(
            self.style.SUCCESS('Starting performance monitoring...')
        )
        
        report_data = {}
        
        if report_type in ['cache', 'all']:
            report_data['cache'] = self.get_cache_performance()
            
        if report_type in ['database', 'all']:
            report_data['database'] = self.get_database_performance()
            
        if report_type in ['system', 'all']:
            report_data['system'] = self.get_system_performance()
        
        # Generate timestamp
        report_data['timestamp'] = datetime.now().isoformat()
        report_data['report_type'] = report_type
        
        # Output report
        if output_format == 'json':
            self.output_json_report(report_data, save_to_file)
        else:
            self.output_table_report(report_data, save_to_file)
    
    def get_cache_performance(self):
        """Get Redis cache performance metrics"""
        cache_stats = CacheStats()
        stats = cache_stats.get_cache_info()
        
        # Test cache performance
        cache_performance = self.test_cache_performance()
        
        return {
            'stats': stats,
            'performance': cache_performance,
            'redis_info': self.get_redis_info()
        }
    
    def get_database_performance(self):
        """Get database performance metrics"""
        with connection.cursor() as cursor:
            # Get database size and table statistics
            db_stats = self.get_database_stats(cursor)
            
            # Test query performance
            query_performance = self.test_query_performance()
            
            # Get slow queries (if available)
            slow_queries = self.get_slow_queries(cursor)
            
        return {
            'stats': db_stats,
            'query_performance': query_performance,
            'slow_queries': slow_queries
        }
    
    def get_system_performance(self):
        """Get system performance metrics"""
        return {
            'cpu': {
                'usage_percent': psutil.cpu_percent(interval=1),
                'count': psutil.cpu_count(),
                'load_average': psutil.getloadavg() if hasattr(psutil, 'getloadavg') else None
            },
            'memory': {
                'total': psutil.virtual_memory().total,
                'available': psutil.virtual_memory().available,
                'percent': psutil.virtual_memory().percent,
                'used': psutil.virtual_memory().used
            },
            'disk': {
                'total': psutil.disk_usage('/').total,
                'used': psutil.disk_usage('/').used,
                'free': psutil.disk_usage('/').free,
                'percent': psutil.disk_usage('/').percent
            } if hasattr(psutil, 'disk_usage') else None,
            'network': dict(psutil.net_io_counters()._asdict()) if hasattr(psutil, 'net_io_counters') else None
        }
    
    def test_cache_performance(self):
        """Test cache read/write performance"""
        test_data = {'test': 'performance_data', 'timestamp': time.time()}
        
        # Test write performance
        start_time = time.time()
        for i in range(100):
            cache.set(f'perf_test_{i}', test_data, 60)
        write_time = time.time() - start_time
        
        # Test read performance
        start_time = time.time()
        for i in range(100):
            cache.get(f'perf_test_{i}')
        read_time = time.time() - start_time
        
        # Cleanup
        for i in range(100):
            cache.delete(f'perf_test_{i}')
        
        return {
            'write_time_100_ops': round(write_time, 4),
            'read_time_100_ops': round(read_time, 4),
            'avg_write_time_ms': round((write_time / 100) * 1000, 2),
            'avg_read_time_ms': round((read_time / 100) * 1000, 2)
        }
    
    def test_query_performance(self):
        """Test database query performance"""
        queries = [
            ('Count Movies', lambda: Movie.objects.count()),
            ('Count Genres', lambda: Genre.objects.count()),
            ('Count Ratings', lambda: UserMovieRating.objects.count()),
            ('Popular Movies', lambda: list(Movie.objects.filter(popularity__gt=50).order_by('-popularity')[:10])),
            ('Movies with Genres', lambda: list(Movie.objects.prefetch_related('genres')[:10])),
        ]
        
        results = {}
        
        for query_name, query_func in queries:
            start_time = time.time()
            try:
                query_func()
                execution_time = time.time() - start_time
                results[query_name] = {
                    'execution_time_ms': round(execution_time * 1000, 2),
                    'status': 'success'
                }
            except Exception as e:
                results[query_name] = {
                    'execution_time_ms': None,
                    'status': 'error',
                    'error': str(e)
                }
        
        return results
    
    def get_database_stats(self, cursor):
        """Get database statistics"""
        stats = {}
        
        if connection.vendor == 'sqlite':
            # SQLite specific queries
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
            tables = [row[0] for row in cursor.fetchall()]
            
            stats['tables'] = {}
            for table in tables:
                if not table.startswith('sqlite_'):
                    cursor.execute(f"SELECT COUNT(*) FROM {table}")
                    count = cursor.fetchone()[0]
                    stats['tables'][table] = {'row_count': count}
        
        elif connection.vendor == 'postgresql':
            # PostgreSQL specific queries
            cursor.execute("""
                SELECT schemaname, tablename, n_tup_ins, n_tup_upd, n_tup_del
                FROM pg_stat_user_tables
            """)
            stats['table_stats'] = cursor.fetchall()
        
        return stats
    
    def get_slow_queries(self, cursor):
        """Get slow queries (database-specific)"""
        if connection.vendor == 'postgresql':
            try:
                cursor.execute("""
                    SELECT query, mean_time, calls, total_time
                    FROM pg_stat_statements
                    ORDER BY mean_time DESC
                    LIMIT 10
                """)
                return cursor.fetchall()
            except Exception:
                return []
        
        return []
    
    def get_redis_info(self):
        """Get Redis server information"""
        try:
            from django_redis import get_redis_connection
            redis_conn = get_redis_connection("default")
            info = redis_conn.info()
            
            return {
                'version': info.get('redis_version'),
                'used_memory': info.get('used_memory'),
                'used_memory_human': info.get('used_memory_human'),
                'connected_clients': info.get('connected_clients'),
                'total_commands_processed': info.get('total_commands_processed'),
                'keyspace_hits': info.get('keyspace_hits'),
                'keyspace_misses': info.get('keyspace_misses'),
                'hit_rate': round(
                    (info.get('keyspace_hits', 0) / 
                     max(info.get('keyspace_hits', 0) + info.get('keyspace_misses', 0), 1)) * 100, 2
                )
            }
        except Exception as e:
            return {'error': str(e)}
    
    def output_json_report(self, report_data, save_to_file=None):
        """Output report in JSON format"""
        json_output = json.dumps(report_data, indent=2, default=str)
        
        if save_to_file:
            with open(save_to_file, 'w') as f:
                f.write(json_output)
            self.stdout.write(
                self.style.SUCCESS(f'Report saved to {save_to_file}')
            )
        else:
            self.stdout.write(json_output)
    
    def output_table_report(self, report_data, save_to_file=None):
        """Output report in table format"""
        output_lines = []
        output_lines.append("=" * 80)
        output_lines.append(f"PERFORMANCE REPORT - {report_data['timestamp']}")
        output_lines.append("=" * 80)
        
        if 'system' in report_data:
            output_lines.append("\nSYSTEM PERFORMANCE:")
            output_lines.append("-" * 40)
            sys_data = report_data['system']
            
            if 'cpu' in sys_data:
                output_lines.append(f"CPU Usage: {sys_data['cpu']['usage_percent']}%")
                output_lines.append(f"CPU Count: {sys_data['cpu']['count']}")
            
            if 'memory' in sys_data:
                mem = sys_data['memory']
                output_lines.append(f"Memory Usage: {mem['percent']}%")
                output_lines.append(f"Memory Used: {mem['used'] / (1024**3):.2f} GB")
                output_lines.append(f"Memory Available: {mem['available'] / (1024**3):.2f} GB")
        
        if 'cache' in report_data:
            output_lines.append("\nCACHE PERFORMANCE:")
            output_lines.append("-" * 40)
            cache_data = report_data['cache']
            
            if 'performance' in cache_data:
                perf = cache_data['performance']
                output_lines.append(f"Avg Write Time: {perf['avg_write_time_ms']} ms")
                output_lines.append(f"Avg Read Time: {perf['avg_read_time_ms']} ms")
            
            if 'redis_info' in cache_data and 'hit_rate' in cache_data['redis_info']:
                output_lines.append(f"Cache Hit Rate: {cache_data['redis_info']['hit_rate']}%")
        
        if 'database' in report_data:
            output_lines.append("\nDATABASE PERFORMANCE:")
            output_lines.append("-" * 40)
            db_data = report_data['database']
            
            if 'query_performance' in db_data:
                for query_name, result in db_data['query_performance'].items():
                    if result['status'] == 'success':
                        output_lines.append(f"{query_name}: {result['execution_time_ms']} ms")
                    else:
                        output_lines.append(f"{query_name}: ERROR - {result.get('error', 'Unknown')}")
        
        output_lines.append("\n" + "=" * 80)
        
        report_text = "\n".join(output_lines)
        
        if save_to_file:
            with open(save_to_file, 'w') as f:
                f.write(report_text)
            self.stdout.write(
                self.style.SUCCESS(f'Report saved to {save_to_file}')
            )
        else:
            self.stdout.write(report_text)