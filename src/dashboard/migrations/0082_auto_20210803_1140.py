# Generated by Django 3.2 on 2021-08-03 11:40

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('dashboard', '0081_auto_20210803_1115'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='form',
            name='one_row_btns',
        ),
        migrations.AddField(
            model_name='formquestion',
            name='one_row_btns',
            field=models.BooleanField(default=False, verbose_name='Однострочные ответы'),
        ),
    ]
