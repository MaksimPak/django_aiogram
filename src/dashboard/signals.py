import json
import os

import requests
from django.db.models.signals import post_save
from django.dispatch import receiver

from dashboard.models import StudentCourse, Client, Lead, Course, Student, random_int


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


@receiver(post_save, sender=Client)
@receiver(post_save, sender=Lead)
def add_free_courses(sender, instance, created, **kwargs):
    if created:
        courses = Course.objects.filter(is_free=True)
        StudentCourse.objects.bulk_create([StudentCourse(course=course, student=instance) for course in courses])


@receiver(post_save, sender=Course)
def add_students_to_free_course(sender, instance, created, **kwargs):
    if created and instance.is_free:
        students = Student.objects.all()
        StudentCourse.objects.bulk_create([StudentCourse(course=instance, student=student) for student in students])


@receiver(post_save, sender=Lead)
def add_students_to_free_course(sender, instance, created, **kwargs):
    if created and not instance.unique_code:
        Lead.objects.filter(pk=instance.id).update(unique_code=str(instance.id) + random_int())
