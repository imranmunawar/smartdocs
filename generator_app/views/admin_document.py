from ..models import Section, Question, Option, Answer, Template, UserDocument, Category
from django.contrib.auth.decorators import login_required, user_passes_test
from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponseRedirect, HttpResponseForbidden, JsonResponse
from django.conf import settings
from ..enums import messageEnum
from django.contrib import messages
from django.http import QueryDict
from generator_app.views.utils import validate_vimeo_link
# from ..s3.client import S3_Client
from ..gcs.client import GCS_Client
from generator_app.views.utils import placeholder_validation, template_modified
from django.shortcuts import get_object_or_404
from django.http import JsonResponse
import json
import re
from ..services.admin import TemplateManagementService, AdminTemplateService
from ..models import AdminTemplate, AdminSection, AdminQuestion

def is_admin_user(user):
    """Verify if user has admin privileges"""
    return user.is_staff and user.is_active

@login_required
@user_passes_test(is_admin_user)
def admin_template_management(request, template_id: int):
    """
    Admin interface for template management and configuration
    """
    template_service = AdminTemplateService()
    
    try:
        template_details = template_service.get_template_details(template_id)
        template_sections = template_service.get_template_sections(template_id)
        template_metrics = template_service.get_template_metrics(template_id)
        
        context = {
            'template_details': template_details,
            'template_sections': template_sections,
            'template_metrics': template_metrics,
            'admin_metrics': template_service.get_admin_dashboard_metrics()
        }
        
        return render(request, 'admin/templates/management.html', context)
    except Exception as e:
        messages.error(request, f"Admin Error: {str(e)}")
        return redirect('admin:dashboard')

@login_required
@user_passes_test(is_admin_user)
def admin_template_update(request, template_id: int):
    """
    Handle template updates from admin interface
    """
    if request.method != 'POST':
        return JsonResponse({'error': 'Invalid request method'}, status=405)
        
    template_service = TemplateManagementService()
    
    try:
        updated_template = template_service.update_template(
            template_id=template_id,
            update_data=request.POST,
            admin_user=request.user
        )
        return JsonResponse({'status': 'success', 'template': updated_template})
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=400)

@login_required
def view_template_sections(request, template_id:int):
    """
    View to add view a sections present in a template

    :param template_id: ID of the template
    :type template_id: int
    """

    if request.user.is_staff:
        
        template = Template.objects.get(
                id=template_id
        )

        can_remove = True
        document_exists = UserDocument.objects.filter(
            template_id=template_id
        ).exists()
        if document_exists:
            can_remove = False
        
        sections = Section.objects.filter(
            template_id=template_id, 
            parent_section__isnull=True
        ).order_by('sequence_id')
        max_count = sections.count() + 1


        parent_category = Category.objects.get(id=template.category.id)
        category_hierarchy = get_child_categories(parent_category)

        category_hierarchy.append({
            'id': template_id,
            'name': template.name,
            'type': 'template',
            'parent_category_id': None,
        })

        context = {
            'sections': sections,
            'template': template,
            'template_id': template_id,
            'can_remove': can_remove,
            'admin_user': True,
            'max_count': max_count,
            'category_hierarchy': category_hierarchy
        }
        if not template.is_active:
            messages.error(request, 'This template is inactive', extra_tags=messageEnum.DANGER.value)
        return render(request, 'generator_app/admin_template.html', context=context)

    else:
        return HttpResponseRedirect('/login')
    

def get_child_categories(category:Category) -> list:

    category_hierarchy = []
    step = category
    while step != None:
        category_hierarchy.append({
            'id': step.id,
            'name': step.name,
            'type': 'category',
            'parent_category_id': step.parent_category_id,
        })
        step = step.parent_category

    category_hierarchy.reverse()
    return category_hierarchy


