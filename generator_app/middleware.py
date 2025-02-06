import os
from typing import Any
from datetime import datetime

from django.utils.deprecation import MiddlewareMixin
from django.conf import settings
from django.contrib.auth import logout, get_user_model
from django.utils.dateparse import parse_datetime
from django.utils.timezone import now
from django.contrib.sessions.models import Session
from django.http import HttpRequest, HttpResponse
from django_sso import deauthenticate_user
from django_sso.sso_service.backend import acceptor, EventAcceptor



class FileCleanupMiddleware(MiddlewareMixin):
    """Middleware to clean up temporary files after request processing"""

    def process_response(self, request: HttpRequest, response: HttpResponse) -> HttpResponse:
        """Clean up temporary files attached to request"""
        if hasattr(request, 'cleanup_files'):
            for file_path in request.cleanup_files:
                self._safely_remove_file(file_path)
        return response

    def _safely_remove_file(self, file_path: str) -> None:
        """Safely remove a file with error handling"""
        try:
            if os.path.exists(file_path):
                os.remove(file_path)
        except OSError as e:
            # Log error instead of print
            settings.LOGGER.error(f"Error deleting file {file_path}: {e}")


class SessionManagementMiddleware(MiddlewareMixin):
    """Middleware to handle session management and auto-logout"""

    def process_request(self, request: HttpRequest) -> None:
        """Handle session activity tracking and auto-logout"""
        if not request.user.is_authenticated:
            return

        if self._should_logout_user(request):
            self._perform_user_logout(request)
            return

        self._update_activity_timestamp(request)

    def process_response(self, request: HttpRequest, response: HttpResponse) -> HttpResponse:
        """Clean up expired sessions"""
        if hasattr(request, '_session_to_delete'):
            self._cleanup_session(request)
        return response

    def _should_logout_user(self, request: HttpRequest) -> bool:
        """Check if user should be logged out based on inactivity"""
        last_activity_str = request.session.get('last_activity')
        if not last_activity_str:
            return False

        last_activity = parse_datetime(last_activity_str)
        if not last_activity:
            return False

        inactivity_duration = (now() - last_activity).total_seconds()
        return inactivity_duration > settings.SESSION_COOKIE_AGE

    def _perform_user_logout(self, request: HttpRequest) -> None:
        """Perform user logout and clean up session"""
        logout(request)
        if 'last_activity' in request.session:
            del request.session['last_activity']

    def _update_activity_timestamp(self, request: HttpRequest) -> None:
        """Update user's last activity timestamp"""
        request.session['last_activity'] = now().isoformat()

    def _cleanup_session(self, request: HttpRequest) -> None:
        """Clean up marked session"""
        Session.objects.filter(
            session_key=request._session_to_delete
        ).delete()
        request._session_to_delete.clear()


class SSOAccountManager(EventAcceptor):
    """Manager for SSO account operations"""

    USER_BOOLEAN_FIELDS = ['is_active', 'is_staff', 'is_superuser']

    @acceptor
    def update_account(self, fields: dict) -> None:
        """
        Update or create user account from SSO data

        Args:
            fields (dict): User account fields from SSO
        """
        user_model = get_user_model()
        
        user_data = self._prepare_user_data(fields)
        identity_field = {user_model.USERNAME_FIELD: fields['user_identy']}
        
        user_model.objects.update_or_create(
            **identity_field,
            defaults=user_data
        )

    def _prepare_user_data(self, fields: dict) -> dict:
        """Prepare user data for database operation"""
        data = {
            'first_name': fields.get('first_name'),
            'last_name': fields.get('last_name'),
            'role': fields.get('role', 'level-0'),
            'email': fields.get('email'),
            'expiration_date': fields.get('expiration_date'),
        }

        # Add boolean fields if they exist in user model
        user_model = get_user_model()
        for field in self.USER_BOOLEAN_FIELDS:
            if hasattr(user_model, field) and field in fields:
                data[field] = bool(fields[field])

        return data
