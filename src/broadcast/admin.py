import datetime

from django.contrib import admin

from broadcast import models


class Recipients(admin.TabularInline):
    model = models.MessageHistory
    fields = ('contact', 'delivered', 'response', 'delta')
    readonly_fields = ('delta',)

    @admin.display(description='Время ответа')
    def delta(self, instance):
        delta = instance.updated_at - instance.message.delivery_end_time
        return self.strfdelta(delta) if delta > datetime.timedelta(0) else '-'

    @staticmethod
    def strfdelta(delta):
        days = delta.days
        hours, rem = divmod(delta.seconds, 3600)
        mins, seconds = divmod(rem, 60)

        return f'{days} дней, {hours} часов, {mins} мин, {delta.seconds} сек'


@admin.register(models.Message)
class HistoryAdmin(admin.ModelAdmin):
    list_display = ('id', 'text', )
    list_per_page = 10
    inlines = (Recipients,)

    def has_add_permission(self, request, obj=None):
        return False

    def has_change_permission(self, request, obj=None):
        return False
