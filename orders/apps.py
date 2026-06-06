from django.apps import AppConfig


class OrdersConfig(AppConfig):
    name = 'orders'
    default_auto_field = 'django.db.models.BigAutoField'

    def ready(self):
        """
        Import signals module so @receiver decorators are registered
        when Django starts up. Without this, signals are never connected.
        """
        import orders.signals  # noqa: F401
