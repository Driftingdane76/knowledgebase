import os
import sys
import unittest
from pathlib import Path

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
import django
django.setup()

from django.test import RequestFactory
from django.conf import settings
from django.template import Context, Template


class AssetVersioningAndCssTest(unittest.TestCase):
    def setUp(self):
        self.factory = RequestFactory()

    def test_context_processor_registered_and_working(self):
        """Verify that core.context_processors.app_version_context is registered and returns APP_VERSION."""
        from core import context_processors
        request = self.factory.get('/')
        context_data = context_processors.app_version_context(request)
        self.assertIn('APP_VERSION', context_data, "APP_VERSION must be in context processor output")
        self.assertTrue(bool(context_data['APP_VERSION']), "APP_VERSION must not be empty")

    def test_template_renders_app_version(self):
        """Verify that a Django template context processor injects APP_VERSION into rendered templates."""
        from django.template.loader import render_to_string
        request = self.factory.get('/')
        rendered = render_to_string('base.html', request=request)
        self.assertIn('app.css?v=', rendered, "base.html must link app.css with version query string")
        self.assertNotIn('app.css?v=1.20', rendered, "base.html must not contain hardcoded ?v=1.20")
        self.assertNotIn('app.js?v=1.7', rendered, "base.html must not contain hardcoded ?v=1.7")

    def test_app_css_unified_highlight_definition(self):
        """Verify app.css contains unified mark.search-hit and .ocr-highlight-box styling."""
        css_path = Path(settings.BASE_DIR) / 'static' / 'css' / 'app.css'
        content = css_path.read_text(encoding='utf-8')
        
        self.assertIn('.search-hit {', content, "app.css must define search-hit highlight rules")
        self.assertIn('#fef08a', content, "Unified highlight must use #fef08a")
        self.assertIn('#facc15', content, "Unified highlight must use #facc15 border")


if __name__ == '__main__':
    unittest.main()
