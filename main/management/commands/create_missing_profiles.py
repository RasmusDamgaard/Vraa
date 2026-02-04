"""
Management command to create UserProfile for users that do not have one.
"""
from __future__ import annotations

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand

from main.models import UserProfile

User = get_user_model()


class Command(BaseCommand):
    help = 'Create UserProfile for users that do not have one'

    def handle(self, *args, **options):
        users_without_profile = User.objects.filter(profile__isnull=True)
        count = 0

        for user in users_without_profile:
            UserProfile.objects.create(user=user)
            count += 1
            self.stdout.write(f'Created profile for user: {user.username}')

        if count == 0:
            self.stdout.write(
                self.style.SUCCESS('All users already have profiles.')
            )
        else:
            self.stdout.write(
                self.style.SUCCESS(f'Successfully created {count} user profile(s).')
            )
