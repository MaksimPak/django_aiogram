from celery.result import GroupResult
from django.contrib import admin, messages

# Register your models here.
from broadcast import models
from users import models as users_models

#
# class PromotionReport(admin.TabularInline):
#     model = models.SendingReport
#     fields = ('lang', 'sent', 'received', 'failed', 'date_sent', 'report_status')
#     readonly_fields = ('lang', 'sent', 'received', 'failed', 'date_sent', 'report_status')
#     can_delete = False
#     extra = 0
#     classes = ('collapse',)
#
#     @admin.display(description='Дата отправки')
#     def date_sent(self, instance):
#         return instance.created_at
#
#     @admin.display(description='Статус отправки')
#     def report_status(self, instance):
#         if instance.status:
#             return instance.status
#
#         result = GroupResult.restore(instance.celery_id)
#         if not result:
#             return 'Нет статуса'
#
#         if result.ready():
#             instance.status = 'Отправлено'
#             instance.save()
#             return instance.status
#         else:
#             return 'Отправляется'
#
#     def has_add_permission(self, request, obj):
#         return False
#
#
# @admin.register(models.Promotion)
# class PromoAdmin(admin.ModelAdmin):
#     list_display = ('id', 'title', 'description', 'course', 'counter', 'link')
#     list_per_page = 10
#     list_display_links = ('title',)
#     readonly_fields = ('link', 'command',)
#     actions = ('duplicate',)
#     inlines = (PromotionReport,)
#
#     @admin.display(description='Команда для вызова')
#     def command(self, instance):
#         return f'/promo_{instance.unique_code}'
#
#     @admin.display(description='Дублировать (Максимум 3)')
#     def duplicate(self, request, promos):
#         if len(promos) > 3:
#             self.message_user(request, 'Нельзя дублировать больше 3 форм', messages.ERROR)
#             return
#
#         for promo in promos:
#             promo.pk = None
#             promo.unique_code = ''
#             promo.invite_link = ''
#             promo.save()
#
#         self.message_user(request, '{0} промо были успешно дублированны'.format(promos.count()), messages.SUCCESS)
#
#     def change_view(self, request, object_id, form_url='', extra_context=None):
#         extra_context = extra_context or {}
#
#         extra_context['student_model'] = users_models.Student
#         return super().change_view(
#             request, object_id, form_url, extra_context=extra_context,
#         )