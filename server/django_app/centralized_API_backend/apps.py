from django.apps import AppConfig

class CentralizedApiBackendConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "centralized_API_backend"

    def ready(self):
        import centralized_API_backend.signals
