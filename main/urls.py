"""
URL configuration for the ``main`` application.
"""
from __future__ import annotations

from django.contrib.auth import views as auth_views
from django.urls import path, reverse_lazy

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

    # ICS Calendar Export
    path('kalender/export/', views.BookingICSFeedView.as_view(), name='calendar_ics_feed'),
    path('booking/<int:pk>/ics/', views.BookingICSView.as_view(), name='booking_ics'),

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

    # Documentation
    path('brugervejledning/', views.BrugervejledningView.as_view(), name='brugervejledning'),
    path('admin-vejledning/', views.AdminVejledningView.as_view(), name='admin_vejledning'),

    # User profile
    path('profil/', views.ProfileView.as_view(), name='profile'),

    # Notifications
    path('notifikationer/', views.NotificationListView.as_view(), name='notifications'),
    path('notifikationer/<int:pk>/laest/', views.NotificationMarkReadView.as_view(), name='notification_mark_read'),
    path('notifikationer/laes-alle/', views.NotificationMarkAllReadView.as_view(), name='notification_mark_all_read'),

    # Password reset flow
    path('password-reset/',
         auth_views.PasswordResetView.as_view(
             template_name='main/password_reset.html',
             email_template_name='main/password_reset_email.html',
             subject_template_name='main/password_reset_subject.txt',
             success_url=reverse_lazy('main:password_reset_done'),
             extra_context={'title': 'Nulstil adgangskode'},
         ),
         name='password_reset'),
    path('password-reset/done/',
         auth_views.PasswordResetDoneView.as_view(
             template_name='main/password_reset_done.html',
             extra_context={'title': 'E-mail sendt'},
         ),
         name='password_reset_done'),
    path('password-reset/<uidb64>/<token>/',
         auth_views.PasswordResetConfirmView.as_view(
             template_name='main/password_reset_confirm.html',
             success_url=reverse_lazy('main:password_reset_complete'),
             extra_context={'title': 'Ny adgangskode'},
         ),
         name='password_reset_confirm'),
    path('password-reset/complete/',
         auth_views.PasswordResetCompleteView.as_view(
             template_name='main/password_reset_complete.html',
             extra_context={'title': 'Adgangskode nulstillet'},
         ),
         name='password_reset_complete'),

    # Admin dashboard (staff only)
    path('admin-dashboard/brugere/', views.UserManagementView.as_view(), name='user_management'),
    path('admin-dashboard/brugere/<int:pk>/aktiver/', views.UserActivateView.as_view(), name='user_activate'),
    path('admin-dashboard/brugere/<int:pk>/deaktiver/', views.UserDeactivateView.as_view(), name='user_deactivate'),
    path('admin-dashboard/aktivitetslog/', views.AuditLogListView.as_view(), name='audit_log'),
]
