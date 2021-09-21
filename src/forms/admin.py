from functools import partial

from django.contrib import admin, messages

# Register your models here.
from django.db.models.expressions import RawSQL
from django.http import HttpResponseRedirect
from django.template.loader import render_to_string
from django.urls import reverse
from django.utils.safestring import mark_safe

from forms import models
from forms import web_forms


class FormAnswerList(admin.StackedInline):
    model = models.FormAnswer
    fk_name = 'question'

    def formfield_for_foreignkey(self, db_field, request=None, **kwargs):
        field = super(FormAnswerList, self).formfield_for_foreignkey(db_field, request, **kwargs)

        if db_field.name == 'jump_to':
            if request._obj_ is not None:
                field.queryset = field.queryset.filter(
                    form=request._obj_.form).exclude(id=request._obj_.id)
            else:
                field.queryset = field.queryset.none()

        return field


class FormQuestionList(admin.StackedInline):
    model = models.FormQuestion
    fields = ('text', 'multi_answer', 'image', 'custom_answer', 'custom_answer_text',
              'position', 'chat_id', 'accept_file','one_row_btns', 'changeform_link')
    readonly_fields = ('changeform_link', )

    @admin.display(description='Дополнительно')
    def changeform_link(self, object):
        if object.id:
            changeform_url = reverse(
                'admin:dashboard_formquestion_change', args=(object.id,)
            )
            return mark_safe(f'<a href="{changeform_url}" target="_blank">Создать Ответы</a>')
        else:
            return 'Сначала создайте вопрос'

    class Media:
        js = (
            'dashboard/js/form_admin.js',
        )
        css = {
            'all': ('dashboard/css/form_admin.css',)
        }


@admin.register(models.FormQuestion)
class FormQuestionAdmin(admin.ModelAdmin):
    inlines = (FormAnswerList,)

    def get_form(self, request, obj=None, **kwargs):
        # just save obj reference for future processing in Inline
        request._obj_ = obj
        return super(FormQuestionAdmin, self).get_form(request, obj, **kwargs)


@admin.register(models.Form)
class FormAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'type', 'mode', 'statistics', 'created_at')
    list_display_links = ('name',)
    list_per_page = 20
    inlines = (FormQuestionList,)
    readonly_fields = ('bot_command', 'link',)
    exclude = ('unique_code',)
    actions = ('duplicate',)
    form = web_forms.Form
    change_form_template = 'admin/dashboard/form/change_form.html'

    def get_form(self, request, obj=None, change=False, **kwargs):
        form = super(FormAdmin, self).get_form(request, obj=None, change=False, **kwargs)
        form.req = request
        return form

    @admin.display(description='Бот команда')
    def bot_command(self, form):
        return f'/quiz{form.unique_code}' if form.unique_code else '-'

    @admin.display(description='Человек ответило')
    def statistics(self, form):
        return form.contactformanswers_set.count()

    @admin.display(description='Дублировать (Максимум 3)')
    def duplicate(self, request, forms):
        if len(forms) > 3:
            self.message_user(request, 'Нельзя дублировать больше 3 форм', messages.ERROR)
            return

        for form in forms:
            questions = list(form.formquestion_set.all())
            form.pk = None

            form.save()

            for question in questions:
                answers = list(question.answers.all())
                question.id = None
                question.form = form
                question.save()

                for answer in answers:
                    answer.id = None
                    answer.question = question
                    answer.save()

        self.message_user(request, '{0} форм(а) были успешно дублированны'.format(forms.count()), messages.SUCCESS)


@admin.register(models.ContactFormAnswers)
class ContactFormAnswersAdmin(admin.ModelAdmin):
    list_display = ('id', 'contact', 'date_passed', 'is_registered', 'points')
    list_display_links = ('contact',)
    list_per_page = 20
    readonly_fields = ('contact', 'form', 'score',)
    form = web_forms.ContactFormAnswers
    actions = ('send_message',)
    list_filter = ('form', 'score',)
    change_form_template = 'admin/dashboard/contactformanswers/change_form.html'
    change_list_template = 'admin/dashboard/contactformanswers/change_list.html'

    def has_add_permission(self, request, obj=None):
        return False

    @admin.display(description='Зареган', boolean=True, ordering='contact__is_registered')
    def is_registered(self, answer):
        if answer.contact:
            return answer.contact.is_registered
        return False

    @admin.display(description='Дата прохождения')
    def date_passed(self, answer):
        return answer.updated_at if answer.updated_at else answer.created_at

    @admin.display(description='Массовая рассылка')
    def send_message(self, request, answers):
        s = [x.contact.id for x in answers]
        params = f'?_selected_action={"&_selected_action=".join(str(x)  for x in s)}'
        return HttpResponseRedirect(reverse(
                'dashboard:message_contacts') + f'{params}')

    @admin.display(description='Балл')
    def points(self, instance):
        question_count = instance.form.formquestion_set.all().count()
        return f'{instance.score}/{question_count}' if instance.score else None

    def get_list_display(self, request):
        list_display = super(ContactFormAnswersAdmin, self).get_list_display(request)
        form = models.Form.objects.get(pk=request.GET['form__id__exact'])
        questions = form.formquestion_set.all()
        for question in questions:
            attr_name = f'question_{question.id}'
            list_display += (attr_name,)
            func = partial(self._get_answer, field=attr_name)
            func.short_description = question.text
            func.admin_order_field = RawSQL("data->>'%s'", (question.id,))
            setattr(self, attr_name, func)
        return list_display

    @staticmethod
    def _get_answer(instance, field=''):
        key = field.split('_')[-1]

        return render_to_string(
            'dashboard/display_answers.html',
            {
                'answers': instance.data.get(key)
            }
        )

    def get_model_perms(self, request):
        """
        Return empty perms dict thus hiding the model from admin index.
        """
        return {}

    class Media:
        js = (
            'dashboard/js/contactformanswers_admin.js',
        )





