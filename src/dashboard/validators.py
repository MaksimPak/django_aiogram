import os
from django.core.exceptions import ValidationError


def validate_video_extension(value):
    ext = os.path.splitext(value.name)[1]  # [0] returns path+filename
    valid_extensions = ['.webm', '.mpg', '.mp2', '.mpeg', '.mpe', '.mpv', '.ogg', '.mp4',
                        '.m4p', '.m4v', '.avi', '.wmv', '.mov', '.qt', '.flv', '.swf', '.avchd']
    if not ext.lower() in valid_extensions:
        raise ValidationError('Не поддерживаемый формат')


def validate_photo_extension(value):
    ext = os.path.splitext(value.name)[1]  # [0] returns path+filename
    valid_extensions = ['.jpg', '.png', '.bmp', '.svg', '.svgz', '.jpeg', '.jpe']
    if not ext.lower() in valid_extensions:
        raise ValidationError('Не поддерживаемый формат')
