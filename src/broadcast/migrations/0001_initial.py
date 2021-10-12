# Generated by Django 3.2 on 2021-09-21 12:35

import broadcast.utils.uploaders
import django.core.validators
from django.db import migrations, models
import general.validators


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Promotion',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True, null=True, verbose_name='Дата создания')),
                ('updated_at', models.DateTimeField(auto_now=True, null=True, verbose_name='Дата обновления')),
                ('title', models.CharField(max_length=100, verbose_name='Название')),
                ('video', models.FileField(blank=True, help_text='Не больше 50 мб', null=True, upload_to=broadcast.utils.uploaders.message_media_directory, validators=[general.validators.validate_video_extension, general.validators.validate_file_size], verbose_name='Промо видео')),
                ('image', models.ImageField(help_text="\nThe thumbnail should be in JPEG format and less than 200 kB in size. \nA thumbnail's width and height should not exceed 320.\n", upload_to=broadcast.utils.uploaders.message_media_directory, validators=[django.core.validators.validate_image_file_extension], verbose_name='Картинка')),
                ('description', models.TextField(verbose_name='Описание')),
                ('counter', models.IntegerField(default=0, verbose_name='Подсчет просмотра')),
                ('link', models.CharField(blank=True, editable=False, max_length=255, null=True, verbose_name='Инвайт ссылка')),
                ('unique_code', models.CharField(blank=True, editable=False, max_length=255, null=True, unique=True, verbose_name='Инвайт код')),
                ('start_message', models.TextField(verbose_name='Сообщение после регистрации на курс')),
                ('display_link', models.BooleanField(default=False, verbose_name='Показать ссылку')),
            ],
            options={
                'verbose_name': 'Промо',
                'verbose_name_plural': 'Промо',
            },
        ),
    ]