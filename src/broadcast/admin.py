from django.contrib import admin

from broadcast import models


class Recipients(admin.TabularInline):
    model = models.MessageHistory
    fields = ('contact', 'delivered',)


@admin.register(models.Message)
class HistoryAdmin(admin.ModelAdmin):
    list_display = ('id', 'text', )
    list_per_page = 10
    inlines = (Recipients,)

    def has_add_permission(self, request, obj=None):
        return False

    def has_change_permission(self, request, obj=None):
        return False
