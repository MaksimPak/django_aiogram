# Generated by Django 3.2 on 2021-11-01 15:10

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('courses', '0004_auto_20211101_1505'),
        ('users', '0007_rename_learning_centre_student_company'),
        ('companies', '0001_initial'),
    ]

    operations = [
        migrations.RenameModel(
            old_name='LearningCentre',
            new_name='Company',
        ),
    ]