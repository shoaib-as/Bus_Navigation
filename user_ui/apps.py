from django.apps import AppConfig


class UserUiConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'user_ui'

class UserUiConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'user_ui'

    def ready(self):
        import user_ui.signals  # ✅ ensures signals are active
