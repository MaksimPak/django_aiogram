from django.core.exceptions import ValidationError
from django.db import models

from forms.utils.uploaders import form_directory, form_question_directory
from general.models import BaseModel, AccessType


class Form(BaseModel):
    class FormType(models.TextChoices):
        private = 'private', 'Закрытый'
        public = 'public', 'Открытый'

    class FormMode(models.TextChoices):
        quiz = 'quiz', 'Викторина'
        questionnaire = 'questionnaire', 'Вопросник'

    name = models.CharField(max_length=100, verbose_name='Название')
    type = models.CharField(max_length=20, verbose_name='Тип', default=FormType.public, choices=FormType.choices)
    mode = models.CharField(max_length=20, verbose_name='Режим работы', choices=FormMode.choices)
    unique_code = models.IntegerField(verbose_name='Уникальный код', null=True, blank=True)
    link = models.CharField(max_length=50, verbose_name='Линк', null=True, blank=True)
    start_message = models.TextField(verbose_name='Сообщение для отправки при старте')
    end_message = models.JSONField(verbose_name='Сообщение для отправки при завершении',
                                   default=dict, help_text='Формат: Диапазон (ОТ-ДО). Пример 0-100')
    is_active = models.BooleanField(verbose_name='Активна', default=False)
    one_off = models.BooleanField(verbose_name='Одноразовая форма', default=False)
    image = models.ImageField(verbose_name='Картинка', blank=True, null=True, upload_to=form_directory)
    access_level = models.IntegerField(verbose_name='Доступ', default=AccessType.client, choices=AccessType.choices)

    def __str__(self):
        return f'Форма: [{self.name}]'

    class Meta:
        verbose_name = 'Форма'
        verbose_name_plural = 'Формы'


class FormQuestion(BaseModel):
    form = models.ForeignKey(Form, on_delete=models.CASCADE, verbose_name='Форма')
    multi_answer = models.BooleanField(verbose_name='Мульти-ответ', default=False)
    text = models.TextField(verbose_name='Текст')
    image = models.ImageField(verbose_name='Картинка', blank=True,
                              null=True, upload_to=form_question_directory)
    position = models.IntegerField(verbose_name='Нумерация')
    custom_answer = models.BooleanField(verbose_name='Кастомный ответ', default=False)
    custom_answer_text = models.CharField(verbose_name='Текст кастомного ответа',
                                          max_length=100, null=True, blank=True)
    accept_file = models.BooleanField(verbose_name='Принимать файл', default=False)
    chat_id = models.CharField(max_length=255, blank=True, null=True)
    one_row_btns = models.BooleanField(verbose_name='Однострочные ответы', default=False)

    def __str__(self):
        return f'[{self.form.name}]Вопрос: {self.text}'

    def clean(self):
        if self.custom_answer and self.form.mode == Form.FormMode.quiz:
            raise ValidationError('Нельзя добавить кастомный ответ к викторине')

    class Meta:
        verbose_name = 'Вопрос'
        verbose_name_plural = 'Вопросы'
        ordering = ('position', 'id')


class FormAnswer(BaseModel):
    question = models.ForeignKey(FormQuestion, on_delete=models.CASCADE,
                                 verbose_name='Вопрос', related_name='answers', null=True)
    is_correct = models.BooleanField(verbose_name='Правильный ответ', default=False)
    text = models.CharField(max_length=100, verbose_name='Текст ответа')
    jump_to = models.ForeignKey(FormQuestion, on_delete=models.CASCADE,
                                verbose_name='Ведет к вопросу', null=True, blank=True, related_name='jumps')

    def clean(self):
        if self.is_correct and self.question.form.mode == Form.FormMode.questionnaire:
            raise ValidationError('У опросника нет правильного ответа')


class ContactFormAnswers(BaseModel):
    contact = models.ForeignKey('contacts.Contact', on_delete=models.SET_NULL, null=True, verbose_name='Студент')
    form = models.ForeignKey(Form, on_delete=models.SET_NULL, null=True, verbose_name='Форма')
    score = models.IntegerField(verbose_name='Балл', null=True, blank=True)
    data = models.JSONField(verbose_name='Данные', null=True, blank=True, default=dict)

    class Meta:
        verbose_name = 'Ответ на форму'
        verbose_name_plural = 'Ответы на форму'
        unique_together = [['contact', 'form']]
