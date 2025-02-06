from datetime import datetime
from urllib.parse import urlencode
from django.shortcuts import redirect
from django.contrib.auth import authenticate, logout
from django.conf import settings
from django.http import JsonResponse

from ..services.auth import AuthenticationService
from ..services.subscription import SubscriptionService
from ..utils.access import get_user_access_levels
from ..utils.date import check_expiration_date

class LoginManager:
    """Manager for handling login operations"""
    
    def __init__(self):
        self.auth_service = AuthenticationService()
        self.subscription_service = SubscriptionService()

    def handle_authenticated_user(self, request) -> redirect:
        """Handle already authenticated user"""
        try:
            # Set user access levels
            user_role = request.user.role
            request.session['user_access_levels'] = get_user_access_levels(user_role)
            
            # Check subscription status
            has_subscription = self.check_subscription_status(
                user_role=user_role,
                expiration_date=request.user.expiration_date,
                is_staff=request.user.is_staff
            )
            request.session['has_active_subscription'] = has_subscription
            
            # Redirect based on user type
            if request.user.is_staff:
                return redirect('admin:categories')
            return redirect('user:dashboard')
            
        except Exception as e:
            return redirect('login')

    def check_subscription_status(self, user_role: str, expiration_date: datetime, is_staff: bool) -> bool:
        """Check if user has active subscription"""
        if is_staff:
            return True
            
        if user_role == 'level-0':
            return False
            
        return not check_expiration_date(expiration_date)

    def get_login_redirect_url(self, next_url: str = None) -> str:
        """Get SSO login URL with optional redirect"""
        if next_url:
            query_params = {'next': next_url}
            next_path = f'&{urlencode(query_params)}'
        else:
            next_path = ''
            
        return f"{settings.LOGIN_URL}{next_path}"

def login_view(request):
    """Handle user login"""
    if request.user.is_authenticated:
        manager = LoginManager()
        return manager.handle_authenticated_user(request)
        
    # Redirect to SSO login
    next_url = request.GET.get('next')
    manager = LoginManager()
    login_url = manager.get_login_redirect_url(next_url)
    return redirect(login_url)

def logout_view(request):
    """Handle user logout"""
    try:
        logout(request)
        return redirect('login')
    except Exception as e:
        return redirect('dashboard')

def verify_credentials(request):
    """Verify user credentials"""
    if request.method != 'GET':
        return JsonResponse({'error': 'Invalid request method'}, status=405)
        
    auth_service = AuthenticationService()
    
    try:
        email = request.GET.get('email')
        password = request.GET.get('password')
        
        if not email or not password:
            raise ValueError("Email and password are required")
            
        is_valid = auth_service.verify_credentials(
            email=email,
            password=password
        )
        
        return JsonResponse({
            'status': 'OK' if is_valid else 'NOT OK'
        })
    except Exception as e:
        return JsonResponse({
            'status': 'NOT OK',
            'error': str(e)
        }, status=400)

def health_check(request):
    """API health check endpoint"""
    try:
        auth_service = AuthenticationService()
        status = 'OK' if auth_service.check_health() else 'ERROR'
        
        return JsonResponse({
            'status': status,
            'timestamp': datetime.now().isoformat()
        })
    except Exception:
        return JsonResponse({
            'status': 'ERROR'
        }, status=500)
