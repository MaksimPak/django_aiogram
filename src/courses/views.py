import base64
import datetime

from django.contrib import messages
from django.http import HttpResponseNotFound
from django.shortcuts import render, redirect

from courses import models

TELEGRAM_AGENT = 'TelegramBot (like TwitterBot)'


def start_course(request, course_id):
    models.Course.objects.filter(pk=course_id).update(date_started=datetime.datetime.now())
    messages.add_message(request, messages.INFO, 'Курс начат')

    return redirect(request.META['HTTP_REFERER'])


def finish_course(request, course_id):
    models.Course.objects.filter(pk=course_id).update(date_finished=datetime.datetime.now())
    messages.add_message(request, messages.INFO, 'Курс закончен')

    return redirect(request.META['HTTP_REFERER'])


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
