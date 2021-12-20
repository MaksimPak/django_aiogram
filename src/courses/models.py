from django.core.validators import MinValueValidator, MaxValueValidator
from django.db import models
from django.template.defaultfilters import truncatewords

from courses.utils.helpers import course_additional
from courses.utils.uploaders import lesson_upload_directory
from general.models import BaseModel
from general.validators import validate_hashtag, validate_photo_extension, validate_video_extension

COURSE_HELP_TEXT = """
Если вводится Chatid группы вам нужно создать группу, добавить туда бота, узнать её чат айди, и ввести его здесь.
Боту надо дать админ права в группе чтобы он мог форвардить сообщения
"""


class CourseCategory(BaseModel):
    name = models.CharField(max_length=100, verbose_name='Название группы')

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = 'Группа'
        verbose_name_plural = 'Группы'


class Course(BaseModel):
    name = models.CharField(max_length=100, verbose_name='Название курса')
    description = models.TextField(verbose_name='Описание')
    code = models.CharField(max_length=20, verbose_name='Хештег', unique=True,
                            null=True, blank=True, validators=[validate_hashtag])
    company = models.ForeignKey('companies.Company',
                                on_delete=models.PROTECT, verbose_name='Уч центр')
    category = models.ForeignKey('courses.CourseCategory', on_delete=models.CASCADE, verbose_name='Группа')
    data = models.JSONField(null=True, blank=True, default=course_additional)
    date_started = models.DateTimeField(verbose_name='Дата начала курса', null=True, blank=True)
    date_finished = models.DateTimeField(verbose_name='Дата окончания курса', null=True, blank=True)

    set_priority_date = models.DateTimeField(verbose_name='Первый в спике бота', null=True, blank=True)

    chat_id = models.BigIntegerField(verbose_name='Telegram ID', help_text=COURSE_HELP_TEXT)

    def __str__(self):
        return self.name

    @property
    def course_info(self):
        return truncatewords(self.description, 5)

    class Meta:
        verbose_name = 'Курс'
        verbose_name_plural = 'Курсы'


class CourseMedia(Course):

    class Meta:
        proxy = True
        verbose_name = 'Видеоматериал Курса'
        verbose_name_plural = 'Видеоматериалы Курса'


class Lesson(BaseModel):
    name = models.CharField(max_length=100, verbose_name='Название урока')
    description = models.TextField(blank=True, null=True, verbose_name='Описание')
    image = models.ImageField(verbose_name='Картинка', null=True, blank=True,
                              upload_to=lesson_upload_directory,
                              validators=[validate_photo_extension])
    video = models.FileField(verbose_name='Видео к уроку',
                             upload_to=lesson_upload_directory,
                             validators=[validate_video_extension])
    course = models.ForeignKey(Course, on_delete=models.CASCADE)
    homework_desc = models.TextField(verbose_name='Описание дз', null=True, blank=True)

    form = models.ForeignKey('forms.Form', verbose_name='Форма',
                             on_delete=models.SET_NULL,
                             blank=True, null=True)
    form_pass_rate = models.PositiveSmallIntegerField(verbose_name='% Прохождения формы',
                                                      null=True, blank=True, default=0,
                                                      validators=[MinValueValidator(0), MaxValueValidator(100)])

    def __str__(self):
        return self.name

    @property
    def has_hmw(self):
        raise NotImplementedError

    @property
    def lesson_info(self):
        return truncatewords(self.description, 5)

    class Meta:
        verbose_name = 'Урок'
        verbose_name_plural = 'Уроки'


class StudentCourse(BaseModel):
    student = models.ForeignKey('users.Student', on_delete=models.CASCADE)
    course = models.ForeignKey('courses.Course', on_delete=models.CASCADE)
    has_paid = models.BooleanField(verbose_name='Оплатил курс', default=False)

    class Meta:
        unique_together = [['student', 'course']]


class StudentLesson(BaseModel):
    student = models.ForeignKey('users.Student', on_delete=models.CASCADE)
    lesson = models.ForeignKey('courses.Lesson', on_delete=models.CASCADE)

    # todo date_received de facto. rename
    date_sent = models.DateTimeField(verbose_name='Дата получения урока', null=True, blank=True)
    date_watched = models.DateTimeField(verbose_name='Дата дата просмотра урока', null=True, blank=True)
    homework_sent = models.DateTimeField(verbose_name='Дата отправки дз', null=True, blank=True)

    class Meta:
        unique_together = [['student', 'lesson']]
