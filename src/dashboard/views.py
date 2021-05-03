from django.shortcuts import render, get_object_or_404
from django.http import HttpResponseNotFound

# Create your views here.
from dashboard.models import LessonUrl


def watch_video(request, uuid):
    lesson_url = get_object_or_404(LessonUrl, hash=uuid)
    context = {'lesson': lesson_url.lesson}
    if lesson_url:
        lesson_url.delete()
        return render(request, 'dashboard/watch_lesson.html', context)
    else:
        return HttpResponseNotFound('<h1>Page not found</h1>')
