# Generated by Django 3.2 on 2021-05-27 14:05

import dashboard.validators
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('dashboard', '0036_course_hashtag'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='course',
            name='add_message',
        ),
        migrations.AddField(
            model_name='course',
            name='end_message',
            field=models.TextField(blank=True, null=True, verbose_name='Сообщение для отправки студентам после завершения курса'),
        ),
        migrations.AddField(
            model_name='course',
            name='start_message',
            field=models.TextField(blank=True, null=True, verbose_name='Сообщение для отправки студентам после начала курса'),
        ),
        migrations.AlterField(
            model_name='course',
            name='hashtag',
            field=models.CharField(blank=True, max_length=20, null=True, validators=[dashboard.validators.validate_hashtag], verbose_name='Хештег'),
        ),
    ]
