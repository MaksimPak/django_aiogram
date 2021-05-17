from django.apps import AppConfig


class DashboardConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'dashboard'

    def ready(self):
        # noinspection PyUnresolvedReferences
        from . import signals
        # from . import scheduler
        # scheduler.start()
