from django.conf import settings
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.contrib.gis.db.models import PointField
from django.http import HttpResponseRedirect
from django.shortcuts import render
from django.template.loader import render_to_string
from mapwidgets import GooglePointFieldWidget

from broadcast.forms import BroadcastForm
from users import models, forms


@admin.register(models.Lead)
class LeadAdmin(admin.ModelAdmin):
    list_display = ('id', '__str__', 'tg_id', 'application_type', 'blocked_bot', 'phone', 'language_type', 'learning_centre', 'checkout_date', 'get_courses',)
    list_per_page = 20
    list_filter = ('learning_centre', 'application_type',)
    list_display_links = ('__str__',)
    readonly_fields = ('checkout_date', 'invite_link', 'created_at', 'blocked_bot')
    exclude = ('unique_code', 'contact')
    actions = ('send_message', 'send_checkout', 'assign_courses', 'assign_free_courses')
    search_fields = ('id', 'first_name', 'last_name')
    ordering = ('id',)
    date_hierarchy = 'created_at'
    form = forms.StudentAdmin
    change_form_template = 'users/admin/change_form.html'

    @admin.display(description='Блокнул бота', boolean=True)
    def blocked_bot(self, lead):
        return lead.contact.blocked_bot

    @admin.display(description='TG ID')
    def tg_id(self, lead):
        return lead.contact.tg_id

    @admin.display(description='Массовая рассылка')
    def send_message(self, request, leads):
        contact_ids = [lead.contact.id for lead in leads]
        form = BroadcastForm(initial={'_selected_action': contact_ids})
        context = {
            'entities': leads,
            'form': form,
            'referer': request.META['HTTP_REFERER'],
        }
        return render(request, "broadcast/send.html", context=context)

    @admin.display(description='Рассылка чекаута')
    def send_checkout(self, request, leads):
        contact_ids = [lead.contact.id for lead in leads]
        form = BroadcastForm(initial={'_selected_action': contact_ids})
        form.fields['text'].initial = 'https://paynet.uz/checkout_test'
        context = {
            'entities': leads,
            'form': form,
            'referer': request.META['HTTP_REFERER'],
        }
        return render(request, "broadcast/send.html", context=context)

    @admin.display(description='Назначить курсы')
    def assign_courses(self, request, leads):
        if 'assign' in request.POST:
            courses = models.Course.objects.filter(pk__in=request.POST.getlist('course'))
            for lead in leads:
                lead.assign_courses(courses, True)
            return HttpResponseRedirect(request.get_full_path())

        courses = models.Course.objects.filter(is_free=False, is_started=False, is_finished=False)
        return render(request, 'dashboard/assign_courses.html',
                      context={'entities': leads, 'courses': courses, 'action': 'assign_courses'})

    @admin.display(description='Добавить бесплатных курсов')
    def assign_free_courses(self, request, leads):
        if 'assign' in request.POST:
            courses = models.Course.objects.filter(pk__in=request.POST.getlist('course'))
            for lead in leads:
                lead.assign_courses(courses)
            return HttpResponseRedirect(request.get_full_path())

        courses = models.Course.objects.filter(is_free=True, is_started=False, is_finished=False)
        return render(request, 'dashboard/assign_courses.html',
                      context={'entities': leads, 'courses': courses, 'action': 'assign_free_courses'})

    @admin.display(description='Курсы')
    def get_courses(self, lead):
        return render_to_string(
            'users/display_courses.html',
            {
                'courses': lead.courses.values_list('name', flat=True)
            }
        )

    formfield_overrides = {
            PointField: {"widget": GooglePointFieldWidget(settings=settings.MAP_WIDGETS)}
        }


@admin.register(models.Client)
class ClientAdmin(admin.ModelAdmin):
    list_display = ('id', '__str__', 'blocked_bot', 'phone', 'language_type', 'get_courses',)
    list_per_page = 20
    list_filter = ('studentcourse__course__name', 'learning_centre',)
    list_display_links = ('__str__',)
    actions = ('send_message', 'send_checkout', 'assign_courses', 'assign_free_courses')
    readonly_fields = ('unique_code', 'checkout_date', 'invite_link', 'created_at', 'blocked_bot')
    exclude = ('contact',)
    search_fields = ('id', 'first_name', 'last_name')
    ordering = ('id',)
    date_hierarchy = 'created_at'
    form = forms.StudentAdmin
    change_form_template = 'users/admin/change_form.html'

    @admin.display(description='Блокнул бота', boolean=True)
    def blocked_bot(self, lead):
        return lead.contact.blocked_bot

    @admin.display(description='Массовая рассылка')
    def send_message(self, request, leads):
        contact_ids = [lead.contact.id for lead in leads]
        form = BroadcastForm(initial={'_selected_action': contact_ids})
        context = {
            'entities': leads,
            'form': form,
            'referer': request.META['HTTP_REFERER'],
        }
        return render(request, "broadcast/send.html", context=context)

    @admin.display(description='Рассылка чекаута')
    def send_checkout(self, request, client):
        contact_ids = [client.contact.id for client in client]
        form = BroadcastForm(initial={'_selected_action': contact_ids})
        form.fields['text'].initial = 'https://paynet.uz/checkout_test'
        context = {
            'entities': client,
            'form': form,
            'referer': request.META['HTTP_REFERER'],
        }
        return render(request, "broadcast/send.html", context=context)

    @admin.display(description='Курсы')
    def get_courses(self, client):
        return render_to_string(
            'users/display_courses.html',
            {
                'courses': client.courses.values_list('name', flat=True)
            }
        )

    @admin.display(description='Назначить курсы')
    def assign_courses(self, request, clients):
        if 'assign' in request.POST:
            courses = models.Course.objects.filter(pk__in=request.POST.getlist('course'))
            for client in clients:
                client.assign_courses(courses, True)
            return HttpResponseRedirect(request.get_full_path())

        courses = models.Course.objects.filter(is_free=False, is_started=False, is_finished=False)
        return render(request, 'dashboard/assign_courses.html',
                      context={'entities': clients, 'courses': courses, 'action': 'assign_courses'})

    @admin.display(description='Добавить бесплатных курсов')
    def assign_free_courses(self, request, clients):
        if 'assign' in request.POST:
            courses = models.Course.objects.filter(pk__in=request.POST.getlist('course'))
            for client in clients:
                client.assign_courses(courses, True)
            return HttpResponseRedirect(request.get_full_path())

        courses = models.Course.objects.filter(is_free=True, is_started=False, is_finished=False)
        return render(request, 'dashboard/assign_courses.html',
                      context={'entities': clients, 'courses': courses, 'action': 'assign_free_courses'})

    formfield_overrides = {
        PointField: {"widget": GooglePointFieldWidget(settings=settings.MAP_WIDGETS)}
    }


admin.site.register(models.User, UserAdmin)
