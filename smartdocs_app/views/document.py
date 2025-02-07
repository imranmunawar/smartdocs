from django.shortcuts import render, redirect, get_object_or_404
from ..models import UserDocument, Template, Answer, Question, Section, Option
from django.http import HttpResponseRedirect, JsonResponse, FileResponse, HttpResponseNotFound
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_exempt
from django.contrib import messages
from django.conf import settings
from ..helpers.open_ai import OPENAI
from ..enums import messageEnum
from ..s3.client import S3_Client
from ..gcs.client import GCS_Client
from ..services.document import DocumentService
from ..services.video import VideoService
from ..services.storage import StorageService
from ..enums import MessageType
from ..utils.video import format_vimeo_embed

from django.utils.safestring import mark_safe



def get_vimeo_ids(vimeo_link):
    if vimeo_link:
        ids = str(vimeo_link).split("/")
        if len(ids) == 2:
            vimeo_id, vimeo_h = ids
        else:
            vimeo_id = ids[0]
            vimeo_h = None
    else:
        vimeo_id = None
        vimeo_h = None

    return vimeo_id, vimeo_h


def get_vimeo_embed_with_timestamp(vimeo_embed_code, video_timestamp, width=360, height=203):
    """
    Modifies Vimeo embed code by adding a timestamp and ensuring dimensions are set to 360x203 pixels.

    :param vimeo_embed_code: The embed code for Vimeo video
    :param video_timestamp: The timestamp to append
    :param width: Width of the video (default: 360)
    :param height: Height of the video (default: 203)
    :return: Modified embed code with the correct dimensions and timestamp
    """

    src_index_start = vimeo_embed_code.find('src="') + 5
    src_index_end = vimeo_embed_code.find('"', src_index_start)
    vimeo_url = vimeo_embed_code[src_index_start:src_index_end]
    if '#t=' not in vimeo_url:
        vimeo_url += f"#t={video_timestamp}s"
    vimeo_embed_code = f'{vimeo_embed_code[:src_index_start]}{vimeo_url}{vimeo_embed_code[src_index_end:]}'

    # vimeo_embed_code = vimeo_embed_code.replace('width:100%', f'width="{width}"')
    # vimeo_embed_code = vimeo_embed_code.replace('height:100%', f'height="{height}"')
    print(vimeo_embed_code)
    return vimeo_embed_code


class DocumentViewManager:
    """Manager for document view operations"""
    
    def __init__(self):
        self.document_service = DocumentService()
        self.video_service = VideoService()
        self.storage_service = StorageService()

    def get_document_context(self, document_id: int, section_id: int = None) -> dict:
        """Get context data for document view"""
        document = get_object_or_404(UserDocument, id=document_id)
        
        # Sync document if needed
        if not document.is_synced:
            document = self.document_service.sync_document(document)
            
        # Get section data
        section_data = self.get_section_data(document, section_id)
        if not section_data:
            return None
            
        # Get video data
        video_data = self.video_service.get_section_video(
            section_data['subsection']
        )
        
        return {
            'document': document,
            'subsection': section_data['subsection'],
            'selected_section_id': section_data['section_id'],
            'selected_subsection_id': section_data['subsection_id'],
            'vimeo_embed_code': mark_safe(video_data['embed_code']),
            **self.get_navigation_context(document_id, document.document_json, section_data['subsection_id'])
        }

    def get_section_data(self, document: UserDocument, section_id: int = None) -> dict:
        """Get section and subsection data"""
        document_json = document.document_json
        
        if not document_json.get('sections'):
            return None
            
        if section_id:
            return self.get_specific_section(document_json, section_id)
        return self.get_first_section(document_json)

    def get_navigation_context(self, document_id: int, document_json: dict, current_subsection_id: int) -> dict:
        """Get navigation context for next/previous sections"""
        return {
            **self.get_next_section_navigation(document_id, document_json, current_subsection_id),
            **self.get_previous_section_navigation(document_id, document_json, current_subsection_id)
        }

@login_required
def document_view(request, document_id: int):
    """Display document view with first section"""
    manager = DocumentViewManager()
    
    try:
        context = manager.get_document_context(document_id)
        if not context:
            return HttpResponseNotFound("Error rendering document")
            
        return render(request, 'documents/view.html', context)
    except Exception as e:
        messages.error(request, str(e))
        return redirect('dashboard')

