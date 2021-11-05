from django.contrib import admin, messages
from django.shortcuts import render
from django.template.loader import render_to_string
from django.urls import reverse
from django.utils.html import format_html
from django.utils.safestring import mark_safe

from broadcast.forms import BroadcastForm
from courses import models
from courses.filters import FilterByCourse, StatusFilter
from courses.forms import CourseForm


class StudentCourseList(admin.TabularInline):
    model = models.StudentCourse
    fields = ('student_display', 'created_at', 'message_student', 'has_paid')
    readonly_fields = ('student_display', 'created_at', 'message_student')
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

    verbose_name_plural = 'Студенты'


class LessonList(admin.StackedInline):
    model = models.Lesson
    classes = ('collapse',)
    extra = 1


@admin.register(models.Course)
class CourseAdmin(admin.ModelAdmin):
    list_display = ('id', '__str__', 'course_info',
                    'company', 'student_count')
    list_display_links = ('__str__',)
    readonly_fields = ('date_started', 'date_finished', 'created_at',)
    exclude = ('week_size', 'lesson_count',)
    list_per_page = 20
    search_fields = ('id', 'name')
    list_filter = ('company',)
    inlines = (LessonList, StudentCourseList, )
    ordering = ('id',)
    date_hierarchy = 'created_at'
    form = CourseForm
    change_form_template = 'courses/admin/change_form.html'
    actions = ('duplicate',)

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

    @admin.display(description='Количество студентов')
    def student_count(self, course):
        return course.student_set.count()


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
        if request.GET.get('course_id'):
            return ('lesson_name', 'lesson_received', 'lesson_watched',
                    'hw_submitted', 'details',)
        else:
            return ('student',)

    def get_actions(self, request):
        actions = super(StudentProgress, self).get_actions(request)
        if request.GET.get('lesson__id__exact'):
            self.actions.append(self.send_message)
        return actions

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
            f'admin:{app}_{model}_changelist'
        )
        changeform_url += f'?lesson__id__exact={instance.lesson.id}'
        return mark_safe(f'<a href="{changeform_url}">Посмотреть</a>')

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
