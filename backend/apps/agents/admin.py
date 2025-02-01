"""
Django admin interface for Agent models.
"""
from django.contrib import admin
from .models import Agent, AgentRun

@admin.register(Agent)
class AgentAdmin(admin.ModelAdmin):
    list_display = ('name', 'llm_model', 'is_active', 'weight', 'created_at')
    list_filter = ('is_active', 'llm_model')
    search_fields = ('name', 'description')
    readonly_fields = ('id', 'created_at', 'updated_at')
    fieldsets = (
        (None, {
            'fields': ('id', 'name', 'description', 'llm_model')
        }),
        ('Prompts', {
            'fields': ('system_prompt', 'user_prompt_template')
        }),
        ('Configuration', {
            'fields': (
                'temperature',
                'max_tokens',
                'stop_sequences',
                'weight',
                'is_active'
            )
        }),
        ('Metadata', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )

@admin.register(AgentRun)
class AgentRunAdmin(admin.ModelAdmin):
    list_display = ('id', 'agent', 'session_id', 'started_at', 'completed_at')
    list_filter = ('agent', 'started_at')
    search_fields = ('session_id', 'error')
    readonly_fields = (
        'id',
        'agent',
        'session_id',
        'request_data',
        'response_data',
        'error',
        'started_at',
        'completed_at'
    )
    
    def has_add_permission(self, request):
        return False  # AgentRun objects should only be created programmatically
