from ..models import (
    Category, Template, UserDocument, Section, Question
)
from django.contrib.auth.decorators import login_required, user_passes_test
from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponseRedirect, JsonResponse
from django.conf import settings
import os
from ..enums import messageEnum
from django.contrib import messages
from generator_app.helpers.template_duplicate import TemplateDuplicator
import secrets
import string
from ..gcs.client import GCS_Client
from django.db.models import Count
from django.utils import timezone
from django.shortcuts import get_object_or_404
import json
from python_docx_replace import docx_get_keys
from docx import Document
import re
from ..services.admin import (
    AdminCategoryService,
    AdminTemplateService,
    AdminFileService
)
from ..utils.security import generate_secure_hash

def generate_random_hash(length=20):

    characters = string.ascii_letters + string.digits
    random_hash = ''.join(secrets.choice(characters) for _ in range(length))
    return random_hash

def get_template_activity(template_id, template_name):
    has_active_section = False
    has_active_subsection = True
    has_active_questions = True
    error_message = None
    # Get template active section
    active_sections = Section.objects.filter(template_id=template_id, parent_section=None, is_active=True)
    if len(active_sections) > 0:
        has_active_section = True
        for section in active_sections:
            active_subsections = Section.objects.filter(parent_section=section, is_active=True)
            if len(active_subsections) == 0:
                error_message = f"Could not activate template because: Section ({section.name}) has no active Sub Sections"
                has_active_subsection = False
            else:
                for sub_section in active_subsections:
                    active_questions = Question.objects.filter(section=sub_section, is_active=True, parent_question=None)
                    if len(active_questions) == 0:
                        error_message = f"Could not update template because Subsection ({sub_section.name}) has no active Questions"
                        has_active_questions = False
    else:
        error_message = f"Could not update Template ({template_name}) because it has no active section"
    
    return error_message, has_active_section, has_active_subsection, has_active_questions


def is_admin_user(user):
    """Verify if user has admin privileges"""
    return user.is_staff and user.is_active

@login_required
@user_passes_test(is_admin_user)
def admin_category_list(request):
    """Display list of admin categories with hierarchy"""
    category_service = AdminCategoryService()
    
    try:
        root_categories = category_service.get_root_categories()
        category_hierarchy = category_service.build_category_hierarchy()
        empty_categories = category_service.get_empty_categories()

        context = {
            'root_categories': root_categories,
            'category_hierarchy': category_hierarchy,
            'empty_categories': empty_categories,
            'max_sequence': len(root_categories) + 1
        }
        return render(request, 'admin/categories/list.html', context)
    except Exception as e:
        messages.error(request, f"Admin Error: {str(e)}")
        return redirect('admin:dashboard')

@login_required
@user_passes_test(is_admin_user)
def admin_category_detail(request, category_id: int):
    """Display category details with subcategories and templates"""
    category_service = AdminCategoryService()
    template_service = AdminTemplateService()
    
    try:
        category_details = category_service.get_category_details(category_id)
        subcategories = category_service.get_subcategories(category_id)
        category_templates = template_service.get_category_templates(category_id)
        
        context = {
            'category': category_details,
            'subcategories': subcategories,
            'templates': category_templates,
            'hierarchy': category_service.get_category_breadcrumb(category_id),
            'subcategory_max_sequence': len(subcategories) + 1,
            'template_max_sequence': len(category_templates) + 1
        }
        return render(request, 'admin/categories/detail.html', context)
    except Exception as e:
        messages.error(request, f"Admin Error: {str(e)}")
        return redirect('admin:category_list')

@login_required
@user_passes_test(is_admin_user)
def admin_create_template(request):
    """Create new template with file upload"""
    if request.method != 'POST':
        return JsonResponse({'error': 'Invalid request method'}, status=405)

    template_service = AdminTemplateService()
    file_service = AdminFileService()
    
    try:
        template_data = {
            'name': request.POST.get('template_name'),
            'category_id': request.POST.get('category_id'),
            'access_level': request.POST.get('access_level'),
            'sequence_id': request.POST.get('sequence_id'),
            'owner_id': request.user.id
        }

        if 'template_file' not in request.FILES:
            raise ValueError("Template file is required")
            
        template_file = request.FILES['template_file']
        placeholders = file_service.extract_placeholders(template_file)
        
        if not placeholders:
            raise ValueError("No placeholders found in template file")

        file_hash = generate_secure_hash()
        file_path = f'template_{file_hash}.docx'
        
        if file_service.upload_template_file(template_file, file_path):
            template = template_service.create_template(
                template_data=template_data,
                file_path=file_path,
                placeholders=placeholders
            )
            messages.success(request, f'Template created: {template.template_name}')
            return JsonResponse({'status': 'success', 'template_id': template.id})
        else:
            raise ValueError("Failed to upload template file")
            
    except Exception as e:
        messages.error(request, str(e))
        return JsonResponse({'error': str(e)}, status=400)

