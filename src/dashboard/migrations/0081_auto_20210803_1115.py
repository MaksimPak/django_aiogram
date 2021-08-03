# Generated by Django 3.2 on 2021-08-03 11:15

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('dashboard', '0080_auto_20210730_0902'),
    ]

    operations = [
        migrations.AddField(
            model_name='form',
            name='one_row_btns',
            field=models.BooleanField(default=False, verbose_name='Однострочные ответы'),
        ),
        migrations.AlterField(
            model_name='contactformanswers',
            name='contact',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, to='dashboard.contact', verbose_name='Студент'),
        ),
        migrations.AlterField(
            model_name='contactformanswers',
            name='form',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, to='dashboard.form', verbose_name='Форма'),
        ),
    ]
