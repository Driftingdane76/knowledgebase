import os
import time
from django.conf import settings

# Production release identifier (set at startup)
RELEASE_VERSION = os.getenv('APP_VERSION') or os.getenv('WEBSITE_COMMIT_ID') or f"rel-{int(time.time())}"

def app_version_context(request):
    """
    Injects dynamic {{ APP_VERSION }} into all templates for automatic cache-busting.
    """
    return {
        'APP_VERSION': int(time.time()),
    }