@login_required
def add_template_section(request):
    """
    View to add a section in template
    """

    if request.user.is_staff:
        if request.method == 'POST':
            template_id = request.POST.get('template_id')
            section_name = request.POST.get('section_name')
            is_active = request.POST.get('is_active')
            sequence_id = request.POST.get('sequence_id')
            vimeo_embed_code = request.POST.get('vimeo_link')
            video_timestamp = request.POST.get('video_timestamp')

            if video_timestamp == '':
                video_timestamp = None
            else:
                video_timestamp = int(video_timestamp) 

            new_section = Section.objects.create(
                template_id=template_id,
                name=section_name,
                is_active=is_active,
                sequence_id=sequence_id,
                vimeo_link = vimeo_embed_code,
                vimeo_timestamp = video_timestamp
            )
            messages.warning(request, f'New section added: {section_name}', extra_tags=messageEnum.SUCCESS.value)
            UserDocument.objects.filter(template_id=template_id).update(is_synced=False)
            
            template_modified(template_id)

            return redirect(request.META.get('HTTP_REFERER'))

    else:
        return HttpResponseRedirect('/login')


@login_required
def view_section_subsections(request, template_id:int, section_id:int):
    """
    View subsection belonging to a section

    :param template_id: ID of the template
    :type template_id: int
    :param section_id: ID of the section
    :type section_id: int
    """

    if request.user.is_staff:

        can_remove = True
        document_exists = UserDocument.objects.filter(
            template_id=template_id
        ).exists()
        if document_exists:
            can_remove = False
        section = Section.objects.get(id=section_id)
        subsections = Section.objects.filter(
            template_id=template_id, 
            parent_section_id=section_id
        ).order_by('sequence_id')

        template = Template.objects.get(
                id=template_id
        )
        navigation_text = f'{template.name} / {section.name}'
        max_count = subsections.count() + 1


        parent_category = Category.objects.get(id=template.category.id)
        category_hierarchy = get_child_categories(parent_category)

        category_hierarchy.append({
            'id': template_id,
            'name': template.name,
            'type': 'template',
            'parent_category_id': None,
        })

        category_hierarchy.append({
            'id': section_id,
            'name': section.name,
            'type': 'section',
            'parent_category_id': None,
        })


        context = {
            'subsections': subsections,
            'template_id': template_id,
            'section_id': section_id,
            'can_remove': can_remove,
            'parent_section': section,
            'navigation_text': navigation_text,
            'admin_user': True,
            'max_count': max_count,
            'category_hierarchy': category_hierarchy
        }
        if not template.is_active:
            messages.error(request, 'This template is inactive', extra_tags=messageEnum.DANGER.value)
        return render(request, 'generator_app/admin_subsections.html', context=context)

    else:
        return HttpResponseRedirect('/login')


@login_required
def add_template_subsection(request):
    """
    View to add a subsection in template
    """

    if request.user.is_staff:

        if request.method == 'POST':

            template_id = request.POST.get('template_id')
            section_id = request.POST.get('section_id')
            section_name = request.POST.get('subsection_name')
            is_active = request.POST.get('is_active')
            sequence_id = request.POST.get('sequence_id')
            # vimeo_link = request.POST.get('vimeo_link')
            vimeo_embed_code = request.POST.get('vimeo_link')
            video_timestamp = request.POST.get('video_timestamp')

            # if vimeo_link and vimeo_link != '' and not validate_vimeo_link(vimeo_link):
            #     messages.error(request, f'Failed to add new sub section: Invalid Vimeo link', extra_tags=messageEnum.DANGER.value)
            #     return redirect(request.META.get('HTTP_REFERER'))

            # if vimeo_embed_code and video_timestamp.isdigit() and int(video_timestamp) >= 0:
            #     src_index_start = vimeo_embed_code.find('src="') + 5
            #     src_index_end = vimeo_embed_code.find('"', src_index_start)
            #     vimeo_url = vimeo_embed_code[src_index_start:src_index_end]
            #     if '#t=' not in vimeo_url:
            #         vimeo_url += f"#t={video_timestamp}s"
            #     vimeo_embed_code = f'{vimeo_embed_code[:src_index_start]}{vimeo_url}{vimeo_embed_code[src_index_end:]}'

            if video_timestamp == '':
                video_timestamp = None
            else:
                video_timestamp = int(video_timestamp) 
                
            new_section = Section.objects.create(
                template_id=template_id,
                parent_section_id=section_id,
                name=section_name,
                is_active=is_active,
                sequence_id=sequence_id,
                vimeo_link = vimeo_embed_code,
                vimeo_timestamp = video_timestamp
            )
            messages.warning(request, f'New sub section added: {section_name}', extra_tags=messageEnum.SUCCESS.value)
            UserDocument.objects.filter(template_id=template_id).update(is_synced=False)
            template_modified(template_id)

            return redirect(request.META.get('HTTP_REFERER'))

    else:
        return HttpResponseRedirect('/login')


