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
from django.http import JsonResponse
from django.urls import reverse_lazy
from django.utils import timezone
from django.utils.decorators import method_decorator
from django.views import View
from django.views.decorators.cache import cache_page
from django.views.generic import CreateView, DeleteView, ListView, TemplateView, UpdateView

from .forms import BookingForm, CustomUserCreationForm
from .models import Booking, Comment, Message

logger = logging.getLogger(__name__)


class FrontpageView(ListView):
    """Display the frontpage with the message board."""

    model = Message
    template_name = 'main/frontpage.html'
    context_object_name = 'message_list'
    paginate_by = 20
    extra_context = {'title': 'Forside'}

    def get_queryset(self):
        # Optimize queries: prefetch comments and their authors
        return Message.objects.select_related('author').prefetch_related(
            'comments',
            'comments__author',
        )


@method_decorator(cache_page(60 * 60), name='dispatch')
class InformationView(TemplateView):
    template_name = 'main/information.html'
    extra_context = {'title': 'Information'}


@method_decorator(cache_page(60 * 60), name='dispatch')
class ReferaterView(TemplateView):
    template_name = 'main/referater.html'
    extra_context = {'title': 'Referater'}


@method_decorator(cache_page(60 * 60), name='dispatch')
class VedtaegterView(TemplateView):
    template_name = 'main/vedtaegter.html'
    extra_context = {'title': 'Vedtægter'}


class KalenderView(LoginRequiredMixin, ListView):
    """Display calendar with bookings."""

    model = Booking
    template_name = 'main/kalender.html'
    context_object_name = 'bookings'
    extra_context = {'title': 'Kalender'}

    def get_queryset(self):
        return Booking.objects.filter(
            status__in=['pending', 'confirmed'],
            end_date__gte=timezone.now().date(),
        ).select_related('user')


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
        return super().form_valid(form)


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
        form.instance.author = self.request.user
        form.instance.message_id = self.kwargs['message_pk']
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


class BookingCreateView(LoginRequiredMixin, CreateView):
    """Create a new booking."""

    model = Booking
    form_class = BookingForm
    template_name = 'main/booking_form.html'
    success_url = reverse_lazy('main:kalender')
    extra_context = {'title': 'Ny booking'}

    def get_initial(self):
        initial = super().get_initial()
        # Pre-fill dates from query parameters (for click-to-book calendar)
        if 'start' in self.request.GET:
            initial['start_date'] = self.request.GET['start']
        if 'end' in self.request.GET:
            initial['end_date'] = self.request.GET['end']
        return initial

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


class BookingAPIView(LoginRequiredMixin, View):
    """API endpoint for calendar data (JSON)."""

    def get(self, request):
        bookings = Booking.objects.filter(
            status__in=['pending', 'confirmed'],
        ).select_related('user')

        events = []
        for booking in bookings:
            events.append({
                'id': booking.pk,
                'title': booking.user.username,
                'start': booking.start_date.isoformat(),
                'end': booking.end_date.isoformat(),
                'color': '#28a745' if booking.status == 'confirmed' else '#ffc107',
                'extendedProps': {
                    'status': booking.status,
                    'is_owner': booking.user == request.user,
                },
            })

        return JsonResponse(events, safe=False)


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
