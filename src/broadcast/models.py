from django.core.validators import validate_image_file_extension
from django.db import models

from broadcast.utils.uploaders import message_media_directory
from general.models import BaseModel
from general.validators import (
    validate_video_extension, validate_file_size,
    validate_dimensions, validate_thumbnail_size
)

THUMBNAIL_HELP_TEXT = """
The thumbnail should be in JPEG format and less than 200 kB in size. 
A thumbnail\'s width and height should not exceed 320.
"""


class MessageSent(BaseModel):
    text = models.TextField(verbose_name='Описание')
    video = models.FileField(verbose_name='Промо видео', null=True,
                             blank=True, upload_to=message_media_directory,
                             validators=[validate_video_extension, validate_file_size],
                             help_text='Не больше 50 мб')
    image = models.ImageField(verbose_name='Картинка', upload_to=message_media_directory,
                              validators=[validate_image_file_extension],
                              help_text=THUMBNAIL_HELP_TEXT)
    link = models.CharField(max_length=255, null=True, blank=True, verbose_name='Cсылка')

    def clean(self):
        if self.video and self.image:
            validate_dimensions(self.image)
            validate_thumbnail_size(self.image)

    def __str__(self):
        return self.title

    class Meta:
        verbose_name = 'Промо'
        verbose_name_plural = 'Промо'

#
# class SendingReport(BaseModel):
#     # message history model
#     class LanguageType(models.TextChoices):
#         all = 'all', 'Всем'
#         ru = '1', 'Russian'
#         uz = '2', 'Uzbek'
#
#     lang = models.CharField(max_length=20, choices=LanguageType.choices, verbose_name='Язык отправки')
#     promotion = models.ForeignKey(Promotion, on_delete=models.CASCADE, verbose_name='Промо')
#     sent = models.IntegerField(verbose_name='Кол-во получателей', default=0)
#     received = models.IntegerField(verbose_name='Итого отправлено', default=0)
#     failed = models.IntegerField(verbose_name='Не получило', default=0)
#     celery_id = models.CharField(verbose_name='Celery group uuid', max_length=36, editable=False)
#     status = models.CharField(verbose_name='Статус отправки', max_length=50, null=True, blank=True)
#
#     def __str__(self):
#         return f'Отправка №{self.id}'
#
#     class Meta:
#         verbose_name_plural = 'Отчеты'
#         verbose_name = 'Отчет'
