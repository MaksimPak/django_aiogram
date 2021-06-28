# Generated by Django 3.2 on 2021-06-23 17:11

import dashboard.models
import dashboard.validators
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('dashboard', '0051_auto_20210623_1513'),
    ]

    operations = [
        migrations.AlterField(
            model_name='promotion',
            name='thumbnail',
            field=models.ImageField(blank=True, null=True, upload_to=dashboard.models.lesson_upload_directory, validators=[dashboard.validators.validate_photo_extension], verbose_name='Промо превью'),
        ),
    ]