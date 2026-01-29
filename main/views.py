"""
View classes for the ``main`` application.
"""
from __future__ import annotations

from django.contrib import messages
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.http import JsonResponse
from django.urls import reverse_lazy
from django.utils import timezone
from django.utils.decorators import method_decorator
from django.views import View
from django.views.decorators.cache import cache_page
from django.views.generic import CreateView, DeleteView, ListView, TemplateView, UpdateView

from .forms import BookingForm
from .models import Booking, Comment, Message


class FrontpageView(ListView):
    """Display the frontpage with the message board."""

    model = Message
    template_name = 'main/frontpage.html'
    context_object_name = 'message_list'
    paginate_by = 20
    extra_context = {'title': 'Frontpage'}

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

    form_class = UserCreationForm
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
        return response


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
