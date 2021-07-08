import json
import time

from celery import shared_task
from django.core.exceptions import ValidationError
from django.db.models import F

from dashboard.models import Student, Promotion, SendingReport
from dashboard.utils.telegram import Telegram
from dashboard.utils.helpers import prepare_promo_data


@shared_task
def send_video_task(data, thumb, video):
    res = Telegram.video_to_person(data, thumb, video)

    if res['ok']:
        SendingReport.objects.filter(pk=data['report_id']).update(received=F('received') + 1)

    if not res['ok'] and res['error_code'] == 403:
        SendingReport.objects.filter(pk=data['report_id']).update(failed=F('failed') + 1)

        Student.objects.filter(pk=data['report_id']).update(blocked_bot=True)


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
    if not promotion.video_file_id:
        raise ValidationError('Video file id is required')

    video = promotion.video.path
    thumb = promotion.thumbnail.path if promotion.thumbnail else None

    report = SendingReport.objects.create(lang=config['lang'], promotion=promotion, sent=students.count())

    for i, student in enumerate(students):
        if i % 25 == 0:
            time.sleep(1)
        data = prepare_promo_data(
            student.tg_id,
            promotion.video_file_id,
            config['message'],
            config['duration'],
            config['width'],
            config['height'],
            promotion.registration_button,
        )
        data['report_id'] = report.id
        data['student_id'] = student.id

        student.blocked_bot or send_video_task.delay(data, thumb, video)


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
