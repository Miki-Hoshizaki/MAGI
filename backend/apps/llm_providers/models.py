from django.db import models
import uuid
from django.contrib.postgres.fields import ArrayField
from django.core.validators import URLValidator


class LLMProvider(models.Model):
    """
    LLM Provider model to store information about different LLM service providers.
    """
    PROVIDER_TYPES = [
        ('openai', 'OpenAI'),
        ('anthropic', 'Anthropic'),
        ('custom', 'Custom')
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255, unique=True)
    provider_type = models.CharField(max_length=20, choices=PROVIDER_TYPES)
    base_url = models.URLField(null=True, blank=True, validators=[URLValidator()])
    api_key = models.TextField()  # Will be encrypted
    is_active = models.BooleanField(default=True)
    priority = models.IntegerField(default=1)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-priority', '-created_at']
        indexes = [
            models.Index(fields=['provider_type']),
            models.Index(fields=['is_active'])
        ]
        verbose_name = 'LLM Provider'
        verbose_name_plural = 'LLM Providers'

    def __str__(self):
        return f"{self.get_provider_type_display()} ({self.name})"

    def save(self, *args, **kwargs):
        # TODO: Implement encryption for api_key
        super().save(*args, **kwargs)


class LLMModel(models.Model):
    """
    LLM Model represents a specific model provided by an LLM Provider.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    provider = models.ForeignKey(LLMProvider, on_delete=models.CASCADE, related_name='models')
    name = models.CharField(max_length=255)  # Display name
    model_name = models.CharField(max_length=255)  # Actual API model name
    description = models.TextField(blank=True)
    features = models.JSONField(default=dict)  # Store model capabilities and features
    max_tokens = models.IntegerField(default=4096)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ['provider', 'model_name']
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['is_active']),
            models.Index(fields=['model_name'])
        ]
        verbose_name = 'LLM Model'
        verbose_name_plural = 'LLM Models'

    def __str__(self):
        return f"{self.provider.name} - {self.name} ({self.model_name})"
