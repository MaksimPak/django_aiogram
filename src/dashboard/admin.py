import os

from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.http import HttpResponseRedirect
from django.shortcuts import render
import requests

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
    actions = ('send_message',)

    def send_message(self, request, qs):
        clients = models.Client.objects.all()

        if 'send' in request.POST:
            for client in clients:
                url = f"https://api.telegram.org/bot{os.getenv('BOT_TOKEN')}/sendMessage?chat_id={client.tg_id}&text={request.POST['message']}"
                requests.get(url)
            return HttpResponseRedirect(request.get_full_path())

        return render(request, 'dashboard/send_intermediate.html', context={'clients': clients})
    send_message.short_description = 'Массовая рассылка'


admin.site.register(models.User, UserAdmin)
admin.site.register(models.Lead, LeadAdmin)
admin.site.register(models.Client, ClientAdmin)
admin.site.register(models.Course)