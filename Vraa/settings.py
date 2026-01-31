"""
Django settings for the Vraa project.
Refactored for Heroku Deployment.
"""
from __future__ import annotations

import os
from pathlib import Path
import dj_database_url

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

# SECURITY WARNING: keep the secret key used in production secret!
# We get this from the Environment Variable on Heroku. 
# If not found (local dev), we use a fallback insecure key.
SECRET_KEY = os.environ.get('SECRET_KEY', 'django-insecure-local-dev-key-change-me')

# SECURITY WARNING: don't run with debug turned on in production!
# CHANGE: Default to 'True' locally so you can develop without crashing.
# On Heroku, you set DEBUG=False in the config, so it will be safe there.
DEBUG = os.environ.get('DEBUG', 'True') == 'True'

# ALLOWED_HOSTS needed for production
ALLOWED_HOSTS = ['*']
# For stricter security in future:
# ALLOWED_HOSTS = ['vraa.org', 'www.vraa.org', 'your-app-name.herokuapp.com', '127.0.0.1', 'localhost']

# Application definition
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    # WhiteNoise must be before staticfiles
    'whitenoise.runserver_nostatic', 
    'django.contrib.staticfiles',
    # Local apps
    'main',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    # WhiteNoiseMiddleware sits after SecurityMiddleware
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'Vraa.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
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

WSGI_APPLICATION = 'Vraa.wsgi.application'

# Database
# Switches between Postgres (production) and SQLite (local) automatically
DATABASES = {
    'default': dj_database_url.config(
        default=f"sqlite:///{BASE_DIR / 'db.sqlite3'}",
        conn_max_age=600
    )
}

# Password validation
AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]

# Internationalization
LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'Europe/Copenhagen'
USE_I18N = True
USE_TZ = True

# Static files (CSS, JavaScript, Images)
STATIC_URL = '/static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'
# Note: We don't need STATICFILES_DIRS because Django's AppDirectoriesFinder
# automatically finds static files in main/static/. Adding main/static/ to
# STATICFILES_DIRS would cause duplicate file warnings during collectstatic.

# Enable WhiteNoise compression and caching support
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# Authentication settings
LOGIN_REDIRECT_URL = '/'
LOGOUT_REDIRECT_URL = '/'
LOGIN_URL = '/login/'

# =============================================================================
# EMAIL CONFIGURATION
# =============================================================================
# Configure email settings for notifications (e.g., new user registration alerts)
# For production, set these environment variables in Heroku:
# - EMAIL_HOST, EMAIL_PORT, EMAIL_HOST_USER, EMAIL_HOST_PASSWORD, EMAIL_USE_TLS
EMAIL_BACKEND = os.environ.get(
    'EMAIL_BACKEND',
    'django.core.mail.backends.console.EmailBackend'  # Prints to console in development
)
EMAIL_HOST = os.environ.get('EMAIL_HOST', 'smtp.gmail.com')
EMAIL_PORT = int(os.environ.get('EMAIL_PORT', '587'))
EMAIL_USE_TLS = os.environ.get('EMAIL_USE_TLS', 'True') == 'True'
EMAIL_HOST_USER = os.environ.get('EMAIL_HOST_USER', '')
EMAIL_HOST_PASSWORD = os.environ.get('EMAIL_HOST_PASSWORD', '')
DEFAULT_FROM_EMAIL = os.environ.get('DEFAULT_FROM_EMAIL', 'noreply@vraa.org')

# =============================================================================
# CACHING CONFIGURATION
# =============================================================================
# Use dummy cache during tests to avoid interference, local memory cache otherwise
import sys
if 'test' in sys.argv:
    CACHES = {
        'default': {
            'BACKEND': 'django.core.cache.backends.dummy.DummyCache',
        }
    }
else:
    # Local memory cache for development, can upgrade to Redis in production
    CACHES = {
        'default': {
            'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
            'LOCATION': 'vraa-cache',
        }
    }

# =============================================================================
# PRODUCTION SECURITY SETTINGS
# =============================================================================
# These settings are only applied when DEBUG is False (production environment)

if not DEBUG:
    # Restrict allowed hosts to actual domains
    ALLOWED_HOSTS = [
        'vraa.org',
        'www.vraa.org',
        '.herokuapp.com',  # Allows any Heroku subdomain
    ]

    # HTTPS/SSL Settings
    SECURE_SSL_REDIRECT = True  # Redirect all HTTP requests to HTTPS
    SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')  # Trust Heroku's proxy

    # HTTP Strict Transport Security (HSTS)
    # Tells browsers to only use HTTPS for this domain
    SECURE_HSTS_SECONDS = 31536000  # 1 year
    SECURE_HSTS_INCLUDE_SUBDOMAINS = True
    SECURE_HSTS_PRELOAD = True  # Allow inclusion in browser preload lists

    # Secure Cookies
    SESSION_COOKIE_SECURE = True  # Only send session cookie over HTTPS
    CSRF_COOKIE_SECURE = True  # Only send CSRF cookie over HTTPS

    # Additional Security Headers
    SECURE_CONTENT_TYPE_NOSNIFF = True  # Prevent MIME type sniffing
    X_FRAME_OPTIONS = 'DENY'  # Prevent clickjacking (already set by middleware, explicit here)