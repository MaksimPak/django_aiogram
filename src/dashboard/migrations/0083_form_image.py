# Generated by Django 3.2 on 2021-08-03 16:43

import dashboard.models
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('dashboard', '0082_auto_20210803_1140'),
    ]

    operations = [
        migrations.AddField(
            model_name='form',
            name='image',
            field=models.ImageField(blank=True, null=True, upload_to=dashboard.models.form_directory, verbose_name='Картинка'),
        ),
    ]