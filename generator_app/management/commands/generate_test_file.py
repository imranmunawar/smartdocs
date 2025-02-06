from django.core.management.base import BaseCommand
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile

class Command(BaseCommand):
    help = 'Generates a .txt file with "Hello, World!" and uploads it to Google Cloud Storage'

    def handle(self, *args, **kwargs):
        # Define the file name and content
        file_name = 'uploads/hello_world.txt'
        content = 'Hello, World!'
        
        # Create a ContentFile object with bytes content
        file = ContentFile(content.encode('utf-8'))
        
        # Save the file using default_storage
        file_path = default_storage.save(file_name, file)
        
        # Print the file path
        self.stdout.write(self.style.SUCCESS(f'File saved to: {file_path}'))
