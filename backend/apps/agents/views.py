"""
API views for Agent management.
"""
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404
from .models import Agent, AgentRun
from .serializers import AgentSerializer, AgentRunSerializer

class AgentViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing Agents.
    """
    queryset = Agent.objects.all()
    serializer_class = AgentSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        """
        Optionally restricts the returned agents to active ones.
        """
        queryset = Agent.objects.all()
        active_only = self.request.query_params.get('active', False)
        if active_only:
            queryset = queryset.filter(is_active=True)
        return queryset
    
    @action(detail=True, methods=['post'])
    def toggle_active(self, request, pk=None):
        """
        Toggle the active status of an agent.
        """
        agent = self.get_object()
        agent.is_active = not agent.is_active
        agent.save()
        
        return Response({
            'id': agent.id,
            'is_active': agent.is_active
        })

class AgentRunViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet for viewing Agent runs.
    """
    queryset = AgentRun.objects.all()
    serializer_class = AgentRunSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        """
        Optionally filter runs by session_id or agent.
        """
        queryset = AgentRun.objects.all()
        
        session_id = self.request.query_params.get('session_id', None)
        if session_id:
            queryset = queryset.filter(session_id=session_id)
            
        agent_id = self.request.query_params.get('agent_id', None)
        if agent_id:
            queryset = queryset.filter(agent_id=agent_id)
            
        return queryset
    
    @action(detail=False)
    def by_session(self, request):
        """
        Get all runs for a specific session.
        """
        session_id = request.query_params.get('session_id')
        if not session_id:
            return Response(
                {'error': 'session_id is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
            
        runs = self.get_queryset().filter(session_id=session_id)
        serializer = self.get_serializer(runs, many=True)
        return Response(serializer.data)
