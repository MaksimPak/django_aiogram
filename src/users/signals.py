import os

from django.db.models.signals import post_save
from django.dispatch import receiver

from general.utils.helpers import random_int
from users.models import Lead


@receiver(post_save, sender=Lead)
def lead_invite_data(sender, instance, created, **kwargs):
    """
    Create a unique code and invite link for registration for lead upon saving.
    """
    if created:
        unique_code = str(instance.id) + random_int()
        invite_link = f'https://t.me/{os.getenv("BOT_NAME")}?start={unique_code}'
        instance.unique_code = unique_code
        instance.invite_link = invite_link
        instance.save()


