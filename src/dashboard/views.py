import datetime
import json
import os

import requests
from django.contrib import messages
from django.db import IntegrityError
from django.http import HttpResponseNotFound, HttpResponse, HttpResponseRedirect
from django.shortcuts import render, get_object_or_404, redirect
from django.template.loader import render_to_string
from django.urls import reverse

from dashboard.forms import LeadForm
from dashboard.models import LessonUrl, Lead, Student, Course, Lesson, Promotion
from dashboard.tasks import send_promo_task, message_students_task
from dashboard.utils.ffmpeg import get_resolution, get_duration
from dashboard.utils.helpers import prepare_promo_data
from dashboard.utils.telegram import Telegram

TELEGRAM_AGENT = 'TelegramBot (like TwitterBot)'
MESSAGE_URL = f'https://api.telegram.org/bot{os.getenv("BOT_TOKEN")}/sendMessage'
PHOTO_URL = f'https://api.telegram.org/bot{os.getenv("BOT_TOKEN")}/sendPhoto'


def watch_video(request, uuid):
    """
    Handle video request that comes from telegram bot
    """
    if request.META.get('HTTP_USER_AGENT') == TELEGRAM_AGENT:
        return HttpResponseNotFound()

    try:
        lesson_url = LessonUrl.objects.get(hash=uuid)
    except LessonUrl.DoesNotExist:
        msg = 'Ошибка 404. Данный урок не найден - возможно он был удален. ' \
              'Пожалуйста, зайдите в бот, откройте нужный курс и заново выберите требуемый урок.'
        return render(request, 'dashboard/error.html', {'error': msg})

    context = {'lesson': lesson_url.lesson}

    if lesson_url.hits >= 3:
        # Delete record from database once user opens the link
        lesson_url.delete()
        msg = 'Ошибка 403. Ссылка на урок устарела. Если вы хотите просмотреть этот урок, ' \
              'пожалуйста, зайдите в бот, откройте нужный курс и заново выберите требуемый урок.'
        return render(request, 'dashboard/error.html', {'error': msg})
    else:
        lesson_url.hits += 1
        lesson_url.save()
    return render(request, 'dashboard/watch_lesson.html', context)


def auth_and_watch(request, lesson_id):
    """
    Authorize user with telegram and provide access to video
    """

    # authentificating
    tg_id = request.GET.get('id')
    if tg_id and Student.objects.filter(tg_id=tg_id).exists():
        request.session['tg_id'] = tg_id
        request.session.set_expiry(60 * 60)
        return redirect('dashboard:auth_and_watch', lesson_id=lesson_id)

    # authentificated and all ok
    if request.session.get('tg_id'):
        student = Student.objects.get(tg_id=request.session.get('tg_id'))
        lesson = get_object_or_404(Lesson, pk=lesson_id)
        return render(request, 'dashboard/watch_lesson.html', {'lesson': lesson, 'student': student})
    else:
        return render(request, 'dashboard/tg_auth.html', {'id': lesson_id})


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

        config = {
            'is_feedback': is_feedback,
            'students': 'all' if not selected else selected,
            'message': request.POST['message'],
            'course_id': course_id,
            'lesson_id': lesson_id
        }

        message_students_task.delay(config)

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
        kb['inline_keyboard'][0][0]['text'] = 'Получить урок' if student.language_type == Student.LanguageType.ru \
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


def send_promo(request, promo_id, lang):
    promotion = get_object_or_404(Promotion, pk=promo_id)
    message = render_to_string('dashboard/promo_text.html', {'promo': promotion})

    duration = get_duration(promotion.video.path)
    width, height = get_resolution(promotion.video.path)

    config = {
        'promo_id': promo_id,
        'message': message,
        'duration': duration,
        'width': width,
        'height': height,
        'lang': lang
    }
    send_promo_task.delay(config)

    messages.add_message(request, messages.INFO, 'Отправлено всем студентам.')
    return HttpResponseRedirect(reverse('admin:dashboard_promotion_change', args=(promo_id,)))


def send_promo_myself(request, promo_id):
    promotion = get_object_or_404(Promotion, pk=promo_id)
    message = render_to_string('dashboard/promo_text.html', {'promo': promotion})
    video = promotion.video if not promotion.video_file_id else None
    thumb = promotion.thumbnail if promotion.thumbnail else None
    duration = get_duration(promotion.video.path)
    width, height = get_resolution(promotion.video.path)

    data = prepare_promo_data(
        os.getenv('CHAT_ID', None),
        promotion.video_file_id,
        message,
        duration,
        width,
        height,
    )

    resp = Telegram.video_to_person(data, thumb, video)

    if not promotion.video_file_id and resp['ok']:
        promotion.video_file_id = resp['result']['video']['file_id']
        promotion.save()

    messages.add_message(request, messages.INFO, 'Отправлено в общий chat id.')
    return HttpResponseRedirect(reverse('admin:dashboard_promotion_change', args=(promo_id,)))
