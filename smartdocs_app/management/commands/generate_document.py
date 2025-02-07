from django.core.management.base import BaseCommand, CommandError
from django.conf import settings
from ...helpers.process_document import ProcessDocument
from django.conf import settings

class Command(BaseCommand):
    help = 'Converts a document'

    def handle(self, *args, **options):
        input_path = f'{settings.DOCUMENT_TEMPLATE_FILES}/file1.docx'
        output_path = f'{settings.SAVED_DOCUMENTS}/output.docx'
        input_params = {
            '[NAME LLC]': 'COEUS',
            '[DISTRIBUTION]': '20',
            '[jfdlsfjdlskfj]': 'fsdafassaf'
        }
        pd = ProcessDocument()
        pd.process_and_save(input_params, input_path, output_path)
