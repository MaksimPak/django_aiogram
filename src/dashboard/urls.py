from django.urls import path

from dashboard import views

app_name = 'dashboard'

urlpatterns = [
    path('watch/<uuid:uuid>', views.watch_video, name='lesson_video'),
    path('signup', views.signup, name='signup'),
    path('test', views.message_to_students, name='send_message'),
]
