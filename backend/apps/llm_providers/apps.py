from django.apps import AppConfig


class LLMProvidersConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.llm_providers'
    verbose_name = 'LLM Providers'

    def ready(self):
        try:
            import apps.llm_providers.signals  # noqa
        except ImportError:
            pass
