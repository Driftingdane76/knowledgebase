import os
from django.test import TestCase, RequestFactory
from django.core.exceptions import PermissionDenied
from core.middleware import IPWhitelistMiddleware

class IPWhitelistMiddlewareTests(TestCase):
    def setUp(self):
        self.factory = RequestFactory()
        # Mock get_response function
        self.mock_get_response = lambda req: "200 OK"
        
    def test_localhost_ipv4_allowed(self):
        os.environ['ALLOWED_TESTER_IPS'] = '83.166.46.208'
        middleware = IPWhitelistMiddleware(self.mock_get_response)
        request = self.factory.get('/')
        request.META['REMOTE_ADDR'] = '127.0.0.1'
        response = middleware(request)
        self.assertEqual(response, "200 OK")
        
    def test_localhost_ipv6_allowed(self):
        os.environ['ALLOWED_TESTER_IPS'] = '83.166.46.208'
        middleware = IPWhitelistMiddleware(self.mock_get_response)
        request = self.factory.get('/')
        request.META['REMOTE_ADDR'] = '::1'
        response = middleware(request)
        self.assertEqual(response, "200 OK")

    def test_authorized_remote_ip_allowed(self):
        os.environ['ALLOWED_TESTER_IPS'] = '83.166.46.208'
        middleware = IPWhitelistMiddleware(self.mock_get_response)
        request = self.factory.get('/')
        request.META['REMOTE_ADDR'] = '127.0.0.1'
        request.META['HTTP_X_FORWARDED_FOR'] = '83.166.46.208'
        response = middleware(request)
        self.assertEqual(response, "200 OK")

    def test_unauthorized_remote_ip_blocked(self):
        os.environ['ALLOWED_TESTER_IPS'] = '83.166.46.208'
        middleware = IPWhitelistMiddleware(self.mock_get_response)
        request = self.factory.get('/')
        request.META['REMOTE_ADDR'] = '127.0.0.1'
        request.META['HTTP_X_FORWARDED_FOR'] = '99.99.99.99'
        with self.assertRaises(PermissionDenied):
            middleware(request)

    def test_wildcard_allows_all(self):
        os.environ['ALLOWED_TESTER_IPS'] = '*'
        middleware = IPWhitelistMiddleware(self.mock_get_response)
        request = self.factory.get('/')
        request.META['REMOTE_ADDR'] = '127.0.0.1'
        request.META['HTTP_X_FORWARDED_FOR'] = '99.99.99.99'
        response = middleware(request)
        self.assertEqual(response, "200 OK")
