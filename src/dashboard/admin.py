import datetime
import json
import os

import requests
from apscheduler.triggers.cron import CronTrigger
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.http import HttpResponseRedirect
from django.shortcuts import render
from django.template.loader import render_to_string
from django.urls import reverse
from django.utils.html import format_html
from django_apscheduler.models import DjangoJob, DjangoJobExecution

from dashboard import models
from dashboard.forms import StudentAdmin
from dashboard.models import Course
from dashboard.scheduler import SCHEDULER


class TelegramBroadcastMixin:  # todo to separate module
    @staticmethod
    def send_single_message(data):
        url = f"https://api.telegram.org/bot{os.getenv('BOT_TOKEN')}/sendMessage"
        return requests.post(url, data=data).json()

    def send_message(self, request, qs):
        if 'send' in request.POST:
            for record in qs:
                data = {
                    'chat_id': record.tg_id,
                    'text': request.POST['message']
                }
                self.send_single_message(data=data)
            return HttpResponseRedirect(request.get_full_path())

        return render(request, 'dashboard/send_intermediate.html', context={'entities': qs})

    def send_checkout(self, request, qs):
        for record in qs:
            data = {
                'chat_id': record.tg_id,
                'text': 'https://paynet.uz/checkout_test'
            }
            resp = self.send_single_message(data=data)
            resp['ok'] and models.Student.objects.filter(pk=record.id).update(checkout_date=datetime.datetime.now())
        return HttpResponseRedirect(request.get_full_path())


class StudentCourseList(admin.TabularInline):
    model = models.StudentCourse
    fields = ('student_display', 'created_at', 'message_student')  # todo studentcourse__student
    readonly_fields = ('student_display', 'created_at', 'message_student')
    can_delete = False
    extra = 0
    classes = ('collapse',)

    def has_add_permission(self, request, obj):
        return False

    @admin.display(description='Student') # todo delete method
    def student_display(self, instance):
        return format_html(
            '{0}',
            instance.student,
        )

    @admin.display(description='created_at')  # todo delete method
    def created_at(self, instance):
        return format_html(
            '{0}',
            instance.created_at,
        )

    @admin.display(description='message')
    def message_student(self, instance):
        return render_to_string(
            'dashboard/message_form.html',
            {
                'data': instance
            }
        )

    verbose_name_plural = 'Студенты'

    class Media:
        css = {
            'all': ('dashboard/css/studentcourse.css',)
        }



class LessonList(admin.StackedInline):
    model = models.Lesson
    classes = ('collapse',)
    extra = 1


@admin.register(models.Lead)
class LeadAdmin(TelegramBroadcastMixin, admin.ModelAdmin):
    list_display = ('id', '__str__', 'tg_id', 'application_type', 'phone', 'language_type', 'is_client', 'chosen_field', 'checkout_date')
    list_editable = ('is_client',)  # todo remove
    list_per_page = 20
    list_filter = ('chosen_field', 'application_type')
    list_display_links = ('__str__',)
    readonly_fields = ('unique_code', 'checkout_date', 'invite_link', 'created_at',)
    actions = ('send_message', 'send_checkout', 'assign_to_course')
    search_fields = ('id', 'first_name', 'last_name')
    ordering = ('id',)
    date_hierarchy = 'created_at'
    form = StudentAdmin

    @admin.display(description='Массовая рассылка')
    def send_message(self, request, qs):
        return super().send_message(request, qs)

    @admin.display(description='Рассылка чекаута')  #todo make separate method
    def send_checkout(self, request, qs):
        return super().send_checkout(request, qs)

    @admin.display(description='Приписать к курсу')
    def assign_to_course(self, request, qs):  # todo naming
        if 'assign' in request.POST:
            courses = [Course.objects.get(pk=x) for x in request.POST.getlist('course')]  #todo use in
            for client in qs:
                client.courses.set(courses) # todo use transaction atomic / take it to model method
            qs.update(is_client=True)
            return HttpResponseRedirect(request.get_full_path())

        courses = Course.objects.filter(is_free=False)
        return render(request, 'dashboard/assign_to_course.html',
                      context={'entities': qs, 'courses': courses})

    class Media:
        js = (
            'dashboard/js/lead_admin.js',
        )


@admin.register(models.Client)
class ClientAdmin(TelegramBroadcastMixin, admin.ModelAdmin):
    list_display = ('id', '__str__', 'phone', 'language_type', 'get_courses',)
    list_per_page = 20
    list_filter = ('studentcourse__course__name',)
    list_display_links = ('__str__',)
    actions = ('send_message', 'send_checkout')
    readonly_fields = ('unique_code', 'checkout_date', 'invite_link', 'created_at',)
    search_fields = ('id', 'first_name', 'last_name')
    ordering = ('id',)
    date_hierarchy = 'created_at'
    form = StudentAdmin

    @admin.display(description='Массовая рассылка')
    def send_message(self, request, qs):
        return super().send_message(request, qs)

    @admin.display(description='Рассылка чекаута')
    def send_checkout(self, request, qs):
        return super().send_checkout(request, qs)

    @admin.display(description='Курсы')
    def get_courses(self, obj):
        return ',\n'.join([x.name for x in obj.courses.all()])  # todo use li / use values flat true


