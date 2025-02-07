from django.core.management.base import BaseCommand
from django.conf import settings
from io import BytesIO
from ...models import Answer, Question
from ...gcs.client import GCS_Client
from ...s3.client import S3_Client


class Command(BaseCommand):
    
    help = 'Moves image files from S3 to GCS'

    def handle(self, *args, **kwargs):
        # Initialize S3 and GCS clients
        s3_client = S3_Client()
        gcs_client = GCS_Client()

        # Get all answers with questions of type IMAGE
        image_answers = Answer.objects.filter(question__question_type=Question.QuestionTypes.IMAGE)

        for answer in image_answers:
            file_name = answer.answer
            if file_name:
                self.stdout.write(self.style.NOTICE(f'Processing image: {file_name}'))
                # Read the image from S3
                image_content = s3_client.download_image_from_s3(file_name)
                if image_content:
                    # Upload the image to GCS
                    gcs_path = gcs_client.upload_image_file_to_gcs(BytesIO(image_content), file_name)
                    if gcs_path:
                        self.stdout.write(self.style.SUCCESS(f'Successfully moved {file_name} to GCS'))
                    else:
                        self.stdout.write(self.style.ERROR(f'Failed to upload {file_name} to GCS'))
                else:
                    self.stdout.write(self.style.ERROR(f'Failed to read {file_name} from S3'))
            else:
                self.stdout.write(self.style.WARNING(f'Answer {answer.id} has no file name'))