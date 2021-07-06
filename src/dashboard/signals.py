import datetime
import json
import os
import random
import subprocess

from django.db.models.signals import post_save, post_init
from django.dispatch import receiver

from dashboard.models import Lead, Course, Promotion
from dashboard.utils.telegram import Telegram


def random_int():
    return str(random.randint(100, 999))


@receiver(post_init, sender=Course)
def set_is_started_copy(sender, instance, *args, **kwargs):
    """
    Setting local variable _is_started to track if course was started during editing of the course
    """
    instance._is_started = instance.is_started
    instance._is_finished = instance.is_finished


@receiver(post_save, sender=Course)
def send_course_add_message(sender, instance, created, **kwargs):
    """
    Check if is_started variable has been set to True after editing. If yes, send start message to all students
    """
    if instance._is_started != instance.is_started and instance.is_started is True:
        kb = json.dumps(
            {'inline_keyboard': [[
                {'text': 'Начать Курс',
                 'callback_data': f'data|get_course|{instance.id}'}
            ]]}) if instance.autosend else None

        people = instance.student_set.all()
        Telegram.send_to_people(people, instance.start_message, kb)

        instance._is_started = instance.is_started
        Course.objects.filter(pk=instance.id).update(date_started=datetime.datetime.now())


@receiver(post_save, sender=Course)
def send_course_finish_message(sender, instance, created, **kwargs):
    """
    Check if is_finished variable has been set to True after editing. If yes, send end message to all students
    """
    if instance._is_finished != instance.is_finished and instance.is_finished is True:
        people = instance.student_set.all()
        Telegram.send_to_people(people, instance.end_message)

        instance._is_finished = instance.is_finished
        Course.objects.filter(pk=instance.id).update(date_finished=datetime.datetime.now())


@receiver(post_save, sender=Lead)
def lead_invite_data(sender, instance, created, **kwargs):
    """
    Create a unique code and invite link for registration for lead upon saving.
    """
    if created and not instance.unique_code:
        instance.unique_code = str(instance.id) + random_int()
        instance.invite_link = f'https://t.me/{os.getenv("BOT_NAME")}?start={instance.unique_code}'
        instance.save()


@receiver(post_save, sender=Promotion)
def promo_invite_data(sender, instance, created, **kwargs):
    """
    Create a unique code and invite link for registration for promotion upon saving.
    """
    if created and not instance.link:
        unique_code = str(instance.id) + random_int()
        instance.unique_code = unique_code
        instance.link = f'https://t.me/{os.getenv("BOT_NAME")}?start=promo_{unique_code}'

        if not instance.thumbnail:
            img_output_path = instance.thumbnail.storage.path(f'promos/{instance.title}/thumbnail.jpeg')
            subprocess.run(['ffmpeg', '-i', instance.video.path, '-ss',
                            '5', '-s', '320x320', '-frames:v', '1', img_output_path])

            instance.thumbnail.name = f'promos/{instance.title}/thumbnail.jpeg'  # todo: hardcode

        instance.save()
