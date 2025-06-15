"""
Custom middleware for security and performance enhancements
"""
import logging
from django.http import HttpResponseForbidden
from django.core.cache import cache
from django.conf import settings
from django.utils.deprecation import MiddlewareMixin
import time

logger = logging.getLogger('django.security')


class SecurityMiddleware(MiddlewareMixin):
    """
    Enhanced security middleware for HSG Notes
    """
    
    def __init__(self, get_response):
        self.get_response = get_response
        super().__init__(get_response)
    
    def process_request(self, request):
        """
        Process incoming requests for security checks
        """
        # Rate limiting based on IP
        client_ip = self.get_client_ip(request)
        
        # Check for suspicious patterns
        if self.is_suspicious_request(request):
            logger.warning(f"Suspicious request from {client_ip}: {request.path}")
            return HttpResponseForbidden("Access denied")
        
        # Rate limiting
        if self.is_rate_limited(client_ip):
            logger.warning(f"Rate limit exceeded for {client_ip}")
            return HttpResponseForbidden("Rate limit exceeded")
        
        return None
    
    def process_response(self, request, response):
        """
        Add security headers to response
        """
        # Add custom security headers
        response['X-Content-Type-Options'] = 'nosniff'
        response['X-Frame-Options'] = 'DENY'
        response['X-XSS-Protection'] = '1; mode=block'
        response['Referrer-Policy'] = 'strict-origin-when-cross-origin'
        response['Permissions-Policy'] = 'geolocation=(), microphone=(), camera=()'
        
        # Add HSG branding header
        response['X-Powered-By'] = 'HSG Notes - HSG Company'
        response['X-Developer'] = 'محمد زياد - HSG Company'
        
        return response
    
    def get_client_ip(self, request):
        """
        Get the real client IP address
        """
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip
    
    def is_suspicious_request(self, request):
        """
        Check for suspicious request patterns
        """
        suspicious_patterns = [
            'wp-admin', 'wp-login', 'phpmyadmin', 'admin.php',
            'xmlrpc.php', '.env', 'config.php', 'shell.php'
        ]
        
        path = request.path.lower()
        return any(pattern in path for pattern in suspicious_patterns)
    
    def is_rate_limited(self, client_ip):
        """
        Simple rate limiting implementation
        """
        cache_key = f"rate_limit_{client_ip}"
        requests = cache.get(cache_key, 0)
        
        if requests >= 100:  # 100 requests per minute
            return True
        
        cache.set(cache_key, requests + 1, 60)  # 60 seconds
        return False


class PerformanceMiddleware(MiddlewareMixin):
    """
    Performance monitoring middleware
    """
    
    def process_request(self, request):
        request.start_time = time.time()
    
    def process_response(self, request, response):
        if hasattr(request, 'start_time'):
            duration = time.time() - request.start_time
            response['X-Response-Time'] = f"{duration:.3f}s"
            
            # Log slow requests
            if duration > 2.0:  # Log requests taking more than 2 seconds
                logger.warning(f"Slow request: {request.path} took {duration:.3f}s")
        
        return response
