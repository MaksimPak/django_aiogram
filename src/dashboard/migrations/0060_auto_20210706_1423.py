# Generated by Django 3.2 on 2021-07-06 14:23

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('dashboard', '0059_auto_20210706_1311'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='sendingreport',
            options={'verbose_name': 'Отчет', 'verbose_name_plural': 'Отчеты'},
        ),
        migrations.AddField(
            model_name='sendingreport',
            name='failed',
            field=models.IntegerField(default=0, verbose_name='Не получило'),
        ),
    ]
