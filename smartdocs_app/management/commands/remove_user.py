from django.core.management.base import BaseCommand
from django.core.exceptions import ObjectDoesNotExist
from smartdocs_app.models import CustomUser

class Command(BaseCommand):
    help = 'Remove a user by their ID'

    def add_arguments(self, parser):
        # Add an argument to pass the user ID
        parser.add_argument('user_id', type=int, help='ID of the user to be removed')

    def handle(self, *args, **kwargs):
        user_id = kwargs['user_id']

        try:
            # Get the user by ID and delete them
            user = CustomUser.objects.get(id=user_id)
            username = user.username
            user.delete()
            self.stdout.write(self.style.SUCCESS(f'Successfully removed user: {username}'))

        except ObjectDoesNotExist:
            self.stdout.write(self.style.ERROR(f'User with ID "{user_id}" does not exist'))