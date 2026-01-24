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

    # Booking system
    path('booking/ny/', views.BookingCreateView.as_view(), name='booking_create'),
    path('booking/<int:pk>/rediger/', views.BookingUpdateView.as_view(), name='booking_update'),
    path('booking/<int:pk>/annuller/', views.BookingDeleteView.as_view(), name='booking_delete'),
    path('api/bookings/', views.BookingAPIView.as_view(), name='booking_api'),

    # Message board
    path('besked/ny/', views.MessageCreateView.as_view(), name='message_create'),
    path('besked/<int:pk>/rediger/', views.MessageUpdateView.as_view(), name='message_update'),
    path('besked/<int:pk>/slet/', views.MessageDeleteView.as_view(), name='message_delete'),

    # Comments
    path('besked/<int:message_pk>/kommentar/', views.CommentCreateView.as_view(), name='comment_create'),
    path('kommentar/<int:pk>/slet/', views.CommentDeleteView.as_view(), name='comment_delete'),

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
