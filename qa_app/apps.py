from django.apps import AppConfig

class QaAppConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'qa_app'

    def ready(self):
        import qa_app.signals
