from django.apps import AppConfig


class HomeConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'home'

    def ready(self):
        # Registra signals de invalidación de cachés del módulo tipo_usuario
        # (reglas SIESA, normalizaciones, pool de conexiones por fuente).
        from home import signals  # noqa: F401
