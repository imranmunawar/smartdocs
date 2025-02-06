from django.core.management.base import BaseCommand
from ...s3.client import S3_Client
from ...gcs.client import GCS_Client
from ...models import Template, Question
from python_docx_replace import docx_get_keys
from docx import Document
import tempfile
import re


class Command(BaseCommand):
    help = 'Generate template placeholders from a document in S3'

    def handle(self, *args, **kwargs):

        # s3 = S3_Client()
        gcs = GCS_Client()
        
        template_ids = [88]

        for template_id in template_ids:

            template = Template.objects.get(id=template_id)
            filename = template.template_file_name
            # doc_content = s3.read_document_from_s3(filename)
            doc_content = gcs.read_document_from_gcs(filename)

            if doc_content is None:
                self.stdout.write(self.style.ERROR("Failed to read document from S3."))
                return False
            
            self.stdout.write(self.style.SUCCESS("Document read successfully from S3."))

            placeholders = self.get_placeholders_from_file(doc_content)

            template.doc_placeholders = placeholders
            template.save()

            if template.is_active == True:

                left_placeholders = self.match_template_placeholders(template_id)

                if left_placeholders:

                    self.stdout.write(self.style.ERROR(f"Unmatched placeholders:{left_placeholders} .....deactivating template....."))
                    template.is_active = False
                    template.save()

    
    def get_placeholders_from_file(self, file):

        if file:
            with tempfile.NamedTemporaryFile(delete=False) as temp_file:
                temp_file.write(file.read())
                temp_file_path = temp_file.name
            
            doc = Document(temp_file_path)
            placeholders = docx_get_keys(doc)
            placeholders_list = list(placeholders)
            
            return placeholders_list
    

    def match_template_placeholders(self, template_id):
    
        template = Template.objects.get(id=template_id)
        template_placeholders = template.doc_placeholders or [] #All Document Placeholders

        print('---> TEMPLATE PLACEHOLDERS', template_placeholders)

        question_placeholders = set(
            placeholder[2:-1] for placeholder in 
            Question.objects.filter(template_id=template_id)
            .values_list('placeholder', flat=True)
        ) #All Question Placeholders

        print('---> QUESTION PLACEHOLDERS', question_placeholders)

        simple_unmatched_placeholders = [
            placeholder for placeholder in template_placeholders
            if placeholder not in question_placeholders
        ]

        print('---> SIMPLE UNMATCHED PLACEHOLDERS', simple_unmatched_placeholders)

        multiple_placeholders = self.merge_variables(simple_unmatched_placeholders)
        
        multiple_unmatched_placeholders = [
            placeholder for placeholder in multiple_placeholders
            if placeholder not in question_placeholders
        ]

        print('---> ALL (SIMPLE + MULTIPLE) UNMATCHED PLACEHOLDERS', multiple_unmatched_placeholders)

        return multiple_unmatched_placeholders
    

    def merge_variables(self, variable_list):
        merged_variables = {}
        placeholder_mapping = {}

        for variable in variable_list:
            if re.match(r'.*_\d+$', variable):
                prefix, suffix = variable.rsplit('_', 1)
                
                if prefix not in merged_variables:
                    merged_variables[prefix] = f"{prefix}_N"
                
                placeholder_mapping[variable] = merged_variables[prefix]
            else:
                placeholder_mapping[variable] = variable
        
        merged_list = list(set(placeholder_mapping.values()))
        
        return merged_list
