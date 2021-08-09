import uuid

from django.contrib.auth.models import AbstractUser
from django.core.exceptions import ValidationError
from django.db import models, transaction
from django.template.defaultfilters import truncatewords

from dashboard.validators import (
    validate_video_extension, validate_photo_extension,
    validate_hashtag, validate_file_size,
    validate_dimensions, validate_thumbnail_size
)

COURSE_HELP_TEXT = 'Если вводится Chatid группы вам нужно создать группу, добавить туда бота, узнать её чат айди, и ввести его здесь. Боту надо дать админ права в группе чтобы он мог форвардить сообщения'
THUMBNAIL_HELP_TEXT = 'The thumbnail should be in JPEG format and less than 200 kB in size. A thumbnail\'s width and height should not exceed 320.'


def lesson_upload_directory(instance, filename):
    return f'courses/{instance.course.id}/{filename}'


def promo_upload_directory(instance, filename):
    if getattr(instance, 'course'):
        return f'promos/{instance.course.id}/{filename}'
    else:
        return f'promos/{filename}'


def form_question_directory(instance, filename):
    return f'form_questions/{instance.form.id}/{filename}'


def form_directory(instance, filename):
    return f'forms/{instance.id}/{filename}'


def generate_uuid():
    return str(uuid.uuid4())[:8]


class BaseModel(models.Model):
    created_at = models.DateTimeField('Дата создания', auto_now_add=True, null=True, blank=True)
    updated_at = models.DateTimeField('Дата обновления', auto_now=True, null=True, blank=True)

    class Meta:
        abstract = True


class LeadManager(models.Manager):
    def get_queryset(self):
        return super(LeadManager, self).get_queryset().filter(is_client=False)


class ClientManager(models.Manager):
    def get_queryset(self):
        return super(ClientManager, self).get_queryset().filter(is_client=True)


class User(AbstractUser):

    class Meta:
        verbose_name = 'Админ'
        verbose_name_plural = 'Админы'


class CategoryType(BaseModel):
    title = models.CharField(max_length=50, verbose_name='Название категории', unique=True)
    uz_title = models.CharField(max_length=50, verbose_name='Узбекская версия', unique=True, blank=True, null=True)

    def __str__(self):
        return self.title

    class Meta:
        verbose_name = 'Категория'
        verbose_name_plural = 'Категории'


class Contact(BaseModel):
    first_name = models.CharField(verbose_name='ТГ Имя', max_length=255)
    last_name = models.CharField(verbose_name='ТГ Фамилия', max_length=255, null=True, blank=True)
    tg_id = models.BigIntegerField(verbose_name='Telegram ID', blank=True, null=True, unique=True)
    is_registered = models.BooleanField(default=False)
    data = models.JSONField(null=True, blank=True, default=dict)

    def __str__(self):
        return f'TG[{self.first_name}]'

    class Meta:
        verbose_name = 'ТГ Профиль'
        verbose_name_plural = 'ТГ Профили'


class Student(BaseModel):
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
    chosen_field = models.ForeignKey(CategoryType, on_delete=models.PROTECT, verbose_name='Желанная отрасль')
    application_type = models.CharField(verbose_name='Как заполнил форму', max_length=20, choices=ApplicationType.choices, default=ApplicationType.admin)
    unique_code = models.CharField(max_length=255, verbose_name='Инвайт код', unique=True, null=True, blank=True)
    is_client = models.BooleanField(verbose_name='Клиент', default=False)
    checkout_date = models.DateTimeField(blank=True, null=True, verbose_name='Дата чекаута',)
    invite_link = models.CharField(max_length=255, editable=False, null=True, blank=True, verbose_name='Инвайт ссылка')
    courses = models.ManyToManyField('Course', through='StudentCourse')
    lessons = models.ManyToManyField('Lesson', through='StudentLesson')
    promo = models.ForeignKey('Promotion', on_delete=models.SET_NULL, verbose_name='Из какого промо пришел', null=True, blank=True)
    blocked_bot = models.BooleanField(verbose_name='Заблокировал бота', default=False)
    comment = models.TextField(verbose_name='Комментарий к пользователю', blank=True, null=True)
    contact = models.OneToOneField(Contact, on_delete=models.SET_NULL, verbose_name='ТГ Профиль', null=True, blank=True)

    def __str__(self):
        return f'{self.first_name} {self.last_name or ""}'

    @property
    def short_name(self):
        return f'{self.first_name[0]}.{self.last_name or ""}'

    @transaction.atomic
    def assign_courses(self, courses, is_client=False):
        self.courses.add(*courses)
        if is_client:
            self.is_client = is_client
            self.save()

    class Meta:
        verbose_name = 'Студент'
        verbose_name_plural = 'Студенты'


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


