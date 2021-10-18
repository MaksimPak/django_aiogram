import os

from django.contrib import admin

from assets import models


@admin.register(models.Asset)
class AssetAdmin(admin.ModelAdmin):
    list_display = ('id', 'title', 'desc', 'access_level',)
    list_display_links = ('title',)
    readonly_fields = ('link', 'count', 'command')
    list_per_page = 20

    @admin.display(description='Линк')
    def link(self, instance):
        return f'https://t.me/{os.getenv("BOT_NAME")}?start=asset_{instance.id}'

    @admin.display(description='Подсчет')
    def count(self, isntance):
        return isntance.contactasset_set.count()

    @admin.display(description='Команда вызова')
    def command(self, instance):
        return f'/asset_{instance.id}'