@login_required
def document_section_view(request, document_id: int, section_id: int):
    """Display specific section of document"""
    manager = DocumentViewManager()
    
    try:
        context = manager.get_document_context(document_id, section_id)
        if not context:
            return redirect(request.META.get('HTTP_REFERER'))
            
        return render(request, 'documents/view.html', context)
    except Exception as e:
        messages.error(request, str(e))
        return redirect('document_view', document_id=document_id)

@login_required
def create_document_view(request):
    """
    Creates a new document view
    """

    if request.method == 'POST':
        user = request.user
        document_name = request.POST.get('document_name')
        template_id =  request.POST.get('template_id')
        template = Template.objects.get(id=template_id)
        # document_html = get_document_html(template_id=template_id)
        document_json = get_document_json(template_id=template_id)
        user_document = UserDocument.objects.create(
            name = document_name,
            user = user,
            template_file_name=template.template_file_name,
            document_json = document_json,
            template= template
        )

    return HttpResponseRedirect(f'/document/{user_document.id}')


def get_document_json(template_id:int) -> dict:
    """
    Generates json for a user document using template id

    :param template_id: Id of the template from where to fetch the json
    :type template_id: int
    :return: json of the template
    :rtype: str
    """

    result = {}
    result['template_id'] = template_id
    result['sections'] = get_sections_json(template_id)
    return result


def get_sections_json(template_id:int) -> list:
    """
    Returns the list json for a section along with all subsections

    :param template_id: Id of the template from where to fetch the json
    :type template_id: int
    :return: the list of section
    :rtype: list
    """

    sections_list = []
    sections = Section.objects.filter(
        template_id=template_id, 
        parent_section__isnull=True,
        is_active=True
    ).order_by('sequence_id')

    for section in sections:
        section_data = {
            'section_id': section.id,
            'sectionName': section.name,
            'is_active': section.is_active,
            'subsections': get_subsections(section)
        }
        sections_list.append(section_data)
    
    return sections_list


def get_subsections(parent_section:Section) -> list:
    """
    Returns the list of subsection for a section

    :param parent_section: Object of section
    :type parent_section: Section
    :return: the list of subsections
    :rtype: list
    """

    subsections_list = []
    subsections = parent_section.children.all().order_by('sequence_id')
    for section in subsections:
        if section.is_active:
            section_data = {
                'section_id': section.id,
                'sectionName': section.name,
                'questions': get_section_questions(section_id=section.id)
            }
            subsections_list.append(section_data)
    
    return subsections_list


def get_section_questions(section_id:int) -> list:
    """
    Gets the list of questions for subsection
    Also returns all the nested questions

    :param section_id: Id of the section for which the questions are fetched
    :type section_id: int
    :return: the list question
    :rtype: list
    """

    questions_list = []
    questions = Question.objects.filter(section_id=section_id).order_by('sequence_id')
    
    for question in questions:
        if question.parent_question == None:
            question_data = {
                'question_id': question.id,
                'question': question.question,
                'is_active': question.is_active,
                'type': question.question_type,
                'placeholder': question.placeholder,
                'is_ai': question.is_ai,
                'ai_prompt': question.ai_prompt,
                'na_applicable': question.na_applicable,
                'helping_text': question.helping_text
            }
            if question.question_type == 'radio':
                question_data['options'] = get_options(question_id=question.id)

            questions_list.append(question_data)
    return questions_list


def get_options(question_id:int) -> list:
    """
    Return the options and nested questions

    :param question_id: Id of the question
    :type question_id: int
    :return: The options and their nested questions
    :rtype: list
    """

    options_list = []
    options = Option.objects.filter(question_id=question_id)
    for option in options:
        if option.is_active:
            options_data = {
                'option_value': option.name
            }
            next_question = get_next_nested_question(option.child_questions.all())
            if next_question:
                options_data['questions'] = next_question
            options_list.append(options_data)
    return options_list


def get_next_nested_question(questions:list) -> list:
    """
    Return the nested questions of option question field

    :param questions: list of questions
    :type questions: list
    :return: the list of nested questions
    :rtype: list
    """

    question_list = []
    if questions:
        for question in questions:
            question_data = {
                'question_id': question.id,
                'question': question.question,
                'type': question.question_type,
                'placeholder': question.placeholder,
                'is_active': question.is_active,
                'is_ai': question.is_ai,
                'ai_prompt': question.ai_prompt,
                'na_applicable': question.na_applicable,
                'helping_text': question.helping_text
            }
            if question.question_type == 'radio':
                question_data['options'] = get_options(question_id=question.id)
            question_list.append(question_data)
    if len(question_list) == 0:
        return None
    return question_list