@login_required
def get_root_questions(request, template_id:int, section_id:int):
    """
    View to get the parent questions in a subsection

    :param template_id: ID of the template
    :type template_id: int
    :param section_id: ID of the section
    :type section_id: int
    """

    if request.user.is_staff:
    
        try:
            questions_list = []

            can_remove = True
            document_exists = UserDocument.objects.filter(
                template_id=template_id
            ).exists()
            if document_exists:
                can_remove = False
            
            section = Section.objects.get(
                id=section_id
            )
            return_url = f'/view_section_subsections/{template_id}/{section.parent_section_id}'
            questions = Question.objects.filter(
                template_id=template_id,
                section_id=section_id,
                parent_question__isnull=True
            ).order_by('sequence_id')

            for question in questions:
                question_data = {}
                question_data['question'] = question
                if question.question_type == 'radio':
                    options = Option.objects.filter(
                        question_id=question.id
                    )
                    question_data['options'] = options

                questions_list.append(question_data)

            template = Template.objects.get(
                    id=template_id
            )
            navigation_text = f'{template.name} / {section.parent_section.name} /{section.name}'
            max_count = questions.count() + 1

            parent_category = Category.objects.get(id=template.category.id)
            category_hierarchy = get_child_categories(parent_category)

            category_hierarchy.append({
                'id': template_id,
                'name': template.name,
                'type': 'template',
                'parent_category_id': None,
            })

            category_hierarchy.append({
                'id': section.parent_section_id,
                'name': section.parent_section.name,
                'type': 'section',
                'parent_category_id': None,
            })

            category_hierarchy.append({
                'id': section_id,
                'name': section.name,
                'type': 'question',
                'parent_category_id': None,
            })

            context = {
                'questions': questions_list,
                'template_id': template_id,
                'section_id': section_id,
                'return_url': return_url,
                'can_remove': can_remove,
                'parent_subsection': section,
                'navigation_text': navigation_text,
                'admin_user': True,
                'max_count': max_count,
                'category_hierarchy': category_hierarchy
            }
            if not template.is_active:
                messages.error(request, 'This template is inactive', extra_tags=messageEnum.DANGER.value)
            return render(request, 'generator_app/admin_questions.html', context=context)
        except Section.DoesNotExist:
            print(f"Error while getting root questions")
            messages.error(request, f'Selected section is deleted', extra_tags=messageEnum.DANGER.value)
            return redirect(request.META.get('HTTP_REFERER'))
    else:
        return HttpResponseRedirect('/login')


@login_required
def get_questins_and_placeholders(request, template_id:int):
    """
    View to get all the questions and placeholders for the template

    :param template_id: ID of the template
    :type template_id: int
    """

    if request.user.is_staff:

        questions_list = []
        template = Template.objects.get(id=template_id)
        return_url = f'/admin_categories/{template.category.id}'
        # questions = Question.objects.filter(
        #     template_id=template_id,
        # ).order_by('sequence_id')
        
        questions = Question.objects.filter(template_id=template_id).select_related('section').order_by(
            'section__parent_section__sequence_id',  # Order by parent section (main section)
            'section__sequence_id',  # Then by sub-section sequence_id
            'sequence_id'  # Finally, by question sequence_id
        )

        for question in questions:
                question_data = {}
                question_data['question'] = question
                if question.question_type == 'radio':
                    options = Option.objects.filter(
                        question_id=question.id
                    )
                    question_data['options'] = options

                questions_list.append(question_data)

        navigation_text = f'{template.name} / Questions and Placeholders'
        context = {
            'questions': questions_list,
            'template_id': template_id,
            'return_url': return_url,
            'navigation_text': navigation_text
        }
        if not template.is_active:
            messages.error(request, 'This template is inactive', extra_tags=messageEnum.DANGER.value)
        return render(request, 'generator_app/admin_questions_placeholders.html', context=context)

    else:
        return HttpResponseRedirect('/login')


