from django.urls import path

from broadcast import views

app_name = 'broadcast'

urlpatterns = [
    path('prepare-msg/', views.render_send, name='prepare_message'),
    path('resend-msg/<int:msg_id>', views.resend_msg, name='resend_msg'),
    path('send/', views.send, name='send'),
]