class Course(BaseModel):
    class DifficultyType(models.TextChoices):
        easy = '1', 'Beginner',
        medium = '2', 'Intermediate',
        hard = '3', 'Advanced'

    name = models.CharField(max_length=50, verbose_name='Название курса')
    info = models.TextField(blank=True, null=True, verbose_name='Описание')
    hashtag = models.CharField(max_length=20, verbose_name='Хештег', null=True, blank=True, validators=[validate_hashtag])
    category = models.ForeignKey(CategoryType, on_delete=models.PROTECT, verbose_name='Категория')
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


class Promotion(BaseModel):
    title = models.CharField(max_length=50, verbose_name='Название')
    video = models.FileField(verbose_name='Промо видео', upload_to=promo_upload_directory, validators=[validate_video_extension, validate_file_size], help_text='Не больше 50 мб')
    thumbnail = models.ImageField(verbose_name='Промо превью', null=True, blank=True, upload_to=promo_upload_directory, validators=[validate_dimensions, validate_thumbnail_size], help_text=THUMBNAIL_HELP_TEXT)
    description = models.TextField(verbose_name='Описание')
    course = models.ForeignKey(Course, on_delete=models.SET_NULL, verbose_name='Курс', null=True, blank=True)
    counter = models.IntegerField('Подсчет просмотра', default=0)
    link = models.CharField(max_length=255, editable=False, null=True, blank=True, verbose_name='Инвайт ссылка')
    video_file_id = models.CharField(verbose_name='Video file ID', null=True, blank=True, editable=False, max_length=255)
    unique_code = models.CharField(max_length=255, verbose_name='Инвайт код', unique=True, null=True, blank=True, editable=False)
    start_message = models.TextField(verbose_name='Сообщение после регистрации на курс')
    display_link = models.BooleanField(verbose_name='Показать ссылку', default=False)

    def __str__(self):
        return self.title

    class Meta:
        verbose_name = 'Промо'
        verbose_name_plural = 'Промо'


class Lesson(BaseModel):
    title = models.CharField(max_length=50, verbose_name='Название урока')
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
    student = models.ForeignKey(Student, on_delete=models.CASCADE, verbose_name='Студент')
    hash = models.CharField(max_length=36, default=generate_uuid, unique=True)
    lesson = models.ForeignKey(Lesson, on_delete=models.CASCADE, verbose_name='Урок')
    hits = models.IntegerField(verbose_name='Количество возможных переховод по ссылке', default=0)

    class Meta:
        unique_together = [['student', 'lesson']]


class StudentCourse(BaseModel):
    student = models.ForeignKey(Student, on_delete=models.CASCADE)
    course = models.ForeignKey(Course, on_delete=models.CASCADE)
    has_paid = models.BooleanField(verbose_name='Оплатил курс', default=False)

    class Meta:
        unique_together = [['student', 'course']]


class StudentLesson(BaseModel):
    student = models.ForeignKey(Student, on_delete=models.CASCADE)
    lesson = models.ForeignKey(Lesson, on_delete=models.CASCADE)

    date_sent = models.DateTimeField(verbose_name='Дата получения урока', null=True, blank=True)
    date_watched = models.DateTimeField(verbose_name='Дата дата просмотра урока', null=True, blank=True)
    homework_sent = models.DateTimeField(verbose_name='Дата отправки дз', null=True, blank=True)

    class Meta:
        unique_together = [['student', 'lesson']]


