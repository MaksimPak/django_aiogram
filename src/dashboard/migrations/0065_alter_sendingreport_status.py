# Generated by Django 3.2 on 2021-07-09 17:26

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('dashboard', '0064_auto_20210709_1613'),
    ]

    operations = [
        migrations.AlterField(
            model_name='sendingreport',
            name='status',
            field=models.CharField(blank=True, choices=[('PENDING', 'Отправляется'), ('DONE', 'Отправлено')], max_length=50, null=True, verbose_name='Статус отправки'),
        ),
    ]
