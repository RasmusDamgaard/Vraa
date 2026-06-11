"""
URL configuration for the Vraa project.

This module defines the top‑level URL patterns. It delegates URL
resolution to the ``main`` app for the site's custom pages and
exposes the Django administration interface under the ``/admin/``
prefix.
"""
from __future__ import annotations

from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path, re_path
from django.views.static import serve

urlpatterns = [
    # Admin site URLs
    path('admin/', admin.site.urls),
    # Include URL patterns from the main application
    path('', include('main.urls')),
]

# Serve media files (uploaded documents)
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
else:
    # Low-traffic family site: serve media through Django in production too.
    # LoginRequiredMiddleware gates /media/ so documents stay members-only.
    urlpatterns += [
        re_path(r'^media/(?P<path>.*)$', serve, {'document_root': settings.MEDIA_ROOT}),
    ]
