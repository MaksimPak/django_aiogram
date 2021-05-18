# Generated by Django 3.2 on 2021-05-18 11:34

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('dashboard', '0027_auto_20210514_0958'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='student',
            options={'verbose_name': 'Студент', 'verbose_name_plural': 'Студенты'},
        ),
        migrations.AddField(
            model_name='course',
            name='date_finished',
            field=models.DateTimeField(blank=True, null=True, verbose_name='Дата окончания курса'),
        ),
        migrations.AddField(
            model_name='course',
            name='date_started',
            field=models.DateTimeField(blank=True, null=True, verbose_name='Дата начала курса'),
        ),
    ]
