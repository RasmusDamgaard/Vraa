"""
URL configuration for the Vraa project.

This module defines the top‑level URL patterns. It delegates URL
resolution to the ``main`` app for the site's custom pages and
exposes the Django administration interface under the ``/admin/``
prefix.
"""
from __future__ import annotations

from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    # Admin site URLs
    path('admin/', admin.site.urls),
    # Include URL patterns from the main application
    path('', include('main.urls')),
]
