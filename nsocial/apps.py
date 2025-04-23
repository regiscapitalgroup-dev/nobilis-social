from django.apps import AppConfig


class NsocialConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'nsocial'

    def ready(self):
        import nsocial.signals
