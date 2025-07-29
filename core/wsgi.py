"""
WSGI config for core project.

It exposes the WSGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/5.2/howto/deployment/wsgi/
"""

import os
from django.core.wsgi import get_wsgi_application

# Use DJANGO_PRODUCTION=true to activate production settings
if os.getenv('DJANGO_PRODUCTION', '').lower() == 'true':
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings.production')
else:
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings.development')  # or just 'core.settings'

application = get_wsgi_application()
