import datetime
from io import BytesIO

from PIL import Image
from PIL import ImageDraw
from PIL import ImageFont
from django.core.files.uploadedfile import InMemoryUploadedFile


def generate_cert(instance):
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
