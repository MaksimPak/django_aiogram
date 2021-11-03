import datetime
import json
import time

from celery import shared_task, chord
from loguru import logger

from broadcast import models
from broadcast.models import MessageHistory
from broadcast.utils.telegram import TelegramSender
from contacts import models as contact_models
from general.utils.ffmpeg import get_duration, get_resolution


def set_blocked(chat_id):
    """
    Update student status if he has blocked the bot
    """
    contact_models.Contact.objects.filter(tg_id=chat_id).update(blocked_bot=True)


def feedback_keyboard(is_keyboard, cb_identifier, history_id):
    """
    Markup generator
    """
    kb = None
    if is_keyboard:
        kb = json.dumps({'inline_keyboard': [
                [{
                    'text': 'Ответить',
                    'callback_data': f'data|feedback_student|{cb_identifier}|{history_id}'
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


def get_config(message, data):
    """
    Get config to pass further to Telegram sender
    """
    kb = feedback_keyboard(data['is_feedback'], data['contact_id'], data['history_id'])
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
def send_message(message_id, contact_id, ctx):
    """
    Send message and save status sending
    """
    message = models.Message.objects.get(pk=message_id)
    message_history = MessageHistory(
        message_id=message_id,
        contact_id=contact_id,
        delivered=False
    )
    message_history.save()  # Only to retrieve id of created object
    ctx['history_id'] = message_history.pk
    data = get_config(message, ctx)
    resp = TelegramSender(**data).send()

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
            tasks.append(send_message.s(message.id, contact.id, {
                'contact_id': contact.id,
                'is_feedback': data['is_feedback'],
                'tg_id': contact.tg_id,
            }))
    chord(tasks)(save_msg.si(message.id))
