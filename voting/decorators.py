"""
Authentication and authorization decorators for CHAINVOTE.
"""

from functools import wraps
from django.conf import settings
from django.shortcuts import redirect
from django.contrib import messages


def get_authorized_admin_username():
    return getattr(settings, 'AUTHORIZED_ADMIN_USERNAME', 'yash')


def is_authorized_admin(user):
    """
    Check whether a user is the strictly authorized single administrator.
    Only username 'yash' is granted administrative access.
    """
    if not user or not user.is_authenticated or not user.is_active:
        return False
    return user.username == get_authorized_admin_username()


def add_no_cache_headers(response):
    """Enforces no-cache, no-store headers on sensitive responses."""
    if response is not None and hasattr(response, '__setitem__'):
        response['Cache-Control'] = 'no-cache, no-store, must-revalidate, private'
        response['Pragma'] = 'no-cache'
        response['Expires'] = '0'
    return response


def admin_required(view_func):
    """
    Decorator for administrative views ensuring that the user is authenticated,
    active, and strictly the authorized administrator ('yash').

    - Unauthenticated requests are redirected to LOGIN_URL with ?next=<path>.
    - Authenticated non-authorized users (including other staff/superusers) are blocked,
      redirected to 'home', and presented with an access restriction error.
    - Adds no-store / no-cache response headers.
    """
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        if not request.user.is_authenticated:
            login_url = getattr(settings, 'LOGIN_URL', '/login/')
            return redirect(f"{login_url}?next={request.path}")
        if not is_authorized_admin(request.user):
            messages.error(
                request,
                "Access restricted: Only the authorized administrator may access this portal."
            )
            return redirect('home')
        response = view_func(request, *args, **kwargs)
        return add_no_cache_headers(response)

    return _wrapped_view