@login_required
def create_question(request):
    """
    View to add a question
    """
    
    if request.user.is_staff:

        if request.method == 'POST':

            template_id = request.POST.get('template_id')
            section_id = request.POST.get('section_id')
            question_text = request.POST.get('question_text')
            is_active = request.POST.get('is_active')
            question_type = request.POST.get('question_type')
            options = request.POST.getlist('option')
            is_ai = request.POST.get('is_ai')
            sequence_id = request.POST.get('sequence_id')
            ai_prompt = ''
            request_prompt = request.POST.get('ai_prompt')
            if is_ai == 'True' and request_prompt != '':
                ai_prompt = request_prompt
            elif is_ai == 'True' and request_prompt == '':
                ai_prompt = question_text
            na_applicable = request.POST.get('na_applicable')
            helping_text = request.POST.get('helping_text')

            vimeo_embed_code = request.POST.get('vimeo_link')
            video_timestamp = request.POST.get('video_timestamp')

            if video_timestamp == '':
                video_timestamp = None
            else:
                video_timestamp = int(video_timestamp) 

            
            question_placeholder = request.POST.get('question_placeholder')
            if not placeholder_validation(question_placeholder):
                messages.error(request,
                               f'Invalid Placeholder -  Placeholder must be alphanumeric with underscores and inside ${{}}:{question_placeholder}',
                               extra_tags=messageEnum.DANGER.value
                )
            else:
                new_question = Question.objects.create(
                    question=question_text,
                    placeholder=question_placeholder,
                    question_type=question_type,
                    template_id=template_id,
                    section_id=section_id,
                    is_ai=is_ai,
                    ai_prompt=ai_prompt,
                    na_applicable=na_applicable,
                    helping_text=helping_text,
                    is_active=is_active,
                    sequence_id=sequence_id,
                    vimeo_link = vimeo_embed_code,
                    vimeo_timestamp = video_timestamp
                )

                if question_type == 'radio':
                    for option in options:
                        if option != '':
                            Option.objects.create(
                                name=option,
                                question_id=new_question.id
                            )
            
                messages.warning(request, f'New question added: {question_text}', extra_tags=messageEnum.SUCCESS.value)
                UserDocument.objects.filter(template_id=template_id).update(is_synced=False)
                template_modified(template_id)

                left_placeholders = match_template_placeholders(template_id)
                if left_placeholders:

                    new_template = Template.objects.get(
                        id=template_id
                    )

                    messages.error(request, f'This template has been deactivated. It will not be visible to the users now. Please make questions for following placeholders: {left_placeholders}', extra_tags=messageEnum.DANGER.value)
                    new_template.is_active = False
                    new_template.save()
            
        return redirect(request.META.get('HTTP_REFERER'))

    else:
        return HttpResponseRedirect('/login')


def match_template_placeholders(template_id):

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

    multiple_placeholders = merge_variables(simple_unmatched_placeholders)
    
    multiple_unmatched_placeholders = [
        placeholder for placeholder in multiple_placeholders
        if placeholder not in question_placeholders
    ]

    print('---> ALL (SIMPLE + MULTIPLE) UNMATCHED PLACEHOLDERS', multiple_unmatched_placeholders)

    return multiple_unmatched_placeholders


def merge_variables(variable_list):
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


