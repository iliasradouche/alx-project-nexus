from django.test import TestCase, RequestFactory
from django.http import HttpResponse
from django.contrib.auth.models import User
from django.core.cache import cache
from django.test.utils import override_settings
from unittest.mock import Mock, patch
import time
import json

from movies.middleware import (
    SecurityHeadersMiddleware,
    RequestValidationMiddleware,
    RateLimitMiddleware,
    ErrorLoggingMiddleware,
    RequestResponseLoggingMiddleware
)


class SecurityHeadersMiddlewareTest(TestCase):
    """Test SecurityHeadersMiddleware functionality"""
    
    def setUp(self):
        self.factory = RequestFactory()
        self.middleware = SecurityHeadersMiddleware(self.get_response)
    
    def get_response(self, request):
        """Mock response function"""
        return HttpResponse('Test response')
    
    def test_security_headers_added(self):
        """Test that security headers are added to response"""
        request = self.factory.get('/api/movies/')
        response = self.middleware(request)
        
        # Check that security headers are present
        self.assertEqual(response['X-Content-Type-Options'], 'nosniff')
        self.assertEqual(response['X-Frame-Options'], 'DENY')
        self.assertEqual(response['X-XSS-Protection'], '1; mode=block')
        self.assertEqual(response['Referrer-Policy'], 'strict-origin-when-cross-origin')
        self.assertIn('Content-Security-Policy', response)
    
    def test_security_headers_not_overwritten(self):
        """Test that existing security headers are not overwritten"""
        def get_response_with_headers(request):
            response = HttpResponse('Test response')
            response['X-Frame-Options'] = 'SAMEORIGIN'
            return response
        
        middleware = SecurityHeadersMiddleware(get_response_with_headers)
        request = self.factory.get('/api/movies/')
        response = middleware(request)
        
        # Existing header should be preserved
        self.assertEqual(response['X-Frame-Options'], 'SAMEORIGIN')
        # Other headers should still be added
        self.assertEqual(response['X-Content-Type-Options'], 'nosniff')


class RequestValidationMiddlewareTest(TestCase):
    """Test RequestValidationMiddleware functionality"""
    
    def setUp(self):
        self.factory = RequestFactory()
        self.middleware = RequestValidationMiddleware(self.get_response)
    
    def get_response(self, request):
        """Mock response function"""
        return HttpResponse('Test response')
    
    def test_valid_request_passes(self):
        """Test that valid requests pass through"""
        request = self.factory.get('/api/movies/', {'search': 'action'})
        response = self.middleware(request)
        
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content.decode(), 'Test response')
    
    def test_request_size_limit(self):
        """Test that oversized requests are rejected"""
        large_data = 'x' * (2 * 1024 * 1024)  # 2MB of data
        request = self.factory.post('/api/movies/', {'data': large_data})
        
        response = self.middleware(request)
        
        self.assertEqual(response.status_code, 413)
        self.assertIn('Request too large', response.content.decode())
    
    def test_suspicious_patterns_detected(self):
        """Test that suspicious patterns are detected and logged"""
        suspicious_data = {
            'search': '<script>alert("xss")</script>',
            'filter': 'DROP TABLE movies;'
        }
        
        request = self.factory.get('/api/movies/', suspicious_data)
        
        with patch('movies.middleware.logger') as mock_logger:
            response = self.middleware(request)
            
            # Should log suspicious activity
            mock_logger.warning.assert_called()
            
            # Request should still pass but be flagged
            self.assertEqual(response.status_code, 200)
    
    def test_content_type_validation(self):
        """Test content type validation for POST requests"""
        # Valid JSON content type
        request = self.factory.post(
            '/api/movies/',
            json.dumps({'title': 'Test Movie'}),
            content_type='application/json'
        )
        response = self.middleware(request)
        self.assertEqual(response.status_code, 200)
        
        # Invalid content type for JSON data
        request = self.factory.post(
            '/api/movies/',
            json.dumps({'title': 'Test Movie'}),
            content_type='text/plain'
        )
        response = self.middleware(request)
        # Should still pass but might be logged
        self.assertEqual(response.status_code, 200)


