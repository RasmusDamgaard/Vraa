"""
View classes for the ``main`` application.
"""
from __future__ import annotations

import logging

from django.conf import settings
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.contrib.auth.models import User
from django.core.mail import send_mail
from django.http import HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404
from django.urls import reverse_lazy
from django.utils import timezone
from django.utils.decorators import method_decorator
from django.views import View
from django.views.decorators.cache import cache_page
from django.views.generic import CreateView, DeleteView, DetailView, ListView, TemplateView, UpdateView
from django_ratelimit.decorators import ratelimit
from django_ratelimit.exceptions import Ratelimited

from .forms import BookingForm, CustomUserCreationForm, UserProfileForm
from .models import AuditLog, Booking, Comment, Document, HeritageLine, MaintenanceRequest, Message, Notification, ReservedWeek, UserProfile
from .services import AuditService, NotificationService, WeatherService

logger = logging.getLogger(__name__)


class FrontpageView(ListView):
    """Display the frontpage with the message board."""

    model = Message
    template_name = 'main/frontpage.html'
    context_object_name = 'message_list'
    paginate_by = 20
    extra_context = {'title': 'Forside'}

    def get_queryset(self):
        # Optimize queries: prefetch comments and their authors with profiles
        # Messages are ordered by -is_pinned, -pinned_at, -created_at (in model Meta)
        return Message.objects.select_related('author', 'author__profile').prefetch_related(
            'comments',
            'comments__author',
            'comments__author__profile',
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Separate pinned and regular messages for template
        all_messages = list(context['message_list'])
        context['pinned_messages'] = [m for m in all_messages if m.is_pinned]
        context['regular_messages'] = [m for m in all_messages if not m.is_pinned]
        return context


class InformationView(TemplateView):
    """Display information page with weather widget."""

    template_name = 'main/information.html'
    extra_context = {'title': 'Information'}

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Add weather data (cached in WeatherService)
        context['weather'] = WeatherService.get_weather()
        return context


@method_decorator(cache_page(60 * 60), name='dispatch')
class ReferaterView(TemplateView):
    template_name = 'main/referater.html'
    extra_context = {'title': 'Referater'}


@method_decorator(cache_page(60 * 60), name='dispatch')
class VedtaegterView(TemplateView):
    template_name = 'main/vedtaegter.html'
    extra_context = {'title': 'Vedtægter'}


class KalenderView(LoginRequiredMixin, ListView):
    """Display calendar with bookings and reserved weeks."""

    model = Booking
    template_name = 'main/kalender.html'
    context_object_name = 'bookings'
    extra_context = {'title': 'Kalender'}

    def get_queryset(self):
        return Booking.objects.filter(
            status__in=['pending', 'confirmed'],
            end_date__gte=timezone.now().date(),
        ).select_related('user', 'user__profile', 'user__profile__heritage_line')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Add heritage lines for the legend
        context['heritage_lines'] = HeritageLine.objects.all().order_by('order')
        return context


class RegisterView(CreateView):
    """User registration with admin approval workflow."""

    form_class = CustomUserCreationForm
    template_name = 'main/register.html'
    success_url = reverse_lazy('main:login')
    extra_context = {'title': 'Registrer'}

    def form_valid(self, form):
        response = super().form_valid(form)
        # Set user as inactive until admin approves
        self.object.is_active = False
        self.object.save()
        messages.success(
            self.request,
            'Din konto er oprettet og afventer godkendelse af administrator.',
        )
        # Send email notification to admin users
        self._notify_admins(self.object)
        return response

    def _notify_admins(self, new_user):
        """Send email notification to all admin users about a new registration."""
        # Get all staff users with email addresses
        admin_emails = list(
            User.objects.filter(is_staff=True, is_active=True)
            .exclude(email='')
            .values_list('email', flat=True)
        )

        if not admin_emails:
            logger.warning('No admin email addresses configured for registration notifications')
            return

        subject = f'Ny bruger registreret: {new_user.username}'
        message = (
            f'En ny bruger har registreret sig på Vraa-hjemmesiden.\n\n'
            f'Brugernavn: {new_user.username}\n'
            f'E-mail: {new_user.email}\n'
            f'Tidspunkt: {timezone.now().strftime("%d. %B %Y kl. %H:%M")}\n\n'
            f'Brugeren er inaktiv og afventer godkendelse.\n'
            f'Log ind på admin-panelet for at aktivere kontoen.'
        )

        try:
            send_mail(
                subject=subject,
                message=message,
                from_email=settings.DEFAULT_FROM_EMAIL if hasattr(settings, 'DEFAULT_FROM_EMAIL') else None,
                recipient_list=admin_emails,
                fail_silently=True,
            )
            logger.info(f'Registration notification sent for user {new_user.username}')
        except Exception as e:
            logger.error(f'Failed to send registration notification: {e}')


class MessageCreateView(LoginRequiredMixin, CreateView):
    """Create a new message (authenticated users only)."""

    model = Message
    fields = ['content']
    template_name = 'main/message_form.html'
    success_url = reverse_lazy('main:frontpage')
    extra_context = {'title': 'Ny besked'}

    def form_valid(self, form):
        form.instance.author = self.request.user
        response = super().form_valid(form)

        # Notify users about new message
        NotificationService.notify_new_message(self.object)

        # Check for @mentions
        NotificationService.parse_and_notify_mentions(
            self.object.content,
            self.request.user,
            self.object,
        )

        return response


class MessageUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    """Edit a message (author only)."""

    model = Message
    fields = ['content']
    template_name = 'main/message_form.html'
    success_url = reverse_lazy('main:frontpage')
    extra_context = {'title': 'Rediger besked'}

    def test_func(self):
        return self.get_object().author == self.request.user


class MessageDeleteView(LoginRequiredMixin, UserPassesTestMixin, DeleteView):
    """Delete a message (author only)."""

    model = Message
    template_name = 'main/message_confirm_delete.html'
    success_url = reverse_lazy('main:frontpage')
    extra_context = {'title': 'Slet besked'}

    def test_func(self):
        return self.get_object().author == self.request.user


class CommentCreateView(LoginRequiredMixin, CreateView):
    """Create a new comment on a message (authenticated users only)."""

    model = Comment
    fields = ['content']
    template_name = 'main/comment_form.html'
    extra_context = {'title': 'Tilføj kommentar'}

    def form_valid(self, form):
        from django.shortcuts import render

        form.instance.author = self.request.user
        form.instance.message_id = self.kwargs['message_pk']
        self.object = form.save()

        # Send notification to the message author
        message = Message.objects.get(pk=self.kwargs['message_pk'])
        NotificationService.notify_comment_on_message(message, self.object)

        # Check for @mentions in comment
        NotificationService.parse_and_notify_mentions(
            self.object.content,
            self.request.user,
            self.object,
        )

        # If HTMX request, return partial template
        if self.request.headers.get('HX-Request'):
            return render(self.request, 'main/partials/comment.html', {
                'comment': self.object,
                'user': self.request.user,
            })

        return super().form_valid(form)

    def get_success_url(self):
        return reverse_lazy('main:frontpage')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['message'] = Message.objects.get(pk=self.kwargs['message_pk'])
        return context


class CommentDeleteView(LoginRequiredMixin, UserPassesTestMixin, DeleteView):
    """Delete a comment (author only)."""

    model = Comment
    template_name = 'main/comment_confirm_delete.html'
    success_url = reverse_lazy('main:frontpage')
    extra_context = {'title': 'Slet kommentar'}

    def test_func(self):
        return self.get_object().author == self.request.user

    def delete(self, request, *args, **kwargs):
        """Handle DELETE request with HTMX support."""
        self.object = self.get_object()
        self.object.delete()

        # If HTMX request, return empty response to remove element
        if request.headers.get('HX-Request'):
            return HttpResponse(status=200)

        return HttpResponse(status=302, headers={'Location': self.success_url})


class BookingCreateView(LoginRequiredMixin, CreateView):
    """Create a new booking."""

    model = Booking
    form_class = BookingForm
    template_name = 'main/booking_form.html'
    extra_context = {'title': 'Ny booking'}

    def get_initial(self):
        initial = super().get_initial()
        # Pre-fill dates from query parameters (for click-to-book calendar)
        if 'start' in self.request.GET:
            initial['start_date'] = self.request.GET['start']
        if 'end' in self.request.GET:
            initial['end_date'] = self.request.GET['end']
        return initial

    def get_success_url(self):
        # Redirect to booking detail page for print/confirmation
        return reverse_lazy('main:booking_detail', kwargs={'pk': self.object.pk})

    def form_valid(self, form):
        form.instance.user = self.request.user
        form.instance.status = 'pending'
        messages.success(
            self.request,
            'Din booking er oprettet og afventer godkendelse af administrator.',
        )
        return super().form_valid(form)


class BookingUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    """Edit a booking (owner only, pending bookings only)."""

    model = Booking
    form_class = BookingForm
    template_name = 'main/booking_form.html'
    success_url = reverse_lazy('main:kalender')
    extra_context = {'title': 'Rediger booking'}

    def test_func(self):
        booking = self.get_object()
        return booking.user == self.request.user and booking.status == 'pending'


class BookingDeleteView(LoginRequiredMixin, UserPassesTestMixin, DeleteView):
    """Cancel a booking (owner only)."""

    model = Booking
    template_name = 'main/booking_confirm_delete.html'
    success_url = reverse_lazy('main:kalender')
    extra_context = {'title': 'Annuller booking'}

    def test_func(self):
        return self.get_object().user == self.request.user


class BookingDetailView(LoginRequiredMixin, DetailView):
    """Display booking confirmation/details (printable)."""

    model = Booking
    template_name = 'main/booking_confirmation_print.html'
    context_object_name = 'booking'
    extra_context = {'title': 'Bookingbekræftelse'}

    def get_queryset(self):
        # Only show user's own bookings or all bookings for staff
        if self.request.user.is_staff:
            return Booking.objects.select_related('user', 'user__profile', 'user__profile__heritage_line')
        return Booking.objects.filter(user=self.request.user).select_related(
            'user', 'user__profile', 'user__profile__heritage_line'
        )


@method_decorator(ratelimit(key='user', rate='60/h', method='GET', block=True), name='get')
class BookingAPIView(LoginRequiredMixin, View):
    """API endpoint for calendar data (JSON) with rate limiting, including reserved weeks."""

    def get(self, request):
        from datetime import datetime, timedelta
        from django.urls import reverse

        bookings = Booking.objects.filter(
            status__in=['pending', 'confirmed'],
        ).select_related('user', 'user__profile', 'user__profile__heritage_line')

        events = []
        for booking in bookings:
            is_owner = booking.user == request.user
            can_edit = is_owner and booking.status == 'pending'

            # Use display name if profile exists, otherwise fall back to username
            if hasattr(booking.user, 'profile'):
                title = booking.user.profile.get_display_name()
            else:
                title = booking.user.username

            # Get booking color based on status and heritage line
            color = self._get_booking_color(booking)

            events.append({
                'id': f'booking-{booking.pk}',
                'title': title,
                'start': booking.start_date.isoformat(),
                'end': booking.end_date.isoformat(),
                'color': color,
                'extendedProps': {
                    'type': 'booking',
                    'status': booking.status,
                    'status_display': booking.get_status_display(),
                    'is_owner': is_owner,
                    'notes': booking.notes or '',
                    'duration': booking.duration_days,
                    'created_at': booking.created_at.strftime('%d. %B %Y'),
                    'edit_url': reverse('main:booking_update', args=[booking.pk]) if can_edit else '',
                    'delete_url': reverse('main:booking_delete', args=[booking.pk]) if is_owner else '',
                    'heritage_line': (
                        booking.user.profile.heritage_line.short_name
                        if hasattr(booking.user, 'profile') and booking.user.profile.heritage_line
                        else None
                    ),
                },
            })

        # Add reserved weeks to the calendar
        start_str = request.GET.get('start')
        end_str = request.GET.get('end')

        if start_str and end_str:
            try:
                start_date = datetime.fromisoformat(start_str.replace('Z', '+00:00')).date()
                end_date = datetime.fromisoformat(end_str.replace('Z', '+00:00')).date()
            except ValueError:
                # Fallback: show reserved weeks for current year +/- 1 year
                today = datetime.now().date()
                start_date = today.replace(month=1, day=1)
                end_date = today.replace(month=12, day=31)
        else:
            # No date range provided, use sensible defaults
            today = datetime.now().date()
            start_date = today - timedelta(days=30)
            end_date = today + timedelta(days=365)

        reserved_weeks = ReservedWeek.get_reserved_for_date_range(start_date, end_date)

        for reservation in reserved_weeks:
            # End date needs +1 day for FullCalendar to show correctly
            events.append({
                'id': f'reserved-{reservation.pk}',
                'title': f'{reservation.heritage_line.short_name} - Reserveret',
                'start': reservation.start_date.isoformat(),
                'end': (reservation.end_date + timedelta(days=1)).isoformat(),
                'color': reservation.heritage_line.color,
                'display': 'background',  # Shows as background event
                'extendedProps': {
                    'type': 'reserved_week',
                    'heritage_line': reservation.heritage_line.short_name,
                    'heritage_line_name': reservation.heritage_line.name,
                    'week_number': reservation.week_number,
                    'is_locked': reservation.is_locked,
                },
            })

        return JsonResponse(events, safe=False)

    def _get_booking_color(self, booking):
        """Get color for booking based on status and heritage line."""
        if booking.status == 'pending':
            return '#ffc107'  # Yellow for pending
        if hasattr(booking.user, 'profile') and booking.user.profile.heritage_line:
            return booking.user.profile.heritage_line.color
        return '#28a745'  # Default green for confirmed


@method_decorator(cache_page(60 * 60), name='dispatch')
class BrugervejledningView(TemplateView):
    """User guide page accessible to all visitors."""

    template_name = 'main/brugervejledning.html'
    extra_context = {'title': 'Brugervejledning'}


class AdminVejledningView(LoginRequiredMixin, UserPassesTestMixin, TemplateView):
    """Admin guide page accessible only to staff users."""

    template_name = 'main/admin_vejledning.html'
    extra_context = {'title': 'Admin Vejledning'}
    login_url = reverse_lazy('main:login')

    def test_func(self):
        return self.request.user.is_staff


class ProfileView(LoginRequiredMixin, TemplateView):
    """Display user profile with their bookings."""

    template_name = 'main/profile.html'
    extra_context = {'title': 'Min profil'}

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        today = timezone.now().date()

        # Ensure user has a profile
        if not hasattr(user, 'profile'):
            UserProfile.objects.create(user=user)

        # Separate bookings by time and status
        context['upcoming_bookings'] = Booking.objects.filter(
            user=user,
            end_date__gte=today,
            status__in=['pending', 'confirmed'],
        ).select_related('user').order_by('start_date')

        context['past_bookings'] = Booking.objects.filter(
            user=user,
            end_date__lt=today,
        ).select_related('user').order_by('-start_date')[:10]

        context['cancelled_bookings'] = Booking.objects.filter(
            user=user,
            status='cancelled',
        ).select_related('user').order_by('-created_at')[:5]

        # User statistics
        context['total_bookings'] = Booking.objects.filter(user=user).count()
        context['total_messages'] = Message.objects.filter(author=user).count()
        context['total_comments'] = Comment.objects.filter(author=user).count()

        return context


class ProfileEditView(LoginRequiredMixin, UpdateView):
    """Allow users to edit their display name and bio."""

    model = UserProfile
    form_class = UserProfileForm
    template_name = 'main/profile_edit.html'
    success_url = reverse_lazy('main:profile')
    extra_context = {'title': 'Rediger profil'}

    def get_object(self, queryset=None):
        """Return the current user's profile, creating one if needed."""
        user = self.request.user
        profile, created = UserProfile.objects.get_or_create(user=user)
        return profile

    def form_valid(self, form):
        messages.success(self.request, 'Din profil er opdateret.')
        return super().form_valid(form)


class BookingICSView(LoginRequiredMixin, View):
    """Generate ICS file for a single booking or all bookings."""

    def get(self, request, pk=None):
        if pk:
            # Single booking export
            booking = get_object_or_404(Booking, pk=pk)
            bookings = [booking]
            filename = f'vraa-booking-{pk}.ics'
        else:
            # All confirmed bookings
            bookings = Booking.objects.filter(status='confirmed').select_related('user')
            filename = 'vraa-bookinger.ics'

        # Generate ICS content
        ics_content = self._generate_ics(bookings)

        response = HttpResponse(ics_content, content_type='text/calendar')
        response['Content-Disposition'] = f'attachment; filename="{filename}"'
        return response

    def _generate_ics(self, bookings):
        """Generate ICS formatted calendar."""
        lines = [
            'BEGIN:VCALENDAR',
            'VERSION:2.0',
            'PRODID:-//Vraa//Booking System//DA',
            'CALSCALE:GREGORIAN',
            'METHOD:PUBLISH',
            'X-WR-CALNAME:Vraa Bookinger',
        ]

        for booking in bookings:
            uid = f'booking-{booking.pk}@vraa.dk'
            dtstart = booking.start_date.strftime('%Y%m%d')
            dtend = booking.end_date.strftime('%Y%m%d')
            dtstamp = booking.created_at.strftime('%Y%m%dT%H%M%SZ')
            summary = f'Vraa: {booking.user.username}'
            description = booking.notes.replace('\n', '\\n') if booking.notes else ''

            lines.extend([
                'BEGIN:VEVENT',
                f'UID:{uid}',
                f'DTSTART;VALUE=DATE:{dtstart}',
                f'DTEND;VALUE=DATE:{dtend}',
                f'DTSTAMP:{dtstamp}',
                f'SUMMARY:{summary}',
            ])

            if description:
                lines.append(f'DESCRIPTION:{description}')

            lines.append('END:VEVENT')

        lines.append('END:VCALENDAR')
        return '\r\n'.join(lines)


class BookingICSFeedView(LoginRequiredMixin, View):
    """
    ICS feed URL for calendar subscription.
    Returns all confirmed bookings.
    """

    def get(self, request):
        # All confirmed bookings
        bookings = Booking.objects.filter(
            status='confirmed',
        ).select_related('user')

        # Generate ICS using the helper from BookingICSView
        ics_view = BookingICSView()
        ics_content = ics_view._generate_ics(bookings)

        response = HttpResponse(ics_content, content_type='text/calendar')
        response['Content-Disposition'] = 'inline; filename="vraa-calendar.ics"'
        return response


class NotificationListView(LoginRequiredMixin, ListView):
    """Display user's notifications."""

    model = Notification
    template_name = 'main/notifications.html'
    context_object_name = 'notifications'
    paginate_by = 20
    extra_context = {'title': 'Notifikationer'}

    def get_queryset(self):
        return Notification.objects.filter(user=self.request.user)


class NotificationMarkReadView(LoginRequiredMixin, View):
    """Mark notification as read (AJAX)."""

    def post(self, request, pk):
        notification = get_object_or_404(
            Notification, pk=pk, user=request.user
        )
        notification.is_read = True
        notification.save()
        return JsonResponse({'success': True})


class NotificationMarkAllReadView(LoginRequiredMixin, View):
    """Mark all notifications as read."""

    def post(self, request):
        Notification.objects.filter(
            user=request.user, is_read=False
        ).update(is_read=True)

        # Check if this is an AJAX request
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({'success': True})

        return HttpResponse(status=204)


# =============================================================================
# ADMIN DASHBOARD VIEWS
# =============================================================================


class UserManagementView(LoginRequiredMixin, UserPassesTestMixin, ListView):
    """Dashboard for managing users (staff only)."""

    model = User
    template_name = 'main/user_management.html'
    context_object_name = 'users'
    extra_context = {'title': 'Brugerstyring'}

    def test_func(self):
        return self.request.user.is_staff

    def get_queryset(self):
        return User.objects.all().order_by('-date_joined')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['pending_users'] = User.objects.filter(is_active=False).order_by('-date_joined')
        context['active_users'] = User.objects.filter(is_active=True).order_by('username')
        context['total_users'] = User.objects.count()
        context['pending_count'] = context['pending_users'].count()
        context['active_count'] = context['active_users'].count()
        return context


class UserActivateView(LoginRequiredMixin, UserPassesTestMixin, View):
    """Activate a pending user (staff only)."""

    def test_func(self):
        return self.request.user.is_staff

    def post(self, request, pk):
        user = get_object_or_404(User, pk=pk)
        user.is_active = True
        user.save()

        # Log the action
        AuditService.log_user_activated(request, user)

        # Send welcome email
        if user.email:
            try:
                send_mail(
                    subject='Din konto er aktiveret - Vraa',
                    message=(
                        f'Hej {user.username},\n\n'
                        f'Din konto på Vraa-hjemmesiden er nu aktiveret.\n'
                        f'Du kan nu logge ind og bruge siden.\n\n'
                        f'Venlig hilsen,\nVraa'
                    ),
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    recipient_list=[user.email],
                    fail_silently=True,
                )
            except Exception as e:
                logger.error(f'Failed to send activation email: {e}')

        messages.success(request, f'Brugeren {user.username} er nu aktiveret.')
        return HttpResponse(status=204, headers={'HX-Trigger': 'userUpdated'})


class UserDeactivateView(LoginRequiredMixin, UserPassesTestMixin, View):
    """Deactivate a user (staff only)."""

    def test_func(self):
        return self.request.user.is_staff

    def post(self, request, pk):
        user = get_object_or_404(User, pk=pk)
        if user == request.user:
            messages.error(request, 'Du kan ikke deaktivere din egen konto.')
            return HttpResponse(status=400)

        user.is_active = False
        user.save()

        # Log the action
        AuditService.log_user_deactivated(request, user)

        messages.success(request, f'Brugeren {user.username} er nu deaktiveret.')
        return HttpResponse(status=204, headers={'HX-Trigger': 'userUpdated'})


class AuditLogListView(LoginRequiredMixin, UserPassesTestMixin, ListView):
    """View audit logs (staff only)."""

    model = AuditLog
    template_name = 'main/audit_log.html'
    context_object_name = 'logs'
    paginate_by = 50
    extra_context = {'title': 'Aktivitetslog'}

    def test_func(self):
        return self.request.user.is_staff

    def get_queryset(self):
        queryset = AuditLog.objects.select_related('user')

        # Filter by action if specified
        action = self.request.GET.get('action')
        if action:
            queryset = queryset.filter(action=action)

        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['action_choices'] = AuditLog.ACTION_CHOICES
        context['selected_action'] = self.request.GET.get('action', '')
        return context


class ReferaterDynamicView(TemplateView):
    """Display referater from database with fallback to static files."""

    template_name = 'main/referater.html'
    extra_context = {'title': 'Referater'}

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # Get documents from database
        documents = Document.objects.filter(category='referat')

        # Group by year
        years = {}
        for doc in documents:
            year = doc.document_date.year
            if year not in years:
                years[year] = []
            years[year].append(doc)

        context['documents_by_year'] = dict(sorted(years.items(), reverse=True))
        context['has_dynamic_documents'] = documents.exists()
        return context


class VedtaegterDynamicView(TemplateView):
    """Display vedtaegter from database with fallback to static files."""

    template_name = 'main/vedtaegter.html'
    extra_context = {'title': 'Vedtægter'}

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # Get documents from database
        documents = Document.objects.filter(category='vedtaegt')
        context['dynamic_documents'] = documents
        context['has_dynamic_documents'] = documents.exists()
        return context


# =============================================================================
# MAINTENANCE REQUEST VIEWS
# =============================================================================


class MaintenanceListView(LoginRequiredMixin, ListView):
    """List all maintenance requests."""

    model = MaintenanceRequest
    template_name = 'main/maintenance_list.html'
    context_object_name = 'requests'
    paginate_by = 20
    extra_context = {'title': 'Vedligeholdelse'}

    def get_queryset(self):
        queryset = MaintenanceRequest.objects.select_related('reporter')

        # Filter by status if specified
        status = self.request.GET.get('status')
        if status and status in dict(MaintenanceRequest.STATUS_CHOICES):
            queryset = queryset.filter(status=status)

        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['status_choices'] = MaintenanceRequest.STATUS_CHOICES
        context['selected_status'] = self.request.GET.get('status', '')
        context['pending_count'] = MaintenanceRequest.objects.filter(status='pending').count()
        context['in_progress_count'] = MaintenanceRequest.objects.filter(status='in_progress').count()
        return context


class MaintenanceCreateView(LoginRequiredMixin, CreateView):
    """Create a new maintenance request."""

    model = MaintenanceRequest
    fields = ['title', 'description', 'location', 'priority']
    template_name = 'main/maintenance_form.html'
    success_url = reverse_lazy('main:maintenance_list')
    extra_context = {'title': 'Ny anmodning'}

    def form_valid(self, form):
        form.instance.reporter = self.request.user
        response = super().form_valid(form)
        messages.success(
            self.request,
            'Din vedligeholdelsesanmodning er oprettet.',
        )
        return response


class MaintenanceDetailView(LoginRequiredMixin, DetailView):
    """View a specific maintenance request."""

    model = MaintenanceRequest
    template_name = 'main/maintenance_detail.html'
    context_object_name = 'request'
    extra_context = {'title': 'Anmodning'}

    def get_queryset(self):
        return MaintenanceRequest.objects.select_related('reporter')


class MaintenanceUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    """Update a maintenance request (staff only for status changes)."""

    model = MaintenanceRequest
    template_name = 'main/maintenance_form.html'
    extra_context = {'title': 'Opdater anmodning'}

    def test_func(self):
        maintenance = self.get_object()
        # Reporter can edit their own pending requests, staff can edit all
        if self.request.user.is_staff:
            return True
        return maintenance.reporter == self.request.user and maintenance.status == 'pending'

    def get_fields(self):
        """Return different fields based on user permissions."""
        if self.request.user.is_staff:
            return ['title', 'description', 'location', 'priority', 'status', 'admin_notes']
        return ['title', 'description', 'location', 'priority']

    def get_form_class(self):
        from django import forms

        class DynamicMaintenanceForm(forms.ModelForm):
            class Meta:
                model = MaintenanceRequest
                fields = self.get_fields()

        return DynamicMaintenanceForm

    def form_valid(self, form):
        # If status changed to resolved, set resolved_at
        if 'status' in form.changed_data:
            if form.cleaned_data['status'] == 'resolved':
                form.instance.resolved_at = timezone.now()
            else:
                form.instance.resolved_at = None

        response = super().form_valid(form)
        messages.success(self.request, 'Anmodningen er opdateret.')
        return response

    def get_success_url(self):
        return reverse_lazy('main:maintenance_detail', kwargs={'pk': self.object.pk})


# =============================================================================
# SEARCH VIEW
# =============================================================================


class SearchView(LoginRequiredMixin, ListView):
    """Search messages and documents."""

    template_name = 'main/search_results.html'
    context_object_name = 'results'
    paginate_by = 20
    extra_context = {'title': 'Søg'}

    def get_queryset(self):
        from django.contrib.postgres.search import SearchQuery, SearchRank
        from django.db import connection
        from django.db.models import F, Q

        query = self.request.GET.get('q', '').strip()
        search_type = self.request.GET.get('type', 'all')

        if not query:
            return []

        results = []

        # Search messages
        if search_type in ('all', 'messages'):
            if connection.vendor == 'postgresql':
                # PostgreSQL full-text search with Danish config
                search_query = SearchQuery(query, config='danish')
                message_results = Message.objects.annotate(
                    rank=SearchRank(F('search_vector'), search_query)
                ).filter(
                    search_vector=search_query
                ).select_related(
                    'author', 'author__profile', 'author__profile__heritage_line'
                ).order_by('-rank')
            else:
                # Fallback for SQLite (development): simple contains search
                message_results = Message.objects.filter(
                    content__icontains=query
                ).select_related(
                    'author', 'author__profile', 'author__profile__heritage_line'
                ).order_by('-created_at')

            for msg in message_results:
                results.append({
                    'type': 'message',
                    'object': msg,
                    'rank': getattr(msg, 'rank', 0.5),
                })

        # Search documents
        if search_type in ('all', 'documents'):
            documents = Document.objects.filter(
                Q(title__icontains=query) |
                Q(description__icontains=query)
            ).order_by('-document_date')

            for doc in documents:
                results.append({
                    'type': 'document',
                    'object': doc,
                    'rank': 0.5,  # Lower rank than text match
                })

        # Sort by rank (highest first)
        results.sort(key=lambda x: x['rank'], reverse=True)

        return results

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['query'] = self.request.GET.get('q', '')
        context['search_type'] = self.request.GET.get('type', 'all')
        return context


# =============================================================================
# RATE LIMIT ERROR VIEW
# =============================================================================


def ratelimit_error_view(request, exception):
    """Custom error view for rate limit exceeded."""
    return JsonResponse(
        {'error': 'For mange forespørgsler. Prøv igen senere.'},
        status=429
    )
