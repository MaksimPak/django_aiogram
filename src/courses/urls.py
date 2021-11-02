from django.urls import path

from courses import views

app_name = 'courses'

urlpatterns = [
    path('watch/<str:base64_id>', views.watch_video, name='watch_lesson'),
]
