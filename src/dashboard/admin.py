import os

from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.http import HttpResponseRedirect
from django.shortcuts import render
import requests

from dashboard import models


class TelegramBroadcastMixin:
    def send_message(self, request, qs, checkout=False):
        if not checkout:
            if 'send' in request.POST:
                for record in qs:
                    url = f"https://api.telegram.org/bot{os.getenv('BOT_TOKEN')}/sendMessage?chat_id={record.tg_id}&text={request.POST['message']}"
                    requests.get(url)
                return HttpResponseRedirect(request.get_full_path())

            return render(request, 'dashboard/send_intermediate.html', context={'entities': qs})
        else:
            for record in qs:
                url = f"https://api.telegram.org/bot{os.getenv('BOT_TOKEN')}/sendMessage?chat_id={record.tg_id}&text=https://paynet.uz/checkout_test"
                requests.get(url)
            return HttpResponseRedirect(request.get_full_path())


class StudentCourseList(admin.TabularInline):
    model = models.StudentCourse
    classes = ('collapse',)
    extra = 1


class LeadAdmin(TelegramBroadcastMixin, admin.ModelAdmin):
    list_display = ('id', '__str__', 'tg_id', 'application_type', 'phone', 'language_type', 'is_client', 'chosen_field')
    list_editable = ('is_client',)
    list_per_page = 20
    list_filter = ('chosen_field', 'application_type')
    list_display_links = ('__str__',)
    actions = ('send_message', 'send_checkout',)
    search_fields = ('id', 'first_name', 'last_name')
    ordering = ('id',)
    date_hierarchy = 'created_at'

    def send_message(self, request, qs, checkout=False):
        return super().send_message(request, qs)

    def send_checkout(self, request, qs, checkout=True):
        return super().send_message(request, qs, checkout)

    send_message.short_description = 'Массовая рассылка'
    send_checkout.short_description = 'Рассылка чекаута'

    class Media:
        js = (
            'dashboard/js/admin.js',
        )


class ClientAdmin(TelegramBroadcastMixin, admin.ModelAdmin):
    list_display = ('id', '__str__', 'tg_id', 'application_type', 'phone', 'language_type', 'is_client',)
    list_editable = ('is_client',)
    list_per_page = 20
    list_filter = ('studentcourse__course__name',)
    list_display_links = ('__str__',)
    actions = ('send_message', 'send_checkout')
    search_fields = ('id', 'first_name', 'last_name')
    ordering = ('id',)
    date_hierarchy = 'created_at'

    def send_message(self, request, qs, checkout=False):
        return super().send_message(request, qs)

    def send_checkout(self, request, qs, checkout=True):
        return super().send_message(request, qs, checkout)

    send_message.short_description = 'Массовая рассылка'
    send_checkout.short_description = 'Рассылка чекаута'


class CourseAdmin(admin.ModelAdmin):
    list_display = ('id', '__str__', 'short_info', 'category', 'difficulty', 'price')
    list_display_links = ('__str__',)
    list_per_page = 20
    search_fields = ('id', 'name')
    list_filter = ('category', 'price',)
    inlines = (StudentCourseList,)
    ordering = ('id',)
    date_hierarchy = 'created_at'


class LessonAdmin(admin.ModelAdmin):
    list_display = ('id', '__str__', 'short_info', 'video', 'course')
    list_display_links = ('__str__',)
    list_per_page = 20
    search_fields = ('id', 'title', 'course')
    list_filter = ('course',)
    ordering = ('id',)
    date_hierarchy = 'created_at'


admin.site.register(models.User, UserAdmin)
admin.site.register(models.Lead, LeadAdmin)
admin.site.register(models.Client, ClientAdmin)
admin.site.register(models.Course, CourseAdmin)
admin.site.register(models.Lesson, LessonAdmin)
