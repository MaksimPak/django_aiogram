import os

import requests
from django.apps import apps
from django.contrib import admin, messages
from django.db.models import Count, Q
from django.middleware.csrf import get_token
from django.shortcuts import render
from django.template.loader import render_to_string
from django.urls import reverse
from django.utils.html import format_html
from django.utils.http import urlencode
from django.utils.safestring import mark_safe

from broadcast.forms import BroadcastForm
from courses import models
from courses.filters import FilterByCourse, StatusFilter
from courses.forms import CourseForm


class LessonMedia(admin.TabularInline):
    model = models.Lesson
    extra = 0
    fields = ('video', 'watch_count',)
    readonly_fields = ('watch_count',)

    @admin.display(description='Просмотров')
    def watch_count(self, instance):
        count = models.StudentLesson.objects.filter(lesson=instance,
                                                    date_watched__isnull=False).count()
        return count

    def has_add_permission(self, request, course):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


class StudentCourseList(admin.TabularInline):
    model = models.StudentCourse
    fields = ('student_display', 'created_at', 'message_student', 'has_paid', 'has_finished', 'delete_student')
    readonly_fields = ('student_display', 'created_at', 'message_student', 'has_finished', 'delete_student')
    can_delete = False
    extra = 0
    classes = ('collapse',)

    def has_add_permission(self, request, course):
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
            'courses/message_link.html',
            {
                'data': instance,
            }
        )

    @admin.display(description='Удалить')
    def delete_student(self, instance):
        return render_to_string(
            'courses/delete_student.html',
            {
                'data': instance,
            }
        )

    verbose_name_plural = 'Студенты'


class LessonList(admin.StackedInline):
    model = models.Lesson
    readonly_fields = ('link',)
    classes = ('collapse',)
    extra = 1

    @admin.display(description='Ссылка на урок')
    def link(self, instance):
        return f'https://t.me/{os.getenv("BOT_NAME")}?start=lesson{instance.id}'

    def formfield_for_foreignkey(self, db_field, request=None, **kwargs):
        field = super(LessonList, self).formfield_for_foreignkey(db_field, request, **kwargs)

        if db_field.name == 'form':
            field.queryset = field.queryset.filter(
                mode='quiz')

        return field


@admin.register(models.CourseCategory)
class CourseCategoryAdmin(admin.ModelAdmin):
    list_display = ('id', 'name')
    list_per_page = 10


@admin.register(models.Course)
class CourseAdmin(admin.ModelAdmin):
    list_display = ('id', '__str__', 'course_info',
                    'company', 'student_count', 'finished_count',)
    list_display_links = ('__str__',)
    readonly_fields = ('date_started', 'date_finished', 'created_at', 'link',)
    exclude = ('week_size', 'lesson_count', 'set_priority_date')
    list_per_page = 20
    search_fields = ('id', 'name')
    list_filter = ('company',)
    inlines = (LessonList, StudentCourseList, )
    ordering = ('id',)
    date_hierarchy = 'created_at'
    form = CourseForm
    change_form_template = 'courses/admin/change_form.html'
    actions = ('duplicate',)

    def get_queryset(self, request):
        qs = super(CourseAdmin, self).get_queryset(request)
        qs = qs.annotate(
            student_total=Count('student'),
            num_finished=Count('studentcourse', filter=Q(studentcourse__has_finished=True))
        )
        return qs

    @admin.display(description='Ссылка на курс')
    def link(self, instance):
        return f'https://t.me/{os.getenv("BOT_NAME")}?start=course{instance.id}'

    @admin.display(description='Дублировать (Максимум 3)')
    def duplicate(self, request, courses):
        if len(courses) > 3:
            self.message_user(request, 'Нельзя дублировать больше 3 курсов', messages.ERROR)
            return

        for course in courses:
            lessons = list(course.lesson_set.all())
            course.pk = None

            course.date_started = None
            course.date_finished = None
            course.code = None
            course.save()

            for lesson in lessons:
                lesson.id = None
                lesson.course = course
                lesson.date_sent = None
                lesson.save()

        self.message_user(request, '{0} курс(а) были успешно дублированны'.format(courses.count()), messages.SUCCESS)

    @admin.display(description='Количество студентов',ordering='student_total')
    def student_count(self, course):
        return course.student_set.count()

    @admin.display(description='Количество завершивших', ordering='num_finished')
    def finished_count(self, course):
        return course.studentcourse_set.filter(has_finished=True).count()


