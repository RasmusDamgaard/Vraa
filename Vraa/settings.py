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

# ALLOWED_HOSTS configuration
# In DEBUG mode, allow localhost and common development hosts
# In production, use environment variable or defaults
if DEBUG:
    ALLOWED_HOSTS = ['localhost', '127.0.0.1', '[::1]', '.localhost']
else:
    # Allow setting ALLOWED_HOSTS via environment variable (comma-separated)
    _allowed_hosts_env = os.environ.get('ALLOWED_HOSTS', '')
    if _allowed_hosts_env:
        ALLOWED_HOSTS = [h.strip() for h in _allowed_hosts_env.split(',') if h.strip()]
    else:
        # Default production hosts
        ALLOWED_HOSTS = [
            'vraa.org',
            'www.vraa.org',
            '.herokuapp.com',  # Allows any Heroku subdomain
        ]

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
    # CSP middleware for Content Security Policy headers
    'csp.middleware.CSPMiddleware',
    # Permissions-Policy middleware
    'main.middleware.PermissionsPolicyMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'main.middleware.LoginRequiredMiddleware',  # Require login for entire site
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
                'main.context_processors.notifications',
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

# Media files (user uploads like documents)
MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# Authentication settings
LOGIN_REDIRECT_URL = '/'
LOGOUT_REDIRECT_URL = '/'
LOGIN_URL = '/login/'
AUTHENTICATION_BACKENDS = [
    'main.backends.EmailOrUsernameBackend',
]

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

# Site URL for email links
SITE_URL = os.environ.get('SITE_URL', 'https://vraa.org')

# =============================================================================
# TEST CONFIGURATION
# =============================================================================
# Special settings for running tests
# Note: Test-specific overrides (ALLOWED_HOSTS, SSL redirect) are applied
# at the end of this file to ensure they override production settings.
import sys
_is_testing = 'test' in sys.argv or 'pytest' in sys.modules
if _is_testing:
    # Use dummy cache to avoid interference
    CACHES = {
        'default': {
            'BACKEND': 'django.core.cache.backends.dummy.DummyCache',
        }
    }
    # Use simpler static files storage (no manifest required)
    STATICFILES_STORAGE = 'django.contrib.staticfiles.storage.StaticFilesStorage'
else:
    # =============================================================================
    # CACHING CONFIGURATION
    # =============================================================================
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

    # Referrer Policy - controls how much referrer info is sent
    SECURE_REFERRER_POLICY = 'strict-origin-when-cross-origin'

    # Cross-Origin Opener Policy - prevents window.opener attacks
    SECURE_CROSS_ORIGIN_OPENER_POLICY = 'same-origin'

# =============================================================================
# CONTENT SECURITY POLICY (CSP) CONFIGURATION
# =============================================================================
# django-csp settings - helps prevent XSS attacks
# These settings apply to both development and production

# Default source for all content types not explicitly configured
CSP_DEFAULT_SRC = ("'self'",)

# Allowed sources for stylesheets
CSP_STYLE_SRC = (
    "'self'",
    "'unsafe-inline'",  # Required for Bootstrap and inline styles
)

# Allowed sources for scripts
CSP_SCRIPT_SRC = (
    "'self'",
    "'unsafe-inline'",  # Required for Bootstrap and inline scripts
)

# Allowed sources for fonts
CSP_FONT_SRC = (
    "'self'",
)

# Allowed sources for images
CSP_IMG_SRC = (
    "'self'",
    "data:",  # For inline images
    "https:",  # Allow external images over HTTPS
)

# Allowed sources for AJAX/fetch requests
CSP_CONNECT_SRC = (
    "'self'",
    "https://api.met.no",  # Weather API if used
)

# Prevent embedding in frames (clickjacking protection)
CSP_FRAME_ANCESTORS = ("'none'",)

# Restrict form submissions to same origin
CSP_FORM_ACTION = ("'self'",)

# Block all object/embed elements (Flash, etc.)
CSP_OBJECT_SRC = ("'none'",)

# Restrict base URI to same origin
CSP_BASE_URI = ("'self'",)

# =============================================================================
# RATE LIMITING CONFIGURATION
# =============================================================================
# Using django-ratelimit to protect API endpoints from abuse
RATELIMIT_ENABLE = True
RATELIMIT_USE_CACHE = 'default'
RATELIMIT_VIEW = 'main.views.ratelimit_error_view'  # Custom error view for rate limit exceeded

# =============================================================================
# SENTRY ERROR TRACKING (Production Only)
# =============================================================================
# Configure Sentry for error tracking and monitoring in production
# Set SENTRY_DSN environment variable to enable
SENTRY_DSN = os.environ.get('SENTRY_DSN')

if not DEBUG and SENTRY_DSN:
    try:
        import sentry_sdk
        from sentry_sdk.integrations.django import DjangoIntegration

        sentry_sdk.init(
            dsn=SENTRY_DSN,
            integrations=[DjangoIntegration()],
            traces_sample_rate=0.1,  # 10% of transactions for performance monitoring
            send_default_pii=False,  # Don't send personally identifiable information
            environment=os.environ.get('ENVIRONMENT', 'production'),
        )
    except ImportError:
        import warnings
        warnings.warn(
            "SENTRY_DSN is set but sentry-sdk is not installed. "
            "Install it with: pip install sentry-sdk",
            RuntimeWarning
        )

# =============================================================================
# PRODUCTION ENVIRONMENT VALIDATION
# =============================================================================
# Validate critical environment variables in production
if not DEBUG and not _is_testing:
    required_env_vars = [
        'SECRET_KEY',
        'DATABASE_URL',
    ]

    missing_vars = [var for var in required_env_vars if not os.environ.get(var)]

    if missing_vars:
        import warnings
        warnings.warn(
            f"Missing required environment variables: {', '.join(missing_vars)}. "
            "Application may not function correctly.",
            RuntimeWarning
        )

    # Validate SECRET_KEY is not the default insecure value
    if SECRET_KEY == 'django-insecure-local-dev-key-change-me':
        raise ValueError(
            "SECRET_KEY is set to the default development value. "
            "Set a secure SECRET_KEY environment variable for production."
        )

# =============================================================================
# TEST OVERRIDES (must come last to override production settings)
# =============================================================================
# These settings are applied after all other settings to ensure tests work
# correctly even when DEBUG=False (e.g., in CI environments)
if _is_testing:
    # Allow test hosts - Django's test client uses 'testserver' by default
    ALLOWED_HOSTS = ['testserver', 'localhost', '127.0.0.1']

    # Disable SSL redirect during tests to avoid 301 redirects
    SECURE_SSL_REDIRECT = False

    # Disable HSTS during tests
    SECURE_HSTS_SECONDS = 0

    # Disable secure cookie settings during tests (test client doesn't use HTTPS)
    SESSION_COOKIE_SECURE = False
    CSRF_COOKIE_SECURE = False