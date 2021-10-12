from django.db import models

from general.models import BaseModel


class Contact(BaseModel):
    first_name = models.CharField(verbose_name='ТГ Имя', max_length=255)
    last_name = models.CharField(verbose_name='ТГ Фамилия', max_length=255, null=True, blank=True)
    tg_id = models.BigIntegerField(verbose_name='Telegram ID', blank=True, null=True, unique=True)
    is_registered = models.BooleanField(default=False, verbose_name='Зареган')
    blocked_bot = models.BooleanField(default=False, editable=False, verbose_name='Блокнул бота')
    data = models.JSONField(null=True, blank=True, default=dict)

    def __str__(self):
        return f'TG[{self.first_name}]'

    class Meta:
        verbose_name = 'ТГ Профиль'
        verbose_name_plural = 'ТГ Профили'
