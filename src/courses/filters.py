from datetime import date

from django.contrib import admin
from django.utils.translation import gettext_lazy as _


class FilterByCourse(admin.SimpleListFilter):
    title = 'Список курсов'
    parameter_name = 'course_id'

    def lookups(self, request, model_admin):
        return (request.GET.get(self.parameter_name), ''),

    def queryset(self, request, queryset):
        return queryset
