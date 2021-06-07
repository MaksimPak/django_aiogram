import uuid

from django.contrib.auth.models import AbstractUser
from django.db import models, transaction
from django.template.defaultfilters import truncatewords

from dashboard.validators import validate_video_extension, validate_photo_extension, validate_hashtag

COURSE_HELP_TEXT = 'Если вводится Chatid группы вам нужно создать группу, добавить туда бота, узнать её чат айди, и ввести его здесь. Боту надо дать админ права в группе чтобы он мог форвардить сообщения'


class LeadManager(models.Manager):
    def get_queryset(self):
        return super(LeadManager, self).get_queryset().filter(is_client=False)


class ClientManager(models.Manager):
    def get_queryset(self):
        return super(ClientManager, self).get_queryset().filter(is_client=True)


def lesson_upload_directory(instance, filename):
    return f'{instance.course.name}/{instance.title}/{filename}'


class CategoryType(models.TextChoices):
    game_dev = '1', 'Game Development'
    web = '2', 'Web Development',


class User(AbstractUser):

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
    last_name = models.CharField(max_length=50, verbose_name='Фамилия', null=True, blank=True)
    city = models.CharField(max_length=50, verbose_name='Город проживания')
    tg_id = models.BigIntegerField(verbose_name='Telegram ID', blank=True, null=True, unique=True)
    language_type = models.CharField(max_length=20, verbose_name='Язык ученика', choices=LanguageType.choices, default=LanguageType.ru)
    phone = models.CharField(max_length=20, verbose_name='Контактный телефон', unique=True)
    chosen_field = models.CharField(max_length=20, verbose_name='Желанная отрасль', choices=CategoryType.choices)
    application_type = models.CharField(verbose_name='Как заполнил форму', max_length=20, choices=ApplicationType.choices, default=ApplicationType.admin)
    unique_code = models.CharField(max_length=255, verbose_name='Инвайт код', unique=True, null=True, blank=True)
    is_client = models.BooleanField(verbose_name='Клиент', default=False)
    checkout_date = models.DateTimeField(blank=True, null=True, verbose_name='Дата чекаута',)
    invite_link = models.CharField(max_length=255, editable=False, null=True, blank=True, verbose_name='Инвайт ссылка')
    courses = models.ManyToManyField('Course', through='StudentCourse')
    lessons = models.ManyToManyField('Lesson', through='StudentLesson')

    created_at = models.DateTimeField('Дата создания', auto_now_add=True, null=True, blank=True)
    updated_at = models.DateTimeField('Дата обновления', auto_now=True, null=True, blank=True)

    def __str__(self):
        return f'{self.first_name} {self.last_name}'

    @property
    def short_name(self):
        return f'{self.first_name[0]}.{self.last_name}'

    class Meta:
        verbose_name = 'Студент'
        verbose_name_plural = 'Студенты'


class Lead(Student):

    objects = LeadManager()

    @transaction.atomic
    def assign_courses(self, courses, is_client=False):
        self.courses.add(*courses)
        if is_client:
            self.is_client = is_client
            self.save()

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


class Course(models.Model):
    class DifficultyType(models.TextChoices):
        easy = '1', 'Beginner',
        medium = '2', 'Intermediate',
        hard = '3', 'Advanced'

    name = models.CharField(max_length=50, verbose_name='Название курса')
    info = models.TextField(blank=True, null=True, verbose_name='Описание')
    hashtag = models.CharField(max_length=20, verbose_name='Хештег', null=True, blank=True, validators=[validate_hashtag])
    category = models.CharField(max_length=20, choices=CategoryType.choices, verbose_name='Категория')
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

    date_started = models.DateTimeField(verbose_name='Дата начала курса', null=True, blank=True)
    date_finished = models.DateTimeField(verbose_name='Дата окончания курса', null=True, blank=True)

    created_at = models.DateTimeField('Дата создания', auto_now_add=True, null=True, blank=True)
    updated_at = models.DateTimeField('Дата обновления', auto_now=True, null=True, blank=True)

    def __str__(self):
        return self.name

    @property
    def course_info(self):
        return truncatewords(self.info, 5)

    class Meta:
        verbose_name = 'Курс'
        verbose_name_plural = 'Курсы'


class Lesson(models.Model):
    title = models.CharField(max_length=50, verbose_name='Название урока')
    info = models.TextField(blank=True, null=True, verbose_name='Описание')
    image = models.ImageField(verbose_name='Картинка', null=True, blank=True, upload_to=lesson_upload_directory, validators=[validate_photo_extension])
    image_file_id = models.CharField(verbose_name='Photo file ID', null=True, blank=True, editable=False, max_length=255)
    video = models.FileField(verbose_name='Видео к уроку', upload_to=lesson_upload_directory, validators=[validate_video_extension])
    course = models.ForeignKey(Course, on_delete=models.CASCADE)
    has_homework = models.BooleanField(verbose_name='Есть домашнее задание', default=False)
    homework_desc = models.TextField(verbose_name='Homework description', null=True, blank=True)
    date_sent = models.DateTimeField(verbose_name='Дата отсылки урока', null=True, blank=True, editable=False)

    created_at = models.DateTimeField('Дата создания', auto_now_add=True, null=True, blank=True)
    updated_at = models.DateTimeField('Дата обновления', auto_now=True, null=True, blank=True)

    def __str__(self):
        return self.title

    @property
    def lesson_info(self):
        return truncatewords(self.info, 5)

    class Meta:
        verbose_name = 'Урок'
        verbose_name_plural = 'Уроки'


class LessonUrl(models.Model):
    student = models.ForeignKey(Student, on_delete=models.CASCADE, verbose_name='Студент')
    hash = models.CharField(max_length=36, default=uuid.uuid4, unique=True)
    lesson = models.ForeignKey(Lesson, on_delete=models.CASCADE, verbose_name='Урок')

    created_at = models.DateTimeField('Дата создания', auto_now_add=True, null=True, blank=True)
    updated_at = models.DateTimeField('Дата обновления', auto_now=True, null=True, blank=True)

    class Meta:
        unique_together = [['student', 'lesson']]


class StudentCourse(models.Model):
    student = models.ForeignKey(Student, on_delete=models.CASCADE)
    course = models.ForeignKey(Course, on_delete=models.CASCADE)

    created_at = models.DateTimeField('Дата создания', auto_now_add=True, null=True, blank=True)
    updated_at = models.DateTimeField('Дата обновления', auto_now=True, null=True, blank=True)

    class Meta:
        unique_together = [['student', 'course']]


class StudentLesson(models.Model):
    student = models.ForeignKey(Student, on_delete=models.CASCADE)
    lesson = models.ForeignKey(Lesson, on_delete=models.CASCADE)

    date_sent = models.DateTimeField(verbose_name='Дата получения урока', null=True, blank=True)
    date_watched = models.DateTimeField(verbose_name='Дата дата просмотра урока', null=True, blank=True)
    homework_sent = models.DateTimeField(verbose_name='Дата отправки дз', null=True, blank=True)

    created_at = models.DateTimeField('Дата создания', auto_now_add=True, null=True, blank=True)
    updated_at = models.DateTimeField('Дата обновления', auto_now=True, null=True, blank=True)

    class Meta:
        unique_together = [['student', 'lesson']]
