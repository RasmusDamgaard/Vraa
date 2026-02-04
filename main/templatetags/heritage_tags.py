"""
Template tags for displaying heritage line information.
"""
from __future__ import annotations

from django import template
from django.utils.html import format_html

register = template.Library()


@register.simple_tag
def heritage_badge(user):
    """
    Display heritage line badge for a user.

    Usage: {% heritage_badge user %}

    Returns an HTML badge element with the user's heritage line info,
    or an empty string if the user has no heritage line assigned.
    """
    if not hasattr(user, 'profile') or not user.profile.heritage_line:
        return ''

    line = user.profile.heritage_line
    return format_html(
        '<span class="badge {} heritage-badge" title="{}">{}</span>',
        line.badge_class,
        line.name,
        line.short_name
    )


@register.simple_tag
def heritage_color(user):
    """
    Return heritage line color for calendar events.

    Usage: {% heritage_color user %}

    Returns a hex color code string.
    """
    if not hasattr(user, 'profile') or not user.profile.heritage_line:
        return '#6c757d'  # Default gray
    return user.profile.heritage_line.color


@register.inclusion_tag('main/partials/heritage_badge.html')
def heritage_badge_full(user):
    """
    Display a full heritage badge with optional role indicator.

    Usage: {% heritage_badge_full user %}

    Returns a rendered template with heritage line information.
    """
    context = {
        'has_heritage': False,
        'heritage_line': None,
        'family_role': None,
        'family_role_display': None,
    }

    if hasattr(user, 'profile') and user.profile.heritage_line:
        context['has_heritage'] = True
        context['heritage_line'] = user.profile.heritage_line
        context['family_role'] = user.profile.family_role
        context['family_role_display'] = user.profile.get_family_role_display()

    return context