@admin.register(models.Course)
class CourseAdmin(admin.ModelAdmin):
    list_display = ('id', '__str__', 'short_info', 'is_started', 'category', 'difficulty', 'price')
    list_display_links = ('__str__',)
    list_editable = ('is_started',)
    readonly_fields = ('date_started', 'date_finished', 'created_at',)
    exclude = ('week_size', 'lesson_count',)
    list_per_page = 20
    search_fields = ('id', 'name')
    list_filter = ('category', 'price',)
    inlines = (LessonList, StudentCourseList, )
    ordering = ('id',)
    date_hierarchy = 'created_at'
    change_form_template = 'admin/dashboard/Course/change_form.html'

    @staticmethod
    def send_lessons(lessons, tg_id):
        for lesson in lessons:
            kb = {
                'inline_keyboard': [
                    [{
                        'text': 'Посмотреть урок',
                        'callback_data': f'lesson|{lesson.id}'
                    }],
                ]
            }
            d = {
                'chat_id': tg_id,
                'text': lesson.title,
                'reply_markup': json.dumps(kb)
            }
            url = f"https://api.telegram.org/bot{os.getenv('BOT_TOKEN')}/sendMessage"
            requests.post(url, data=d)

    @staticmethod
    def send_students(students, lessons):
        [CourseAdmin.send_lessons(lessons, x.tg_id) for x in students]

    @staticmethod
    def set_schedule(obj):
        students = obj.student_set.all()
        lessons = obj.lesson_set.all()[obj.last_lesson_index: obj.last_lesson_index + obj.week_size]
        obj.last_lesson_index += obj.week_size
        if lessons:
            obj.save()
            CourseAdmin.send_students(students, lessons)
        else:
            obj.last_lesson_index = 0
            obj.is_started = False
            obj.save()
            SCHEDULER.pause_job(f'course_{obj.id}')
            SCHEDULER.remove_job(f'course_{obj.id}')

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
            obj.is_started = True
            obj.save()
        return super().response_change(request, obj)

    def change_view(self, request, object_id, form_url='', extra_context=None):
        extra_context = extra_context or {}
        course = models.Course.objects.get(pk=object_id)
        extra_context['lessons'] = course.lesson_set.all()
        extra_context['studentcourse'] = course.studentcourse_set.all()  # todo templates Course with lower
        return super().change_view(
            request, object_id, form_url, extra_context=extra_context,
        )

    class Media:
        js = (
            'dashboard/js/course_admin.js',
        )
        css = {
            'all': ('dashboard/css/course_admin.css',)
        }


@admin.register(models.Lesson)
class LessonAdmin(TelegramBroadcastMixin, admin.ModelAdmin):
    list_display = ('id', '__str__', 'short_info', 'video', 'course')
    list_display_links = ('__str__',)
    list_per_page = 20
    readonly_fields = ('date_sent',)
    search_fields = ('id', 'title', 'course')
    list_filter = ('course',)
    ordering = ('id',)
    actions = ('send_lesson_block',)
    date_hierarchy = 'created_at'

    @staticmethod
    def prepare_data(students, lesson):  # todo remove
        for student in students:
            kb = {
                'inline_keyboard': [
                    [{
                        'text': 'Посмотреть урок',
                        'callback_data': f'lesson|{lesson.id}'
                    }],
                ]
            }
            data = {
                'chat_id': student.tg_id,
                'text': lesson.title,
                'reply_markup': json.dumps(kb)
            }
            LessonAdmin.send_single_message(data=data)

    def send_lesson_block(self, request, qs):
        [LessonAdmin.prepare_data(lesson.course.student_set.all(), lesson) for lesson in qs]

    send_lesson_block.short_description = 'Послать уроки'

    class Media:
        js = (
            'dashboard/js/lesson_admin.js',
        )


@admin.register(models.Student)  # todo delete
class Student(admin.ModelAdmin):
    def response_change(self, request, obj):
        return HttpResponseRedirect(reverse('admin:dashboard_course_changelist'))

    def get_model_perms(self, request):
        """
        Return empty perms dict thus hiding the model from admin index.
        """
        return {}


admin.site.register(models.User, UserAdmin)
admin.site.unregister(DjangoJob)
admin.site.unregister(DjangoJobExecution)
