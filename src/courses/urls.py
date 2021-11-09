from django.urls import path

from courses import views

app_name = 'courses'

urlpatterns = [
    path('watch/<str:base64_id>', views.watch_video, name='watch_lesson'),
    path('start/<int:course_id>', views.start_course, name='start_course'),
    path('finish/<str:course_id>', views.finish_course, name='finish_course'),
    path('delete-from-course/<int:course_id>/<int:student_id>',
         views.delete_from_course, name='delete_from_course'),
]