class SendingReport(BaseModel):
    class LanguageType(models.TextChoices):
        all = 'all', 'Всем'
        ru = '1', 'Russian'
        uz = '2', 'Uzbek'

    lang = models.CharField(max_length=20, choices=LanguageType.choices, verbose_name='Язык отправки')
    promotion = models.ForeignKey(Promotion, on_delete=models.CASCADE, verbose_name='Промо')
    sent = models.IntegerField(verbose_name='Кол-во получателей', default=0)
    received = models.IntegerField(verbose_name='Итого отправлено', default=0)
    failed = models.IntegerField(verbose_name='Не получило', default=0)
    celery_id = models.CharField(verbose_name='Celery group uuid', max_length=36, editable=False)
    status = models.CharField(verbose_name='Статус отправки', max_length=50, null=True, blank=True)

    def __str__(self):
        return f'Отправка №{self.id}'

    class Meta:
        verbose_name_plural = 'Отчеты'
        verbose_name = 'Отчет'


class Form(BaseModel):
    class FormType(models.TextChoices):
        private = 'private', 'Закрытый'
        public = 'public', 'Открытый'

    class FormMode(models.TextChoices):
        quiz = 'quiz', 'Викторина'
        questionnaire = 'questionnaire', 'Вопросник'

    name = models.CharField(max_length=50, verbose_name='Название')
    type = models.CharField(max_length=20, verbose_name='Тип', default=FormType.public, choices=FormType.choices)
    mode = models.CharField(max_length=20, verbose_name='Режим работы', choices=FormMode.choices)
    unique_code = models.IntegerField(verbose_name='Уникальный код', null=True, blank=True)
    link = models.CharField(max_length=50, verbose_name='Линк', null=True, blank=True)
    start_message = models.CharField(max_length=50, verbose_name='Сообщение для отправки при старте')
    end_message = models.CharField(max_length=50, verbose_name='Сообщение для отправки при завершении')
    is_active = models.BooleanField(verbose_name='Активна', default=False)
    one_off = models.BooleanField(verbose_name='Одноразовая форма', default=False)
    image = models.ImageField(verbose_name='Картинка', blank=True, null=True, upload_to=form_directory)

    def __str__(self):
        return f'Форма: [{self.name}]'

    class Meta:
        verbose_name = 'Форма'
        verbose_name_plural = 'Формы'


class FormQuestion(BaseModel):
    form = models.ForeignKey(Form, on_delete=models.CASCADE, verbose_name='Форма')
    multi_answer = models.BooleanField(verbose_name='Мульти-ответ', default=False)
    text = models.CharField(max_length=50, verbose_name='Текст')
    image = models.ImageField(verbose_name='Картинка', blank=True, null=True, upload_to=form_question_directory)
    position = models.IntegerField(verbose_name='Нумерация')
    custom_answer = models.BooleanField(verbose_name='Кастомный ответ', default=False)
    custom_answer_text = models.CharField(verbose_name='Текст кастомного ответа', max_length=50, null=True, blank=True)
    one_row_btns = models.BooleanField(verbose_name='Однострочные ответы', default=False)

    def __str__(self):
        return f'[{self.form.name}]Вопрос: {self.text}'

    def clean(self):
        if self.custom_answer and self.form.mode == Form.FormMode.quiz:
            raise ValidationError('Нельзя добавить кастомный ответ к викторине')

    class Meta:
        verbose_name = 'Вопрос'
        verbose_name_plural = 'Вопросы'
        ordering = ('position', 'id')


class FormAnswer(BaseModel):
    question = models.ForeignKey(FormQuestion, on_delete=models.CASCADE, verbose_name='Вопрос', related_name='questions', null=True)
    is_correct = models.BooleanField(verbose_name='Правильный ответ', default=False)
    text = models.CharField(max_length=50, verbose_name='Текст ответа')
    jump_to = models.ForeignKey(FormQuestion, on_delete=models.CASCADE, verbose_name='Ведет к вопросу', null=True, blank=True, related_name='jumps')

    def clean(self):
        if self.is_correct and self.question.form.mode == Form.FormMode.questionnaire:
            raise ValidationError('У опросника нет правильного ответа')


class ContactFormAnswers(BaseModel):
    contact = models.ForeignKey(Contact, on_delete=models.SET_NULL, null=True, verbose_name='Студент')
    form = models.ForeignKey(Form, on_delete=models.SET_NULL, null=True, verbose_name='Форма')
    score = models.IntegerField(verbose_name='Балл', null=True, blank=True)
    data = models.JSONField(verbose_name='Данные', null=True, blank=True, default=dict)

    class Meta:
        verbose_name = 'Ответ на форму'
        verbose_name_plural = 'Ответы на форму'
        unique_together = [['contact', 'form']]

