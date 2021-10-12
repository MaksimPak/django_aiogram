import datetime
import json
import time

from celery import shared_task, chord
from loguru import logger

from broadcast import models
from broadcast.models import MessageHistory
from broadcast.utils.telegram import Telegram, TelegramSender
from contacts import models as contact_models
from general.utils.decorators import deprecated
from general.utils.ffmpeg import get_duration, get_resolution
from users.models import Student


def set_blocked(chat_id):
    """
    Update student status if he has blocked the bot
    """
    contact_models.Contact.objects.filter(tg_id=chat_id).update(blocked_bot=True)


def feedback_keyboard(is_keyboard, cb_identifier):
    """
    Markup generator
    """
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
    """
    If target is not in a list, make one
    """
    resp = target
    if type(target) is not list:
        resp = [target]
    return resp


def generate_config(message, data):
    """
    Get config to pass further to Telegram sender
    """
    kb = feedback_keyboard(data['is_feedback'], data['contact_id'])
    image = None
    video = None
    thumb = None
    duration = None
    width = None
    height = None

    if message.image:
        image = message.image.path

    if message.video:
        video = message.video.path
        thumb = image
        duration = get_duration(video)
        width, height = get_resolution(video)
        image = None

    return {
        'message_id': data['message_id'],
        'contact_id': data['contact_id'],
        'chat_id': data['tg_id'],
        'text': message.text,
        'photo': image,
        'video': video,
        'thumbnail': thumb,
        'duration': duration,
        'width': width,
        'height': height,
        'markup': kb,
    }


@shared_task
def save_msg(msg_id):
    """
    Chord callback function to mark message sending as finished
    """
    msg = models.Message.objects.get(pk=msg_id)
    msg.delivery_end_time = datetime.datetime.now()
    msg.save()


@shared_task
def send_message(data):
    """
    Send message and save status sending
    """
    message_history = MessageHistory(
        message_id=data['message_id'],
        contact_id=data['contact_id'],
        delivered=False
    )
    resp = TelegramSender(chat_id=data.get('chat_id'), text=data.get('text'),
                          photo=data.get('photo'), video=data.get('video'),
                          duration=data.get('duration'), width=data.get('width'),
                          height=data.get('height'), thumbnail=data.get('thumbnail'),
                          markup=data.get('markup')).send()

    if resp.get('ok'):
        message_history.delivered = True

    if resp.get('ok') is False and resp.get('error_code') == 403:
        set_blocked(data.get('chat_id'))

    message_history.save()
    logger.info(resp)


@shared_task
def send_to_queue(data):
    """
    Prepare config for every intended recipient and send message
    """
    message = models.Message.objects.get(pk=data['message_id'])
    contacts = contact_models.Contact.objects.filter(pk__in=_listify(data['ids']))
    tasks = []
    for counter, contact in enumerate(contacts, start=1):
        # https://core.telegram.org/bots/faq#my-bot-is-hitting-limits-how-do-i-avoid-this
        # Telegram imposes restriction on sending message to 30 users per sec
        if counter % 25 == 0:
            time.sleep(1)

        if not contact.blocked_bot:
            config = generate_config(message, {
                'is_feedback': data['is_feedback'],
                'contact_id': contact.id,
                'tg_id': contact.tg_id,
                'message_id': message.id,
            })
            tasks.append(send_message.s(config))
    chord(tasks)(save_msg.si(message.id))


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
