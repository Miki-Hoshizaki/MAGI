from rest_framework import serializers
from .models import Task, Vote


class VoteSerializer(serializers.ModelSerializer):
    class Meta:
        model = Vote
        fields = ['id', 'voter_id', 'result', 'reason', 'created_at']
        read_only_fields = ['id', 'created_at']


class TaskSerializer(serializers.ModelSerializer):
    votes = VoteSerializer(many=True, read_only=True)
    
    class Meta:
        model = Task
        fields = ['id', 'request_id', 'status', 'original_request', 
                 'generated_content', 'voters', 'votes', 'created_at', 'updated_at']
        read_only_fields = ['id', 'created_at', 'updated_at']
