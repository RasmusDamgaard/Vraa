"""
View classes for the ``main`` application.
"""
from __future__ import annotations

from django.contrib import messages
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.urls import reverse_lazy
from django.views.generic import CreateView, DeleteView, ListView, TemplateView, UpdateView

from .models import Message


class FrontpageView(ListView):
    """Display the frontpage with the message board."""

    model = Message
    template_name = 'main/frontpage.html'
    context_object_name = 'message_list'
    paginate_by = 20
    extra_context = {'title': 'Frontpage'}


class InformationView(TemplateView):
    template_name = 'main/information.html'
    extra_context = {'title': 'Information'}


class ReferaterView(TemplateView):
    template_name = 'main/referater.html'
    extra_context = {'title': 'Referater'}


class VedtaegterView(TemplateView):
    template_name = 'main/vedtaegter.html'
    extra_context = {'title': 'Vedtægter'}


class KalenderView(TemplateView):
    template_name = 'main/kalender.html'
    extra_context = {'title': 'Kalender'}


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
