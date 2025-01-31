from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from .models import LLMProvider, LLMModel
from .serializers import LLMProviderSerializer, LLMModelSerializer


class LLMProviderViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing LLM providers.
    Only admin users can create, update, or delete providers.
    """
    queryset = LLMProvider.objects.all()
    serializer_class = LLMProviderSerializer
    permission_classes = [IsAuthenticated]

    def get_permissions(self):
        """
        Override to ensure only admin users can modify providers.
        """
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            return [IsAdminUser()]
        return super().get_permissions()

    @action(detail=True, methods=['post'])
    def toggle_active(self, request, pk=None):
        """
        Toggle the active status of a provider.
        """
        provider = self.get_object()
        provider.is_active = not provider.is_active
        provider.save()
        return Response({'status': 'success', 'is_active': provider.is_active})

    @action(detail=True)
    def models(self, request, pk=None):
        """
        Get all models for a specific provider.
        """
        provider = self.get_object()
        models = provider.models.all()
        serializer = LLMModelSerializer(models, many=True)
        return Response(serializer.data)


class LLMModelViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing LLM models.
    Only admin users can create, update, or delete models.
    """
    queryset = LLMModel.objects.all()
    serializer_class = LLMModelSerializer
    permission_classes = [IsAuthenticated]

    def get_permissions(self):
        """
        Override to ensure only admin users can modify models.
        """
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            return [IsAdminUser()]
        return super().get_permissions()

    @action(detail=True, methods=['post'])
    def toggle_active(self, request, pk=None):
        """
        Toggle the active status of a model.
        """
        model = self.get_object()
        model.is_active = not model.is_active
        model.save()
        return Response({'status': 'success', 'is_active': model.is_active})
