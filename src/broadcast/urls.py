from django.urls import path

from broadcast import views

app_name = 'broadcast'

urlpatterns = [
    path('send-message', views.message_to_students, name='send_message'),
    path('send/<int:contact_id>', views.send, name='message'),
    path('send/', views.send_multiple, name='message_multiple'),
]
