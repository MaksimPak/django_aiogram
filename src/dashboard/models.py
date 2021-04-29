import uuid

from django.db import models
from django.contrib.auth.models import AbstractUser

# Create your models here.


class User(AbstractUser):
    pass


class Student(models.Model):
    class ApplicationType(models.TextChoices):
        web = '1', 'Web',
        telegram = '2', 'Telegram'

    first_name = models.CharField(max_length=50, verbose_name='Имя')
    last_name = models.CharField(max_length=50, verbose_name='Фамилия')
    tg_id = models.BigIntegerField(verbose_name='Telegram ID', blank=True, null=True)
    phone = models.CharField(max_length=20)
    application_type = models.CharField(max_length=20, choices=ApplicationType.choices, default=ApplicationType.web)
    register_link = models.CharField(max_length=200, blank=True, null=True, verbose_name='Ссылка на регистрацию')
    courses = models.ManyToManyField('Course', through='StudentCourse')
    lessons = models.ManyToManyField('Lesson', through='StudentLesson')


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

    name = models.CharField(max_length=50)
    info = models.TextField(blank=True, null=True)
    category = models.CharField(max_length=20, choices=CategoryType.choices)
    difficulty = models.CharField(max_length=20, choices=DifficultyType.choices)
    price = models.BigIntegerField()


class Lesson(models.Model):
    title = models.CharField(max_length=50, verbose_name='Название урока')
    info = models.TextField(blank=True, null=True)


class LessonUrl(models.Model):
    student = models.OneToOneField(Student, on_delete=models.CASCADE, primary_key=True)
    hash = models.UUIDField(default=uuid.uuid4)
    lesson = models.ForeignKey(Lesson, on_delete=models.CASCADE, verbose_name='Урок')


class StudentCourse(models.Model):
    student = models.ForeignKey(Student, on_delete=models.CASCADE)
    course = models.ForeignKey(Course, on_delete=models.CASCADE)
    stream = models.ForeignKey(Stream, on_delete=models.PROTECT)


class StudentLesson(models.Model):
    student = models.ForeignKey(Student, on_delete=models.CASCADE)
    lesson = models.ForeignKey(Lesson, on_delete=models.CASCADE)
    has_homework = models.BooleanField(verbose_name='Есть домашнее задание', default=False)
