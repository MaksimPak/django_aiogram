import datetime
import os
from contextlib import suppress

from apscheduler.schedulers import SchedulerAlreadyRunningError
from apscheduler.triggers.cron import CronTrigger
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.http import HttpResponseRedirect
from django.shortcuts import render
import requests

from dashboard import models
from dashboard.management.commands.runapscheduler import SCHEDULER


class TelegramBroadcastMixin:
    @staticmethod
    def send_single_message(tg_id, message):
        url = f"https://api.telegram.org/bot{os.getenv('BOT_TOKEN')}/sendMessage?chat_id={tg_id}&text={message}"
        requests.get(url)

    def send_message(self, request, qs):
        if 'send' in request.POST:
            for record in qs:
                self.send_single_message(record.tg_id, request.POST['message'])
            return HttpResponseRedirect(request.get_full_path())

        return render(request, 'dashboard/send_intermediate.html', context={'entities': qs})

    def send_checkout(self, request, qs):
        for record in qs:
            url = f"https://api.telegram.org/bot{os.getenv('BOT_TOKEN')}/sendMessage?chat_id={record.tg_id}&text=https://paynet.uz/checkout_test"
            resp = requests.get(url).json()
            resp['ok'] and models.Student.objects.filter(pk=record.id).update(checkout_date=datetime.datetime.now())

        return HttpResponseRedirect(request.get_full_path())


class StudentCourseList(admin.TabularInline):
    model = models.StudentCourse
    classes = ('collapse',)
    extra = 1


class LessonList(admin.StackedInline):
    model = models.Lesson
    classes = ('collapse',)
    extra = 1


class LeadAdmin(TelegramBroadcastMixin, admin.ModelAdmin):
    list_display = ('id', '__str__', 'tg_id', 'application_type', 'phone', 'language_type', 'is_client', 'chosen_field')
    list_editable = ('is_client',)
    list_per_page = 20
    list_filter = ('chosen_field', 'application_type')
    list_display_links = ('__str__',)
    readonly_fields = ('unique_code', 'checkout_date', 'invite_link')
    actions = ('send_message', 'send_checkout',)
    search_fields = ('id', 'first_name', 'last_name')
    ordering = ('id',)
    date_hierarchy = 'created_at'

    def send_message(self, request, qs):
        return super().send_message(request, qs)

    def send_checkout(self, request, qs):
        return super().send_checkout(request, qs)

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
    readonly_fields = ('unique_code', 'checkout_date', 'invite_link')
    search_fields = ('id', 'first_name', 'last_name')
    ordering = ('id',)
    date_hierarchy = 'created_at'

    def send_message(self, request, qs):
        return super().send_message(request, qs)

    def send_checkout(self, request, qs):
        return super().send_checkout(request, qs)

    send_message.short_description = 'Массовая рассылка'
    send_checkout.short_description = 'Рассылка чекаута'


class CourseAdmin(admin.ModelAdmin):
    list_display = ('id', '__str__', 'short_info', 'is_started', 'category', 'difficulty', 'price')
    list_display_links = ('__str__',)
    list_per_page = 20
    search_fields = ('id', 'name')
    list_filter = ('category', 'price',)
    inlines = (StudentCourseList, LessonList)
    ordering = ('id',)
    date_hierarchy = 'created_at'

    @staticmethod
    def send_lessons(lessons, tg_id):
        for lesson in lessons:
            url = f"https://api.telegram.org/bot{os.getenv('BOT_TOKEN')}/" \
                  f"sendMessage?chat_id={tg_id}&text={lesson.title}"
            requests.get(url)

    @staticmethod
    def send_students(students, lessons):
        [CourseAdmin.send_lessons(lessons, x.tg_id) for x in students]

    @staticmethod
    def set_schedule(obj):
        students = obj.student_set.all()
        lessons = obj.lesson_set.all()[obj.last_lesson_index: obj.last_lesson_index + obj.week_size]
        CourseAdmin.send_students(students, lessons)
        obj.is_started = True
        obj.save()

    def response_change(self, request, obj):
        if '_start_course' in request.POST:
            SCHEDULER.add_job(
                self.set_schedule,
                trigger=CronTrigger(second='*/10'),
                args=(obj,),
                id=f'course_{obj.id}',
                max_instances=1,
                replace_existing=True,
            )
            with suppress(SchedulerAlreadyRunningError):
                SCHEDULER.start()
        return super().response_change(request, obj)


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
