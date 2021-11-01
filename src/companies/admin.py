from django.contrib import admin

from companies import models


@admin.register(models.Company)
class CompanyAdmin(admin.ModelAdmin):
    list_display = ('id', 'title')
    list_per_page = 10
    list_display_links = ('title',)
