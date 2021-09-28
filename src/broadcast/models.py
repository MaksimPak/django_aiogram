from django.core.validators import validate_image_file_extension
from django.db import models

from broadcast.utils.uploaders import message_media_directory
from general.models import BaseModel
from general.validators import (
    validate_video_extension, validate_file_size,
    validate_dimensions, validate_thumbnail_size
)
from django.utils import timezone

THUMBNAIL_HELP_TEXT = """
The thumbnail should be in JPEG format and less than 200 kB in size. 
A thumbnail\'s width and height should not exceed 320.
"""


class Message(BaseModel):
    text = models.TextField(verbose_name='Текст')
    video = models.FileField(verbose_name='Видео', null=True,
                             blank=True, upload_to=message_media_directory,
                             validators=[validate_video_extension, validate_file_size],
                             help_text='Не больше 50 мб')
    image = models.ImageField(verbose_name='Картинка', upload_to=message_media_directory,
                              null=True, blank=True,
                              validators=[validate_image_file_extension],
                              help_text=THUMBNAIL_HELP_TEXT)
    link = models.CharField(max_length=255, null=True, blank=True, verbose_name='Cсылка')

    delivery_start_time = models.DateTimeField('Начало отправки', default=timezone.now)
    delivery_end_time = models.DateTimeField('Окончание отправки', null=True, blank=True)

    def __str__(self):
        return f'MessageId{self.id}'

    class Meta:
        verbose_name = 'Сообщение'
        verbose_name_plural = 'Сообщения'


class MessageHistory(BaseModel):
    message = models.ForeignKey(Message, verbose_name='Сообщение', on_delete=models.CASCADE)
    contact = models.ForeignKey('contacts.Contact', verbose_name='Получатель', on_delete=models.CASCADE)
    delivered = models.BooleanField(verbose_name='Отправлено')

    def __str__(self):
        return f'Отправка №{self.id}'

    class Meta:
        verbose_name_plural = 'Отправленное сообщение'
        verbose_name = 'Отправленные сообщения'
