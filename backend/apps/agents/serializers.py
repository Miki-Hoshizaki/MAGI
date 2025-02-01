"""
Serializers for Agent models.
"""
from rest_framework import serializers
from .models import Agent, AgentRun
from apps.llm_providers.models import LLMModel

class AgentSerializer(serializers.ModelSerializer):
    """
    Serializer for the Agent model.
    """
    llm_model_name = serializers.CharField(source='llm_model.name', read_only=True)
    
    class Meta:
        model = Agent
        fields = (
            'id',
            'name',
            'description',
            'llm_model',
            'llm_model_name',
            'system_prompt',
            'user_prompt_template',
            'temperature',
            'max_tokens',
            'stop_sequences',
            'is_active',
            'weight',
            'created_at',
            'updated_at'
        )
        read_only_fields = ('id', 'created_at', 'updated_at')
    
    def validate_llm_model(self, value):
        """
        Validate that the LLM model is active.
        """
        if not value.is_active:
            raise serializers.ValidationError(
                "Cannot use inactive LLM model"
            )
        return value
    
    def validate_temperature(self, value):
        """
        Validate temperature is between 0 and 1.
        """
        if not 0 <= value <= 1:
            raise serializers.ValidationError(
                "Temperature must be between 0 and 1"
            )
        return value

class AgentRunSerializer(serializers.ModelSerializer):
    """
    Serializer for the AgentRun model.
    """
    agent_name = serializers.CharField(source='agent.name', read_only=True)
    
    class Meta:
        model = AgentRun
        fields = (
            'id',
            'agent',
            'agent_name',
            'session_id',
            'request_data',
            'response_data',
            'error',
            'started_at',
            'completed_at'
        )
        read_only_fields = fields  # All fields are read-only