@login_required
@user_passes_test(is_admin_user)
def admin_update_category_sequence(request):
    """Update category sequence numbers in bulk"""
    if request.method != 'POST':
        return JsonResponse({'error': 'Invalid request method'}, status=405)
        
    category_service = AdminCategoryService()
    
    try:
        sequence_data = request.POST.get('sequence_data')
        if not sequence_data:
            raise ValueError("No sequence data provided")
            
        updated_categories = category_service.update_category_sequence(
            sequence_data=json.loads(sequence_data)
        )
        return JsonResponse({
            'status': 'success',
            'message': f'Updated {len(updated_categories)} categories'
        })
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=400)

@login_required
def admin_categories_page(request):
    """
    View for the categories page
    """

    if request.user.is_staff:
        top_categories = Category.objects.filter(parent_category__isnull=True).order_by('sequence_id')
        categories_max_count = top_categories.count() + 1
        all_categories = Category.objects.all()
        empty_categories = [category for category in all_categories if not category.template_set.exists() and not category.children.exists()]
        hierarchical_categories = []
        for category in top_categories:
            get_sub_categories(hierarchical_categories, category, 0)

        context = {
            'categories': top_categories,
            'all_categories': all_categories,
            'admin_user': True,
            'empty_categories': empty_categories,
            'hierarchical_categories': hierarchical_categories,
            'categories_max_count': categories_max_count
        }
        return render(request, 'generator_app/admin_categories.html', context=context)
    else:
        return HttpResponseRedirect('/')


def get_sub_categories(hierarchical_categories, category, level=0):
    category_dict = {
        'level': level,
        'category': category
    }
    hierarchical_categories.append(category_dict)
    sub_categories = Category.objects.filter(parent_category=category)
    level += 1
    for category in sub_categories:
        get_sub_categories(hierarchical_categories, category, level)


@login_required
def admin_child_categories_page(request, parent_category_id:int):
    """
    View for the child categories page

    :param parent_category_id: Id of the category for which children will be displayed
    :type parent_category_id: int
    """

    if request.user.is_staff:
        try:
            parent_category = Category.objects.get(id=parent_category_id)
            category_hierarchy = get_child_categories(request, parent_category)

            child_categories = parent_category.children.all().order_by('sequence_id')
            categories_max_count = child_categories.count() + 1

            templates = Template.objects.filter(category=parent_category).order_by('sequence_id')
            templates_max_count = templates.count() + 1

            all_categories = Category.objects.all()

            parent_categories = Category.objects.filter(parent_category=None)
            empty_categories = [category for category in all_categories if not category.template_set.exists() and not category.children.exists()]
            hierarchical_categories = []
            for category in parent_categories:
                get_sub_categories(hierarchical_categories, category, 0)

            template_documents = {}
            for template in templates:
                user_documents = UserDocument.objects.filter(
                    template_id = template.id
                )

                if user_documents:
                    template_documents[template.id] = list(user_documents)

            context = {
                'current_category': parent_category_id,
                'categories': child_categories,
                'category_hierarchy': category_hierarchy,
                'templates': templates,
                'template_documents': template_documents,
                'all_categories': all_categories,
                'admin_user': True,
                'hierarchical_categories': hierarchical_categories,
                'empty_categories': empty_categories,
                'categories_max_count': categories_max_count,
                'templates_max_count': templates_max_count
            }

            return render(request, 'generator_app/admin_categories.html', context)
        
        except Category.DoesNotExist:
            print(f"Error while getting admin child categories page")
            messages.error(request, f'Selected category is already deleted', extra_tags=messageEnum.DANGER.value)
            return redirect(request.META.get('HTTP_REFERER'))

    else:
        return HttpResponseRedirect('/login')


