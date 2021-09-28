import os

from django.db.models.signals import post_save
from django.dispatch import receiver

from forms.models import Form
from general.utils.helpers import random_int


@receiver(post_save, sender=Form)
def form_modify_data(sender, instance, created, **kwargs):
    """
    Create a unique code and invite link for registration for promotion upon saving.
    """
    if created:
        unique_code = str(instance.id) + random_int()
        link = f'https://t.me/{os.getenv("BOT_NAME")}?start=quiz{unique_code}'
        instance.unique_code = unique_code
        instance.link = link

        Form.objects.filter(pk=instance.id).update(unique_code=unique_code, link=link)
