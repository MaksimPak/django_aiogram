# Generated by Django 3.2 on 2021-05-06 09:11

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('dashboard', '0009_auto_20210505_1945'),
    ]

    operations = [
        migrations.AddField(
            model_name='student',
            name='checkout_date',
            field=models.DateTimeField(blank=True, null=True, verbose_name='Дата чекаута'),
        ),
        migrations.AlterField(
            model_name='course',
            name='add_message',
            field=models.TextField(blank=True, null=True, verbose_name='Сообщение для отправки студенту после добавления'),
        ),
        migrations.AlterField(
            model_name='student',
            name='application_type',
            field=models.CharField(choices=[('1', 'Admin'), ('2', 'Telegram'), ('3', 'Web')], default='1', max_length=20, verbose_name='Как заполнил форму'),
        ),
    ]