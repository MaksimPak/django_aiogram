# Generated by Django 3.2 on 2021-08-13 10:29

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('dashboard', '0085_auto_20210811_1416'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='promotion',
            name='video_file_id',
        ),
    ]
