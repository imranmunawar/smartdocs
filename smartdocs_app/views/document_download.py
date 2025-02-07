from ..models import Category, Template, UserDocument, Answer, Question
from django.contrib.auth.decorators import login_required, user_passes_test
from django.shortcuts import render, get_object_or_404
import time
from datetime import date, datetime
from django.http import JsonResponse, HttpResponse, HttpResponseNotFound, HttpResponseServerError
from django.conf import settings
from ..helpers.process_document import ProcessDocument
from django.http import FileResponse
import os
from django.views.decorators.csrf import csrf_exempt
import json
import subprocess
import shutil
import secrets
import string
from django.contrib.auth import authenticate
from ..services.document import DocumentService, DocumentProcessingService
from ..services.file import FileService
from ..utils.security import generate_secure_token
from ..utils.date import format_date_string


class DocumentDownloadManager:
    """Manager class for document download operations"""
    
    def __init__(self):
        self.document_service = DocumentService()
        self.file_service = FileService()
        self.processor = DocumentProcessingService()

    def process_document(self, template_id: int, document_name: str, user) -> dict:
        """Process document and prepare for download"""
        try:
            template = get_object_or_404(AdminTemplate, id=template_id)
            document_data = self.document_service.create_document_data(
                template=template,
                name=document_name,
                user=user
            )
            
            output_path = self.file_service.get_output_path(template_id)
            input_data = self.document_service.get_document_input_data(document_data)
            
            self.processor.process_document(
                input_data=input_data,
                template_file=template.template_file_name,
                output_path=output_path
            )
            
            return {
                'success': True,
                'output_path': output_path,
                'document_name': document_name
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }

    def generate_pdf(self, document_path: str) -> str:
        """Convert document to PDF format"""
        try:
            pdf_path = self.file_service.get_pdf_path(document_path)
            self.file_service.convert_to_pdf(document_path, pdf_path)
            return pdf_path
        except Exception as e:
            raise ValueError(f"PDF conversion failed: {str(e)}")


@csrf_exempt
@login_required
def download_dummy_document(request):

    if request.method == 'POST':
        
        user = request.user
        data = json.loads(request.body)
        template_id = data.get('template_id')
        document_name = data.get('document_name')
        template = Template.objects.get(id=template_id)
        document_json = get_document_json(template_id=template_id)
        try:
            document_obj = UserDocument.objects.create(
                name = document_name,
                user = user,
                template_file_name=template.template_file_name,
                document_json = document_json,
                template= template
            )

            template_id = document_obj.document_json['template_id']
            template = Template.objects.get(
                id = template_id
            )

            today = date.today()
            formatted_date = today.strftime("%Y-%m-%d")
            output_path = f'{settings.SAVED_DOCUMENTS}/output_{template_id}_{formatted_date}.docx'

            input_params, image_params = get_dummy_input_params(document_obj)

            pd = ProcessDocument()
            pd.process_and_save(input_params, image_params, template.template_file_name, output_path)
            
            if os.path.exists(output_path):
                with open(output_path, 'rb') as document_file:
                    try:
                        response = HttpResponse(document_file.read(), content_type='application/msword')
                        response['Content-Disposition'] = f'attachment; filename="Preview - {template.name}.docx"'
                        
                    except Exception as e:
                        return HttpResponseServerError("An error occurred while processing the document.")

                document_obj.delete()        
                os.remove(output_path)
                return response
            else:
                document_obj.delete()
                return HttpResponseNotFound("The requested document was not found.")

        except Exception as e:
            
            if 'document_obj' in locals():
                document_obj.delete()
            if output_path and os.path.exists(output_path):
                os.remove(output_path)
            return HttpResponseServerError("An error occurred while processing the request.")

    return HttpResponseNotFound("The requested document was not found.")


