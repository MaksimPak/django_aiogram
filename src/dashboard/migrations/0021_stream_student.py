# Generated by Django 3.2 on 2021-05-12 10:23

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('dashboard', '0020_alter_lesson_homework_desc'),
    ]

    operations = [
        migrations.AddField(
            model_name='stream',
            name='student',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='dashboard.client'),
        ),
    ]
