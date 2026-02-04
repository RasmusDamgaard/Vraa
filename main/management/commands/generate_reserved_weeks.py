"""
Management command to generate reserved weeks for a specific year.
"""
from __future__ import annotations

from datetime import datetime

from django.core.management.base import BaseCommand, CommandError

from main.models import HeritageLine, ReservedWeek


class Command(BaseCommand):
    help = 'Generate reserved weeks for heritage lines for a specific year'

    def add_arguments(self, parser):
        parser.add_argument(
            'year',
            type=int,
            nargs='?',
            default=None,
            help='Year to generate weeks for (defaults to current year)',
        )
        parser.add_argument(
            '--next',
            action='store_true',
            help='Generate weeks for the next year instead',
        )
        parser.add_argument(
            '--years',
            type=int,
            nargs='+',
            help='Generate weeks for multiple years (e.g., --years 2024 2025 2026)',
        )
        parser.add_argument(
            '--force',
            action='store_true',
            help='Delete existing reserved weeks and regenerate',
        )

    def handle(self, *args, **options):
        # Check if heritage lines exist
        heritage_line_count = HeritageLine.objects.count()
        if heritage_line_count == 0:
            raise CommandError(
                'No heritage lines exist. Please create heritage lines first via the admin interface or by loading fixtures.'
            )

        # Determine which years to generate
        years_to_generate = []

        if options['years']:
            years_to_generate = options['years']
        elif options['year']:
            years_to_generate = [options['year']]
        elif options['next']:
            years_to_generate = [datetime.now().year + 1]
        else:
            years_to_generate = [datetime.now().year]

        total_created = 0
        total_deleted = 0

        for year in years_to_generate:
            self.stdout.write(f'\nProcessing year {year}...')

            # Show which weeks each heritage line will have
            self.stdout.write(self.style.MIGRATE_HEADING(f'  Week assignments for {year}:'))
            for line in HeritageLine.objects.all().order_by('order'):
                weeks = line.get_reserved_weeks_for_year(year)
                if weeks:
                    self.stdout.write(f'    {line.name}: Weeks {", ".join(map(str, weeks))}')
                else:
                    self.stdout.write(
                        self.style.WARNING(f'    {line.name}: No base weeks configured')
                    )

            # Delete existing if force flag is set
            if options['force']:
                deleted, _ = ReservedWeek.objects.filter(year=year).delete()
                if deleted:
                    self.stdout.write(
                        self.style.WARNING(f'  Deleted {deleted} existing reserved weeks for {year}')
                    )
                    total_deleted += deleted

            # Generate reserved weeks
            count = ReservedWeek.generate_for_year(year)
            total_created += count

            if count > 0:
                self.stdout.write(
                    self.style.SUCCESS(f'  Created {count} reserved weeks for {year}')
                )
            else:
                self.stdout.write(f'  No new reserved weeks created (may already exist)')

        # Summary
        self.stdout.write('')
        self.stdout.write(self.style.SUCCESS(f'Summary:'))
        self.stdout.write(f'  Years processed: {len(years_to_generate)}')
        self.stdout.write(f'  Total created: {total_created}')
        if total_deleted:
            self.stdout.write(f'  Total deleted: {total_deleted}')

        # Show verification
        self.stdout.write('')
        self.stdout.write(self.style.MIGRATE_HEADING('Reserved weeks in database:'))
        for line in HeritageLine.objects.all().order_by('order'):
            for year in years_to_generate:
                weeks = ReservedWeek.objects.filter(
                    heritage_line=line, year=year
                ).values_list('week_number', flat=True)
                if weeks:
                    self.stdout.write(
                        f'  {line.short_name} ({year}): Weeks {", ".join(map(str, weeks))} '
                        f'({ReservedWeek.objects.filter(heritage_line=line, year=year).first().start_date} - '
                        f'{ReservedWeek.objects.filter(heritage_line=line, year=year).last().end_date})'
                    )
