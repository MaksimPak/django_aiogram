import os

from django.core.exceptions import ValidationError


def validate_x_y(value):
    if len(value) < 2:
        raise ValidationError('Введите два значения через запятую')
