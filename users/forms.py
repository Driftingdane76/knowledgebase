import os
import json
import urllib.request
import urllib.parse
from django import forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError

User = get_user_model()

class CustomUserCreationForm(UserCreationForm):
    recaptcha_token = forms.CharField(widget=forms.HiddenInput(), required=False)

    class Meta(UserCreationForm.Meta):
        model = User
        fields = ('email',)

    def clean(self):
        cleaned_data = super().clean()
        
        # Verify reCAPTCHA v3
        token = cleaned_data.get('recaptcha_token')
        secret_key = os.getenv('RECAPTCHA_PRIVATE_KEY', '')
        
        # Only enforce reCAPTCHA if the key is provided in .env
        if secret_key:
            if not token:
                raise ValidationError("reCAPTCHA verification failed. No token provided.")
            
            try:
                verify_url = 'https://www.google.com/recaptcha/api/siteverify'
                data = urllib.parse.urlencode({
                    'secret': secret_key,
                    'response': token
                }).encode('utf-8')
                
                req = urllib.request.Request(verify_url, data=data)
                with urllib.request.urlopen(req, timeout=5) as response:
                    result = json.loads(response.read().decode())
                
                # Require success and a decent human score
                if not result.get('success') or result.get('score', 0) < 0.5:
                    raise ValidationError("reCAPTCHA score too low. Bot traffic suspected.")
            except Exception:
                raise ValidationError("Failed to communicate with reCAPTCHA service.")
                
        return cleaned_data

class CustomAuthenticationForm(AuthenticationForm):
    """
    Standard authentication form, customized to use Email.
    Rate-limiting logic is handled at the View level to block IPs before they hit the DB.
    """
    username = forms.EmailField(widget=forms.EmailInput(attrs={'autofocus': True}))
