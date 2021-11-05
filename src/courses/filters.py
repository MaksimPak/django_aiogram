from django.contrib import admin


class FilterByCourse(admin.SimpleListFilter):
    title = ''
    parameter_name = 'course_id'
    template = "courses/admin/empty_filter.html"

    def lookups(self, request, model_admin):
        return (request.GET.get(self.parameter_name), ''),

    def queryset(self, request, queryset):
        if self.value():
            course_id = self.value()
            qs = queryset.filter(lesson__course_id=course_id)
            return qs


class StatusFilter(admin.SimpleListFilter):
    title = 'Фильтр уроков'
    parameter_name = 'status'

    def lookups(self, request, model_admin):
        return (
            ('sent', 'Получили урок'),
            ('watched', 'Посмотрели урок'),
            ('submitted', 'Сдали домашку'),
        )

    def queryset(self, request, queryset):
        lesson_id = request.GET.get('lesson__id__exact')
        if self.value() == 'sent':
            return queryset.filter(date_sent__isnull=False,
                                   lesson_id=lesson_id)

        if self.value() == 'watched':
            return queryset.filter(date_watched__isnull=False,
                                   lesson_id=lesson_id)

        if self.value() == 'submitted':
            return queryset.filter(homework_sent__isnull=False,
                                   lesson_id=lesson_id)