@login_required
def get_child_categories(request, category:Category) -> list:
    """
    Helper method
    Return the child category names for a provided category

    :param category: The category for whild children are fetched
    :type category: Category
    :return: The list of the childern categories
    :rtype: list
    """

    category_hierarchy = []
    step = category
    while step != None:
        category_hierarchy.append(step)
        step = step.parent_category

    category_hierarchy.reverse()
    return category_hierarchy


def get_placeholders_from_file(file):
    if file.name.endswith('.docx'):

        temp_file_path = '/tmp/' + file.name
        with open(temp_file_path, 'wb+') as temp_file:
            for chunk in file.chunks():
                temp_file.write(chunk)
        
        doc = Document(temp_file_path)
        placeholders = docx_get_keys(doc)
        placeholders_list = list(placeholders)

        file.seek(0)

        return placeholders_list
    return []


@login_required
def create_template_view(request):
    """
    Creates a new template view
    """

    if request.user.is_staff:
        
        if request.method == 'POST':
            template_name = request.POST.get('template_name')
            category_id =  request.POST.get('category_id')
            access_level = request.POST.get('access_level')
            sequence_id =  request.POST.get('sequence_id')
            user_id = request.user.id

            if 'file' in request.FILES:
                file = request.FILES['file']
                
                placeholders = get_placeholders_from_file(file)

                if not placeholders:
                    messages.warning(request, 'No placeholders found in the uploaded file...', extra_tags=messageEnum.DANGER.value)
                    return redirect(request.META.get('HTTP_REFERER'))
            
                if not file.size > 0:
                    messages.warning(request, 'Please upload a valid file...', extra_tags=messageEnum.DANGER.value)
                    return redirect(request.META.get('HTTP_REFERER'))

                random_hash = generate_random_hash()
                unique_filename = f'template_{random_hash}.docx'

                # s3 = S3_Client()
                gcs = GCS_Client()
                try:
                    # file_key = s3.upload_template_file_to_s3(file, unique_filename)
                    file_key = gcs.upload_template_file_to_gcs(file, unique_filename)

                    if file_key:
                        new_template = Template.objects.create(
                            name=template_name,
                            category_id=category_id,
                            user_id=user_id,
                            access_level=access_level,
                            is_active=False,
                            template_file_name = unique_filename,
                            created_at = timezone.now(), 
                            last_modified = timezone.now(),
                            sequence_id=sequence_id,
                            doc_placeholders=placeholders
                        )

                        messages.warning(request, f'Template created: {template_name}', extra_tags=messageEnum.SUCCESS.value)
                    else:
                        messages.warning(request, 'Template upload failed...', extra_tags=messageEnum.DANGER.value)

                except ValueError as e:
                    messages.warning(request, str(e), extra_tags=messageEnum.DANGER.value)

            else:
                print("NO FILE UPLOADED")
                messages.warning(request, 'Please upload a template file', extra_tags=messageEnum.DANGER.value)

        return redirect(request.META.get('HTTP_REFERER'))

    else:
        return HttpResponseRedirect('/login')


@login_required
def duplicate_template(request):
    if request.method == 'POST':
        template_id = request.POST.get('template_id')
        template_name = request.POST.get('template_name')
        duplicate_questions = request.POST.get('duplicate_questions') == 'true'

        if 'file' in request.FILES:
            file = request.FILES['file']
            duplicator = TemplateDuplicator(template_id, template_name, duplicate_questions, file, request.user)
            duplicator.duplicate()
            messages.warning(request, f'Template duplicated: {template_name}', extra_tags=messageEnum.SUCCESS.value)
        else:
            print("NO FILE UPLOADED")
            messages.warning(request, 'Please upload a template file', extra_tags=messageEnum.DANGER.value)


        print(f"Template Name: {template_name} - Template ID: {template_id} - Duplicate Questions: {duplicate_questions}")
        return redirect(request.META.get('HTTP_REFERER'))


