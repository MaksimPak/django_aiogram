from django.core.validators import validate_image_file_extension
from django.db import models

# Create your models here.
from companies.utils.uploaders import lc_upload_directory
from general.models import BaseModel


class LearningCentre(BaseModel):
    title = models.CharField(max_length=100, verbose_name='Название Уч центра', unique=True)
    uz_title = models.CharField(max_length=50, verbose_name='Узбекская версия', unique=True, blank=True, null=True)
    photo = models.ImageField(blank=True, null=True, verbose_name='Картинка', upload_to=lc_upload_directory, validators=[validate_image_file_extension])
    description = models.TextField(verbose_name='Описание')
    link = models.CharField(max_length=255, blank=True, null=True, verbose_name='Ссылка', help_text='При добавлении в боте появится кнопка ссылка')
    slug = models.SlugField(unique=True, verbose_name='Поисковое поле')

    def __str__(self):
        return self.title

    class Meta:
        verbose_name = 'Уч центр'
        verbose_name_plural = 'Уч центры'
