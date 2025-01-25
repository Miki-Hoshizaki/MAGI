from django.test import TestCase
from rest_framework.test import APITestCase
from rest_framework import status
from django.urls import reverse
from .models import Task, Vote


class TaskModelTests(TestCase):
    def setUp(self):
        self.task = Task.objects.create(
            request_id='test-request-1',
            original_request='Test Request',
            generated_content='Test Content',
            voters=['voter1', 'voter2']
        )

    def test_task_creation(self):
        self.assertEqual(self.task.status, 'pending')
        self.assertEqual(len(self.task.voters), 2)

    def test_task_str_representation(self):
        self.assertEqual(str(self.task), f"Task {self.task.request_id} ({self.task.status})")


class VoteModelTests(TestCase):
    def setUp(self):
        self.task = Task.objects.create(
            request_id='test-request-1',
            original_request='Test Request',
            generated_content='Test Content',
            voters=['voter1']
        )
        self.vote = Vote.objects.create(
            task=self.task,
            voter_id='voter1',
            result='pass',
            reason='Test Pass'
        )

    def test_vote_creation(self):
        self.assertEqual(self.vote.result, 'pass')
        self.assertEqual(self.vote.voter_id, 'voter1')

    def test_vote_str_representation(self):
        self.assertEqual(str(self.vote), f"Vote by {self.vote.voter_id} on Task {self.task.request_id}")


class TaskAPITests(APITestCase):
    def setUp(self):
        self.task_data = {
            'request_id': 'test-request-1',
            'original_request': 'Test Request',
            'generated_content': 'Test Content',
            'voters': ['voter1', 'voter2']
        }

    def test_create_task(self):
        url = reverse('task-list')
        response = self.client.post(url, self.task_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Task.objects.count(), 1)
        self.assertEqual(Task.objects.get().request_id, 'test-request-1')

    def test_vote_on_task(self):
        # Create task
        task = Task.objects.create(**self.task_data)
        task.status = 'processing'
        task.save()

        # Submit vote
        url = reverse('task-vote', args=[task.request_id])
        vote_data = {
            'voter_id': 'voter1',
            'result': 'pass',
            'reason': 'Test Pass'
        }
        response = self.client.post(url, vote_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Vote.objects.count(), 1)

    def test_get_task_status(self):
        task = Task.objects.create(**self.task_data)
        url = reverse('task-status', args=[task.request_id])
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['task']['request_id'], task.request_id)
