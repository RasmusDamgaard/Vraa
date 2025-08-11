"""
URL configuration for the ``main`` application.

This module maps relative paths to view functions. Each page in the
site is represented by a dedicated view. The ``path`` definitions
include a ``name`` argument to allow for reverse URL resolution in
templates.
"""
from __future__ import annotations

from django.urls import path

from . import views

app_name = 'main'

urlpatterns = [
    path('', views.frontpage, name='frontpage'),
    path('information/', views.information, name='information'),
    path('referater/', views.referater, name='referater'),
    path('vedtaegter/', views.vedtaegter, name='vedtaegter'),
    path('kalender/', views.kalender, name='kalender'),
]
