import os

from django.core.exceptions import ValidationError


def validate_video_extension(value):
    ext = os.path.splitext(value.name)[1]  # [0] returns path+filename
    valid_extensions = ['.webm', '.mpg', '.mp2', '.mpeg', '.mpe', '.mpv', '.mp4',
                        '.m4p', '.m4v', '.avi', '.wmv', '.mov', '.qt', '.flv', '.swf', '.avchd']
    if not ext.lower() in valid_extensions:
        raise ValidationError('Не поддерживаемый формат')


def validate_photo_extension(value):
    ext = os.path.splitext(value.name)[1]  # [0] returns path+filename
    valid_extensions = ['.jpg', '.png', '.bmp', '.svg', '.svgz', '.jpeg', '.jpe']
    if not ext.lower() in valid_extensions:
        raise ValidationError('Не поддерживаемый формат')


def validate_hashtag(value):
    if not value.startswith('#'):
        raise ValidationError('Хештег должен начинаться с #')


def validate_file_size(value):
    filesize = value.size

    if filesize > 52428800:
        raise ValidationError("Максимальный размер не больше 50 мб")
    else:
        return value


def validate_dimensions(value):
    if value.width > 320 or value.height > 320:
        raise ValidationError({value.field.name: "Максимальная (ширина)х(высота): 320x320"})


def validate_thumbnail_size(value):
    if value.size > 327680:
        raise ValidationError({value.field.name: "Максимальный размер картинки: 320kB"})
