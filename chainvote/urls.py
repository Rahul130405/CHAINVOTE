from django.contrib import admin
from django.urls import path, include
from django.views.generic.base import RedirectView
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('voting.urls')),
    path('favicon.ico', RedirectView.as_view(url=settings.STATIC_URL + 'voting/images/chainvote-logo.png')),
]
