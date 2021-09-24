import json

from django.contrib import admin
from django.http import HttpResponseRedirect
from django.shortcuts import render
from django.urls import reverse
from django.utils.safestring import mark_safe

from contacts import models
from contacts.filters import StatusFilter
from broadcast.utils.telegram import Telegram
# from contacts.forms import BroadcastForm, PromoForm
from contacts.forms import BroadcastForm


@admin.register(models.Contact)
class ContactAdmin(admin.ModelAdmin):
    list_display = ('id', 'profile_link', 'tg_id', 'created_at', 'updated_at')
    list_display_links = ('profile_link',)
    list_per_page = 20
    list_filter = (StatusFilter, 'blocked_bot')
    actions = ('send_message',)
    readonly_fields = ('data', 'is_registered', 'blocked_bot', 'profile_link',)
    search_fields = ('id', 'first_name', 'student__first_name',)
    change_form_template = 'contacts/admin/change_form.html'

    @admin.display(description='Массовая рассылка')
    def send_message(self, request, contacts):
        form = BroadcastForm(initial={'_selected_action': contacts.values_list('id', flat=True)})
        context = {
            'entities': contacts,
            'form': form,
            'referer': request.META['HTTP_REFERER'],
        }
        return render(request, "broadcast/send.html", context=context)
    #
    # @admin.display(description='Отправить промо')
    # def send_promo(self, request, contacts):
    #     form = PromoForm(initial={'_selected_action': contacts.values_list('id', flat=True)})
    #     context = {
    #         'form_url': 'broadcast:message_multiple',
    #         'entities': contacts,
    #         'form': form,
    #         'referer': request.META['HTTP_REFERER'],
    #     }
    #     return render(request, "broadcast/send.html", context=context)

    @admin.display(description='Ссылка на профиль')
    def profile_link(self, instance):
        if hasattr(instance, 'student'):
            obj = instance.student
            model = 'client' if instance.student.is_client else 'lead'
        else:
            obj = instance
            model = instance._meta.model_name
        app = obj._meta.app_label
        changeform_url = reverse(
            f'admin:{app}_{model}_change', args=(obj.id,)
        )

        return mark_safe(f'<a href="{changeform_url}" target="_blank">{self.get_name(instance)}</a>')

    @staticmethod
    def get_name(instance):
        return instance.student.first_name if hasattr(instance, 'student') else instance.first_name

    class Media:
        js = ('contacts/js/contact_admin.js',)
