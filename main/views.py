"""
View classes for the ``main`` application.
Refactored to use Django's generic TemplateView for cleaner code.
"""
from __future__ import annotations
from django.views.generic import TemplateView

class FrontpageView(TemplateView):
    template_name = 'main/frontpage.html'
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