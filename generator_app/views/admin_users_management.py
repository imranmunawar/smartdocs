from ..models import CustomUser
from django.shortcuts import render, redirect, get_object_or_404
from django.core.paginator import Paginator
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required, user_passes_test
from django.http import HttpResponseRedirect
from django.db.models import OuterRef, Subquery, Value
from django.db.models.functions import Coalesce
from ..models import UserDocument
from ..enums import messageEnum
from django.contrib import messages
from ..models import stripe_subscription
from ..services.admin import AdminUserService
from ..enums import AdminMessageType
from ..utils.security import validate_password

def is_admin_user(user):
    """Verify if user has admin privileges"""
    return user.is_staff and user.is_active

@login_required
@user_passes_test(is_admin_user)
def admin_user_list(request):
    """
    Display paginated list of users with subscription status
    """
    user_service = AdminUserService()
    
    try:
        users_with_subscriptions = user_service.get_users_with_subscriptions()
        paginator = Paginator(users_with_subscriptions, per_page=10)
        current_page = paginator.get_page(request.GET.get('page'))
        
        context = {
            'page_obj': current_page,
            'total_users': users_with_subscriptions.count(),
            'active_users': user_service.get_active_user_count()
        }
        return render(request, 'admin/users/list.html', context)
    except Exception as e:
        messages.error(request, f"Admin Error: {str(e)}")
        return redirect('admin:dashboard')

@login_required
@user_passes_test(is_admin_user)
def admin_create_user(request):
    """
    Create new user with specified role and permissions
    """
    if request.method != 'POST':
        return JsonResponse({'error': 'Invalid request method'}, status=405)
        
    user_service = AdminUserService()
    
    try:
        user_data = {
            'username': request.POST.get('username'),
            'email': request.POST.get('email'),
            'password': request.POST.get('password'),
            'confirm_password': request.POST.get('confirm_password'),
            'user_type': request.POST.get('user_type'),
            'is_active': request.POST.get('user_status') != 'False'
        }

        # Validate password match
        if not validate_password(user_data['password'], user_data['confirm_password']):
            return JsonResponse({
                'status': 'error',
                'message': 'Passwords do not match'
            }, status=400)

        # Check email uniqueness
        if user_service.email_exists(user_data['email']):
            return JsonResponse({
                'status': 'error',
                'message': 'Email already exists'
            }, status=400)

        # Create user
        new_user = user_service.create_user(user_data)
        
        messages.success(
            request, 
            f'User {new_user.username} created successfully',
            extra_tags=AdminMessageType.SUCCESS.value
        )
        return JsonResponse({'status': 'success', 'user_id': new_user.id})
        
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=400)

@login_required
@user_passes_test(is_admin_user)
def admin_update_user(request):
    """
    Update existing user details and permissions
    """
    if request.method != 'POST':
        return JsonResponse({'error': 'Invalid request method'}, status=405)
        
    user_service = AdminUserService()
    
    try:
        user_data = {
            'user_id': request.POST.get('user_id'),
            'username': request.POST.get('username'),
            'email': request.POST.get('email'),
            'password': request.POST.get('password'),
            'confirm_password': request.POST.get('confirm_password'),
            'user_type': request.POST.get('user_type'),
            'is_active': request.POST.get('user_status') != 'False'
        }

        # Validate password if provided
        if user_data['password']:
            if not validate_password(user_data['password'], user_data['confirm_password']):
                messages.error(
                    request,
                    'Password update failed: Passwords do not match',
                    extra_tags=AdminMessageType.ERROR.value
                )
                return redirect('admin:user_list')

        # Update user
        updated_user = user_service.update_user(user_data)
        
        messages.success(
            request,
            f'User {updated_user.username} updated successfully',
            extra_tags=AdminMessageType.SUCCESS.value
        )
        return redirect('admin:user_list')
        
    except Exception as e:
        messages.error(request, str(e), extra_tags=AdminMessageType.ERROR.value)
        return redirect('admin:user_list')

@login_required
@user_passes_test(is_admin_user)
def admin_user_documents(request, user_id: int):
    """
    Display documents associated with specific user
    """
    user_service = AdminUserService()
    
    try:
        user_details = user_service.get_user_details(user_id)
        user_documents = user_service.get_user_documents(user_id)
        
        context = {
            'user_details': user_details,
            'user_documents': user_documents,
            'document_count': len(user_documents)
        }
        return render(request, 'admin/users/documents.html', context)
    except Exception as e:
        messages.error(request, str(e))
        return redirect('admin:user_list')

@login_required
@user_passes_test(is_admin_user)
def admin_delete_user(request):
    """
    Remove user and associated data
    """
    if request.method != 'POST':
        return JsonResponse({'error': 'Invalid request method'}, status=405)
        
    user_service = AdminUserService()
    
    try:
        user_id = request.POST.get('user_id')
        deleted_user = user_service.delete_user(user_id)
        
        messages.success(
            request,
            f'User {deleted_user.username} removed successfully',
            extra_tags=AdminMessageType.SUCCESS.value
        )
        return redirect(request.META.get('HTTP_REFERER'))
        
    except Exception as e:
        messages.error(request, str(e))
        return redirect('admin:user_list')
