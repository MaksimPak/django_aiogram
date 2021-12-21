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
    actions = ('send_cert',)
    list_per_page = 10

    @admin.display(description='Курс')
    def course(self, cert):
        return cert.template.course

    @admin.display(description='Отправить сертификаты')
    def send_cert(self, request, certs):
        url = os.environ.get('DOMAIN') + '/broadcast/send/'
        referer = os.environ.get('DOMAIN') + request.get_full_path()
        for cert in certs:
            headers = {'X-CSRFToken': get_token(request), 'Referer': referer}
            data = {
                '_selected_action': cert.student.id,
                'text': f'Сертификат по курсу {cert.template.course}'
            }
            requests.post(url, data=data, headers=headers,
                          files={'image': cert.generated_cert.read()}, cookies=request.COOKIES)


