import datetime
import json

from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.http import HttpResponseRedirect
from django.shortcuts import render
from django.template.loader import render_to_string
from django.urls import resolve
from django.utils.html import format_html

from dashboard import models
from dashboard.forms import StudentAdmin
from dashboard.models import Course
from dashboard.telegram import Telegram


class StudentCourseList(admin.TabularInline):
    model = models.StudentCourse
    fields = ('student_display', 'created_at', 'message_student')
    readonly_fields = ('student_display', 'created_at', 'message_student')
    can_delete = False
    extra = 0
    classes = ('collapse',)

    def get_parent_object_from_request(self, request):
        """
        Returns the parent object from the request or None.

        Note that this only works for Inlines, because the `parent_model`
        is not available in the regular admin.ModelAdmin as an attribute.
        """
        resolved = resolve(request.path_info)
        if resolved.args:
            return self.parent_model.objects.get(pk=resolved.args[0])
        return None

    def has_add_permission(self, request, obj):
        return False

    @admin.display(description='Студент')
    def student_display(self, instance):
        return format_html(
            '{0}',
            instance.student,
        )

    @admin.display(description='message')
    def message_student(self, instance):
        return render_to_string(
            'dashboard/message_link.html',
            {
                'data': instance,
                'course_id': instance.course.id
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
    readonly_fields = ('date_sent',)
    extra = 1


@admin.register(models.Lead)
class LeadAdmin(admin.ModelAdmin):
    list_display = ('id', '__str__', 'tg_id', 'application_type', 'phone', 'language_type', 'chosen_field', 'checkout_date')
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
    def send_message(self, request, leads):
        if 'send' in request.POST:
            is_feedback = request.POST.get('is_feedback')
            if is_feedback:
                for student in leads:
                    kb = {'inline_keyboard': [[{'text': 'Ответить', 'callback_data': f'data|feedback_student|{student.id}'}]]}
                    data = {
                        'chat_id': student.tg_id,
                        'parse_mode': 'html',
                        'text': request.POST['message'],
                        'reply_markup': json.dumps(kb)
                    }
                    Telegram.send_single_message(data)
            else:
                Telegram.send_to_people(leads, request.POST['message'])
            return HttpResponseRedirect(request.get_full_path())

        return render(request, 'dashboard/send_intermediate.html', context={'entities': leads})

    @admin.display(description='Рассылка чекаута')
    def send_checkout(self, request, leads):
        for lead in leads:
            data = {
                'chat_id': lead.tg_id,
                'text': 'https://paynet.uz/checkout_test'
            }
            resp = Telegram.send_single_message(data=data)
            resp['ok'] and models.Student.objects.filter(pk=lead.id).update(checkout_date=datetime.datetime.now())
        return HttpResponseRedirect(request.get_full_path())

    @admin.display(description='Приписать к курсу')
    def assign_to_course(self, request, leads):
        if 'assign' in request.POST:
            courses = Course.objects.filter(pk__in=request.POST.getlist('course'))
            for lead in leads:
                lead.make_client(courses)
            return HttpResponseRedirect(request.get_full_path())

        courses = Course.objects.filter(is_free=False)
        return render(request, 'dashboard/assign_to_course.html',
                      context={'entities': leads, 'courses': courses})


@admin.register(models.Client)
class ClientAdmin(admin.ModelAdmin):
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
    change_form_template = 'admin/dashboard/student/change_form.html'

    @admin.display(description='Массовая рассылка')
    def send_message(self, request, clients):
        if 'send' in request.POST:
            is_feedback = request.POST.get('is_feedback')
            if is_feedback:
                for student in clients:
                    kb = {'inline_keyboard': [
                        [{'text': 'Ответить', 'callback_data': f'data|feedback_student|{student.id}'}]]}
                    data = {
                        'chat_id': student.tg_id,
                        'parse_mode': 'html',
                        'text': request.POST['message'],
                        'reply_markup': json.dumps(kb)
                    }
                    Telegram.send_single_message(data)
            else:
                Telegram.send_to_people(clients, request.POST['message'])
            return HttpResponseRedirect(request.get_full_path())

        return render(request, 'dashboard/send_intermediate.html', context={'entities': clients})

    @admin.display(description='Выслать чекаут')
    def send_checkout(self, request, clients):
        for client in clients:
            data = {
                'chat_id': client.tg_id,
                'text': 'https://paynet.uz/checkout_test'
            }
            resp = Telegram.send_single_message(data=data)
            resp['ok'] and models.Student.objects.filter(pk=client.id).update(checkout_date=datetime.datetime.now())
        return HttpResponseRedirect(request.get_full_path())

    @admin.display(description='Курсы')
    def get_courses(self, client):
        return render_to_string(
            'dashboard/display_courses.html',
            {
                'courses': client.courses.values_list('name', flat=True)
            }
        )


@admin.register(models.Course)
class CourseAdmin(admin.ModelAdmin):
    list_display = ('id', '__str__', 'course_info', 'is_started', 'category', 'difficulty', 'price')
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
    change_form_template = 'admin/dashboard/course/change_form.html'

    def change_view(self, request, object_id, form_url='', extra_context=None):
        extra_context = extra_context or {}
        course = models.Course.objects.get(pk=object_id)

        lessons = course.lesson_set.all().order_by('id')
        lessons_stat = []
        for lesson in lessons:
            data = {
                'lesson': lesson,
                'received': set(),
                'viewed': set(),
                'hw': set(),
            }
            for record in lesson.studentlesson_set.all():
                if record.date_sent:
                    data['received'].add(record.student)
                if record.date_watched:
                    data['viewed'].add(record.student)
                if record.homework_sent:
                    data['hw'].add(record.student)
            lessons_stat.append(data)

        extra_context['lessons_stat'] = lessons_stat
        extra_context['studentcourse'] = course.studentcourse_set.all()
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
class LessonAdmin(admin.ModelAdmin):
    list_display = ('id', '__str__', 'lesson_info', 'video', 'course')
    list_display_links = ('__str__',)
    list_per_page = 20
    readonly_fields = ('date_sent',)
    search_fields = ('id', 'title', 'course')
    list_filter = ('course',)
    ordering = ('id',)
    date_hierarchy = 'created_at'

    class Media:
        js = (
            'dashboard/js/lesson_admin.js',
        )


admin.site.register(models.User, UserAdmin)
