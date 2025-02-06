from django.core.management.base import BaseCommand
from django.conf import settings
from io import BytesIO
from ...models import Template
from ...gcs.client import GCS_Client
from ...s3.client import S3_Client

class Command(BaseCommand):
    help = 'Moves template files from S3 to GCS'

    def handle(self, *args, **kwargs):
        # Initialize S3 and GCS clients
        s3_client = S3_Client()
        gcs_client = GCS_Client()

        # Get all templates
        templates = Template.objects.all()

        for template in templates:
            file_name = template.template_file_name
            if file_name:
                self.stdout.write(self.style.WARNING(f'Processing {file_name}'))
                # Read the file from S3
                file_content = s3_client.read_document_from_s3(file_name)
                if file_content:
                    # Upload the file to GCS
                    gcs_path = gcs_client.upload_template_file_to_gcs(file_content, file_name)
                    if gcs_path:
                        self.stdout.write(self.style.SUCCESS(f'Successfully moved {file_name} to GCS'))
                    else:
                        self.stdout.write(self.style.ERROR(f'Failed to upload {file_name} to GCS'))
                else:
                    self.stdout.write(self.style.ERROR(f'Failed to read {file_name} from S3'))
                
            else:
                self.stdout.write(self.style.WARNING(f'Template {template.name} has no file name'))