@csrf_exempt
@login_required
def download_dummy_document_pdf(request):

    if request.method == 'POST':
        
        user = request.user
        data = json.loads(request.body)
        template_id = data.get('template_id')
        document_name = data.get('document_name')
        template = Template.objects.get(id=template_id)
        document_json = get_document_json(template_id=template_id)
        try:
            document_obj = UserDocument.objects.create(
                name=document_name,
                user=user,
                template_file_name=template.template_file_name,
                document_json=document_json,
                template=template
            )

            today = date.today()
            formatted_date = today.strftime("%Y-%m-%d")
            docx_output_path = f'{settings.SAVED_DOCUMENTS}/output_{template_id}_{formatted_date}.docx'
            pdf_output_path = f'{settings.SAVED_DOCUMENTS}/output_{template_id}_{formatted_date}.pdf'

            input_params, image_params = get_dummy_input_params(document_obj)

            pd = ProcessDocument()
            pd.process_and_save(input_params, image_params, template.template_file_name, docx_output_path)

            if os.path.exists(docx_output_path):
                convert_docx_to_pdf(docx_output_path, pdf_output_path)

                if os.path.exists(pdf_output_path):
                    with open(pdf_output_path, 'rb') as pdf_file:
                        response = HttpResponse(pdf_file.read(), content_type='application/pdf')
                        response['Content-Disposition'] = f'attachment; filename="Preview - {template.name}.pdf"'
                        
                    document_obj.delete()
                    os.remove(docx_output_path)
                    os.remove(pdf_output_path)
                    return response
                else:
                    document_obj.delete()
                    os.remove(docx_output_path)
                    return HttpResponseNotFound("The requested PDF document was not found.")
            else:
                document_obj.delete()
                return HttpResponseNotFound("The requested document was not found.")

        except Exception as e:
            if 'document_obj' in locals():
                document_obj.delete()
            if docx_output_path and os.path.exists(docx_output_path):
                os.remove(docx_output_path)
            if pdf_output_path and os.path.exists(pdf_output_path):
                os.remove(pdf_output_path)
            return HttpResponseServerError("An error occurred while processing the request.")

    return HttpResponseNotFound("The requested document was not found.")


def get_dummy_input_params(user_document_obj):
    image_params = {}
    input_params = {}
    for section in user_document_obj.document_json['sections']:
        for subsection in section['subsections']:
            for question in subsection['questions']:
                if question['type'] == 'image':
                    image_params[question['placeholder']] = 'image.png'
                else:
                    if question['type'] == 'multiple':
                        input_params = input_params | get_dummy_multiple_answer_param(question['placeholder'])
                    elif question['type'] == 'single_checkbox':
                        input_params = input_params | get_dummy_single_checkbox_answer_param(question['placeholder'])
                    else:
                        input_params[question['placeholder']] = 'USER_ANSWER'
                    if question['type'] == 'radio':
                        nested_input_params ,nested_image_params = get_dummy_nested_input_params(user_document_obj.id, subsection['section_id'], question)
                        input_params = input_params | nested_input_params
                        image_params = image_params | nested_image_params

    return input_params, image_params


def get_dummy_multiple_answer_param(question_placeholder):
    input_params = {}
    answers = ['DUMMY_VAL1', 'DUMMY_VAL2', 'DUMMY_VAL3', 'DUMMY_VAL4', 'DUMMY_VAL5']
    placeholder = question_placeholder.rsplit("_", 1)[0]
    index = 1
    for answer in answers:
        full_placeholder = placeholder + "_" + str(index) + "}"
        input_params[full_placeholder] = answer
        index += 1

    return input_params


def get_dummy_single_checkbox_answer_param(question_placeholder):
    input_param = {}

    yes_placeholder = question_placeholder.replace("_X", "_YES")
    no_placeholder = question_placeholder.replace("_X", "_NO")

    input_param[yes_placeholder] = '☑'
    input_param[no_placeholder] = '☑'

    return input_param


def get_dummy_nested_input_params(user_document_id, section_id, question):
    image_params = {}
    input_params = {}
    for option in question['options']:
        if 'questions' in option:
            for option_question in option['questions']:
                if option_question['type'] == 'image':
                    image_params[option_question['placeholder']] = 'image.png'
                else:
                    if option_question['type'] == 'multiple':
                        input_params = input_params | get_dummy_multiple_answer_param(option_question['placeholder'])
                    elif option_question['type'] == 'single_checkbox':
                        input_params = input_params | get_dummy_single_checkbox_answer_param(option_question['placeholder'])
                    else:
                        input_params[option_question['placeholder']] = 'USER ANSWER'
                    if option_question['type'] == 'radio':
                        return_input_param, return_image_param = get_dummy_nested_input_params(user_document_id, section_id, option_question)
                        input_params = input_params | return_input_param
                        image_params = image_params | return_image_param

    return input_params, image_params



