from rest_framework import serializers
from .models import LLMProvider, LLMModel


class LLMModelSerializer(serializers.ModelSerializer):
    """
    Serializer for LLM models.
    """
    class Meta:
        model = LLMModel
        fields = ['id', 'name', 'model_name', 'description', 'features',
                 'max_tokens', 'is_active', 'created_at', 'updated_at']
        read_only_fields = ['id', 'created_at', 'updated_at']


class LLMProviderSerializer(serializers.ModelSerializer):
    """
    Serializer for LLM providers.
    """
    models = LLMModelSerializer(many=True, read_only=True)

    class Meta:
        model = LLMProvider
        fields = ['id', 'name', 'provider_type', 'base_url', 'is_active',
                 'priority', 'models', 'created_at', 'updated_at']
        read_only_fields = ['id', 'created_at', 'updated_at']

    def create(self, validated_data):
        api_key = self.context['request'].data.get('api_key')
        if not api_key:
            raise serializers.ValidationError({'api_key': 'This field is required.'})
        
        # Create provider with API key
        provider = LLMProvider.objects.create(
            **validated_data,
            api_key=api_key  # Will be encrypted in model's save method
        )
        return provider
