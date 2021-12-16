import datetime

from django.contrib import admin
from django.db.models import F

from broadcast import models


class Recipients(admin.TabularInline):
    model = models.MessageHistory
    fields = ('contact', 'delivered', 'response', 'delta')
    readonly_fields = ('delta',)

    def get_queryset(self, request):
        qs = super(Recipients, self).get_queryset(request)
        qs = qs.annotate(_delta=F('updated_at') - F('message__delivery_end_time'))
        qs = qs.order_by('-_delta')
        return qs

    @admin.display(description='Время ответа')
    def delta(self, instance):
        if instance._delta and instance._delta > datetime.timedelta(0):
            return self.strfdelta(instance._delta)
        return '-'

    @staticmethod
    def strfdelta(delta):
        days = delta.days
        hours, rem = divmod(delta.seconds, 3600)
        mins, seconds = divmod(rem, 60)

        return f'{days} дней, {hours} часов, {mins} мин, {seconds} сек'


@admin.register(models.Message)
class HistoryAdmin(admin.ModelAdmin):
    list_display = ('id', 'text', 'recipients_count')
    readonly_fields = ('recipients_count',)
    list_per_page = 10
    inlines = (Recipients,)
    change_form_template = 'broadcast/admin/message_form_list.html'

    @admin.display(description='Кол-во получателей')
    def recipients_count(self, instance):
        return instance.messagehistory_set.count()

    def has_add_permission(self, request, obj=None):
        return False

    def has_change_permission(self, request, obj=None):
        return False
