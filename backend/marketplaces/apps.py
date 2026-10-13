from django.apps import AppConfig


class MarketplacesConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "marketplaces"

    def ready(self):
        from . import signals  # noqa: F401
