# Generated by Django 3.2 on 2021-12-13 16:07

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('forms', '0002_alter_formquestion_text'),
    ]

    operations = [
        migrations.AlterField(
            model_name='formquestion',
            name='text',
            field=models.TextField(verbose_name='Текст'),
        ),
    ]