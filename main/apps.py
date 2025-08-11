"""
Application configuration for the ``main`` app.

This class is referenced in :mod:`Vraa.settings` to register the
application with Django. It also defines human‑readable labels for the
app and may include runtime setup code in future revisions.
"""
from __future__ import annotations

from django.apps import AppConfig


class MainConfig(AppConfig):
    """Configuration class for the ``main`` application."""

    default_auto_field = 'django.db.models.BigAutoField'
    name = 'main'
    verbose_name = 'Main'
