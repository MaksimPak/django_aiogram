# Generated by Django 3.2 on 2021-09-08 11:02

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('dashboard', '0101_auto_20210908_1059'),
    ]

    operations = [
        migrations.AlterField(
            model_name='learningcentre',
            name='slug',
            field=models.SlugField(unique=True, verbose_name='Поисковое поле'),
        ),
    ]
