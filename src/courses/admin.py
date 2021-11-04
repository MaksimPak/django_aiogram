from django import forms
from django.contrib import admin, messages

from django.template.loader import render_to_string
from django.utils.html import format_html

from courses import models
from courses.filters import FilterByCourse
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
    actions = ['duplicate']

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
    list_display = ('lesson_name',)
    list_filter = (FilterByCourse,)

    @admin.display(description='Урок')
    def lesson_name(self, instance):
        return instance.lesson.name

    def get_queryset(self, request):
        if request.GET.get('course_id'):
            qs = super(StudentProgress, self).get_queryset(request)
            qs = qs.filter(lesson__course_id=request.GET['course_id'])
            return qs
        return models.StudentLesson.objects.none()

    def get_model_perms(self, request):
        """
        Return empty perms dict thus hiding the model from admin index.
        """
        return {}

# @admin.register(models.Lesson)
# class LessonAdmin(admin.ModelAdmin):
#     list_display = ('id', '__str__', 'lesson_info', 'video', 'course')
#     list_display_links = ('__str__',)
#     list_per_page = 20
#     readonly_fields = ('date_sent',)
#     search_fields = ('id', 'title', 'course')
#     list_filter = ('course',)
#     ordering = ('id',)
#     date_hierarchy = 'created_at'
#
#     class Media:
#         js = (
#             'dashboard/js/lesson_admin.js',
#         )
#
#
