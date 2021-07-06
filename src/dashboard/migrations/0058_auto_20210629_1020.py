# Generated by Django 3.2 on 2021-06-29 10:20

import dashboard.models
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('dashboard', '0057_alter_quizanswer_options'),
    ]

    operations = [
        migrations.AddField(
            model_name='lessonurl',
            name='hits',
            field=models.IntegerField(default=0, verbose_name='Количество возможных переховод по ссылке'),
        ),
        migrations.AlterField(
            model_name='lessonurl',
            name='hash',
            field=models.CharField(default=dashboard.models.generate_uuid, max_length=36, unique=True),
        ),
    ]