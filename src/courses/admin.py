from django.contrib import admin, messages

# Register your models here.
from django.template.loader import render_to_string
from django.utils.html import format_html

from courses import models


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

    def has_add_permission(self, request, course):
        if course:
            return False if course.is_started else True
        return True


@admin.register(models.Course)
class CourseAdmin(admin.ModelAdmin):
    list_display = ('id', '__str__', 'course_info', 'is_started', 'learning_centre', 'difficulty', 'price', 'student_count')
    list_display_links = ('__str__',)
    list_editable = ('is_started',)
    readonly_fields = ('date_started', 'date_finished', 'created_at',)
    exclude = ('week_size', 'lesson_count',)
    list_per_page = 20
    search_fields = ('id', 'name')
    list_filter = ('learning_centre', 'price',)
    inlines = (LessonList, StudentCourseList, )
    ordering = ('id',)
    date_hierarchy = 'created_at'
    change_form_template = 'courses/admin/change_form.html'
    actions = ['duplicate']

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

    @admin.display(description='Дублировать (Максимум 3)')
    def duplicate(self, request, courses):
        if len(courses) > 3:
            self.message_user(request, 'Нельзя дублировать больше 3 курсов', messages.ERROR)
            return

        for course in courses:
            lessons = list(course.lesson_set.all())
            course.pk = None

            course.is_started = False
            course.is_finished = False
            course.hashtag = ''
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


