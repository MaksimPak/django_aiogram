from django.urls import path

from dashboard import views

app_name = 'dashboard'

urlpatterns = [
    path('watch/<slug:uuid>', views.watch_video, name='lesson_video'),
    path('watch/<int:lesson_id>', views.auth_and_watch, name='auth_and_watch'),
    path('form-report/<int:form_id>', views.form_report, name='form_report'),
    path('send-message', views.message_to_students, name='send_message'),
    path('message-contacts', views.message_contacts, name='message_contacts'),
    path('send-lesson/<int:course_id>/<int:lesson_id>', views.send_lesson, name='send_lesson'),
    path('send-promo/<int:promo_id>/<str:lang>', views.send_promo, name='send_promo'),
    path('send-promo-myself/<int:promo_id>/', views.send_promo_myself, name='send_promo_myself'),
    path('send-promo-v2/', views.send_promo_v2, name='send_promo_v2'),
]
