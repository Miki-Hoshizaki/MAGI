"""
Django application configuration for agents app.
"""
from django.apps import AppConfig


class AgentsConfig(AppConfig):
    """
    Configuration class for the agents application.
    """
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.agents'
    verbose_name = 'Agents'

    def ready(self):
        """
        Perform initialization when the application is ready.
        """
        try:
            # Import signal handlers
            import apps.agents.signals  # noqa
        except ImportError:
            pass