@login_required
def get_child_questions(request, template_id:int, section_id:int, question_id:int):
    """
    Gets the child questions of a question

    :param template_id: ID of the template
    :type template_id: int
    :param section_id: ID of the section
    :type section_id: int
    :param question_id: ID of the question
    :type question_id: int
    """

    if request.user.is_staff:
        
        return_url = ''
        questions_list = []

        can_remove = True
        document_exists = UserDocument.objects.filter(
            template_id=template_id
        ).exists()
        if document_exists:
            can_remove = False
        
        p_question = Question.objects.get(
            id=question_id
        )
        p_options = Option.objects.filter(
            question_id=p_question.id
        )
        parent_question = {
            'question': p_question,
            'options': p_options
        }
        
        for option in p_options:
            questions = option.child_questions.all().order_by('sequence_id')
            for question in questions:
                question_data = {}
                question_data['parent_option'] = option.name
                question_data['question'] = question
                if question.question_type == 'radio':
                    options = Option.objects.filter(
                        question_id=question.id
                    )
                    question_data['options'] = options

                questions_list.append(question_data)

        if p_question.parent_question == None:
            return_url = f'/get_root_questions/{template_id}/{section_id}'
            print("return_url111:", return_url)
        else:
            return_url = f'/get_child_questions/{template_id}/{section_id}/{p_question.parent_question_id}'
            print("return_url222:", return_url)
        
        template = Template.objects.get(
                id=template_id
        )
        section = Section.objects.get(
            id=section_id
        )

        navigation_text = f'{template.name} / {section.parent_section.name} /{section.name}'


        parent_category = Category.objects.get(id=template.category.id)
        category_hierarchy = get_child_categories(parent_category)

        category_hierarchy.append({
                'id': template_id,
                'name': template.name,
                'type': 'template',
                'parent_category_id': None,
            })

        category_hierarchy.append({
                'id': section.parent_section_id,
                'name': section.parent_section.name,
                'type': 'section',
                'parent_category_id': None,
            })

        category_hierarchy.append({
                'id': section_id,
                'name': section.name,
                'type': 'question',
                'parent_category_id': None,
            })
        

        navigation_questions = []
        navigation_questions_hierarchy = []
        nav_ques = p_question
        while nav_ques != None:
            navigation_questions.append(nav_ques)
            
            navigation_questions_hierarchy.append({
                    'id': nav_ques.id,
                    'name': nav_ques.question,
                    'type': 'subquestion',
                    'parent_category_id': None,
                })
            nav_ques = nav_ques.parent_question

        navigation_questions.reverse()
        navigation_questions_hierarchy.reverse()

        category_hierarchy.extend(navigation_questions_hierarchy)

        
        context = {
            'questions': questions_list,
            'template_id': template_id,
            'section_id': section_id,
            'parent_question': parent_question,
            'return_url': return_url,
            'can_remove': can_remove,
            'options': p_options,
            'navigation_text': navigation_text,
            'navigation_questions': navigation_questions,
            'admin_user': True,
            'category_hierarchy': category_hierarchy
        }
        if not template.is_active:
            messages.error(request, 'This template is inactive', extra_tags=messageEnum.DANGER.value)
        return render(request, 'generator_app/admin_subquestions.html', context=context)

    else:
        return HttpResponseRedirect('/login')


@login_required
def create_subquestion(request):
    """
    Creates a new subquestion
    """

    if request.user.is_staff:

        if request.method == 'POST':

            template_id = request.POST.get('template_id')
            section_id = request.POST.get('section_id')
            question_text = request.POST.get('question_text')
            question_type = request.POST.get('question_type')
            options = request.POST.getlist('option')
            question_placeholder = request.POST.get('question_placeholder')
            parent_option_id = request.POST.get('parent_option_id')
            parent_question_id = request.POST.get('parent_question_id')
            is_active = request.POST.get('is_active')
            is_ai = request.POST.get('is_ai')
            sequence_id = request.POST.get('sequence_id')
            ai_prompt = ''
            request_prompt = request.POST.get('ai_prompt')
            if is_ai == 'True' and request_prompt != '':
                ai_prompt = request_prompt
            elif is_ai == 'True' and request_prompt == '':
                ai_prompt = question_text
            na_applicable = request.POST.get('na_applicable')
            helping_text = request.POST.get('helping_text')

            vimeo_embed_code = request.POST.get('vimeo_link')
            video_timestamp = request.POST.get('video_timestamp')

            if video_timestamp == '':
                video_timestamp = None
            else:
                video_timestamp = int(video_timestamp) 

            if not placeholder_validation(question_placeholder):
                messages.error(request,
                               f'Invalid Placeholder -  Placeholder must be alphanumeric with underscores and inside ${{}}:{question_placeholder}',
                               extra_tags=messageEnum.DANGER.value
                )
            else:

                new_question = Question.objects.create(
                    question=question_text,
                    placeholder=question_placeholder,
                    question_type=question_type,
                    template_id=template_id,
                    section_id=section_id,
                    parent_question_id=parent_question_id,
                    is_ai=is_ai,
                    ai_prompt=ai_prompt,
                    na_applicable=na_applicable,
                    helping_text=helping_text,
                    is_active=is_active,
                    sequence_id=sequence_id,
                    vimeo_link = vimeo_embed_code,
                    vimeo_timestamp = video_timestamp
                )
                if question_type == 'radio':
                    for option in options:
                        Option.objects.create(
                            name=option,
                            question_id=new_question.id
                        )
                parent_option = Option.objects.get(
                    id=parent_option_id
                )

                parent_option.child_questions.add(new_question)

                messages.warning(request, f'New sub question added: {question_text}', extra_tags=messageEnum.SUCCESS.value)    
                UserDocument.objects.filter(template_id=template_id).update(is_synced=False)
                template_modified(template_id)

                left_placeholders = match_template_placeholders(template_id)
                if left_placeholders:

                    new_template = Template.objects.get(
                        id=template_id
                    )

                    messages.error(request, f'This template has been deactivated. It will not be visible to the users now. Please make questions for following placeholders: {left_placeholders}', extra_tags=messageEnum.DANGER.value)
                    new_template.is_active = False
                    new_template.save()

        updated_url = remove_params(request.META.get('HTTP_REFERER'))
        return redirect(updated_url)
    else:
        return HttpResponseRedirect('/login')



