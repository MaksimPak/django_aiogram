from django.db.models.signals import post_save
from django.dispatch import receiver

from certificates.models import Certificate
from certificates.utils.helpers import generate_cert


@receiver(post_save, sender=Certificate)
def cert_modify_data(sender, instance, created, **kwargs):
    """
    Create a unique code and invite link for registration for promotion upon saving.
    """
    if created:
        generate_cert(instance)

