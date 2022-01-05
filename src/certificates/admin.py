import os

import requests
from django.contrib import admin
from django.middleware import csrf
from django.middleware.csrf import get_token

from certificates import models

# Register your models here.


@admin.register(models.CertTemplate)
class TemplatesAdmin(admin.ModelAdmin):
    list_display = ('id', 'course', 'template')
    list_per_page = 10


@admin.register(models.Certificate)
class CertificateAdmin(admin.ModelAdmin):
    list_display = ('id', 'student', 'course')
    readonly_fields = ('generated_cert',)
    list_filter = ('template__course',)
    list_per_page = 10

    @admin.display(description='Курс')
    def course(self, cert):
        return cert.template.course
