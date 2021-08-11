# Generated by Django 3.2 on 2021-08-09 18:10

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('dashboard', '0083_form_image'),
    ]

    operations = [
        migrations.AddField(
            model_name='formquestion',
            name='custom_answer_text',
            field=models.CharField(blank=True, max_length=50, null=True),
        ),
        migrations.AddField(
            model_name='promotion',
            name='display_link',
            field=models.BooleanField(default=False, verbose_name='Показать ссылку'),
        ),
    ]