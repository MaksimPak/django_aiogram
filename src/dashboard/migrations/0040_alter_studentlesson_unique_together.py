# Generated by Django 3.2 on 2021-06-02 16:22

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('dashboard', '0039_rename_date_received_studentlesson_date_sent'),
    ]

    operations = [
        migrations.AlterUniqueTogether(
            name='studentlesson',
            unique_together={('student', 'lesson')},
        ),
    ]