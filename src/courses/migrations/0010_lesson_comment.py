# Generated by Django 3.2 on 2021-12-21 12:40

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('courses', '0009_auto_20211220_1341'),
    ]

    operations = [
        migrations.AddField(
            model_name='lesson',
            name='comment',
            field=models.TextField(blank=True, null=True, verbose_name='Сообщение по завершению'),
        ),
    ]