@login_required
def download_document(request, user_document_id):
    document_obj = UserDocument.objects.get(id=user_document_id)
    user_access_levels = request.session.get('user_access_levels', [])
    has_download_access = False

    if 'request-activation' in user_access_levels:
        has_download_access = True

    if (request.user.id == document_obj.user_id and has_download_access) or request.user.is_staff:
        try:
            template_id = document_obj.document_json['template_id']
            template = Template.objects.get(
                id = template_id
            )

            today = date.today()
            formatted_date = today.strftime("%Y-%m-%d")
            output_path = f'{settings.SAVED_DOCUMENTS}/output_{template_id}_{formatted_date}.docx'

            template_questions = Question.objects.filter(template_id=template_id)
            all_placeholders = set()

            for question in template_questions:
                placeholder = question.placeholder
                all_placeholders.add(placeholder)

            input_params, image_params = get_input_params(user_document_id, document_obj)

            for placeholder in all_placeholders:
                if placeholder not in input_params:
                    input_params[placeholder] = 'N/A'

            pd = ProcessDocument()
            pd.process_and_save(input_params, image_params, template.template_file_name, output_path)
            
            if os.path.exists(output_path):
                with open(output_path, 'rb') as document_file:
                    try:
                        response = HttpResponse(document_file.read(), content_type='application/msword')
                        response['Content-Disposition'] = f'attachment; filename="{document_obj.name}.docx"'                    

                    except Exception as e:
                        return HttpResponseServerError("An error occurred while processing the document.")

                os.remove(output_path)
                return response

            else:
                return HttpResponseNotFound("The requested document was not found.")

        except Exception as e:
            if output_path and os.path.exists(output_path):
                os.remove(output_path)
            return HttpResponseServerError("An error occurred while processing the request.")

    return HttpResponseNotFound("The requested document was not found.")


@login_required
def download_document_pdf(request, user_document_id):
    document_obj = UserDocument.objects.get(id=user_document_id)
    user_access_levels = request.session.get('user_access_levels', [])
    has_download_access = False

    if 'request-activation' in user_access_levels:
        has_download_access = True

    if (request.user.id == document_obj.user_id and has_download_access) or request.user.is_staff:
        try:
            template_id = document_obj.document_json['template_id']
            template = Template.objects.get(id=template_id)

            today = date.today()
            formatted_date = today.strftime("%Y-%m-%d")
            docx_output_path = f'{settings.SAVED_DOCUMENTS}/output_{template_id}_{formatted_date}.docx'
            pdf_output_path = f'{settings.SAVED_DOCUMENTS}/output_{template_id}_{formatted_date}.pdf'

            template_questions = Question.objects.filter(template_id=template_id)
            all_placeholders = set()

            for question in template_questions:
                placeholder = question.placeholder
                all_placeholders.add(placeholder)

            input_params, image_params = get_input_params(user_document_id, document_obj)

            for placeholder in all_placeholders:
                if placeholder not in input_params:
                    input_params[placeholder] = 'N/A'

            pd = ProcessDocument()
            pd.process_and_save(input_params, image_params, template.template_file_name, docx_output_path)

            if os.path.exists(docx_output_path):
                convert_docx_to_pdf(docx_output_path, pdf_output_path)

                if os.path.exists(pdf_output_path):
                    with open(pdf_output_path, 'rb') as pdf_file:
                        response = HttpResponse(pdf_file.read(), content_type='application/pdf')
                        response['Content-Disposition'] = f'attachment; filename="{document_obj.name}.pdf"'

                    os.remove(docx_output_path)
                    os.remove(pdf_output_path)
                    return response
                else:
                    return HttpResponseNotFound("The requested PDF document was not found.")
            else:
                return HttpResponseNotFound("The requested document was not found.")

        except Exception as e:
            if docx_output_path and os.path.exists(docx_output_path):
                os.remove(docx_output_path)
            if pdf_output_path and os.path.exists(pdf_output_path):
                os.remove(pdf_output_path)
            return HttpResponseServerError("An error occurred while processing the request.")

    return HttpResponseNotFound("The requested document was not found.")


def convert_docx_to_pdf(docx_file, pdf_output):
    command = [
        'libreoffice',
        '--headless',
        '--convert-to',
        'pdf',
        '--outdir',
        os.path.dirname(pdf_output),
        docx_file
    ]
    env = os.environ.copy()
    env['HOME'] = '/tmp'

    subprocess.run(command, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, env=env)
    expected_pdf_file = os.path.join(os.path.dirname(pdf_output), os.path.splitext(os.path.basename(docx_file))[0] + '.pdf')
    if os.path.exists(expected_pdf_file):
        shutil.move(expected_pdf_file, pdf_output)


