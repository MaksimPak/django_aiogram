# Generated by Django 3.2 on 2021-09-08 10:16

import dashboard.models
import django.core.validators
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('dashboard', '0098_auto_20210907_1557'),
    ]

    operations = [
        migrations.AddField(
            model_name='learningcentre',
            name='description',
            field=models.TextField(default='ENTER DESCRIPTION', verbose_name='Описание'),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='learningcentre',
            name='link',
            field=models.CharField(blank=True, max_length=255, null=True, verbose_name='Ссылка'),
        ),
        migrations.AddField(
            model_name='learningcentre',
            name='photo',
            field=models.ImageField(blank=True, null=True, upload_to=dashboard.models.lc_upload_directory, validators=[django.core.validators.validate_image_file_extension], verbose_name='Картинка'),
        ),
        migrations.AlterField(
            model_name='course',
            name='learning_centre',
            field=models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to='dashboard.learningcentre', verbose_name='Уч центр'),
        ),
        migrations.AlterField(
            model_name='learningcentre',
            name='title',
            field=models.CharField(max_length=100, unique=True, verbose_name='Название категории'),
        ),
        migrations.AlterField(
            model_name='student',
            name='learning_centre',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, to='dashboard.learningcentre', verbose_name='Учебный центр'),
        ),
    ]