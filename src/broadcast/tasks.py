import json

from celery import shared_task

from broadcast.utils.telegram import Telegram, TelegramSender
from users.models import Student
from contacts import models as contact_models
from loguru import logger


def set_blocked(chat_id):
    contact_models.Contact.objects.filter(tg_id=chat_id).update(blocked_bot=True)


def feedback_keyboard(is_keyboard, cb_identifier):
    kb = None
    if is_keyboard:
        kb = json.dumps({'inline_keyboard': [
                [{
                    'text': 'Ответить',
                    'callback_data': f'data|feedback_student|{cb_identifier}'
                }]
            ]
        })
    return kb


def _listify(target):
    resp = target
    if type(target) is not list:
        resp = [target]
    return resp


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
def send_to_queue(config):
    contacts = contact_models.Contact.objects.filter(pk__in=_listify(config['ids']))
    for contact in contacts:
        if not contact.blocked_bot:
            kb = feedback_keyboard(config['is_feedback'], contact.id)
            data = {
                'chat_id': contact.tg_id,
                'text': config.get('text'),
                'photo': config.get('photo'),
                'video': config.get('video'),
                'duration': config.get('duration'),
                'width': config.get('width'),
                'height': config.get('height'),
                'thumbnail': config.get('thumbnail'),
                'markup': kb,
            }
            send_message.delay(data)


@shared_task
def send_single_message_task(data):
    Telegram.send_single_message(data)


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