def is_data_changed(question, question_text, question_placeholder, is_ai, ai_prompt, 
                    na_applicable, helping_text, is_active, sequence_id, question_type, options, vimeo_embed_code, video_timestamp):
    """
    Checks if any data has changed for the question
    """

    filtered_options = [item for item in options if item]

    return (
        question.question != question_text or
        question.placeholder != question_placeholder or
        str(question.is_ai) != is_ai or
        question.ai_prompt != ai_prompt or
        str(question.na_applicable) != na_applicable or
        question.helping_text != helping_text or
        str(question.is_active) != is_active or
        str(question.sequence_id) != sequence_id or
        question.question_type != question_type or
        str(question.vimeo_link) != vimeo_embed_code or
        str(question.vimeo_timestamp) != str(video_timestamp) or
        (len(filtered_options) > 0)
    )


@login_required
def update_question(request):
    """
    Updates a question
    """

    if request.user.is_staff:

        if request.method == 'POST':
            question_text = request.POST.get('question_text')
            options = request.POST.getlist('option')
            question_placeholder = request.POST.get('question_placeholder')
            question_id = request.POST.get('question_id')
            is_ai = request.POST.get('edit_is_ai')
            is_active = request.POST.get('is_active')
            ai_prompt = ''

            request_prompt = request.POST.get('edit_ai_prompt')
            if is_ai == 'True' and request_prompt != '':
                ai_prompt = request_prompt
            elif is_ai == 'True' and request_prompt == '':
                ai_prompt = question_text

            na_applicable = request.POST.get('na_applicable')
            helping_text = request.POST.get('helping_text')
            sequence_id = request.POST.get('sequence_id')

            question_type_new = request.POST.get('question_type_edit')
            question_type_previous = request.POST.get('question_type_previous')

            vimeo_embed_code = request.POST.get('vimeo_link')
            video_timestamp = request.POST.get('video_timestamp')
            
            if video_timestamp == '':
                video_timestamp = None
            else:
                video_timestamp = int(video_timestamp) 
                
            update_question = Question.objects.get(
                id=question_id
            )            

            if not placeholder_validation(question_placeholder):
                messages.error(request,
                               f'Invalid Placeholder -  Placeholder must be alphanumeric with underscores and inside ${{}}:{question_placeholder}',
                               extra_tags=messageEnum.DANGER.value
                )
            else:
                if is_data_changed(update_question, question_text, question_placeholder, is_ai, 
                                   ai_prompt, na_applicable, helping_text, is_active, sequence_id, question_type_new, options,
                                   vimeo_embed_code, video_timestamp):
                    
                    
                    if question_type_new != question_type_previous:

                        if question_type_previous== 'radio':
                            p_options = Option.objects.filter(
                                    question_id=question_id)
                                   
                            for option in p_options:
                                questions = option.child_questions.all().order_by('sequence_id')
                                for question in questions:
                                    question.delete()
                                option.delete()
              

                    if question_type_new == 'radio':
                        for option in options:
                            if option != '':
                                Option.objects.create(
                                    name=option,
                                    question_id=update_question.id
                                )

                    template_id = update_question.template.id
                    UserDocument.objects.filter(template_id=template_id).update(is_synced=False)
                    template_modified(template_id)

                    # s3_client = S3_Client()
                    gcs = GCS_Client()
                    relevant_answers = Answer.objects.filter(question_id=update_question.id)
                    for answer in relevant_answers:
                        if answer.question.question_type == 'image':
                            file_name = answer.answer
                            # success = s3_client.remove_image_from_s3(file_name)
                            success = gcs.remove_image_from_gcs(file_name)
                            if not success:
                                messages.error(request, f'Error removing image: {file_name} from S3.', extra_tags='danger')

                        answer.delete()
                    
                    update_question.question=question_text
                    update_question.placeholder=question_placeholder
                    update_question.is_ai=is_ai
                    update_question.ai_prompt=ai_prompt
                    update_question.na_applicable=na_applicable
                    update_question.helping_text=helping_text
                    update_question.is_active=is_active
                    update_question.sequence_id=sequence_id
                    update_question.question_type=question_type_new
                    update_question.vimeo_link = vimeo_embed_code
                    update_question.vimeo_timestamp = video_timestamp

                    update_question.save()

                    messages.warning(request, f'Question updated: {update_question.id}', extra_tags=messageEnum.SUCCESS.value) 

                    left_placeholders = match_template_placeholders(template_id)
                    if left_placeholders:

                        new_template = Template.objects.get(
                            id=template_id
                        )

                        messages.error(request, f'This template has been deactivated. It will not be visible to the users now. Please make questions for following placeholders: {left_placeholders}', extra_tags=messageEnum.DANGER.value)
                        new_template.is_active = False
                        new_template.save()
        
        updated_url = remove_params(request.META.get('HTTP_REFERER'))
        return redirect(updated_url)

    else:
        return HttpResponseRedirect('/login')


