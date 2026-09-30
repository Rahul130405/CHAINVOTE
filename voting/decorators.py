"""
Authentication and authorization decorators for CHAINVOTE.
"""

from functools import wraps
from django.conf import settings
from django.shortcuts import redirect
from django.contrib import messages


def admin_required(view_func):
    """
    Decorator for administrative views ensuring that the user is authenticated
    and possesses staff or superuser privileges.

    - Unauthenticated requests are redirected to LOGIN_URL with ?next=<path>.
    - Authenticated non-staff/non-superuser requests are blocked server-side,
      redirected to 'home', and presented with an access restriction error.
    - Staff and superusers are granted access.
    """
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        if not request.user.is_authenticated:
            login_url = getattr(settings, 'LOGIN_URL', '/login/')
            return redirect(f"{login_url}?next={request.path}")
        if not (request.user.is_staff or request.user.is_superuser):
            messages.error(
                request,
                "Access restricted: Staff or administrator credentials required to access this area."
            )
            return redirect('home')
        return view_func(request, *args, **kwargs)

    return _wrapped_view
