from django.db import models

from assets.utils.uploaders import asset_directory
from general.models import BaseModel, AccessType


class Asset(BaseModel):
    title = models.CharField(max_length=50, verbose_name='Название')
    file = models.FileField(verbose_name='Файл', upload_to=asset_directory)
    desc = models.TextField(verbose_name='Описание', blank=True, null=True)
    access_level = models.IntegerField(verbose_name='Доступ', default=AccessType.client, choices=AccessType.choices)

    def __str__(self):
        return self.title

    class Meta:
        verbose_name = 'Ассет'
        verbose_name_plural = 'Ассеты'


class ContactAsset(BaseModel):
    contact = models.ForeignKey('contacts.Contact', on_delete=models.CASCADE, null=True, verbose_name='Студент')
    asset = models.ForeignKey(Asset, on_delete=models.CASCADE, null=True, verbose_name='Ассет')

    class Meta:
        verbose_name = 'Ассет студента'
        verbose_name_plural = 'Ассеты студента'
        unique_together = [['contact', 'asset']]