@login_required
def remove_question(request):
    """
    Removes a question
    """

    if request.user.is_staff:

        if request.method == 'POST':
            question_id = request.POST.get('question_id')
            remove_question = Question.objects.get(
                id=question_id
            )
            remove_question.delete()
            remove_question_text = remove_question.question

            template_id = remove_question.template.id
            template_modified(template_id)

            messages.warning(request, f'Question removed: {remove_question_text}', extra_tags=messageEnum.SUCCESS.value) 

            left_placeholders = match_template_placeholders(template_id)
            if left_placeholders:

                new_template = Template.objects.get(
                    id=template_id
                )

                messages.error(request, f'This template has been deactivated. It will not be visible to the users now. Please make questions for following placeholders: {left_placeholders}', extra_tags=messageEnum.DANGER.value)
                new_template.is_active = False
                new_template.save()

            updated_url = remove_params(request.META.get('HTTP_REFERER'))

            
            return redirect(updated_url)
    else:
        return HttpResponseRedirect('/login')


@login_required
def remove_section(request):
    """
    Removes a section
    """

    if request.user.is_staff:

        if request.method == 'POST':
            try:
                section_id = request.POST.get('section_id')
                remove_section = Section.objects.get(
                    id=section_id
                )
                remove_section_name = remove_section.name
                remove_section.delete()

                template_id = remove_section.template.id
                template_modified(template_id)

                left_placeholders = match_template_placeholders(template_id)
                if left_placeholders:

                    new_template = Template.objects.get(
                        id=template_id
                    )

                    messages.error(request, f'This template has been deactivated. It will not be visible to the users now. Please make questions for following placeholders: {left_placeholders}', extra_tags=messageEnum.DANGER.value)
                    new_template.is_active = False
                    new_template.save()

                messages.warning(request, f'Section removed: {remove_section_name}', extra_tags=messageEnum.SUCCESS.value) 
            except Section.DoesNotExist:
                print(f"Error while removing Section")
                messages.error(request, f'Selected section is already deleted', extra_tags=messageEnum.DANGER.value)

            return redirect(request.META.get('HTTP_REFERER'))
    else:
        return HttpResponseRedirect('/login')


