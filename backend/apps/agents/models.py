"""
Agent models for the MAGI system.
"""
from django.db import models
import uuid
from django.contrib.postgres.fields import JSONField
from apps.llm_providers.models import LLMModel

class Agent(models.Model):
    """
    Agent model represents a configurable entity that can process user requests
    using specific prompts and an LLM model.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    llm_model = models.ForeignKey(
        LLMModel,
        on_delete=models.PROTECT,
        related_name='agents'
    )
    
    # Agent configuration
    system_prompt = models.TextField(
        help_text="System prompt that defines the agent's role and behavior"
    )
    user_prompt_template = models.TextField(
        help_text="Template for formatting user requests"
    )
    temperature = models.FloatField(
        default=0.7,
        help_text="Controls randomness in the model's output"
    )
    max_tokens = models.IntegerField(
        null=True,
        blank=True,
        help_text="Maximum tokens for response. If null, uses model's default"
    )
    
    # Agent behavior settings
    stop_sequences = models.JSONField(
        default=list,
        help_text="Sequences that will stop the model's generation"
    )
    is_active = models.BooleanField(default=True)
    weight = models.FloatField(
        default=1.0,
        help_text="Weight for this agent's vote in the final decision"
    )
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['is_active']),
        ]
    
    def __str__(self):
        return f"{self.name} ({self.llm_model})"
    
    def format_prompt(self, user_request: str) -> str:
        """
        Format the user request using the agent's prompt template.
        
        Args:
            user_request: The raw user request
            
        Returns:
            str: The formatted prompt
        """
        return self.user_prompt_template.format(
            user_request=user_request
        )
    
    def get_llm_parameters(self) -> dict:
        """
        Get the parameters for LLM API call.
        
        Returns:
            dict: Parameters for the LLM API call
        """
        params = {
            'temperature': self.temperature,
            'stop': self.stop_sequences if self.stop_sequences else None,
        }
        
        if self.max_tokens:
            params['max_tokens'] = min(
                self.max_tokens,
                self.llm_model.max_tokens
            )
            
        return params


class AgentRun(models.Model):
    """
    Represents a single run of an agent on a specific request.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    agent = models.ForeignKey(
        Agent,
        on_delete=models.PROTECT,
        related_name='runs'
    )
    session_id = models.UUIDField()
    request_data = models.JSONField()
    response_data = models.JSONField(null=True)
    error = models.TextField(null=True, blank=True)
    started_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True)
    
    class Meta:
        ordering = ['-started_at']
        indexes = [
            models.Index(fields=['session_id']),
            models.Index(fields=['started_at']),
        ]
    
    def __str__(self):
        return f"Run {self.id} for Agent {self.agent.name}"
