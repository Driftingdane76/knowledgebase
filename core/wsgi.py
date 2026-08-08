import os
import sys
from pathlib import Path

# Automatically add pre-built package directory if present on Azure App Service
base_dir = Path(__file__).resolve().parent.parent
site_packages_dir = base_dir / '.python_packages' / 'lib' / 'site-packages'
if site_packages_dir.exists():
    sys.path.insert(0, str(site_packages_dir))

from django.core.wsgi import get_wsgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
application = get_wsgi_application()

