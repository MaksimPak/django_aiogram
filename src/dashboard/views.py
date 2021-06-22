import datetime
import json
import os

import requests
from django.contrib import messages
from django.db import IntegrityError
from django.http import HttpResponseNotFound, HttpResponse, HttpResponseRedirect
from django.shortcuts import render, get_object_or_404
from django.template.loader import render_to_string
from django.urls import reverse

from dashboard.forms import LeadForm
from dashboard.models import LessonUrl, Lead, Student, Course, Lesson, Promotion
from dashboard.utils.ffmpeg import get_resolution, get_duration
from dashboard.utils.telegram import Telegram

TELEGRAM_AGENT = 'TelegramBot (like TwitterBot)'
MESSAGE_URL = f'https://api.telegram.org/bot{os.getenv("BOT_TOKEN")}/sendMessage'
PHOTO_URL = f'https://api.telegram.org/bot{os.getenv("BOT_TOKEN")}/sendPhoto'


def get_promo_data(
        chat_id,
        video_id,
        message,
        duration,
        width,
        height,
        is_markup=False
):
    data = {
        'chat_id': chat_id,
        'caption': message,
        'duration': duration,
        'width': width,
        'height': height,
        'parse_mode': 'html',
    }

    if video_id:
        data['video'] = video_id

    if is_markup:
        data['reply_markup'] = json.dumps(
            {'inline_keyboard': [[{'text': 'Регистрация', 'callback_data': 'data|tg_reg'}]]}
        )
    return data


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
    students = Student.objects.all()
    selected = getattr(request, request.method).getlist('_selected_action')

    if selected:
        students = Student.objects.filter(pk__in=selected)

    course_id = getattr(request, request.method).get('course_id')
    lesson_id = getattr(request, request.method).get('lesson_id')
    if 'send' in request.POST:
        is_feedback = request.POST.get('is_feedback')

        if is_feedback:
            for student in students:
                text = 'Ответить' if student.language_type == Student.LanguageType.ru else 'Javob'
                kb = {'inline_keyboard': [[{'text': text, 'callback_data': f'data|feedback|{course_id}|{student.id}|{lesson_id}'}]]}
                data = {
                    'chat_id': student.tg_id,
                    'parse_mode': 'html',
                    'text': request.POST['message'],
                    'reply_markup': json.dumps(kb)
                }
                Telegram.send_single_message(data)
        else:
            Telegram.send_to_people(students, request.POST['message'])

        return HttpResponseRedirect(reverse('admin:dashboard_course_changelist'))

    return render(request, 'dashboard/send_intermediate.html', context={
        'entities': students,
        'course_id': course_id,
        'lesson_id': lesson_id
    })


def send_lesson(request, course_id, lesson_id):
    """
    Handles lesson sending to students from Course in Admin panel
    """
    course = Course.objects.get(pk=course_id)
    lesson = Lesson.objects.get(pk=lesson_id)
    students = course.student_set.all()

    kb = {'inline_keyboard': [[{'text': '', 'callback_data': f'data|lesson|{lesson.id}'}]]}

    url = MESSAGE_URL
    image = lesson.image.read() if lesson.image and not lesson.image_file_id else None

    for student in students:
        # todo studentlesson create record
        kb['inline_keyboard'][0][0]['text'] = 'Посмотреть урок' if student.language_type == Student.LanguageType.ru \
            else 'Darsni tomosha qiling'
        data = {
            'chat_id': student.tg_id,
            'parse_mode': 'html',
            'text': render_to_string('dashboard/tg_lesson_info.html', {'lesson': lesson}),
            'reply_markup': json.dumps(kb)
        }

        files = None
        if lesson.image:
            url = PHOTO_URL
            data.pop('text')
            data['caption'] = render_to_string('dashboard/tg_lesson_info.html', {'lesson': lesson})
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


def send_promo(request, promo_id):
    students = Student.objects.all()
    promotion = get_object_or_404(Promotion, pk=promo_id)
    message = render_to_string('dashboard/promo_text.html', {'promo': promotion})
    video = promotion.video if not promotion.video_file_id else None
    thumb = promotion.thumbnail if promotion.thumbnail else None

    duration = get_duration(promotion.video.path)
    width, height = get_resolution(promotion.video.path)

    for student in students:
        data = get_promo_data(
            student.tg_id,
            promotion.video_file_id,
            message,
            duration,
            width,
            height,
            promotion.registration_button
        )

        resp = Telegram.video_to_person(data, thumb, video)

        if not promotion.video_file_id and resp['ok']:
            promotion.video_file_id = resp['result']['video']['file_id']
            promotion.save()

    messages.add_message(request, messages.INFO, 'Отправлено всем студентам.')
    return HttpResponseRedirect(reverse('admin:dashboard_promotion_change', args=(promo_id,)))


def send_promo_myself(request, promo_id):
    promotion = get_object_or_404(Promotion, pk=promo_id)
    message = render_to_string('dashboard/promo_text.html', {'promo': promotion})
    video = promotion.video if not promotion.video_file_id else None
    thumb = promotion.thumbnail if promotion.thumbnail else None
    duration = get_duration(promotion.video.path)
    width, height = get_resolution(promotion.video.path)

    data = get_promo_data(
        os.getenv('CHAT_ID', None),
        promotion.video_file_id,
        message,
        duration,
        width,
        height,
        promotion.registration_button
    )

    resp = Telegram.video_to_person(data, thumb, video)

    if not promotion.video_file_id and resp['ok']:
        promotion.video_file_id = resp['result']['video']['file_id']
        promotion.save()

    messages.add_message(request, messages.INFO, 'Отправлено в общий chat id.')
    return HttpResponseRedirect(reverse('admin:dashboard_promotion_change', args=(promo_id,)))

