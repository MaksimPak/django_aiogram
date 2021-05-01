import uuid

from django.db import models
from django.contrib.auth.models import AbstractUser
from django.template.defaultfilters import truncatewords

from dashboard.misc import LeadManager, ClientManager


class User(AbstractUser):
    pass


class Student(models.Model):
    class ApplicationType(models.TextChoices):
        web = '1', 'Web',
        telegram = '2', 'Telegram'

    first_name = models.CharField(max_length=50, verbose_name='Имя')
    last_name = models.CharField(max_length=50, verbose_name='Фамилия')
    tg_id = models.BigIntegerField(verbose_name='Telegram ID', blank=True, null=True)
    phone = models.CharField(max_length=20, verbose_name='Контактный телефон')
    application_type = models.CharField(verbose_name='Как заполнил форму', max_length=20, choices=ApplicationType.choices, default=ApplicationType.web)
    is_client = models.BooleanField(verbose_name='Клиент', default=False)
    courses = models.ManyToManyField('Course', through='StudentCourse')
    lessons = models.ManyToManyField('Lesson', through='StudentLesson')

    def __str__(self):
        return f'{self.first_name} {self.last_name}'


class Lead(Student):

    objects = LeadManager()

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


class Course(models.Model):
    class CategoryType(models.TextChoices):
        game_dev = '1', 'Game Development'
        web = '2', 'Web Development',

    class DifficultyType(models.TextChoices):
        easy = '1', 'Beginner',
        medium = '2', 'Intermediate',
        hard = '3', 'Advanced'

    name = models.CharField(max_length=50, verbose_name='Название курса')
    info = models.TextField(blank=True, null=True, verbose_name='Описание')
    category = models.CharField(max_length=20, choices=CategoryType.choices, verbose_name='Категория')
    difficulty = models.CharField(max_length=20, choices=DifficultyType.choices, verbose_name='Сложность')
    price = models.BigIntegerField(verbose_name='Цена')

    def __str__(self):
        return self.name

    @property
    def short_info(self):
        return truncatewords(self.info, 10)

    class Meta:
        verbose_name = 'Курс'
        verbose_name_plural = 'Курсы'


class Lesson(models.Model):
    title = models.CharField(max_length=50, verbose_name='Название урока')
    info = models.TextField(blank=True, null=True, verbose_name='Описание')

    def __str__(self):
        return self.title

    class Meta:
        verbose_name = 'Урок'
        verbose_name_plural = 'Уроки'


class LessonUrl(models.Model):
    student = models.OneToOneField(Student, on_delete=models.CASCADE, primary_key=True)
    hash = models.UUIDField(default=uuid.uuid4, unique=True)
    lesson = models.ForeignKey(Lesson, on_delete=models.CASCADE, verbose_name='Урок')


class StudentCourse(models.Model):
    student = models.ForeignKey(Student, on_delete=models.CASCADE)
    course = models.ForeignKey(Course, on_delete=models.CASCADE)
    stream = models.ForeignKey(Stream, on_delete=models.PROTECT, blank=True, null=True)


class StudentLesson(models.Model):
    student = models.ForeignKey(Student, on_delete=models.CASCADE)
    lesson = models.ForeignKey(Lesson, on_delete=models.CASCADE)
    has_homework = models.BooleanField(verbose_name='Есть домашнее задание', default=False)