@login_required
def create_category_view(request):
    """
    Create a new category
    """

    if request.user.is_staff:

        if request.method == 'POST':
            category_name = request.POST.get('category_name')
            category_id =  request.POST.get('parent_category_id')
            sequence_id =  request.POST.get('sequence_id')

            #Category status field is for future cases. Currently,
            #is set to True for every case.
            category_status = True
            if category_id == '':
                category_id = None

            Category.objects.create(
                name=category_name,
                status=category_status,
                parent_category_id=category_id,
                sequence_id=sequence_id
            )

        messages.warning(request, f'New Category created: {category_name}', extra_tags=messageEnum.SUCCESS.value)

        return redirect(request.META.get('HTTP_REFERER'))

    else:
        return HttpResponseRedirect('/login')


@login_required
def update_template(request):
    """
    Updates a template view
    """

    if request.user.is_staff:

        if request.method == 'POST':
            template_name = request.POST.get('template_name')
            template_id = request.POST.get('template_id')
            access_level = request.POST.get('access_level')
            is_active = request.POST.get('is_active')
            category_id = request.POST.get('category_id')
            sequence_id = request.POST.get('sequence_id')

            new_template = Template.objects.get(
                id=template_id
            )
            try:
                category = Category.objects.get(id=category_id)
                new_template.category = category
            except Exception as e:
                print('Category not found.')

            new_template.name = template_name
            new_template.access_level = access_level
            new_template.last_modified = timezone.now() 
            new_template.sequence_id = sequence_id

            if 'file' in request.FILES:
                file = request.FILES['file']

                placeholders = get_placeholders_from_file(file)

                if not placeholders:
                    messages.warning(request, 'No placeholders found in the uploaded file...', extra_tags=messageEnum.DANGER.value)
                    return redirect(request.META.get('HTTP_REFERER'))
                
                new_template.doc_placeholders=placeholders

                filename = new_template.template_file_name
                
                if not filename:
                    print("No previous file name found... Making new one")
                    random_hash = generate_random_hash()
                    filename = f'template_{random_hash}.docx'
                    print(filename)

                # s3 = S3_Client()
                # filekey = s3.upload_template_file_to_s3(file, filename)
                gcs = GCS_Client()
                filekey = gcs.update_template_file_in_gcs(file, filename)
                if filekey == None:
                    print("FILE UPLOAD FAILED")
                
            else:
                print("NO FILE UPLOADED")

            if is_active == "True":
                # Check for template file
                if not new_template.template_file_name:
                    messages.error(request, f'Template file was not uploaded for: {template_name}', extra_tags=messageEnum.DANGER.value)
                error_message, has_active_section, has_active_subsection, has_active_questions = get_template_activity(template_id, template_name)

                if has_active_section and has_active_subsection and has_active_questions:
                    new_template.is_active = is_active
                    new_template.save()
                    messages.warning(request, f'Template updated: {template_name}', extra_tags=messageEnum.SUCCESS.value)
                else:
                    messages.error(request, error_message, extra_tags=messageEnum.DANGER.value)
            else:
                new_template.is_active = is_active
                new_template.save()
                messages.warning(request, f'Template updated: {template_name}', extra_tags=messageEnum.SUCCESS.value)

            if is_active == "True":

                left_placeholders = match_template_placeholders(template_id)
                if left_placeholders:
                    messages.error(request, f'This template cannot be activated. Please make questions for following placeholders: {left_placeholders}', extra_tags=messageEnum.DANGER.value)
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
def remove_template(request):
    
    if request.user.is_staff:
        if request.method == 'POST':
            template_id = request.POST.get('template_id')
            template = Template.objects.get(
                id=template_id
            )

            if template.user == None or template.user == request.user:

                template_name = template.name

                if not remove_template_file(template.template_file_name):
                    messages.warning(request, f'Template removed: {template_name}', extra_tags=messageEnum.DANGER.value)
                    return redirect(request.META.get('HTTP_REFERER'))

                user_documents = UserDocument.objects.filter(
                    template_id = template_id
                )

                user_documents = UserDocument.objects.filter(template_id=template_id)
                deleted_count, _ = user_documents.delete()
                print(f"Deleted {deleted_count} UserDocument(s) with template_id={template_id}.")

                template.delete()
                print(f"Deleted template_id={template_id}.")
                messages.warning(request, f'Template removed: {template_name}', extra_tags=messageEnum.SUCCESS.value)

            else:
                messages.warning(request, f'You are not authorized to remove template: {template.name}', extra_tags=messageEnum.DANGER.value)
            
            return redirect(request.META.get('HTTP_REFERER'))

        else:
            return HttpResponseRedirect('/login')


