from django.core.validators import MinValueValidator, MaxValueValidator
from django.db import models
from django.template.defaultfilters import truncatewords

from courses import help_texts
from courses.utils.helpers import course_additional
from courses.utils.uploaders import lesson_upload_directory
from general.models import BaseModel, AccessType
from general.validators import validate_hashtag, validate_photo_extension, validate_video_extension


class CourseCategory(BaseModel):
    name = models.CharField(max_length=100, verbose_name='Название группы')

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = 'Группа курса'
        verbose_name_plural = 'Группы Курсов'


class LessonCategory(BaseModel):
    name = models.CharField(max_length=100, verbose_name='Название группы')

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = 'Группа урока'
        verbose_name_plural = 'Группы уроков'


class Course(BaseModel):
    COURSE_LEVELS = AccessType.choices + [(4, 'Контролируемый')]  # Extra option needed for rare cases

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
    access_level = models.IntegerField(verbose_name='Доступ', default=AccessType.client,
                                       choices=COURSE_LEVELS, help_text=help_texts.COURSE_ACCESS_LEVEL)

    chat_id = models.BigIntegerField(verbose_name='Telegram ID', help_text=help_texts.COURSE_CHAT_ID)

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
    comment = models.TextField(verbose_name='Сообщение по завершению', null=True, blank=True)
    rate_lesson_msg = models.TextField(verbose_name='Сообщение при оценке урока', null=True, blank=True)

    form = models.ForeignKey('forms.Form', verbose_name='Форма',
                             on_delete=models.SET_NULL,
                             blank=True, null=True)
    form_pass_rate = models.PositiveSmallIntegerField(verbose_name='% Прохождения формы',
                                                      null=True, blank=True, default=0,
                                                      validators=[MinValueValidator(0), MaxValueValidator(100)])

    likes = models.IntegerField(verbose_name='Лайки', default=0)
    dislikes = models.IntegerField(verbose_name='Дизлайки', default=0)

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
    has_finished = models.BooleanField(verbose_name='Завершил курс', default=False)

    class Meta:
        unique_together = [['student', 'course']]


class StudentLesson(BaseModel):
    student = models.ForeignKey('users.Student', on_delete=models.CASCADE)
    lesson = models.ForeignKey('courses.Lesson', on_delete=models.CASCADE)
    is_rated = models.BooleanField(editable=False, default=False)

    # todo date_received de facto. rename
    date_sent = models.DateTimeField(verbose_name='Дата получения урока', null=True, blank=True)
    date_watched = models.DateTimeField(verbose_name='Дата дата просмотра урока', null=True, blank=True)
    homework_sent = models.DateTimeField(verbose_name='Дата отправки дз', null=True, blank=True)

    class Meta:
        unique_together = [['student', 'lesson']]
