# Generated by Django 3.2 on 2021-12-24 12:02

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('courses', '0014_course_access_level'),
    ]

    operations = [
        migrations.AddField(
            model_name='studentcourse',
            name='has_finished',
            field=models.BooleanField(default=False, verbose_name='Завершил курс'),
        ),
    ]