@csrf_exempt
@login_required
def create_or_update_answer_view(request):
    """
    View to create a answer if not existing in db.
    Otherwise update
    """

    if request.method == 'POST':
        #Todo: Optimize using ids only
        section_id = Section.objects.get(id=int(request.POST.get('section_id')))
        question_id = Question.objects.get(id=int(request.POST.get('question_id')))
        user_document_id = UserDocument.objects.get(id=int(request.POST.get('user_document_id')))
        answer_text = request.POST.get('new_answer_text')

        answer = Answer.objects.filter(
                section=section_id,
                question=question_id,
                user_document=user_document_id
        ).first()
        if answer:
            answer.answer = answer_text
            answer.save()
        else:
            answer = Answer.objects.create(
                    section=section_id,
                    question=question_id,
                    user_document=user_document_id,
                    answer = answer_text
            )
        return JsonResponse({'status': 'success'})
    else:
        return JsonResponse({'status': 'error', 'message': 'Invalid request method'})


@csrf_exempt
@login_required
def delete_empty_answer(request):
    """
    View to delete empty answer.
    """

    if request.method == 'POST':
        section_id = Section.objects.get(id=int(request.POST.get('section_id')))
        question_id = Question.objects.get(id=int(request.POST.get('question_id')))
        user_document_id = UserDocument.objects.get(id=int(request.POST.get('user_document_id')))
        answer_text = request.POST.get('new_answer_text')

        answer = Answer.objects.filter(
                section=section_id,
                question=question_id,
                user_document=user_document_id
        ).first()
        if answer:
            if answer_text.strip() == '':
                answer.delete()

        return JsonResponse({'status': 'success'})
    else:
        return JsonResponse({'status': 'error', 'message': 'Invalid request method'})


@csrf_exempt
@login_required
def create_or_update_image_answer_view(request):
    """
    View to create an image answer if not existing in db.
    Otherwise update
    """

    if request.method == 'POST':

        #Todo: Optimize using ids only
        section_id = request.POST.get('section_id')
        question_id = request.POST.get('question_id')
        user_document_id = request.POST.get('user_document_id')
        new_answer_file = request.FILES.get('new_answer_text')

        if new_answer_file.content_type.startswith('image'):

            answer = Answer.objects.filter(
                section_id=section_id,
                question_id=question_id,
                user_document_id=user_document_id
            ).first()
            if answer:
                file_name = answer.answer
                # s3_client = S3_Client()
                # key = s3_client.upload_image_file_to_s3(new_answer_file, file_name)
                gcs = GCS_Client()
                key = gcs.upload_image_file_to_gcs(new_answer_file, file_name)
                if not key:
                    return JsonResponse({'error': 'Image upload failed'}, status=400)
                
            else:
                file_name = f"{user_document_id}-{section_id}-{question_id}.{new_answer_file.name.split('.')[-1]}"
                # s3_client = S3_Client()
                # key = s3_client.upload_image_file_to_s3(new_answer_file, file_name)
                gcs = GCS_Client()
                key = gcs.upload_image_file_to_gcs(new_answer_file, file_name)
                if key:
                    answer = Answer.objects.create(
                            section_id=section_id,
                            question_id=question_id,
                            user_document_id=user_document_id,
                            answer = file_name
                    )
                else:
                    return JsonResponse({'error': 'Image upload failed'}, status=400)

            return JsonResponse({'success': True})
        else:
            return JsonResponse({'error': 'Uploaded file is not an image'}, status=400)
    else:
        return JsonResponse({'error': 'Method not allowed'}, status=405)


def get_section_progress(request, section_id:int, user_document_id:int):
    """
    Returns the progress of a section in boolean.
    Checks if answers in a section are there or not

    :param section_id: Id of the section
    :type section_id: int
    :param user_document_id: Id of the user document
    :type user_document_id: int
    """

    user_document_obj = UserDocument.objects.get(id=user_document_id)
    section = get_subsection_by_id(user_document_obj.document_json, section_id)

    for question in section['questions']:
        if question['is_active']:
            answer = check_answer_in_db(section_id, user_document_id, question['question_id'])
            if not answer:
                return JsonResponse({'progress': False})
            if answer and answer.answer == '':
                return JsonResponse({'progress': False})
            if question['type'] == 'radio' and not get_radio_nested_progress(question, answer, section_id, user_document_id):
                return JsonResponse({'progress': False})
    return JsonResponse({'progress': True})


