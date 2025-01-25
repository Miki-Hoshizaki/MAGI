from django.db import models
import uuid
from django.contrib.postgres.fields import ArrayField


class Task(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('processing', 'Processing'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    request_id = models.CharField(max_length=255, unique=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    original_request = models.TextField()
    generated_content = models.TextField()
    voters = ArrayField(models.CharField(max_length=255), blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['request_id']),
            models.Index(fields=['status']),
            models.Index(fields=['created_at']),
        ]

    def __str__(self):
        return f"Task {self.request_id} ({self.status})"


class Vote(models.Model):
    RESULT_CHOICES = [
        ('pass', 'Pass'),
        ('fail', 'Fail'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    task = models.ForeignKey(Task, on_delete=models.CASCADE, related_name='votes')
    voter_id = models.CharField(max_length=255)
    result = models.CharField(max_length=10, choices=RESULT_CHOICES)
    reason = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['voter_id']),
            models.Index(fields=['result']),
            models.Index(fields=['created_at']),
        ]
        unique_together = ['task', 'voter_id']

    def __str__(self):
        return f"Vote by {self.voter_id} on Task {self.task.request_id}"
