import datetime
import json
import os
import random

import requests
from django.db.models.signals import post_save, post_init
from django.dispatch import receiver

from dashboard.models import Lead, Course


def random_int():
    return str(random.randint(100, 999))


@receiver(post_init, sender=Course)
def set_is_started_copy(sender, instance, *args, **kwargs):
    """
    Setting local variable _is_started to track if course was started during editing of the course
    """
    instance._is_started = instance.is_started


@receiver(post_save, sender=Course)
def send_course_add_message(sender, instance, created, **kwargs):
    """
    Check if is_started variable has been set to True after editing. If yes, send a course message to all students
    """
    if instance._is_started is not True:
        course_id = instance.id
        kb = json.dumps({'inline_keyboard': [[{'text': 'Начать Курс', 'callback_data': f'get_course|{course_id}'}]]})
        url = f"https://api.telegram.org/bot{os.getenv('BOT_TOKEN')}/sendMessage"
        for student in instance.student_set.all():
            data = {
                'chat_id': student.tg_id,
                'text': instance.add_message,
                'reply_markup': kb
            }

            requests.post(url, data=data)

        instance._is_started = instance.is_started
        Course.objects.filter(pk=instance.id).update(date_started=datetime.datetime.now())


@receiver(post_save, sender=Lead)
def lead_invite_data(sender, instance, created, **kwargs):
    """
    Create a unique code and invite link for registration for a lead upon saving.
    """
    if created and not instance.unique_code:
        instance.unique_code = str(instance.id) + random_int()
        instance.invite_link = f'https://t.me/{os.getenv("BOT_NAME")}?start={instance.unique_code}'
        instance.save()