def get_radio_nested_progress(question:dict, db_answer:Answer, section_id:int, user_document_id:int) -> bool:
    """
    Gets the nested progress of radio field

    :param question: Dict containing the question fields
    :type question: dict
    :param db_answer: Object of an answer stored in db for a radio option
    :type db_answer: Answer
    :param section_id: Id of the section
    :type section_id: int
    :param user_document_id: Id of the user document
    :type user_document_id: int
    :return: If the progress is complete or not
    :rtype: bool
    """

    for option in question['options']:
        if option['option_value'] == db_answer.answer and 'questions' in option:
            for option_question in option['questions']:
                if option_question['is_active']:
                    answer = check_answer_in_db(section_id, user_document_id, option_question['question_id'])
                    if not answer:
                        return False
                    if answer and answer.answer == '':
                        return False
                    if option_question['type'] == 'radio' and not get_radio_nested_progress(option_question, answer, section_id, user_document_id):
                        return False
    return True

        
def get_subsection_by_id(document_json:dict, section_id:int) -> dict:
    """
    Returns subsection in a document json corresponding to an id

    :param document_json: Json of a document
    :type document_json: Dict
    :param section_id: Id of the section
    :type section_id: int
    :returns: subsection corresponding to the id
    :rtype: dict
    """

    for section in document_json['sections']:
        if 'subsections' in section:
            for subsection in section['subsections']:
                if subsection['section_id'] == section_id:
                    return subsection
    return None


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


def get_section_subsections(document_json:dict, section_id:int) -> list:
    """
    Get the subsections belonging to a certain section

    :param document_json: JSON of the document
    :type document_json: dict
    :param section_id: ID of the section
    :type section_id: int
    :return: List of the subsections belonging to the section
    :rtype: list
    """

    for section in document_json['sections']:
        if section['section_id'] == section_id:
            return section['subsections']

    return None


def get_parent_section_progress(request, section_id:int, user_document_id:int):
    """
    Returns the progress of a section

    :param section_id: ID of the section
    :type section_id: int
    :user_document_id: ID of the user document
    :type document_id: int
    :returns: if the section progress is complete
    :rtype: json
    """

    user_document_obj = UserDocument.objects.get(id=user_document_id)
    subsections_list = get_section_subsections(user_document_obj.document_json, section_id)

    for subsection in subsections_list:
        for question in subsection['questions']:
            if question['is_active']:
                answer = check_answer_in_db(subsection['section_id'], user_document_id, question['question_id'])
                
                if not answer:
                    return JsonResponse({'progress': False})
                if answer and answer.answer == '':
                    return JsonResponse({'progress': False})
                if question['type'] == 'radio' and not get_radio_nested_progress(question, answer, subsection['section_id'], user_document_id):
                    return JsonResponse({'progress': False})
        
    return JsonResponse({'progress': True})


def get_next_sections_navigation(document_id:int, document_json:dict, current_subsection_id:int) -> dict:
    """
    Get the next section navigations parameters

    :user_document_id: ID of the user document
    :type document_id: int
    :param document_json: JSON of the document
    :type document_json: dict
    :current_subsection_id: ID of the current subsection
    :type current_subsection_id: int
    :returns: Name and url of the next subsection
    :rtype: dict
    """

    next_subsection_id = None
    next_subsection_name = None
    next_subsection_url = None

    for section_index, section in enumerate(document_json['sections']):
        for subsection_index, subsection in enumerate(section['subsections']):
            if subsection['section_id'] == current_subsection_id:
                if subsection_index < len(section['subsections']) - 1:
                    next_subsection_id = section['subsections'][subsection_index + 1]['section_id']
                    next_subsection_name = section['subsections'][subsection_index + 1]['sectionName']
                else:
                    if section_index < len(document_json['sections']) - 1:
                        next_section = document_json['sections'][section_index + 1]
                        if len(next_section['subsections']) > 0:
                            next_subsection_id = next_section['subsections'][0]['section_id']
                            next_subsection_name = next_section['sectionName']
                break

        if next_subsection_id:
            break

    if next_subsection_id:
        next_subsection_url=f'/document/{document_id}/{next_subsection_id}'

    return {
        'next_subsection_name': next_subsection_name,
        'next_subsection_url': next_subsection_url
    }   


