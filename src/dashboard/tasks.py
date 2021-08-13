import json
import time

from celery import shared_task, group
from django.db.models import F

from app.celery import app
from dashboard.models import Student, Promotion, SendingReport
from ffmpeg import get_duration, get_resolution
from dashboard.utils.telegram import Telegram, TelegramSender


@app.task
def add(x, y):
    time.sleep(3)
    return x + y


@shared_task
def send_video_task(data, report_id, student_id):
    res = TelegramSender(
            data['chat_id'],
            data['message'],
            data['image'],
            data['video'],
            data['duration'],
            data['width'],
            data['height'],
            data['thumb']
        ).send()

    if res['ok']:
        SendingReport.objects.filter(pk=report_id).update(received=F('received') + 1)

    if not res['ok'] and res['error_code'] == 403:
        SendingReport.objects.filter(pk=report_id).update(failed=F('failed') + 1)

        Student.objects.filter(pk=student_id).update(blocked_bot=True)


@shared_task
def send_single_message_task(data):
    Telegram.send_single_message(data)


@shared_task
def send_promo_task(config):
    if config['lang'] != 'all':
        students = Student.objects.filter(language_type=config['lang'])
    else:
        students = Student.objects.all()

    promotion = Promotion.objects.get(pk=config['promo_id'])
    message = config['message']
    image = promotion.image.path
    video = None
    thumb = None
    duration = None
    width = None
    height = None

    if promotion.video:
        image = None
        video = promotion.video.path
        thumb = promotion.image.path
        duration = get_duration(promotion.video.path)
        width, height = get_resolution(promotion.video.path)

    report = SendingReport.objects.create(lang=config['lang'], promotion=promotion, sent=students.count())

    tasks = []
    for i, student in enumerate(students):
        if i % 25 == 0:
            time.sleep(1)

        data = {
            'chat_id': student.tg_id,
            'message': message,
            'image': image,
            'video': video,
            'duration': duration,
            'width': width,
            'height': height,
            'thumb': thumb
        }

        student.blocked_bot or tasks.append(send_video_task.s(data, report.id, student.id))
    result = group(tasks)().save()
    SendingReport.objects.filter(pk=report.id).update(celery_id=result.id)


@shared_task
def message_students_task(config):
    students = Student.objects.all() if config['students'] == 'all'\
        else Student.objects.filter(pk__in=config['students'])

    for student in students:
        text = 'Ответить' if student.language_type == Student.LanguageType.ru else 'Javob'
        kb = {
                'inline_keyboard': [[
                    {
                        'text': text,
                        'callback_data': f'data|feedback|{config["course_id"]}|{student.id}|{config["lesson_id"]}'
                    }]
                ]
        } if config['is_feedback'] else None

        data = {
            'chat_id': student.tg_id,
            'parse_mode': 'html',
            'text': config['message']
        }
        if kb:
            data['reply_markup'] = json.dumps(kb)
        send_single_message_task.delay(data)