@login_required
def update_template_section(request):

    if request.user.is_staff:

        if request.method == 'POST':

            try:
            
                section_id = request.POST.get('section_id')
                section_name = request.POST.get('section_name')
                is_active = request.POST.get('is_active')
                sequence_id = request.POST.get('sequence_id')
                # vimeo_link = request.POST.get('vimeo_link')
                vimeo_embed_code = request.POST.get('vimeo_link')
                video_timestamp = request.POST.get('video_timestamp')
                
                if video_timestamp == '':
                    video_timestamp = None
                else:
                    video_timestamp = int(video_timestamp) 

                section = Section.objects.get(
                    id=section_id
                )
                section.name = section_name
                section.is_active=is_active
                section.sequence_id=sequence_id
                section.vimeo_link = vimeo_embed_code
                section.vimeo_timestamp = video_timestamp
                section.save()

                template_id = section.template.id
                template_modified(template_id)
                
                UserDocument.objects.filter(template_id=template_id).update(is_synced=False)

                messages.warning(request, f'Section updated: {section_name}', extra_tags=messageEnum.SUCCESS.value) 

            except Section.DoesNotExist:
                print(f"Error while updating template section")
                messages.error(request, f'Selected section is already deleted', extra_tags=messageEnum.DANGER.value)

            return redirect(request.META.get('HTTP_REFERER'))
    else:
        return HttpResponseRedirect('/login')

@login_required
def remove_option(request):
    """
    Removes a option
    """

    if request.user.is_staff:

        if request.method == 'POST':

            option_id = request.POST.get('option_id')
            remove_option = Option.objects.get(id=option_id)
            remove_option_name = remove_option.name
            associated_questions = remove_option.child_questions.all()

            for question in associated_questions:
                question.delete()

            remove_option.delete()

            template_id = remove_option.question.template.id
            template_modified(template_id)

            left_placeholders = match_template_placeholders(template_id)
            if left_placeholders:

                new_template = Template.objects.get(
                    id=template_id
                )

                messages.error(request, f'This template has been deactivated. It will not be visible to the users now. Please make questions for following placeholders: {left_placeholders}', extra_tags=messageEnum.DANGER.value)
                new_template.is_active = False
                new_template.save()
            
            messages.warning(request, f'Option removed: {remove_option_name}', extra_tags=messageEnum.SUCCESS.value)
            updated_url = remove_params(request.META.get('HTTP_REFERER'))
            return redirect(updated_url + '?tab=options')
    else:
        return HttpResponseRedirect('/login')


@login_required
def edit_option(request):
    """
    Edits an option
    """

    if request.user.is_staff:

        if request.method == 'POST':

            option_id = request.POST.get('option_id')
            option_name = request.POST.get('option_name')
            edit_option = Option.objects.get(id=option_id)
            is_active = request.POST.get('is_active')

            edit_option.name = option_name
            edit_option.is_active = is_active
            edit_option.save()

            template_id = edit_option.question.template.id
            UserDocument.objects.filter(template_id=template_id).update(is_synced=False)
            Answer.objects.filter(question_id=edit_option.question.id).delete()

            template_modified(template_id)

            messages.warning(request, f'Option updated: {option_name}', extra_tags=messageEnum.SUCCESS.value)
            updated_url = remove_params(request.META.get('HTTP_REFERER'))
            return redirect(updated_url + '?tab=options')
    else:
        return HttpResponseRedirect('/login')


def remove_params(url):
    
    return url.split('?')[0]


@login_required
def bulk_update_sequence_questions(request):
    try:
        sequence_data = request.POST.get('sequence_data')
        
        if sequence_data:     

            sequence_data = json.loads(sequence_data)
            
            # Iterate over the list of question IDs and update their sequence
            for item in sequence_data:
                question_id = item.get('question_id')
                sequence_id = item.get('sequence_id')

                if question_id and sequence_id:
                    question = get_object_or_404(Question, id=question_id)
                    question.sequence_id = sequence_id
                    question.save()

            return JsonResponse({'status': 'success', 'message': 'Sequence updated successfully!'})
        else:
            return JsonResponse({'status': 'error', 'message': 'No sequence data provided'}, status=400)

    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=500)


@login_required
def bulk_update_sequence_sections(request):
    try:
        sequence_data = request.POST.get('sequence_data')
        
        if sequence_data:
            sequence_data = json.loads(sequence_data)
            
            # Iterate over the list of section IDs and update their sequence
            for item in sequence_data:
                section_id = item.get('section_id')
                sequence_id = item.get('sequence_id')

                if section_id and sequence_id:
                    section = get_object_or_404(Section, id=section_id)
                    section.sequence_id = sequence_id
                    section.save()

            return JsonResponse({'status': 'success', 'message': 'Section sequence updated successfully!'})
        else:
            return JsonResponse({'status': 'error', 'message': 'No sequence data provided'}, status=400)

    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=500)
