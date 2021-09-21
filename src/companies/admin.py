from django.contrib import admin

# Register your models here.
from companies import models


@admin.register(models.LearningCentre)
class LearningCentreAdmin(admin.ModelAdmin):
    list_display = ('id', 'title')
    list_per_page = 10
    list_display_links = ('title',)
