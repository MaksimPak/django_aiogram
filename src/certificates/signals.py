import sys

from django.core.files.uploadedfile import InMemoryUploadedFile
from django.db.models.signals import post_save
import datetime
from django.dispatch import receiver
from PIL import Image
from PIL import ImageFont
from PIL import ImageDraw
from certificates.models import Certificate
from io import BytesIO
from django.core.files.uploadedfile import InMemoryUploadedFile


@receiver(post_save, sender=Certificate)
def cert_modify_data(sender, instance, created, **kwargs):
    """
    Create a unique code and invite link for registration for promotion upon saving.
    """
    if created:
        font = ImageFont.truetype("certificates/resources/FreeMono.ttf", 50)
        img = Image.open(instance.template.template)
        draw = ImageDraw.Draw(img)
        date = datetime.datetime.today().strftime('%d/%m/%Y')
        name = instance.student.student.full_name if hasattr(instance.student, 'student') else instance.student.__str__()
        draw.text(instance.template.date_coord,
                  date, font=font, fill=(0, 0, 0))  # Write current date
        draw.text(instance.template.name_coord, name,
                  font=font, fill=(0, 0, 0))  # Write name
        buffer = BytesIO()
        img.save(fp=buffer, format=img.format)  # Save to buffer

        instance.generated_cert.save(f'{instance.id}.png', InMemoryUploadedFile(
             buffer,
             None, '',
             'image/png',
             img.size,
             None)
        )