def remove_template_file(filename):
    """
    Removes a template and associated data
    """
    
    # s3 = S3_Client()
    gcs = GCS_Client()
    # if s3.remove_template_file_from_s3(filename):
    if gcs.remove_template_file_from_gcs(filename):
        print(f"File {filename} removed successfully.")
        return True

    print("Error occurred while removing file")
    return False


@login_required
def remove_category(request):
    """
    Removes a template and performs required actions
    """

    if request.user.is_staff:
        if request.method == 'POST':
            
            category_id = request.POST.get('category_id')
            new_category_id = request.POST.get('associate_category')
            is_empty_category = request.POST.get('is_empty_category')
            print(f"Category ID: {category_id}")
            try:
                if is_empty_category == "True":
                    remove_category = Category.objects.get(
                        id = category_id
                    )
                    remove_category_name = remove_category.name
                    remove_category.delete()
                    messages.error(request, f'Category removed: {remove_category_name}', extra_tags=messageEnum.SUCCESS.value)
                else:
                    if category_id != new_category_id:

                        child_categories = Category.objects.filter(
                            parent_category_id = category_id
                        )

                        child_templates = Template.objects.filter(
                            category_id = category_id
                        )
                        
                        child_categories.update(
                            parent_category_id = new_category_id
                        )

                        child_templates.update(
                            category_id = new_category_id
                        )

                        remove_category = Category.objects.get(
                            id = category_id
                        )
                        remove_category_name =remove_category.name
                        remove_category.delete()
                        messages.warning(request, f'Category removed: {remove_category_name}', extra_tags=messageEnum.SUCCESS.value)
            except Category.DoesNotExist:
                print(f"Error while removing category")
                messages.error(request, f'Selected category is already deleted', extra_tags=messageEnum.DANGER.value)

        return redirect(request.META.get('HTTP_REFERER'))
        
    else:
        return HttpResponseRedirect('/login')


@login_required
def update_category(request):
    """
    Updates a Category info
    """

    if request.user.is_staff:
        if request.method == 'POST':
            
            category_id = request.POST.get('category_id')
            category_name = request.POST.get('category_name')
            sequence_id = request.POST.get('sequence_id')

            try:
                category = Category.objects.get(id=category_id)
                category.name = category_name
                category.sequence_id = sequence_id
                category.save()
                messages.warning(request, f'Category updated: {category_name}', extra_tags=messageEnum.SUCCESS.value)

            except Exception as e:
                print('Category not found.')
                messages.error(request, f'Error while updating category', extra_tags=messageEnum.DANGER.value)

        return redirect(request.META.get('HTTP_REFERER'))


@login_required
def bulk_update_sequence_categories(request):
    try:
        sequence_data = request.POST.get('sequence_data')
        
        if sequence_data:
            sequence_data = json.loads(sequence_data)
            
            for item in sequence_data:
                category_id = item.get('category_id')
                sequence_id = item.get('sequence_id')

                if category_id and sequence_id:
                    category = get_object_or_404(Category, id=category_id)
                    category.sequence_id = sequence_id
                    category.save()

            return JsonResponse({'status': 'success', 'message': 'Category sequence updated successfully!'})
        else:
            return JsonResponse({'status': 'error', 'message': 'No sequence data provided'}, status=400)

    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=500)


@login_required
def bulk_update_sequence_templates(request):
    if request.method == 'POST':
        try:
            sequence_data = json.loads(request.POST.get('sequence_data', '[]'))
            
            for item in sequence_data:
                template_id = item.get('template_id')
                sequence_id = item.get('sequence_id')
                
                template = Template.objects.get(id=template_id)
                template.sequence_id = sequence_id
                template.save()
            
            return JsonResponse({'message': 'Template sequences updated successfully!'}, status=200)

        except Template.DoesNotExist:
            return JsonResponse({'message': 'One or more templates not found.'}, status=404)

        except Exception as e:
            return JsonResponse({'message': f'An error occurred: {str(e)}'}, status=500)

    else:
        return JsonResponse({'message': 'Invalid request method. Use POST.'}, status=400)
