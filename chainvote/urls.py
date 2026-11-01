from django.contrib import admin
from django.urls import path, include
from django.views.generic.base import RedirectView
from django.conf import settings
from django.conf.urls.static import static

# Restrict Django Admin exclusively to the designated single admin (yash)
def single_admin_has_permission(request):
    """
    Restrict Django Admin access exclusively to the authorized single admin (yash).
    Denies all other staff or superuser accounts from accessing Django Admin.
    """
    if not (request.user.is_active and request.user.is_authenticated):
        return False
    authorized_admin = getattr(settings, 'AUTHORIZED_ADMIN_USERNAME', 'yash')
    return request.user.username == authorized_admin

admin.site.has_permission = single_admin_has_permission

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('voting.urls')),
    path('favicon.ico', RedirectView.as_view(url=settings.STATIC_URL + 'favicon.ico')),
]
