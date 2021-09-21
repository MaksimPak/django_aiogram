from django.core.exceptions import ValidationError
from django.db import models

# Create your models here.
from django.template.defaultfilters import truncatewords

from courses.utils.uploaders import lesson_upload_directory
from general.models import BaseModel, AccessType
from general.utils.helpers import generate_uuid
from general.validators import validate_hashtag, validate_photo_extension, validate_video_extension

COURSE_HELP_TEXT = """
Если вводится Chatid группы вам нужно создать группу, добавить туда бота, узнать её чат айди, и ввести его здесь.
Боту надо дать админ права в группе чтобы он мог форвардить сообщения
"""


class Course(BaseModel):
    class DifficultyType(models.TextChoices):
        easy = '1', 'Beginner',
        medium = '2', 'Intermediate',
        hard = '3', 'Advanced'

    name = models.CharField(max_length=100, verbose_name='Название курса')
    info = models.TextField(blank=True, null=True, verbose_name='Описание')
    hashtag = models.CharField(max_length=20, verbose_name='Хештег', null=True, blank=True, validators=[validate_hashtag])
    learning_centre = models.ForeignKey('companies.LearningCentre', on_delete=models.PROTECT, verbose_name='Уч центр')
    start_message = models.TextField(verbose_name='Сообщение для отправки студентам после начала курса', blank=True, null=True)
    end_message = models.TextField(verbose_name='Сообщение для отправки студентам после завершения курса', blank=True, null=True)
    difficulty = models.CharField(max_length=20, choices=DifficultyType.choices, verbose_name='Сложность')
    price = models.BigIntegerField(verbose_name='Цена')
    is_free = models.BooleanField(verbose_name='Бесплатный курс', default=False)
    week_size = models.IntegerField(verbose_name='Количество уроков в неделю', default=0)
    is_started = models.BooleanField(verbose_name='Курс начат', default=False)
    is_finished = models.BooleanField(verbose_name='Курс закончен', default=False)
    chat_id = models.BigIntegerField(verbose_name='Telegram ID', help_text=COURSE_HELP_TEXT)
    autosend = models.BooleanField(verbose_name='Авто-отправка', default=False)
    access_level = models.IntegerField(verbose_name='Доступ', default=AccessType.client, choices=AccessType.choices)

    date_started = models.DateTimeField(verbose_name='Дата начала курса', null=True, blank=True)
    date_finished = models.DateTimeField(verbose_name='Дата окончания курса', null=True, blank=True)

    def __str__(self):
        return self.name

    def clean(self):
        if self.is_started and not self.lesson_set.all():
            raise ValidationError('Нельзя начать курс, если нет уроков')

    @property
    def course_info(self):
        return truncatewords(self.info, 5)

    class Meta:
        verbose_name = 'Курс'
        verbose_name_plural = 'Курсы'


class Lesson(BaseModel):
    title = models.CharField(max_length=100, verbose_name='Название урока')
    info = models.TextField(blank=True, null=True, verbose_name='Описание')
    image = models.ImageField(verbose_name='Картинка', null=True, blank=True, upload_to=lesson_upload_directory, validators=[validate_photo_extension])
    image_file_id = models.CharField(verbose_name='Photo file ID', null=True, blank=True, editable=False, max_length=255)
    video = models.FileField(verbose_name='Видео к уроку', upload_to=lesson_upload_directory, validators=[validate_video_extension])
    course = models.ForeignKey(Course, on_delete=models.CASCADE)
    has_homework = models.BooleanField(verbose_name='Есть домашнее задание', default=False)
    homework_desc = models.TextField(verbose_name='Homework description', null=True, blank=True)
    date_sent = models.DateTimeField(verbose_name='Дата отсылки урока', null=True, blank=True, editable=False)

    def __str__(self):
        return self.title

    @property
    def lesson_info(self):
        return truncatewords(self.info, 5)

    class Meta:
        verbose_name = 'Урок'
        verbose_name_plural = 'Уроки'


class LessonUrl(BaseModel):
    student = models.ForeignKey('users.Student', on_delete=models.CASCADE, verbose_name='Студент')
    hash = models.CharField(max_length=36, default=generate_uuid, unique=True)
    lesson = models.ForeignKey('courses.Lesson', on_delete=models.CASCADE, verbose_name='Урок')
    hits = models.IntegerField(verbose_name='Количество возможных переховод по ссылке', default=0)

    class Meta:
        unique_together = [['student', 'lesson']]


class StudentCourse(BaseModel):
    student = models.ForeignKey('users.Student', on_delete=models.CASCADE)
    course = models.ForeignKey('courses.Course', on_delete=models.CASCADE)
    has_paid = models.BooleanField(verbose_name='Оплатил курс', default=False)

    class Meta:
        unique_together = [['student', 'course']]


class StudentLesson(BaseModel):
    student = models.ForeignKey('users.Student', on_delete=models.CASCADE)
    lesson = models.ForeignKey('courses.Lesson', on_delete=models.CASCADE)

    date_sent = models.DateTimeField(verbose_name='Дата получения урока', null=True, blank=True)
    date_watched = models.DateTimeField(verbose_name='Дата дата просмотра урока', null=True, blank=True)
    homework_sent = models.DateTimeField(verbose_name='Дата отправки дз', null=True, blank=True)

    class Meta:
        unique_together = [['student', 'lesson']]
