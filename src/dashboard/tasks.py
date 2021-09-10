import json
import time

from celery import shared_task, group
from django.db.models import F

from dashboard.models import Student, Promotion, SendingReport, Contact
from ffmpeg import get_duration, get_resolution
from loguru import logger
from dashboard.utils.telegram import Telegram, TelegramSender


@shared_task
def send_promo_task(data, report_id, student_id):
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


def set_blocked(chat_id):
    Contact.objects.filter(tg_id=chat_id).update(blocked_bot=True)


@shared_task
def send_message(data):
    resp = TelegramSender(chat_id=data.get('chat_id'), text=data.get('text'),
                          photo=data.get('photo'), video=data.get('video'),
                          duration=data.get('duration'), width=data.get('width'),
                          height=data.get('height'), thumbnail=data.get('thumbnail'),
                          markup=data.get('markup')).send()

    if resp.get('ok') is False and resp.get('error_code') == 403:
        set_blocked(data.get('chat_id'))
    logger.info(resp)


@shared_task
def initiate_promo_task(config):
    # todo refactor
    if config.get('lang') and config.get('lang') != 'all':
        students = Student.objects.filter(language_type=config['lang'])
        lang = config.get('lang')
    elif config.get('contact_ids'):
        students = Contact.objects.filter(pk__in=config['contact_ids'])
        lang = 'undefined'
    else:
        students = Student.objects.all()
        lang = 'all'

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

    report = SendingReport.objects.create(lang=lang, promotion=promotion, sent=students.count())

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

        student.blocked_bot or tasks.append(send_promo_task.s(data, report.id, student.id))
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


@shared_task
def message_contacts_task(config):
    contacts = Contact.objects.all() if config['contacts'] == 'all'\
        else Contact.objects.filter(pk__in=config['contacts'])

    for contact in contacts:
        kb = {
                'inline_keyboard': [[
                    {
                        'text': 'Ответить',
                        'callback_data': f'data|feedback_student|{contact.id}'
                    }]
                ]
        } if config['is_feedback'] else None

        data = {
            'chat_id': contact.tg_id,
            'text': config['message']
        }
        if kb:
            data['markup'] = json.dumps(kb)

        if not contact.blocked_bot:
            send_message.delay(data)
