# Generated by Django 3.2 on 2021-07-16 11:24

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('dashboard', '0066_alter_sendingreport_status'),
    ]

    operations = [
        migrations.CreateModel(
            name='Contact',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True, null=True, verbose_name='Дата создания')),
                ('updated_at', models.DateTimeField(auto_now=True, null=True, verbose_name='Дата обновления')),
                ('first_name', models.CharField(max_length=255, verbose_name='ТГ Имя')),
                ('last_name', models.CharField(blank=True, max_length=255, null=True, verbose_name='ТГ Фамилия')),
                ('tg_id', models.BigIntegerField(blank=True, null=True, unique=True, verbose_name='Telegram ID')),
                ('data', models.JSONField(blank=True, default=dict, null=True)),
            ],
            options={
                'verbose_name': 'Пре Лид',
                'verbose_name_plural': 'Пре Лиды',
            },
        ),
    ]