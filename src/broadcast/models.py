from django.core.validators import validate_image_file_extension
from django.db import models

from broadcast.utils.uploaders import promo_upload_directory
from general.models import BaseModel
from general.validators import (
    validate_video_extension, validate_file_size,
    validate_dimensions, validate_thumbnail_size
)

THUMBNAIL_HELP_TEXT = """
The thumbnail should be in JPEG format and less than 200 kB in size. 
A thumbnail\'s width and height should not exceed 320.
"""


class Promotion(BaseModel):
    title = models.CharField(max_length=100, verbose_name='Название')
    video = models.FileField(verbose_name='Промо видео', null=True, blank=True, upload_to=promo_upload_directory, validators=[validate_video_extension, validate_file_size], help_text='Не больше 50 мб')
    image = models.ImageField(verbose_name='Картинка', upload_to=promo_upload_directory, validators=[validate_image_file_extension], help_text=THUMBNAIL_HELP_TEXT)
    description = models.TextField(verbose_name='Описание')
    course = models.ForeignKey('courses.Course', on_delete=models.SET_NULL, verbose_name='Курс', null=True, blank=True)
    counter = models.IntegerField('Подсчет просмотра', default=0)
    link = models.CharField(max_length=255, editable=False, null=True, blank=True, verbose_name='Инвайт ссылка')
    unique_code = models.CharField(max_length=255, verbose_name='Инвайт код', unique=True, null=True, blank=True, editable=False)
    start_message = models.TextField(verbose_name='Сообщение после регистрации на курс')
    display_link = models.BooleanField(verbose_name='Показать ссылку', default=False)

    def clean(self):
        if self.video and self.image:
            validate_dimensions(self.image)
            validate_thumbnail_size(self.image)

    def __str__(self):
        return self.title

    class Meta:
        verbose_name = 'Промо'
        verbose_name_plural = 'Промо'
