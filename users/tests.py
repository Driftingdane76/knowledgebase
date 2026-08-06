from django.test import TestCase, Client
from django.contrib.auth import get_user_model
from django.urls import reverse
from django.utils import timezone
from datetime import timedelta

from .models import LoginAttempt
from .views import check_rate_limit

User = get_user_model()

class CustomUserManagerTests(TestCase):
    def test_create_user(self):
        user = User.objects.create_user(email='normal@user.com', password='foo')
        self.assertEqual(user.email, 'normal@user.com')
        self.assertTrue(user.is_active)
        self.assertFalse(user.is_staff)
        self.assertFalse(user.is_superuser)
        # Ensure username field doesn't exist or is None
        self.assertFalse(hasattr(user, 'username') and user.username)
        
        with self.assertRaises(ValueError):
            User.objects.create_user(email='', password='foo')

    def test_create_superuser(self):
        admin_user = User.objects.create_superuser(email='super@user.com', password='foo')
        self.assertEqual(admin_user.email, 'super@user.com')
        self.assertTrue(admin_user.is_active)
        self.assertTrue(admin_user.is_staff)
        self.assertTrue(admin_user.is_superuser)

class RateLimiterTests(TestCase):
    def setUp(self):
        self.ip = "127.0.0.1"

    def test_rate_limiter_allows_under_limit(self):
        # Create 4 failed attempts
        for _ in range(4):
            LoginAttempt.objects.create(ip_address=self.ip, username_attempted='test@test.com', was_successful=False)
        self.assertTrue(check_rate_limit(self.ip))

    def test_rate_limiter_blocks_at_limit(self):
        # Create 5 failed attempts
        for _ in range(5):
            LoginAttempt.objects.create(ip_address=self.ip, username_attempted='test@test.com', was_successful=False)
        self.assertFalse(check_rate_limit(self.ip))

    def test_rate_limiter_ignores_successful_attempts(self):
        # Create 5 successful attempts
        for _ in range(5):
            LoginAttempt.objects.create(ip_address=self.ip, username_attempted='test@test.com', was_successful=True)
        self.assertTrue(check_rate_limit(self.ip))

    def test_rate_limiter_ignores_old_attempts(self):
        # Create 5 old failed attempts
        old_time = timezone.now() - timedelta(minutes=20)
        for _ in range(5):
            attempt = LoginAttempt.objects.create(ip_address=self.ip, username_attempted='test@test.com', was_successful=False)
            # Force update timestamp (auto_now_add usually overrides on creation)
            LoginAttempt.objects.filter(pk=attempt.pk).update(timestamp=old_time)
            
        self.assertTrue(check_rate_limit(self.ip))

class AuthViewsTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.login_url = reverse('login')
        # Ensure we use an IP that isn't shared across other tests accidentally
        self.ip = '10.0.0.1'

    def test_login_rate_limiting_view(self):
        # Simulate 5 failed logins via the client
        for _ in range(5):
            response = self.client.post(self.login_url, {'username': 'wrong@test.com', 'password': 'bad'}, REMOTE_ADDR=self.ip)
            self.assertEqual(response.status_code, 200) # Form invalid simply re-renders page
        
        # 6th attempt should be blocked by our rate limiter
        response = self.client.post(self.login_url, {'username': 'wrong@test.com', 'password': 'bad'}, REMOTE_ADDR=self.ip)
        self.assertEqual(response.status_code, 429)
        self.assertContains(response, "Too many failed login attempts", status_code=429)