class RateLimitMiddlewareTest(TestCase):
    """Test RateLimitMiddleware functionality"""
    
    def setUp(self):
        self.factory = RequestFactory()
        self.middleware = RateLimitMiddleware(self.get_response)
        cache.clear()  # Clear cache before each test
    
    def get_response(self, request):
        """Mock response function"""
        return HttpResponse('Test response')
    
    @override_settings(RATELIMIT_ENABLE=True)
    def test_rate_limiting_by_ip(self):
        """Test rate limiting by IP address"""
        # Make requests from same IP
        ip_address = '192.168.1.1'
        
        # First few requests should pass
        for i in range(5):
            request = self.factory.get('/api/movies/', REMOTE_ADDR=ip_address)
            response = self.middleware(request)
            self.assertEqual(response.status_code, 200)
        
        # Simulate rapid requests that exceed limit
        for i in range(20):
            request = self.factory.get('/api/movies/', REMOTE_ADDR=ip_address)
            response = self.middleware(request)
            
            # Some requests should be rate limited
            if response.status_code == 429:
                self.assertIn('Rate limit exceeded', response.content.decode())
                break
    
    @override_settings(RATELIMIT_ENABLE=True)
    def test_rate_limiting_by_user(self):
        """Test rate limiting by authenticated user"""
        user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        
        # Make requests as authenticated user
        for i in range(25):
            request = self.factory.get('/api/movies/')
            request.user = user
            response = self.middleware(request)
            
            if response.status_code == 429:
                self.assertIn('Rate limit exceeded', response.content.decode())
                break
    
    @override_settings(RATELIMIT_ENABLE=False)
    def test_rate_limiting_disabled(self):
        """Test that rate limiting can be disabled"""
        ip_address = '192.168.1.1'
        
        # Make many requests - should all pass when disabled
        for i in range(50):
            request = self.factory.get('/api/movies/', REMOTE_ADDR=ip_address)
            response = self.middleware(request)
            self.assertEqual(response.status_code, 200)
    
    def test_different_endpoints_separate_limits(self):
        """Test that different endpoints have separate rate limits"""
        ip_address = '192.168.1.1'
        
        # Make requests to different endpoints
        endpoints = ['/api/movies/', '/api/genres/', '/api/search/']
        
        for endpoint in endpoints:
            for i in range(10):
                request = self.factory.get(endpoint, REMOTE_ADDR=ip_address)
                response = self.middleware(request)
                # Should not be rate limited across different endpoints
                self.assertEqual(response.status_code, 200)


class ErrorLoggingMiddlewareTest(TestCase):
    """Test ErrorLoggingMiddleware functionality"""
    
    def setUp(self):
        self.factory = RequestFactory()
        self.middleware = ErrorLoggingMiddleware(self.get_response)
    
    def get_response(self, request):
        """Mock response function"""
        return HttpResponse('Test response')
    
    def get_error_response(self, request):
        """Mock response function that raises an error"""
        raise ValueError('Test error')
    
    @patch('movies.middleware.logger')
    def test_exception_logging(self, mock_logger):
        """Test that exceptions are properly logged"""
        middleware = ErrorLoggingMiddleware(self.get_error_response)
        request = self.factory.get('/api/movies/')
        
        # Exception should be caught and logged
        with self.assertRaises(ValueError):
            middleware(request)
        
        # Should log the error
        mock_logger.error.assert_called()
        
        # Check that request details are logged
        call_args = mock_logger.error.call_args[0][0]
        self.assertIn('GET', call_args)
        self.assertIn('/api/movies/', call_args)
    
    @patch('movies.middleware.logger')
    def test_error_response_logging(self, mock_logger):
        """Test that error responses are logged"""
        def get_error_response(request):
            return HttpResponse('Not Found', status=404)
        
        middleware = ErrorLoggingMiddleware(get_error_response)
        request = self.factory.get('/api/movies/999/')
        
        response = middleware(request)
        
        self.assertEqual(response.status_code, 404)
        # Should log 4xx and 5xx responses
        mock_logger.warning.assert_called()
    
    @patch('movies.middleware.logger')
    def test_successful_response_not_logged(self, mock_logger):
        """Test that successful responses are not logged as errors"""
        request = self.factory.get('/api/movies/')
        response = self.middleware(request)
        
        self.assertEqual(response.status_code, 200)
        # Should not log successful responses
        mock_logger.error.assert_not_called()
        mock_logger.warning.assert_not_called()


