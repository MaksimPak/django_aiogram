import os
import uuid
import random

from django.db import models
from django.contrib.auth.models import AbstractUser
from django.template.defaultfilters import truncatewords, truncatechars
import requests

from dashboard.misc import LeadManager, ClientManager


def random_int():
    return str(random.randint(100, 999))


class CategoryType(models.TextChoices):
    game_dev = '1', 'Game Development'
    web = '2', 'Web Development',


class User(AbstractUser):
    pass

    class Meta:
        verbose_name = 'Админ'
        verbose_name_plural = 'Админы'


class Student(models.Model):
    class LanguageType(models.TextChoices):
        ru = '1', 'Russian'
        uz = '2', 'Uzbek'

    class ApplicationType(models.TextChoices):
        admin = '1', 'Admin',
        telegram = '2', 'Telegram'
        web = '3', 'Web'

    first_name = models.CharField(max_length=50, verbose_name='Имя')
    last_name = models.CharField(max_length=50, verbose_name='Фамилия')
    tg_id = models.BigIntegerField(verbose_name='Telegram ID', blank=True, null=True, unique=True)
    language_type = models.CharField(max_length=20, verbose_name='Язык ученика', choices=LanguageType.choices, default=LanguageType.ru)
    phone = models.CharField(max_length=20, verbose_name='Контактный телефон', unique=True)
    chosen_field = models.CharField(max_length=20, verbose_name='Желанная отрасль', choices=CategoryType.choices)
    application_type = models.CharField(verbose_name='Как заполнил форму', max_length=20, choices=ApplicationType.choices, default=ApplicationType.admin)
    unique_code = models.CharField(max_length=255, verbose_name='Инвайт код', unique=True, null=True, blank=True)
    is_client = models.BooleanField(verbose_name='Клиент', default=False)
    checkout_date = models.DateTimeField(blank=True, null=True, verbose_name='Дата чекаута')
    courses = models.ManyToManyField('Course', through='StudentCourse')

    created_at = models.DateTimeField('Дата создания', auto_now_add=True)
    updated_at = models.DateTimeField('Дата обновления', auto_now=True)

    def __str__(self):
        return f'{self.first_name} {self.last_name}'


class Lead(Student):

    objects = LeadManager()

    def save(self, *args, **kwargs):
        if not self.unique_code:
            super(Lead, self).save(*args, **kwargs)
            self.unique_code = str(self.id) + random_int()
            return super(Lead, self).save(*args, **kwargs)
        else:
            return super(Lead, self).save(*args, **kwargs)

    class Meta:
        proxy = True
        verbose_name = 'Лид'
        verbose_name_plural = 'Лиды'


class Client(Student):

    objects = ClientManager()

    class Meta:
        proxy = True
        verbose_name = 'Клиент'
        verbose_name_plural = 'Клиенты'


class Stream(models.Model):
    name = models.CharField(max_length=50)

    created_at = models.DateTimeField('Дата создания', auto_now_add=True)
    updated_at = models.DateTimeField('Дата обновления', auto_now=True)


class Course(models.Model):
    class DifficultyType(models.TextChoices):
        easy = '1', 'Beginner',
        medium = '2', 'Intermediate',
        hard = '3', 'Advanced'

    name = models.CharField(max_length=50, verbose_name='Название курса')
    info = models.TextField(blank=True, null=True, verbose_name='Описание')
    category = models.CharField(max_length=20, choices=CategoryType.choices, verbose_name='Категория')
    add_message = models.TextField(verbose_name='Сообщение для отправки студенту после добавления', blank=True, null=True)
    difficulty = models.CharField(max_length=20, choices=DifficultyType.choices, verbose_name='Сложность')
    price = models.BigIntegerField(verbose_name='Цена')

    created_at = models.DateTimeField('Дата создания', auto_now_add=True)
    updated_at = models.DateTimeField('Дата обновления', auto_now=True)

    def __str__(self):
        return self.name

    @property
    def short_info(self):
        return truncatewords(self.info, 5)

    class Meta:
        verbose_name = 'Курс'
        verbose_name_plural = 'Курсы'


class Lesson(models.Model):
    title = models.CharField(max_length=50, verbose_name='Название урока')
    info = models.TextField(blank=True, null=True, verbose_name='Описание')
    video = models.FileField(verbose_name='Видео к уроку')
    course = models.ForeignKey(Course, on_delete=models.CASCADE)
    has_homework = models.BooleanField(verbose_name='Есть домашнее задание', default=False)

    created_at = models.DateTimeField('Дата создания', auto_now_add=True)
    updated_at = models.DateTimeField('Дата обновления', auto_now=True)

    def __str__(self):
        return self.title

    @property
    def short_info(self):
        return truncatewords(self.info, 5)

    class Meta:
        verbose_name = 'Урок'
        verbose_name_plural = 'Уроки'


class LessonUrl(models.Model):
    student = models.ForeignKey(Student, on_delete=models.CASCADE, verbose_name='Студент')
    hash = models.CharField(max_length=36, default=uuid.uuid4, unique=True)
    lesson = models.ForeignKey(Lesson, on_delete=models.CASCADE, verbose_name='Урок')

    created_at = models.DateTimeField('Дата создания', auto_now_add=True)
    updated_at = models.DateTimeField('Дата обновления', auto_now=True)

    class Meta:
        unique_together = [['student', 'lesson']]


class StudentCourse(models.Model):
    student = models.ForeignKey(Student, on_delete=models.CASCADE)
    course = models.ForeignKey(Course, on_delete=models.CASCADE)
    stream = models.ForeignKey(Stream, on_delete=models.PROTECT, blank=True, null=True)

    created_at = models.DateTimeField('Дата создания', auto_now_add=True)
    updated_at = models.DateTimeField('Дата обновления', auto_now=True)

    def save(self, *args, **kwargs):
        super(StudentCourse, self).save(*args, **kwargs)
        url = f"https://api.telegram.org/bot{os.getenv('BOT_TOKEN')}/sendMessage?chat_id={self.student.tg_id}&text={self.course.add_message}"
        requests.get(url)

        return super(StudentCourse, self).save(*args, **kwargs)