def get_input_params(user_document_id, user_document_obj):
    image_params = {}
    input_params = {}
    for section in user_document_obj.document_json['sections']:
        for subsection in section['subsections']:
            for question in subsection['questions']:
                answer = check_answer_in_db(subsection['section_id'], user_document_id, question['question_id'])
                if question['type'] == 'image':
                    if answer:
                        image_params[question['placeholder']] = answer.answer
                else:
                    if answer and question['type'] == 'multiple':
                        input_params = input_params | get_multiple_answer_param(answer.answer, question['placeholder'])
                    elif answer and question['type'] == 'single_checkbox':
                        input_params = input_params | get_single_checkbox_answer_param(answer.answer, question['placeholder'])
                    elif answer and question['type'] == 'date':
                        date_str = answer.answer
                        formatted_date = format_date(date_str)
                        if formatted_date:
                            input_params[question['placeholder']] = formatted_date
                        else:
                            input_params[question['placeholder']] = date_str
                    elif answer:
                        input_params[question['placeholder']] = answer.answer
                    if answer and question['type'] == 'radio':
                        nested_input_params ,nested_image_params = get_nested_input_params(user_document_id, subsection['section_id'], question, answer)
                        input_params = input_params | nested_input_params
                        image_params = image_params | nested_image_params

    return input_params, image_params


def get_nested_input_params(user_document_id, section_id, question, db_answer):
    image_params = {}
    input_params = {}
    for option in question['options']:
        if option['option_value'] == db_answer.answer and 'questions' in option:
            for option_question in option['questions']:
                answer = check_answer_in_db(section_id, user_document_id, option_question['question_id'])
                if option_question['type'] == 'image':
                    if answer:
                        image_params[option_question['placeholder']] = answer.answer
                else:
                    if answer and option_question['type'] == 'multiple':
                        input_params = input_params | get_multiple_answer_param(answer.answer, option_question['placeholder'])
                    elif answer and option_question['type'] == 'single_checkbox':
                        input_params = input_params | get_single_checkbox_answer_param(answer.answer, option_question['placeholder'])
                    elif answer and option_question['type'] == 'date':
                        date_str = answer.answer
                        formatted_date = format_date(date_str)
                        if formatted_date:
                            input_params[option_question['placeholder']] = formatted_date
                        else:
                            input_params[option_question['placeholder']] = date_str  
                    elif answer:
                        input_params[option_question['placeholder']] = answer.answer
                    if option_question['type'] == 'radio':
                        nested_input_params ,nested_image_params = get_nested_input_params(user_document_id, section_id, option_question, answer)
                        input_params = input_params | nested_input_params
                        image_params = image_params | nested_image_params

    return input_params, image_params


def check_answer_in_db(section_id:int, user_document_id:int, question_id:int) -> Answer:
    """
    Returns the answer using the params
    
    :param section_id: Id of the section
    :type section_id: int
    :param user_document_id: Id of the user document
    :type user_document_id: int
    :param question_id: Id of the question
    :type question_id: int
    :return: The object of the answer
    :rtype: Answer
    """

    answer = Answer.objects.filter(
        section_id=section_id,
        question_id=question_id,
        user_document_id=user_document_id
    ).first()

    return answer

def get_multiple_answer_param(answer_text, question_placeholder):
    input_params = {}
    answers = answer_text.split('|')
    placeholder = question_placeholder.rsplit("_", 1)[0]
    index = 1
    for answer in answers:
        full_placeholder = placeholder + "_" + str(index) + "}"
        input_params[full_placeholder] = answer
        index += 1

    return input_params


def get_single_checkbox_answer_param(answer_text, question_placeholder):
    input_param = {}

    yes_placeholder = question_placeholder.replace("_X", "_YES")
    no_placeholder = question_placeholder.replace("_X", "_NO")

    if answer_text == "True":
        input_param[yes_placeholder] = '☑'
        input_param[no_placeholder] = '☐'
    else:
        input_param[yes_placeholder] = '☐'
        input_param[no_placeholder] = '☑'
    
    return input_param


def format_date(date_str):
    try:
        date_obj = datetime.strptime(date_str, "%Y-%m-%d")
        formatted_date = date_obj.strftime("%B %-d, %Y")
        return formatted_date
    except ValueError:
        return None


