from django.urls import path

from dashboard import views

app_name = 'dashboard'

urlpatterns = [
    path('watch/<uuid:uuid>', views.watch_video, name='lesson_video'),
]
