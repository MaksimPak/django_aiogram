import datetime
import json
import os

import requests
from django.db import IntegrityError, transaction
from django.http import HttpResponseNotFound, HttpResponse, HttpResponseRedirect
from django.shortcuts import render, get_object_or_404
from django.urls import reverse

from dashboard.forms import ClientForm
from dashboard.models import LessonUrl, Lead, Student, Course, Lesson


def watch_video(request, uuid):
    if request.META.get('HTTP_USER_AGENT') != 'TelegramBot (like TwitterBot)':
        lesson_url = get_object_or_404(LessonUrl, hash=uuid)
        context = {'lesson': lesson_url.lesson}
        if lesson_url:
            lesson_url.delete()
            return render(request, 'dashboard/watch_lesson.html', context)
        else:
            return HttpResponseNotFound('<h1>Page not found</h1>')


def signup(request):
    if request.POST:
        try:
            Lead.objects.create(
                first_name=request.POST['first_name'],
                last_name=request.POST['last_name'],
                language_type=request.POST['language_type'],
                phone=request.POST['phone'],
                chosen_field=request.POST['chosen_field'],
                application_type=3,
                is_client=False
            )
            return HttpResponse('thank you')
        except IntegrityError:
            return HttpResponse('Invalid phone number. Number is already used')
    else:
        form = ClientForm()
        return render(request, 'dashboard/signup.html', {'form': form})


# todo: accept get/post requests
def message_to_students(request):
    clients = [Student.objects.get(pk=x) for x in request.POST.getlist('_student_received')]
    if 'send' in request.POST:
        students = [Student.objects.get(pk=x) for x in request.POST.getlist('_selected_action')]

        for student in students:
            url = f"https://api.telegram.org/bot{os.getenv('BOT_TOKEN')}/sendMessage?chat_id={student.tg_id}&text={request.POST['message']}"
            requests.get(url)

        return HttpResponseRedirect(reverse('admin:dashboard_course_changelist'))

    return render(request, 'dashboard/send_intermediate.html', context={'entities': clients})


@transaction.atomic
def send_lesson(request, course_id, lesson_id):
    course = Course.objects.get(pk=course_id)
    lesson = Lesson.objects.get(pk=lesson_id)
    students = course.student_set.all()
    url = f"https://api.telegram.org/bot{os.getenv('BOT_TOKEN')}/sendMessage"
    for student in students:
        kb = {
            'inline_keyboard': [
                [{
                    'text': 'Посмотреть урок',
                    'callback_data': f'lesson|{lesson.id}'
                }],
            ]
        }
        data = {
            'chat_id': student.tg_id,
            'text': lesson.title,
            'reply_markup': json.dumps(kb)
        }
        requests.post(url, data=data).json()

    course.lesson_count = list(course.lesson_set.all()).index(lesson) + 1
    lesson.date_sent = datetime.datetime.now()

    lesson.save()
    course.save()
    return HttpResponseRedirect(reverse('admin:dashboard_course_change', args=(course_id,)))
