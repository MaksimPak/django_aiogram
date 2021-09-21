# Generated by Django 3.2 on 2021-09-21 11:47

from django.db import migrations, models
import django.db.models.deletion
import forms.utils.uploaders


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('contacts', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='Form',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True, null=True, verbose_name='Дата создания')),
                ('updated_at', models.DateTimeField(auto_now=True, null=True, verbose_name='Дата обновления')),
                ('name', models.CharField(max_length=100, verbose_name='Название')),
                ('type', models.CharField(choices=[('private', 'Закрытый'), ('public', 'Открытый')], default='public', max_length=20, verbose_name='Тип')),
                ('mode', models.CharField(choices=[('quiz', 'Викторина'), ('questionnaire', 'Вопросник')], max_length=20, verbose_name='Режим работы')),
                ('unique_code', models.IntegerField(blank=True, null=True, verbose_name='Уникальный код')),
                ('link', models.CharField(blank=True, max_length=50, null=True, verbose_name='Линк')),
                ('start_message', models.TextField(verbose_name='Сообщение для отправки при старте')),
                ('end_message', models.JSONField(default=dict, help_text='Формат: Диапазон (ОТ-ДО). Пример 0-100', verbose_name='Сообщение для отправки при завершении')),
                ('is_active', models.BooleanField(default=False, verbose_name='Активна')),
                ('one_off', models.BooleanField(default=False, verbose_name='Одноразовая форма')),
                ('image', models.ImageField(blank=True, null=True, upload_to=forms.utils.uploaders.form_directory, verbose_name='Картинка')),
                ('access_level', models.IntegerField(choices=[(1, 'ТГ Профиль'), (2, 'Лид'), (3, 'Клиент')], default=3, verbose_name='Доступ')),
            ],
            options={
                'verbose_name': 'Форма',
                'verbose_name_plural': 'Формы',
            },
        ),
        migrations.CreateModel(
            name='FormQuestion',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True, null=True, verbose_name='Дата создания')),
                ('updated_at', models.DateTimeField(auto_now=True, null=True, verbose_name='Дата обновления')),
                ('multi_answer', models.BooleanField(default=False, verbose_name='Мульти-ответ')),
                ('text', models.CharField(max_length=100, verbose_name='Текст')),
                ('image', models.ImageField(blank=True, null=True, upload_to=forms.utils.uploaders.form_question_directory, verbose_name='Картинка')),
                ('position', models.IntegerField(verbose_name='Нумерация')),
                ('custom_answer', models.BooleanField(default=False, verbose_name='Кастомный ответ')),
                ('custom_answer_text', models.CharField(blank=True, max_length=100, null=True, verbose_name='Текст кастомного ответа')),
                ('accept_file', models.BooleanField(default=False, verbose_name='Принимать файл')),
                ('chat_id', models.CharField(blank=True, max_length=255, null=True)),
                ('one_row_btns', models.BooleanField(default=False, verbose_name='Однострочные ответы')),
                ('form', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='forms.form', verbose_name='Форма')),
            ],
            options={
                'verbose_name': 'Вопрос',
                'verbose_name_plural': 'Вопросы',
                'ordering': ('position', 'id'),
            },
        ),
        migrations.CreateModel(
            name='FormAnswer',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True, null=True, verbose_name='Дата создания')),
                ('updated_at', models.DateTimeField(auto_now=True, null=True, verbose_name='Дата обновления')),
                ('is_correct', models.BooleanField(default=False, verbose_name='Правильный ответ')),
                ('text', models.CharField(max_length=100, verbose_name='Текст ответа')),
                ('jump_to', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='jumps', to='forms.formquestion', verbose_name='Ведет к вопросу')),
                ('question', models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, related_name='answers', to='forms.formquestion', verbose_name='Вопрос')),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='ContactFormAnswers',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True, null=True, verbose_name='Дата создания')),
                ('updated_at', models.DateTimeField(auto_now=True, null=True, verbose_name='Дата обновления')),
                ('score', models.IntegerField(blank=True, null=True, verbose_name='Балл')),
                ('data', models.JSONField(blank=True, default=dict, null=True, verbose_name='Данные')),
                ('contact', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, to='contacts.contact', verbose_name='Студент')),
                ('form', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, to='forms.form', verbose_name='Форма')),
            ],
            options={
                'verbose_name': 'Ответ на форму',
                'verbose_name_plural': 'Ответы на форму',
                'unique_together': {('contact', 'form')},
            },
        ),
    ]
