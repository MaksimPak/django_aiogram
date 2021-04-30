from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from dashboard import models


class CourseList(admin.TabularInline):
    model = models.StudentCourse


class LeadAdmin(admin.ModelAdmin):
    list_display = ('id', '__str__', 'application_type', 'phone')
    list_display_links = ('__str__',)
    inlines = (CourseList,)


class ClientAdmin(admin.ModelAdmin):
    list_display = ('id', '__str__', 'phone')
    list_display_links = ('__str__',)
    inlines = (CourseList,)


admin.site.register(models.User, UserAdmin)
admin.site.register(models.Lead, LeadAdmin)
admin.site.register(models.Client, ClientAdmin)
