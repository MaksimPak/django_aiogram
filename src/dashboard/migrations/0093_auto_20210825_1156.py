# Generated by Django 3.2 on 2021-08-25 11:56

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('dashboard', '0092_auto_20210825_1156'),
    ]

    operations = [
        migrations.AlterField(
            model_name='form',
            name='end_message',
            field=models.JSONField(default=dict, verbose_name='Сообщение для отправки при завершении'),
        ),
        migrations.AlterField(
            model_name='formanswer',
            name='question',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, related_name='answers', to='dashboard.formquestion', verbose_name='Вопрос'),
        ),
    ]