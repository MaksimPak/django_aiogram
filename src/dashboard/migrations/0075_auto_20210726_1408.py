# Generated by Django 3.2 on 2021-07-26 14:08

from django.db import migrations


def delete_all(apps, schema_editor):
    # We can't import the Person model directly as it may be a newer
    # version than this migration expects. We use the historical version.
    StudentForm = apps.get_model('dashboard', 'StudentForm')
    StudentForm.objects.all().delete()


class Migration(migrations.Migration):

    dependencies = [
        ('dashboard', '0074_auto_20210722_1704'),
    ]

    operations = [
        migrations.RunPython(delete_all),
    ]
