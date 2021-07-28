# Generated by Django 3.2 on 2021-05-01 11:57

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('dashboard', '0002_client_lead'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='client',
            options={'verbose_name': 'Клиент', 'verbose_name_plural': 'Клиенты'},
        ),
        migrations.AlterModelOptions(
            name='course',
            options={'verbose_name': 'Курс', 'verbose_name_plural': 'Курсы'},
        ),
        migrations.AlterModelOptions(
            name='lead',
            options={'verbose_name': 'Лид', 'verbose_name_plural': 'Лиды'},
        ),
        migrations.AlterModelOptions(
            name='lesson',
            options={'verbose_name': 'Урок', 'verbose_name_plural': 'Уроки'},
        ),
        migrations.AlterField(
            model_name='course',
            name='category',
            field=models.CharField(choices=[('1', 'Game Development'), ('2', 'Web Development')], max_length=20, verbose_name='Категория'),
        ),
        migrations.AlterField(
            model_name='course',
            name='difficulty',
            field=models.CharField(choices=[('1', 'Beginner'), ('2', 'Intermediate'), ('3', 'Advanced')], max_length=20, verbose_name='Сложность'),
        ),
        migrations.AlterField(
            model_name='course',
            name='info',
            field=models.TextField(blank=True, null=True, verbose_name='Описание'),
        ),
        migrations.AlterField(
            model_name='course',
            name='name',
            field=models.CharField(max_length=50, verbose_name='Название курса'),
        ),
        migrations.AlterField(
            model_name='course',
            name='price',
            field=models.BigIntegerField(verbose_name='Цена'),
        ),
        migrations.AlterField(
            model_name='lesson',
            name='info',
            field=models.TextField(blank=True, null=True, verbose_name='Описание'),
        ),
        migrations.AlterField(
            model_name='student',
            name='application_type',
            field=models.CharField(choices=[('1', 'Web'), ('2', 'Telegram')], default='1', max_length=20, verbose_name='Как заполнил форму'),
        ),
        migrations.AlterField(
            model_name='student',
            name='is_client',
            field=models.BooleanField(default=False, verbose_name='Клиент'),
        ),
        migrations.AlterField(
            model_name='student',
            name='phone',
            field=models.CharField(max_length=20, verbose_name='Контактный телефон'),
        ),
        migrations.AlterField(
            model_name='studentcourse',
            name='stream',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, to='dashboard.stream'),
        ),
    ]
