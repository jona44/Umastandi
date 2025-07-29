# core/settings/production.py

from .base import *
import dj_database_url
import os

DEBUG = True # This is why the error occurs

ALLOWED_HOSTS = [
    'umastandi.onrender.com',
    os.environ.get('RENDER_EXTERNAL_HOSTNAME', ''), # For Render deployments
]
ALLOWED_HOSTS = [host for host in ALLOWED_HOSTS if host] # Remove empty strings
# Database for production (PostgreSQL using dj_database_url)
database_url = os.environ.get('DATABASE_URL')
if database_url:
    DATABASES = {
        'default': dj_database_url.parse(database_url)
    }
else:
    # Fallback or error handling if DATABASE_URL is not set
    # You might want to raise an error or set a default behavior
    print("WARNING: DATABASE_URL environment variable is not set for production!")
    # For now, let's keep a default, but in a real scenario, you'd want this to fail loudly.
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3', # THIS IS NOT FOR PRODUCTION USE
            'NAME': BASE_DIR / 'prod_db.sqlite3',
        }
    }


# Security settings
CSRF_COOKIE_SECURE = True
SESSION_COOKIE_SECURE = True
SECURE_SSL_REDIRECT = True # Ensure HTTPS
SECURE_HSTS_SECONDS = 31536000 # 1 year
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True
SECURE_BROWSER_XSS_FILTER = True
X_FRAME_OPTIONS = 'DENY'

# Email backend for production (real SMTP)
# These settings will be picked up from environment variables in base.py
# If you need specific overrides, you can put them here.
# For example, if you use SendGrid/Mailgun specific settings.