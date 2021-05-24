import datetime
import json
import os

import requests
from django.db.models.signals import post_save, post_init
from django.dispatch import receiver

from dashboard.models import StudentCourse, Client, Lead, Course, Student, random_int


@receiver(post_init, sender=Course)
def set_is_started_copy(sender, instance, *args, **kwargs):
    instance._is_started = instance.is_started


@receiver(post_save, sender=Course)
def send_course_add_message(sender, instance, created, **kwargs):
    if instance._is_started is not True:
        for student in instance.student_set.all():
            kb = {
                'inline_keyboard': [
                    [{
                        'text': 'Начать Курс',
                        'callback_data': f'get_course|{instance.id}'  # instance id out of cycle
                    }],
                ]
            }
            d = {  # todo naming
                'chat_id': student.tg_id,
                'text': instance.add_message,
                'reply_markup': json.dumps(kb)  # todo out of cycle
            }
            url = f"https://api.telegram.org/bot{os.getenv('BOT_TOKEN')}/sendMessage"
            requests.post(url, data=d)

        instance._is_started = instance.is_started
        Course.objects.filter(pk=instance.id).update(date_started=datetime.datetime.now())


@receiver(post_save, sender=Lead)
def lead_invite_data(sender, instance, created, **kwargs):
    if created and not instance.unique_code:
        instance.unique_code = str(instance.id) + random_int()
        instance.invite_link = f'https://t.me/{os.getenv("BOT_NAME")}?start={instance.unique_code}'
        instance.save()
