import os

from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.http import HttpResponseRedirect
from django.shortcuts import render
import requests

from dashboard import models


class StudentCourseList(admin.TabularInline):
    model = models.StudentCourse
    extra = 1


class LessonCourseList(admin.TabularInline):
    model = models.LessonCourse
    extra = 1


class LeadAdmin(admin.ModelAdmin):
    list_display = ('id', '__str__', 'application_type', 'phone')
    list_per_page = 20
    list_display_links = ('__str__',)
    inlines = (StudentCourseList,)
    search_fields = ('id', 'first_name', 'last_name')
    ordering = ('id',)
    date_hierarchy = 'created_at'


class ClientAdmin(admin.ModelAdmin):
    list_display = ('id', '__str__', 'phone')
    list_per_page = 20
    list_display_links = ('__str__',)
    inlines = (StudentCourseList,)
    actions = ('send_message',)
    search_fields = ('id', 'first_name', 'last_name')
    ordering = ('id',)
    date_hierarchy = 'created_at'

    def send_message(self, request, qs):
        clients = models.Client.objects.all()

        if 'send' in request.POST:
            for client in clients:
                url = f"https://api.telegram.org/bot{os.getenv('BOT_TOKEN')}/sendMessage?chat_id={client.tg_id}&text={request.POST['message']}"
                requests.get(url)
            return HttpResponseRedirect(request.get_full_path())

        return render(request, 'dashboard/send_intermediate.html', context={'clients': clients})
    send_message.short_description = 'Массовая рассылка'


class CourseAdmin(admin.ModelAdmin):
    list_display = ('id', '__str__', 'short_info', 'category', 'difficulty', 'price')
    list_display_links = ('__str__',)
    list_per_page = 20
    search_fields = ('id', 'name')
    list_filter = ('category', 'price',)
    inlines = (StudentCourseList, LessonCourseList)
    ordering = ('id',)
    date_hierarchy = 'created_at'


class LessonAdmin(admin.ModelAdmin):
    list_display = ('id', '__str__', 'info')
    list_display_links = ('__str__',)
    list_per_page = 20
    search_fields = ('id', 'title')
    ordering = ('id',)
    date_hierarchy = 'created_at'


admin.site.register(models.User, UserAdmin)
admin.site.register(models.Lead, LeadAdmin)
admin.site.register(models.Client, ClientAdmin)
admin.site.register(models.Course, CourseAdmin)
admin.site.register(models.Lesson, LessonAdmin)
