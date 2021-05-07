import json
import os

import requests
from django.db.models.signals import post_save
from django.dispatch import receiver

from dashboard.models import StudentCourse


@receiver(post_save, sender=StudentCourse)
def send_course_add_message(sender, instance, created, **kwargs):
    if created:
        kb = {
            'inline_keyboard': [
                [{
                    'text': 'Начать Курс',
                    'callback_data': f'get_course|{instance.course.id}'
                }],
            ]
        }
        d = {
            'chat_id': instance.student.tg_id,
            'text': instance.course.add_message,
            'reply_markup': json.dumps(kb)
        }
        url = f"https://api.telegram.org/bot{os.getenv('BOT_TOKEN')}/sendMessage"
        requests.post(url, data=d)
