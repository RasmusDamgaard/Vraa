"""
ASGI config for the Vraa project.

It exposes the ASGI callable as a module-level variable named
``application``.

For more information on this file, see
https://docs.djangoproject.com/en/4.0/howto/deployment/asgi/
"""
from __future__ import annotations

import os

from django.core.asgi import get_asgi_application  # type: ignore

# Set the default settings module for the 'django' program.
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'Vraa.settings')

application = get_asgi_application()
