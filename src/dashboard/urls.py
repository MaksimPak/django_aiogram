from django.urls import path

from dashboard import views

app_name = 'dashboard'

urlpatterns = [
    path('watch/<slug:uuid>', views.watch_video, name='lesson_video'),
    path('watch/<int:lesson_id>', views.auth_and_watch, name='auth_and_watch'),
    path('send-message', views.message_to_students, name='send_message'),
    path('send-lesson/<int:course_id>/<int:lesson_id>', views.send_lesson, name='send_lesson'),
    path('send-promo/<int:promo_id>/<str:lang>', views.send_promo, name='send_promo'),
    path('send-promo-myself/<int:promo_id>/', views.send_promo_myself, name='send_promo_myself'),
    path('form-report/<int:pk>', views.FormReport.as_view(), name='form_report'),
]
