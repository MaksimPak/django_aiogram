import datetime
import json
import os

import requests
from django.db import IntegrityError
from django.http import HttpResponseNotFound, HttpResponse, HttpResponseRedirect
from django.shortcuts import render, get_object_or_404
from django.template.loader import render_to_string
from django.urls import reverse

from dashboard.forms import LeadForm
from dashboard.models import LessonUrl, Lead, Student, Course, Lesson

TELEGRAM_AGENT = 'TelegramBot (like TwitterBot)'
MESSAGE_URL = f'https://api.telegram.org/bot{os.getenv("BOT_TOKEN")}/sendMessage'
PHOTO_URL = f'https://api.telegram.org/bot{os.getenv("BOT_TOKEN")}/sendPhoto'


def watch_video(request, uuid):
    """
    Handle video request that comes from telegram bot
    """
    if request.META.get('HTTP_USER_AGENT') != TELEGRAM_AGENT:
        lesson_url = get_object_or_404(LessonUrl, hash=uuid)
        context = {'lesson': lesson_url.lesson}
        if lesson_url:
            # Delete record from database once user opens the link
            lesson_url.delete()
            return render(request, 'dashboard/watch_lesson.html', context)
        else:
            return HttpResponseNotFound('<h1>Page not found</h1>')  # todo change page not found


def signup(request):
    """
    Save lead from signup page
    """
    if request.POST:
        try:
            Lead.objects.create(
                first_name=request.POST['first_name'],
                last_name=request.POST['last_name'],
                language_type=request.POST['language_type'],
                phone=request.POST['phone'],
                chosen_field=request.POST['chosen_field'],
                application_type=Lead.ApplicationType.web,
                is_client=False
            )
            return HttpResponse('thank you')
        except IntegrityError:
            return HttpResponse('Invalid phone number. Number is already used')
    else:
        form = LeadForm()
        return render(request, 'dashboard/signup.html', {'form': form})


def message_to_students(request):
    """
    Handles message sending to students from Course in Admin panel
    """
    students = Student.objects.filter(pk__in=getattr(request, request.method).getlist('_selected_action'))

    if 'send' in request.POST:

        for student in students:
            data = {
                'chat_id': student.tg_id,
                'text': request.POST['message'],
            }
            url = MESSAGE_URL
            requests.post(url, data=data)

        return HttpResponseRedirect(reverse('admin:dashboard_course_changelist'))

    return render(request, 'dashboard/send_intermediate.html', context={'entities': students})


def send_lesson(request, course_id, lesson_id):
    """
    Handles lesson sending to students from Course in Admin panel
    """
    course = Course.objects.get(pk=course_id)
    lesson = Lesson.objects.get(pk=lesson_id)
    students = course.student_set.all()

    kb = {'inline_keyboard': [[{'text': 'Посмотреть урок', 'callback_data': f'lesson|{lesson.id}'}]]}
    url = MESSAGE_URL
    image = lesson.image.read() if lesson.image and not lesson.image_file_id else None

    for student in students:
        # todo studentlesson create record

        data = {
            'chat_id': student.tg_id,
            'parse_mode': 'html',
            'text': render_to_string('dashboard/lesson_info.html', {'lesson': lesson}),
            'reply_markup': json.dumps(kb)
        }

        files = None
        if lesson.image:
            url = PHOTO_URL
            data.pop('text')
            data['caption'] = render_to_string('dashboard/lesson_info.html', {'lesson': lesson})
            if lesson.image_file_id:
                data['photo'] = lesson.image_file_id
            else:
                files = {'photo': image}

        resp = requests.post(url, data=data, files=files).json()
        if lesson.image and not lesson.image_file_id:
            lesson.image_file_id = resp['result']['photo'][-1]['file_id']

    lesson.date_sent = datetime.datetime.now()
    lesson.save()
    return HttpResponseRedirect(reverse('admin:dashboard_course_change', args=(course_id,)))
