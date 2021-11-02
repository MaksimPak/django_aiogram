"""parcel URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/3.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import path, include

from django.conf import settings
from django.views.generic import RedirectView

from users.views import signup

favicon_view = RedirectView.as_view(url='/static/base/favicon.ico', permanent=True)

urlpatterns = [
    path('admin/', admin.site.urls),
    path('start/', signup, name='web_signup'),
    path('broadcast/', include('broadcast.urls')),
    path('courses/', include('courses.urls')),
    path('forms/', include('forms.urls')),
    path('favicon.ico', favicon_view),
] + static(settings.STATIC_URL, document_root=settings.STATIC_ROOT) \
  + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)


admin.site.site_header = 'Parcel админка'
