# Generated by Django 3.2 on 2021-05-07 20:28

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('dashboard', '0015_course_is_free'),
    ]

    operations = [
        migrations.AddField(
            model_name='student',
            name='invite_link',
            field=models.CharField(blank=True, editable=False, max_length=255, null=True),
        ),
    ]
