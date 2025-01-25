from django.shortcuts import render
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from .models import Task, Vote
from .serializers import TaskSerializer, VoteSerializer


# Create your views here.

class TaskViewSet(viewsets.ModelViewSet):
    queryset = Task.objects.all()
    serializer_class = TaskSerializer
    lookup_field = 'request_id'

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)
        # After creating the task, asynchronously distribute it to voters
        task = serializer.instance
        # TODO: here call distribute_task_to_voters asynchronously
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)

    @action(detail=True, methods=['post'])
    def vote(self, request, request_id=None):
        task = self.get_object()
        if task.status != 'processing':
            return Response(
                {'error': 'Only allowed for tasks with status "processing"'},
                status=status.HTTP_400_BAD_REQUEST
            )

        vote_data = {
            'task': task.id,
            'voter_id': request.data.get('voter_id'),
            'result': request.data.get('result'),
            'reason': request.data.get('reason', '')
        }

        serializer = VoteSerializer(data=vote_data)
        serializer.is_valid(raise_exception=True)
        serializer.save()

        # Check if all voters have voted
        vote_count = task.votes.count()
        if vote_count == len(task.voters):
            # TODO: call aggregate_voting_results asynchronously
            pass

        return Response(serializer.data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=['get'])
    def status(self, request, request_id=None):
        task = self.get_object()
        votes = task.votes.all()
        vote_results = VoteSerializer(votes, many=True).data
        
        response_data = {
            'task': TaskSerializer(task).data,
            'votes': vote_results,
            'total_votes': len(vote_results),
            'expected_votes': len(task.voters) if task.voters else 0
        }
        
        return Response(response_data)
