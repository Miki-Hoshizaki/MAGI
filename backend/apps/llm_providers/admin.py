from django.contrib import admin
from .models import LLMProvider, LLMModel


@admin.register(LLMProvider)
class LLMProviderAdmin(admin.ModelAdmin):
    list_display = ('name', 'provider_type', 'is_active', 'priority', 'created_at')
    list_filter = ('provider_type', 'is_active')
    search_fields = ('name',)
    ordering = ('-priority', '-created_at')
    readonly_fields = ('created_at', 'updated_at')


@admin.register(LLMModel)
class LLMModelAdmin(admin.ModelAdmin):
    list_display = ('name', 'provider', 'model_name', 'is_active', 'created_at')
    list_filter = ('provider', 'is_active')
    search_fields = ('name', 'model_name')
    ordering = ('-created_at',)
    readonly_fields = ('created_at', 'updated_at')