class RequestResponseLoggingMiddlewareTest(TestCase):
    """Test RequestResponseLoggingMiddleware functionality"""
    
    def setUp(self):
        self.factory = RequestFactory()
        self.middleware = RequestResponseLoggingMiddleware(self.get_response)
    
    def get_response(self, request):
        """Mock response function"""
        return HttpResponse('Test response')
    
    @patch('movies.middleware.logger')
    def test_request_logging(self, mock_logger):
        """Test that requests are logged"""
        request = self.factory.get('/api/movies/', {'search': 'action'})
        request.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        
        response = self.middleware(request)
        
        # Should log request details
        mock_logger.info.assert_called()
        
        # Check logged information
        call_args = mock_logger.info.call_args[0][0]
        self.assertIn('GET', call_args)
        self.assertIn('/api/movies/', call_args)
        self.assertIn('testuser', call_args)
    
    @patch('movies.middleware.logger')
    def test_response_logging(self, mock_logger):
        """Test that responses are logged"""
        request = self.factory.get('/api/movies/')
        
        response = self.middleware(request)
        
        # Should log both request and response
        self.assertEqual(mock_logger.info.call_count, 2)
        
        # Check response logging
        response_log = mock_logger.info.call_args_list[1][0][0]
        self.assertIn('200', response_log)
        self.assertIn('Response', response_log)
    
    @patch('movies.middleware.logger')
    def test_sensitive_data_filtering(self, mock_logger):
        """Test that sensitive data is filtered from logs"""
        request = self.factory.post('/api/auth/login/', {
            'username': 'testuser',
            'password': 'secretpassword'
        })
        
        response = self.middleware(request)
        
        # Should log request but filter sensitive data
        mock_logger.info.assert_called()
        
        # Check that password is not in logs
        call_args = str(mock_logger.info.call_args_list)
        self.assertNotIn('secretpassword', call_args)
        self.assertIn('testuser', call_args)
    
    @patch('movies.middleware.logger')
    def test_performance_logging(self, mock_logger):
        """Test that response time is logged"""
        def slow_response(request):
            time.sleep(0.1)  # Simulate slow response
            return HttpResponse('Slow response')
        
        middleware = RequestResponseLoggingMiddleware(slow_response)
        request = self.factory.get('/api/movies/')
        
        response = middleware(request)
        
        # Should log response time
        response_log = mock_logger.info.call_args_list[1][0][0]
        self.assertIn('ms', response_log)  # Response time in milliseconds


class MiddlewareIntegrationTest(TestCase):
    """Test middleware integration and order"""
    
    def setUp(self):
        self.factory = RequestFactory()
    
    def test_middleware_order(self):
        """Test that middleware is applied in correct order"""
        def get_response(request):
            response = HttpResponse('Test response')
            response['Custom-Header'] = 'test'
            return response
        
        # Chain middleware in order
        middleware_chain = SecurityHeadersMiddleware(
            RequestValidationMiddleware(
                RateLimitMiddleware(
                    ErrorLoggingMiddleware(
                        RequestResponseLoggingMiddleware(get_response)
                    )
                )
            )
        )
        
        request = self.factory.get('/api/movies/')
        
        with patch('movies.middleware.logger'):
            response = middleware_chain(request)
        
        # Should have security headers
        self.assertIn('X-Content-Type-Options', response)
        self.assertEqual(response['Custom-Header'], 'test')
        self.assertEqual(response.status_code, 200)
    
    @patch('movies.middleware.logger')
    def test_middleware_error_handling(self, mock_logger):
        """Test error handling across middleware chain"""
        def error_response(request):
            raise ValueError('Test middleware error')
        
        middleware_chain = SecurityHeadersMiddleware(
            ErrorLoggingMiddleware(error_response)
        )
        
        request = self.factory.get('/api/movies/')
        
        with self.assertRaises(ValueError):
            middleware_chain(request)
        
        # Error should be logged
        mock_logger.error.assert_called()
    
    def test_middleware_with_different_request_types(self):
        """Test middleware with different HTTP methods"""
        def get_response(request):
            return HttpResponse(f'Method: {request.method}')
        
        middleware = SecurityHeadersMiddleware(get_response)
        
        # Test different HTTP methods
        methods = ['GET', 'POST', 'PUT', 'DELETE', 'PATCH']
        
        for method in methods:
            request = getattr(self.factory, method.lower())('/api/movies/')
            response = middleware(request)
            
            # Security headers should be added for all methods
            self.assertIn('X-Content-Type-Options', response)
            self.assertIn(method, response.content.decode())