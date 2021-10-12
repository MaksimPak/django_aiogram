# Generated by Django 3.2 on 2021-10-11 11:34

from django.db import migrations
from django.db.migrations import RunPython


def lang_transfer(apps, schema_editor):
    Student = apps.get_model('users', 'Student')

    for student in Student.objects.all():
        student.contact.data['lang'] = student.language_type
        student.contact.save()


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0004_auto_20210928_1052'),
    ]

    operations = [
        migrations.RunPython(lang_transfer, RunPython.noop),
    ]
