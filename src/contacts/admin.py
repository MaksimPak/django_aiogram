import json

from django.contrib import admin

# Register your models here.
from django.http import HttpResponseRedirect
from django.shortcuts import render
from django.urls import reverse
from django.utils.safestring import mark_safe

from contacts import models
from contacts.filters import StatusFilter
from general.utils.telegram import Telegram


@admin.register(models.Contact)
class ContactAdmin(admin.ModelAdmin):
    list_display = ('id', 'profile_link', 'tg_id', 'created_at', 'updated_at')
    list_display_links = ('profile_link',)
    list_per_page = 20
    list_filter = (StatusFilter, 'blocked_bot')
    actions = ('send_message', 'send_promo',)
    readonly_fields = ('data', 'is_registered', 'blocked_bot', 'profile_link',)
    search_fields = ('id', 'first_name', 'student__first_name',)

    @admin.display(description='Массовая рассылка')
    def send_message(self, request, contacts):
        if 'send' in request.POST:
            is_feedback = request.POST.get('is_feedback')
            if is_feedback:
                for contact in contacts:
                    kb = {'inline_keyboard': [[{'text': 'Ответить', 'callback_data': f'data|feedback_student|{contact.id}'}]]}
                    data = {
                        'chat_id': contact.tg_id,
                        'parse_mode': 'html',
                        'text': request.POST['message'],
                        'reply_markup': json.dumps(kb)
                    }
                    Telegram.send_single_message(data)
            else:
                Telegram.send_to_people(contacts, request.POST['message'])
            return HttpResponseRedirect(request.get_full_path())

        return render(request, 'dashboard/send_intermediate.html', context={'entities': contacts})

    @admin.display(description='Ссылка на профиль')
    def profile_link(self, instance):
        if hasattr(instance, 'student'):
            obj = instance.student
            model = 'client' if instance.student.is_client else 'lead'
        else:
            obj = instance
            model = instance._meta.model_name
        changeform_url = reverse(
            f'admin:dashboard_{model}_change', args=(obj.id,)
        )

        return mark_safe(f'<a href="{changeform_url}" target="_blank">{self.get_name(instance)}</a>')

    @admin.display(description='Отправить промо')
    def send_promo(self, request, contacts):
        ids = [contact.id for contact in contacts]
        params = f'?_selected_action={"&_selected_action=".join(str(id) for id in ids)}'
        return HttpResponseRedirect(reverse(
            'dashboard:send_promo_v2') + f'{params}')

    @staticmethod
    def get_name(instance):
        return instance.student.first_name if hasattr(instance, 'student') else instance.first_name

    class Media:
        js = ('dashboard/js/contact_admin.js',)