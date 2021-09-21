from django.contrib.auth.models import AbstractUser
from django.contrib.gis.db.models import PointField
from django.contrib.postgres.fields import ArrayField
from django.db import models, transaction


from general.models import BaseModel
from general.utils.decorators import deprecated
from users.managers import LeadManager, ClientManager


class User(AbstractUser):

    class Meta:
        verbose_name = 'Админ'
        verbose_name_plural = 'Админы'


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
    learning_centre = models.ForeignKey('companies.LearningCentre', on_delete=models.PROTECT, verbose_name='Учебный центр', null=True, blank=True)
    application_type = models.CharField(verbose_name='Как заполнил форму', max_length=20, choices=ApplicationType.choices, default=ApplicationType.admin)
    unique_code = models.CharField(max_length=255, verbose_name='Инвайт код', unique=True, null=True, blank=True)
    is_client = models.BooleanField(verbose_name='Клиент', default=False)
    checkout_date = models.DateTimeField(blank=True, null=True, verbose_name='Дата чекаута',)
    invite_link = models.CharField(max_length=255, editable=False, null=True, blank=True, verbose_name='Инвайт ссылка')
    courses = models.ManyToManyField('courses.Course', through='courses.StudentCourse')
    lessons = models.ManyToManyField('courses.Lesson', through='courses.StudentLesson')
    promo = models.ForeignKey('broadcast.Promotion', on_delete=models.SET_NULL, verbose_name='Из какого промо пришел', null=True, blank=True)
    blocked_bot = models.BooleanField(verbose_name='Заблокировал бота', default=False)
    comment = models.TextField(verbose_name='Комментарий к пользователю', blank=True, null=True)
    contact = models.OneToOneField('contacts.Contact', on_delete=models.SET_NULL, verbose_name='ТГ Профиль', null=True, blank=True)

    location = PointField(null=True, blank=True, verbose_name='Локация')
    games = ArrayField(models.CharField(max_length=50, blank=True), null=True, blank=True, verbose_name='Игры')

    @deprecated
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

    def __str__(self):
        return f'Лид[{self.first_name} {self.last_name or ""}]'

    class Meta:
        proxy = True
        verbose_name = 'Лид'
        verbose_name_plural = 'Лиды'


class Client(Student):

    objects = ClientManager()

    def __str__(self):
        return f'Клиент[{self.first_name} {self.last_name or ""}]'

    class Meta:
        proxy = True
        verbose_name = 'Клиент'
        verbose_name_plural = 'Клиенты'
