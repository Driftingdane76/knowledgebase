import os
from django.core.management.base import BaseCommand
from django.contrib.auth import authenticate, get_user_model
from django.test import RequestFactory

class Command(BaseCommand):
    help = 'Test authentication'

    def handle(self, *args, **options):
        # We need a dummy request for authenticate
        factory = RequestFactory()
        request = factory.post('/admin/login/')
        
        email = "fluencyonlife@gmail.com"
        pwd = "Wtrekker76"
        
        self.stdout.write("--- Testing Authentication ---")
        self.stdout.write(f"Email: {email}")
        
        # Check DB first
        User = get_user_model()
        self.stdout.write(f"Total Users: {User.objects.count()}")
        user_in_db = User.objects.filter(email=email).first()
        if user_in_db:
            self.stdout.write(f"Found user in DB by email: {user_in_db.email}")
            if user_in_db.check_password(pwd):
                self.stdout.write("DB check_password SUCCEEDED")
            else:
                self.stdout.write("DB check_password FAILED")
        else:
            self.stdout.write("NO USER FOUND IN DB WITH THAT EMAIL!")

        # Try authenticate()
        user = authenticate(request, username=email, password=pwd)
        
        if user is not None:
            self.stdout.write(self.style.SUCCESS(f'Authentication SUCCEEDED for user: {user}'))
        else:
            self.stdout.write(self.style.ERROR('Authentication FAILED (authenticate returned None)'))
