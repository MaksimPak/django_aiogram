# Generated by Django 3.2 on 2021-11-09 13:39

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('broadcast', '0005_auto_20211029_1759'),
    ]

    operations = [
        migrations.AddField(
            model_name='message',
            name='notes',
            field=models.TextField(blank=True, null=True, verbose_name='Заметки к сообщению'),
        ),
    ]