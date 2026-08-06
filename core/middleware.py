import os
from django.core.exceptions import PermissionDenied
import logging
from ipware import get_client_ip

logger = logging.getLogger(__name__)

class IPWhitelistMiddleware:
    """
    Middleware that restricts access to the application based on the user's IP address.
    Reads allowed IPs from the ALLOWED_TESTER_IPS environment variable.
    """
    def __init__(self, get_response):
        self.get_response = get_response
        
        # Read allowed IPs from env. Default to 127.0.0.1 for local dev.
        allowed_ips_str = os.getenv('ALLOWED_TESTER_IPS', '127.0.0.1')
        self.allowed_ips = [ip.strip() for ip in allowed_ips_str.split(',') if ip.strip()]

    def __call__(self, request):
        # Allow all if wildcard is set
        if '*' in self.allowed_ips:
            return self.get_response(request)

        client_ip, is_routable = get_client_ip(request)
        if client_ip is None:
            client_ip = ''

        # Always allow localhost (both IPv4 and IPv6) to prevent locking out the local dev browser
        if client_ip not in self.allowed_ips and client_ip not in ['127.0.0.1', '::1']:
            logger.warning(f"Blocked unauthorized IP access attempt from: {client_ip}")
            raise PermissionDenied(f"Access Denied: Your IP address ({client_ip}) is not authorized for testing.")

        return self.get_response(request)