def download_pdf_test_endpoint(request):
    """
    Load testing endpoint
    """
    
    if request.method == 'GET':

        user_document_id = request.GET.get("user_document_id")
        document_obj = UserDocument.objects.get(id=user_document_id)

        try:
            template_id = document_obj.document_json['template_id']
            template = Template.objects.get(id=template_id)

            today = date.today()
            formatted_date = today.strftime("%Y-%m-%d")
            random_hash = generate_random_hash()
            docx_output_path = f'{settings.SAVED_DOCUMENTS}/output_{template_id}_{formatted_date}_{random_hash}.docx'
            pdf_output_path = f'{settings.SAVED_DOCUMENTS}/output_{template_id}_{formatted_date}_{random_hash}.pdf'

            template_questions = Question.objects.filter(template_id=template_id)
            all_placeholders = set()

            for question in template_questions:
                placeholder = question.placeholder
                all_placeholders.add(placeholder)

            input_params, image_params = get_input_params(user_document_id, document_obj)

            for placeholder in all_placeholders:
                if placeholder not in input_params:
                    input_params[placeholder] = 'N/A'

            pd = ProcessDocument()
            pd.process_and_save(input_params, image_params, template.template_file_name, docx_output_path)

            if os.path.exists(docx_output_path):
                convert_docx_to_pdf(docx_output_path, pdf_output_path)

                if os.path.exists(pdf_output_path):
                    with open(pdf_output_path, 'rb') as pdf_file:
                        response = HttpResponse(pdf_file.read(), content_type='application/pdf')
                        response['Content-Disposition'] = f'attachment; filename="{document_obj.name}.pdf"'

                    os.remove(docx_output_path)
                    os.remove(pdf_output_path)
                    return JsonResponse({'status': 'OK'})
                else:
                    return HttpResponseNotFound("The requested PDF document was not found.")
            else:
                return HttpResponseNotFound("The requested document was not found.")

        except Exception as e:
            if docx_output_path and os.path.exists(docx_output_path):
                os.remove(docx_output_path)
            if pdf_output_path and os.path.exists(pdf_output_path):
                os.remove(pdf_output_path)
            return HttpResponseServerError("An error occurred while processing the request.")

        return HttpResponseNotFound("The requested document was not found.")


def generate_random_hash(length=20):

    characters = string.ascii_letters + string.digits
    random_hash = ''.join(secrets.choice(characters) for _ in range(length))
    return random_hash


@csrf_exempt
@login_required
def download_preview_document(request):
    """Generate and download document preview"""
    if request.method != 'POST':
        return JsonResponse({'error': 'Invalid request method'}, status=405)
        
    manager = DocumentDownloadManager()
    
    try:
        data = json.loads(request.body)
        result = manager.process_document(
            template_id=data.get('template_id'),
            document_name=data.get('document_name'),
            user=request.user
        )
        
        if not result['success']:
            return HttpResponseServerError(result['error'])
            
        response = FileService.create_download_response(
            file_path=result['output_path'],
            filename=f"Preview - {result['document_name']}.docx"
        )
        
        FileService.cleanup_files([result['output_path']])
        return response
        
    except Exception as e:
        return HttpResponseServerError(f"Processing failed: {str(e)}")


@login_required
def download_document_pdf(request, document_id: int):
    """Download document as PDF"""
    manager = DocumentDownloadManager()
    
    try:
        document = get_object_or_404(AdminDocument, id=document_id)
        
        if not manager.document_service.has_download_access(request.user, document):
            return HttpResponseForbidden("Access denied")
            
        result = manager.process_document(
            template_id=document.template.id,
            document_name=document.name,
            user=request.user
        )
        
        if not result['success']:
            return HttpResponseServerError(result['error'])
            
        pdf_path = manager.generate_pdf(result['output_path'])
        
        response = FileService.create_download_response(
            file_path=pdf_path,
            filename=f"{result['document_name']}.pdf",
            content_type='application/pdf'
        )
        
        FileService.cleanup_files([result['output_path'], pdf_path])
        return response
        
    except Exception as e:
        return HttpResponseServerError(f"PDF generation failed: {str(e)}")


class DocumentParameterService:
    """Service for handling document parameters"""
    
    @staticmethod
    def get_document_parameters(document_id: int) -> tuple:
        """Get input and image parameters for document"""
        document = get_object_or_404(AdminDocument, id=document_id)
        
        input_params = {}
        image_params = {}
        
        for section in document.document_json['sections']:
            for subsection in section['subsections']:
                for question in subsection['questions']:
                    answer = AdminAnswer.objects.filter(
                        section_id=subsection['section_id'],
                        question_id=question['question_id'],
                        document_id=document_id
                    ).first()
                    
                    if answer:
                        if question['type'] == 'image':
                            image_params[question['placeholder']] = answer.answer
                        else:
                            input_params[question['placeholder']] = (
                                DocumentParameterService.format_answer(
                                    answer.answer,
                                    question['type']
                                )
                            )
                            
        return input_params, image_params

    @staticmethod
    def format_answer(answer: str, question_type: str) -> str:
        """Format answer based on question type"""
        if question_type == 'date':
            return format_date_string(answer)
        elif question_type == 'multiple':
            return ' | '.join(answer.split('|'))
        elif question_type == 'single_checkbox':
            return '☑' if answer == 'True' else '☐'
        return answer
