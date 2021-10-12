from datetime import date

from django.contrib import admin


class StatusFilter(admin.SimpleListFilter):
    title = 'Сортировка статуса'

    parameter_name = 'status'

    def lookups(self, request, model_admin):
        return (
            ('contact', 'ТГ'),
            ('lead', 'Лид'),
            ('client', 'Клиент'),
        )

    def queryset(self, request, queryset):
        if self.value() == 'contact':
            return queryset.filter(student__isnull=True)
        if self.value() == 'lead':
            return queryset.filter(student__isnull=False, student__is_client=False)
        if self.value() == 'client':
            return queryset.filter(student__isnull=False, student__is_client=True)
