# Generated by Django 3.2 on 2021-08-19 10:22
from contextlib import suppress

from django.db import migrations
from django.db.migrations import RunPython


def match_students(apps, schema_editor):
    # We can't import the Person model directly as it may be a newer
    # version than this migration expects. We use the historical version.
    Student = apps.get_model('dashboard', 'Student')
    Contact = apps.get_model('dashboard', 'Contact')

    for contact in Contact.objects.all():
        with suppress(Student.DoesNotExist):
            student = Student.objects.get(tg_id__exact=contact.tg_id)
            if student:
                contact.student = student
                contact.is_registered = True
                contact.save()


class Migration(migrations.Migration):

    dependencies = [
        ('dashboard', '0089_auto_20210816_1718'),
    ]

    operations = [
        migrations.RunPython(match_students, RunPython.noop),
    ]
