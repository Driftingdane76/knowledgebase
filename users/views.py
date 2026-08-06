from django.shortcuts import render, redirect
from django.urls import reverse_lazy
from django.contrib.auth import views as auth_views
from django.contrib.auth import login
from django.views.generic import CreateView
from django.utils import timezone
from datetime import timedelta
from django.http import HttpResponse

from .forms import CustomUserCreationForm, CustomAuthenticationForm
from .models import LoginAttempt

def get_client_ip(request):
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        return x_forwarded_for.split(',')[0].strip()
    return request.META.get('REMOTE_ADDR')

def check_rate_limit(ip_address):
    """
    Blocks IPs with 5 or more failed attempts in the last 15 minutes.
    """
    time_threshold = timezone.now() - timedelta(minutes=15)
    recent_failures = LoginAttempt.objects.filter(
        ip_address=ip_address,
        was_successful=False,
        timestamp__gte=time_threshold
    ).count()
    
    if recent_failures >= 5:
        return False
    return True

class CustomLoginView(auth_views.LoginView):
    form_class = CustomAuthenticationForm
    template_name = 'users/login.html'
    
    def dispatch(self, request, *args, **kwargs):
        ip = get_client_ip(request)
        if not check_rate_limit(ip):
            return HttpResponse(
                "Too many failed login attempts. Please try again in 15 minutes.", 
                status=429
            )
        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        # Record successful login
        ip = get_client_ip(self.request)
        LoginAttempt.objects.create(
            ip_address=ip,
            username_attempted=form.cleaned_data.get('username', ''),
            was_successful=True
        )
        return super().form_valid(form)

    def form_invalid(self, form):
        # Record failed login
        ip = get_client_ip(self.request)
        username = self.request.POST.get('username', '')
        LoginAttempt.objects.create(
            ip_address=ip,
            username_attempted=username,
            was_successful=False
        )
        return super().form_invalid(form)

class RegisterView(CreateView):
    form_class = CustomUserCreationForm
    template_name = 'users/register.html'
    success_url = reverse_lazy('index')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        from django.conf import settings
        context['recaptcha_public_key'] = getattr(settings, 'RECAPTCHA_PUBLIC_KEY', '')
        return context

    def form_valid(self, form):
        user = form.save()
        login(self.request, user)
        return redirect(self.success_url)
