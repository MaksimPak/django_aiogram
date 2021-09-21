from django.urls import path

from broadcast import views

app_name = 'broadcast'

urlpatterns = [
    path('send-message', views.message_to_students, name='send_message'),
]
