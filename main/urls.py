"""
URL configuration for the ``main`` application.
"""
from __future__ import annotations

from django.contrib.auth import views as auth_views
from django.urls import path

from . import views

app_name = 'main'

urlpatterns = [
    # Pages
    path('', views.FrontpageView.as_view(), name='frontpage'),
    path('information/', views.InformationView.as_view(), name='information'),
    path('referater/', views.ReferaterView.as_view(), name='referater'),
    path('vedtaegter/', views.VedtaegterView.as_view(), name='vedtaegter'),
    path('kalender/', views.KalenderView.as_view(), name='kalender'),

    # Message board
    path('besked/ny/', views.MessageCreateView.as_view(), name='message_create'),
    path('besked/<int:pk>/rediger/', views.MessageUpdateView.as_view(), name='message_update'),
    path('besked/<int:pk>/slet/', views.MessageDeleteView.as_view(), name='message_delete'),

    # Authentication
    path('login/', auth_views.LoginView.as_view(
        template_name='main/login.html',
        extra_context={'title': 'Log ind'},
    ), name='login'),
    path('logout/', auth_views.LogoutView.as_view(
        next_page='main:frontpage',
    ), name='logout'),
    path('register/', views.RegisterView.as_view(), name='register'),
]
