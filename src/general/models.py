from django.db import models


class BaseModel(models.Model):
    created_at = models.DateTimeField('Дата создания', auto_now_add=True, null=True, blank=True)
    updated_at = models.DateTimeField('Дата обновления', auto_now=True, null=True, blank=True)

    class Meta:
        abstract = True


class AccessType(models.IntegerChoices):
    contact = 1, 'ТГ Профиль'
    lead = 2, 'Лид'
    client = 3, 'Клиент'
