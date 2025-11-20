"""
URL configuration for the ``main`` application.
"""
from __future__ import annotations
from django.urls import path
from . import views

app_name = 'main'

urlpatterns = [
    path('', views.FrontpageView.as_view(), name='frontpage'),
    path('information/', views.InformationView.as_view(), name='information'),
    path('referater/', views.ReferaterView.as_view(), name='referater'),
    path('vedtaegter/', views.VedtaegterView.as_view(), name='vedtaegter'),
    path('kalender/', views.KalenderView.as_view(), name='kalender'),
]