def get_previous_sections_navigation(document_id:int, document_json:dict, current_subsection_id:int) -> dict:
    """
    Get the previous section navigations parameters

    :user_document_id: ID of the user document
    :type document_id: int
    :param document_json: JSON of the document
    :type document_json: dict
    :current_subsection_id: ID of the current subsection
    :type current_subsection_id: int
    :returns: Name and url of the previous subsection
    :rtype: dict
    """

    previous_subsection_id = None
    previous_subsection_name = None
    previous_subsection_url = None

    for section_index, section in enumerate(document_json['sections']):
        for subsection_index, subsection in enumerate(section['subsections']):
            if subsection['section_id'] == current_subsection_id:
                if subsection_index > 0:
                    previous_subsection_id = section['subsections'][subsection_index - 1]['section_id']
                    previous_subsection_name = section['subsections'][subsection_index - 1]['sectionName']
                else:
                    if section_index > 0:
                        previous_section = document_json['sections'][section_index - 1]
                        if len(previous_section['subsections']) > 0:
                            previous_subsection_index = len(previous_section['subsections']) - 1
                            previous_subsection_id = previous_section['subsections'][previous_subsection_index]['section_id']
                            previous_subsection_name = previous_section['sectionName']
                break

        if previous_subsection_id:
            break
    
    if previous_subsection_id:
        previous_subsection_url=f'/document/{document_id}/{previous_subsection_id}'

    return {
        'previous_subsection_name': previous_subsection_name,
        'previous_subsection_url': previous_subsection_url
    } 


@login_required
def get_ai_answer(request):
    """Get AI-generated answer for question"""
    if request.method != 'GET':
        return JsonResponse({'error': 'Invalid request method'}, status=405)
        
    try:
        prompt = request.GET.get('prompt_value')
        if not prompt:
            raise ValueError("Prompt value is required")
            
        ai_service = OPENAI()
        answer = ai_service.get_answer_response(prompt)
        
        return JsonResponse({'answer': answer.content})
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=400)


@login_required
def remove_document(request):
    """Remove document and associated files"""
    if request.method != 'POST':
        return JsonResponse({'error': 'Invalid request method'}, status=405)
        
    document_service = DocumentService()
    
    try:
        document_id = request.POST.get('user_document_id')
        document = get_object_or_404(UserDocument, id=document_id)
        
        # Remove associated files
        storage_service = StorageService()
        failed_files = storage_service.remove_document_files(document)
        
        if failed_files:
            for file_name in failed_files:
                messages.error(
                    request,
                    f'Failed to remove file: {file_name}',
                    extra_tags=MessageType.ERROR.value
                )
        
        # Remove document
        document_name = document.name
        document.delete()
        
        messages.success(
            request,
            f'Document removed: {document_name}',
            extra_tags=MessageType.SUCCESS.value
        )
        return redirect(request.META.get('HTTP_REFERER'))
        
    except Exception as e:
        messages.error(request, str(e))
        return redirect('dashboard')


@login_required
def serve_document_image(request, file_name: str):
    """Serve document image from storage"""
    storage_service = StorageService()
    
    try:
        image_content = storage_service.get_image(file_name)
        if not image_content:
            return HttpResponseNotFound('Image not found')
            
        local_path = storage_service.save_temp_file(image_content, file_name)
        
        # Track file for cleanup
        if not hasattr(request, 'cleanup_files'):
            request.cleanup_files = []
        request.cleanup_files.append(local_path)
        
        return FileResponse(open(local_path, 'rb'))
    except Exception as e:
        return HttpResponseNotFound(str(e))


@login_required
def get_question_video(request):
    """Get video embed code for question"""
    if request.method != 'GET':
        return JsonResponse({'error': 'Invalid request method'}, status=405)
        
    video_service = VideoService()
    
    try:
        question_id = request.GET.get('question_id')
        question = get_object_or_404(Question, id=int(question_id))
        
        embed_code = video_service.get_question_video(question)
        return JsonResponse({'video_embed_code': embed_code})
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=400)
