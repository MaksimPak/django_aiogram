# Generated by Django 3.2 on 2021-05-18 13:34

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('dashboard', '0028_auto_20210518_1134'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='student',
            name='stream',
        ),
        migrations.RemoveField(
            model_name='studentcourse',
            name='stream',
        ),
        migrations.DeleteModel(
            name='Stream',
        ),
    ]
