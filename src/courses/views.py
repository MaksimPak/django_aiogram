from django.http import HttpResponseNotFound
from django.shortcuts import render
import base64

# Create your views here.
from courses import models

TELEGRAM_AGENT = 'TelegramBot (like TwitterBot)'


def watch_video(request, base64_id):
    """
    Handle video request that comes from telegram bot
    """
    decoded = base64.urlsafe_b64decode(base64_id)
    lesson_id = int.from_bytes(decoded, 'big')

    lesson = models.Lesson.objects.get(pk=lesson_id)

    if request.META.get('HTTP_USER_AGENT') == TELEGRAM_AGENT:
        return HttpResponseNotFound()
    context = {'lesson': lesson}

    return render(request, 'courses/watch_lesson.html', context)
