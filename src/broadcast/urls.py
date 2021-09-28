from django.urls import path

from broadcast import views

app_name = 'broadcast'

urlpatterns = [
    path('send-message', views.message_to_students, name='send_message'),
    path('prepare-msg/', views.send_one, name='prepare_message'),
    path('send/', views.send_multiple, name='send'),
]
