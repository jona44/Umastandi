# core/settings/development.py

from .base import * # Import all from base settings
import os

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

ALLOWED_HOSTS = ['localhost', '127.0.0.1', '0.0.0.0']

# Database for development (SQLite)
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}

# Email backend for development (console output)
EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'

# Optional: Disable CSRF checks for simpler local testing (not recommended for production)
# MIDDLEWARE.insert(0, 'django.middleware.csrf.CsrfViewMiddleware') # Ensure it's there
# if 'django.middleware.csrf.CsrfViewMiddleware' in MIDDLEWARE:
#     MIDDLEWARE.remove('django.middleware.csrf.CsrfViewMiddleware')

# For Django Debug Toolbar (if you use it)
# INSTALLED_APPS += [
#     'debug_toolbar',
# ]
# MIDDLEWARE += [
#     'debug_toolbar.middleware.DebugToolbarMiddleware',
# ]
# INTERNAL_IPS = [
#     '127.0.0.1',
# ]