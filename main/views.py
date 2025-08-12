"""
View functions for the ``main`` application.

Each function renders a specific template corresponding to a page in
the site. The context includes only a title for now; this may be
expanded in the future to include dynamic content.
"""
from __future__ import annotations

from django.shortcuts import render


def frontpage(request):
    """Render the front page of the website."""
    return render(request, 'main/frontpage.html', {
        'title': 'Frontpage',
    })


def information(request):
    """Render the information page."""
    return render(request, 'main/information.html', {
        'title': 'Information',
    })


def referater(request):
    """Render the referater (minutes) page."""
    return render(request, 'main/referater.html', {
        'title': 'Referater',
    })


def vedtaegter(request):
    """Render the vedtægter (statutes) page."""
    return render(request, 'main/vedtaegter.html', {
        'title': 'Vedtægter',
    })


def kalender(request):
    """Render the calendar page."""
    return render(request, 'main/kalender.html', {
        'title': 'Kalender',
    })
