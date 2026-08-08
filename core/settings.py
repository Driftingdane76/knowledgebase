import os
from pathlib import Path
# pyrefly: ignore [missing-import]
from django.contrib.messages import constants as messages

BASE_DIR = Path(__file__).resolve().parent.parent

# Load local environment configuration if present
env_file = BASE_DIR / '.env'
if env_file.exists():
    with open(env_file, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith('#') and '=' in line:
                key, val = line.split('=', 1)
                os.environ.setdefault(key.strip(), val.strip().strip("'").strip('"'))

DEBUG = os.getenv('DEBUG', 'False').lower() in ('true', '1', 'yes')

from django.core.exceptions import ImproperlyConfigured

SECRET_KEY = os.getenv('SECRET_KEY')
if not SECRET_KEY:
    if DEBUG:
        import getpass
        dev_keys = [
            '7@^k#c!p3+u9_w$m(f5*a1-r8=x2%y4&d0)z6t_v!b*q#s^h',
            'v!a5(z^w8#k*p2)m0+y-r_c3%d&x1=f7@t4$q!s#u^b*h9_e'
        ]
        try:
            # Automatically assign a consistent key based on the user's computer name
            user_hash = len(getpass.getuser())
            SECRET_KEY = dev_keys[user_hash % 2]
        except Exception:
            SECRET_KEY = dev_keys[0]
    else:
        raise ImproperlyConfigured("SECRET_KEY must not be empty in production.")

if DEBUG:
    ALLOWED_HOSTS = ['*']
else:
    ALLOWED_HOSTS = [host.strip() for host in os.getenv('ALLOWED_HOSTS', '').split(',') if host.strip()]
    azure_hostname = os.getenv('WEBSITE_HOSTNAME')
    if azure_hostname and azure_hostname not in ALLOWED_HOSTS:
        ALLOWED_HOSTS.append(azure_hostname)
    if not ALLOWED_HOSTS:
        raise ImproperlyConfigured("ALLOWED_HOSTS must not be empty in production.")



INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'corsheaders',
    'django.contrib.postgres',
    'qa_app',
    'users',
]

MIDDLEWARE = [
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.locale.LocaleMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'core.middleware.IPWhitelistMiddleware',
]

ROOT_URLCONF = 'core.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'core.wsgi.application'
ASGI_APPLICATION = 'core.asgi.application'

db_engine = os.getenv('DB_ENGINE', 'django.db.backends.postgresql')

if 'sqlite' in db_engine:
    db_name = os.getenv('DB_NAME', 'db.sqlite3')
    db_path = BASE_DIR / db_name if not os.path.isabs(db_name) else Path(db_name)
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': db_path,
        }
    }
else:
    DATABASES = {
        'default': {
            'ENGINE': db_engine,
            'NAME': os.getenv('DB_NAME', 'knowledgebase'),
            'USER': os.getenv('DB_USER', 'postgres'),
            'PASSWORD': os.getenv('DB_PASSWORD', 'postgres'),
            'HOST': os.getenv('DB_HOST', '127.0.0.1'),
            'PORT': os.getenv('DB_PORT', '5432'),
            'OPTIONS': {
                'connect_timeout': 10,
            },
            'CONN_MAX_AGE': 60,
        }
    }

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
        'OPTIONS': {
            'min_length': 12,
        }
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]

AUTH_USER_MODEL = 'users.CustomUser'

LOGIN_URL = 'login'

LANGUAGE_CODE = 'da'

LANGUAGES = [
    ('da', 'Danish'),
    ('en', 'English'),
]

LOCALE_PATHS = [
    BASE_DIR / 'locale',
]

TIME_ZONE = 'UTC'
USE_I18N = True
USE_TZ = True

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

if DEBUG:
    CORS_ALLOW_ALL_ORIGINS = True
else:
    CORS_ALLOW_ALL_ORIGINS = False
CSRF_TRUSTED_ORIGINS = [
    'https://*.ngrok-free.app',
    'https://*.ngrok-free.dev',
    'https://*.ngrok.io',
    'https://*.ngrok.app',
    'https://*.trycloudflare.com',
]

azure_hostname = os.getenv('WEBSITE_HOSTNAME')
if azure_hostname:
    azure_origin = f"https://{azure_hostname}"
    if azure_origin not in CSRF_TRUSTED_ORIGINS:
        CSRF_TRUSTED_ORIGINS.append(azure_origin)

env_csrf_origins = os.getenv('CSRF_TRUSTED_ORIGINS', '')
if env_csrf_origins:
    for origin in env_csrf_origins.split(','):
        origin = origin.strip()
        if origin:
            if not origin.startswith(('http://', 'https://')):
                origin = f"https://{origin}"
            if origin not in CSRF_TRUSTED_ORIGINS:
                CSRF_TRUSTED_ORIGINS.append(origin)
DATA_UPLOAD_MAX_MEMORY_SIZE = 104857600  # 100MB for base64 screenshots

# ------------------------------------------------------------------
# Static & Media files
# ------------------------------------------------------------------
STATIC_URL = '/static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'
STATICFILES_DIRS = [
    BASE_DIR / 'static',
]
WHITENOISE_USE_FINDERS = True
MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'


# ------------------------------------------------------------------
# Message tag overrides
# ------------------------------------------------------------------
MESSAGE_TAGS = {
    messages.ERROR: 'danger',
}

# ------------------------------------------------------------------
# Authentication & Security
# ------------------------------------------------------------------
LOGIN_URL = 'login'
LOGIN_REDIRECT_URL = 'index'
LOGOUT_REDIRECT_URL = 'login'

# For local testing, print password reset emails to the console
EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'

# Google reCAPTCHA v3 keys (loaded from .env if present)
RECAPTCHA_PUBLIC_KEY = os.getenv('RECAPTCHA_PUBLIC_KEY', '')
RECAPTCHA_PRIVATE_KEY = os.getenv('RECAPTCHA_PRIVATE_KEY', '')

# ------------------------------------------------------------------
# Session & Idle Timeout Settings
# ------------------------------------------------------------------
# Update the session expiry on every request so active users stay logged in.
# If they do not make a request within SESSION_COOKIE_AGE, they will be logged out.
SESSION_SAVE_EVERY_REQUEST = True
SESSION_COOKIE_AGE = 1209600  # 14 days in seconds

# ------------------------------------------------------------------
# Logging Configuration
# ------------------------------------------------------------------
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '{levelname} {asctime} {module} {process:d} {thread:d} {message}',
            'style': '{',
        },
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'verbose',
        },
    },
    'root': {
        'handlers': ['console'],
        'level': 'INFO',
    },
    'loggers': {
        'django': {
            'handlers': ['console'],
            'level': 'INFO',
            'propagate': False,
        },
    },
}

# ------------------------------------------------------------------
# Production Security & Azure Reverse Proxy Settings
# ------------------------------------------------------------------
# Trust proxy headers forwarded by Azure App Service / Easy Auth
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
USE_X_FORWARDED_HOST = True
USE_X_FORWARDED_PORT = True

if not DEBUG:
    # Enforce secure cookies in production behind Azure's SSL termination
    REQUIRE_HTTPS = os.getenv('REQUIRE_HTTPS', 'True').lower() in ('true', '1', 'yes')
    
    if REQUIRE_HTTPS:
        SESSION_COOKIE_SECURE = True
        CSRF_COOKIE_SECURE = True
        SESSION_COOKIE_HTTPONLY = True
        CSRF_COOKIE_HTTPONLY = False
        SESSION_COOKIE_SAMESITE = 'Lax'
        CSRF_COOKIE_SAMESITE = 'Lax'
