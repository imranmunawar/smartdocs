from django.core.management.base import BaseCommand, CommandError
from django.conf import settings


class Command(BaseCommand):
    help = 'List all database settings'

    def handle(self, *args, **options):
        databases = settings.DATABASES

        print("Database settings:")
        for db_alias, db_settings in databases.items():
            print(f"\n{db_alias}")
            for key, value in db_settings.items():
                print(f"{key}: {value}")
