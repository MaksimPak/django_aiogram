# Generated by Django 3.2 on 2021-07-13 16:25

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('dashboard', '0066_alter_sendingreport_status'),
    ]

    operations = [
        migrations.CreateModel(
            name='Form',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True, null=True, verbose_name='Дата создания')),
                ('updated_at', models.DateTimeField(auto_now=True, null=True, verbose_name='Дата обновления')),
                ('name', models.CharField(max_length=50, verbose_name='Название')),
                ('type', models.CharField(choices=[('private', 'Закрытый'), ('public', 'Открытый')], default='public', max_length=20, verbose_name='Тип')),
                ('mode', models.CharField(choices=[('quiz', 'Викторина'), ('questionnaire', 'Вопросник')], max_length=20, verbose_name='Режим работы')),
                ('unique_code', models.IntegerField(blank=True, null=True, verbose_name='Уникальный код')),
                ('link', models.CharField(blank=True, max_length=50, null=True, verbose_name='Линк')),
                ('start_message', models.CharField(blank=True, max_length=50, null=True, verbose_name='Сообщение для отправки при старте')),
                ('start_end', models.CharField(blank=True, max_length=50, null=True, verbose_name='Сообщение для отправки при завершении')),
                ('is_started', models.BooleanField(default=False, verbose_name='Форма начата')),
                ('is_finished', models.BooleanField(default=False, verbose_name='Форма закончена')),
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
                ('text', models.CharField(max_length=50, verbose_name='Текст')),
                ('form', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='dashboard.form', verbose_name='Форма')),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='FormAnswer',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True, null=True, verbose_name='Дата создания')),
                ('updated_at', models.DateTimeField(auto_now=True, null=True, verbose_name='Дата обновления')),
                ('is_correct', models.BooleanField(default=False, verbose_name='Правильный ответ')),
                ('text', models.CharField(max_length=50, verbose_name='Текст ответа')),
                ('ordering', models.IntegerField(verbose_name='Позиция')),
                ('jump_to', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='jumps', to='dashboard.formquestion', verbose_name='Ведет к вопросу')),
                ('question', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='questions', to='dashboard.formquestion', verbose_name='Вопрос')),
            ],
            options={
                'abstract': False,
            },
        ),
    ]