@admin.register(models.CourseMedia)
class CourseMediaAdmin(admin.ModelAdmin):
    list_display = ('id', '__str__')
    list_display_links = ('__str__',)
    inlines = (LessonMedia,)

    def has_add_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False

    def get_fields(self, request, obj=None):
        return []


@admin.register(models.StudentLesson)
class StudentProgress(admin.ModelAdmin):
    list_filter = (FilterByCourse, StatusFilter,)

    def get_queryset(self, request):
        if not request.GET:
            return models.StudentLesson.objects.none()
        return super(StudentProgress, self).get_queryset(request)

    def get_model_perms(self, request):
        """
        Return empty perms dict thus hiding the model from admin index.
        """
        return {}

    def get_list_display(self, request):
        if not request.GET.get('lesson__id__exact'):
            return ('lesson_name', 'lesson_received', 'lesson_watched',
                    'hw_submitted', 'lesson_likes', 'lesson_dislikes',
                    'details',)
        else:
            return 'student',

    def get_actions(self, request):
        actions = super(StudentProgress, self).get_actions(request)
        if request.GET.get('lesson__id__exact'):
            self.actions.append(self.send_message)
            self.actions.append(self.send_certs)
        return actions

    @admin.display(description='👍')
    def lesson_likes(self, instance):
        return instance.lesson.likes

    @admin.display(description='👎')
    def lesson_dislikes(self, instance):
        return instance.lesson.dislikes

    @admin.display(description='Урок')
    def lesson_name(self, instance):
        return instance.lesson.name

    @admin.display(description='#Получили')
    def lesson_received(self, instance):
        course_id = instance.lesson.course_id
        count = models.StudentLesson.objects.filter(
            lesson__course_id=course_id,
            lesson=instance.lesson,
            date_sent__isnull=False,
        ).count()
        return count

    @admin.display(description='#Посмотрели')
    def lesson_watched(self, instance):
        course_id = instance.lesson.course_id
        count = models.StudentLesson.objects.filter(
            lesson__course_id=course_id,
            lesson=instance.lesson,
            date_watched__isnull=False,
        ).count()
        return count

    @admin.display(description='#Сдали домашку')
    def hw_submitted(self, instance):
        course_id = instance.lesson.course_id
        count = models.StudentLesson.objects.filter(
            lesson__course_id=course_id,
            lesson=instance.lesson,
            homework_sent__isnull=False,
            lesson__homework_desc__isnull=False
        ).count()
        return count if count else 'Нет домашки'

    @admin.display(description='Детали')
    def details(self, instance):
        model = instance._meta.model_name
        app = instance._meta.app_label
        changeform_url = reverse(
            f'admin:{app}_{model}_changelist',
        )
        querystrings = {
            'course_id': instance.lesson.course_id,
            'lesson__id__exact': instance.lesson_id,
        }
        changeform_url = '{}?{}'.format(changeform_url, urlencode(querystrings))
        return mark_safe(f'<a href="{changeform_url}">Посмотреть</a>')

    @staticmethod
    @admin.display(description='Сгенерировать сертификаты и отправить')
    def send_certs(modeladmin, request, qs):
        Certificate = apps.get_model('certificates', 'Certificate')
        course = models.Course.objects.get(pk=request.GET.get('course_id'))
        new_certs = Certificate.objects.bulk_create([
            Certificate(student=studlesson.student.contact,
                        template=course.certtemplate) for studlesson in qs]
        )
        modeladmin._send_cert(request, new_certs)

    @staticmethod
    def _send_cert(request, certs):
        url = os.environ.get('DOMAIN') + '/broadcast/send/'
        referer = os.environ.get('DOMAIN') + request.get_full_path()
        for cert in certs:
            headers = {'X-CSRFToken': get_token(request), 'Referer': referer}
            data = {
                '_selected_action': cert.student.id,
                'text': f'Сертификат по курсу {cert.template.course}'
            }
            requests.post(url, data=data, headers=headers,
                          files={'image': cert.generated_cert.read()}, cookies=request.COOKIES)

    @staticmethod
    @admin.display(description='Массовая рассылка')
    def send_message(modeladmin, request, queryset):
        contacts = [x.student.contact for x in queryset]
        form = BroadcastForm(initial={'_selected_action': [contact.id for contact in contacts]})
        context = {
            'entities': contacts,
            'form': form,
            'referer': request.META['HTTP_REFERER'],
        }
        return render(request, "broadcast/send.html", context=context)
