from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import Task, Vote
from .tasks import distribute_task_to_voters, aggregate_voting_results


@receiver(post_save, sender=Task)
def handle_task_creation(sender, instance, created, **kwargs):
    """
    Trigger task distribution when a new task is created
    """
    if created:
        distribute_task_to_voters.delay(str(instance.id))


@receiver(post_save, sender=Vote)
def handle_vote_creation(sender, instance, created, **kwargs):
    """
    Check if results aggregation is needed when a new vote is created
    """
    if created:
        task = instance.task
        vote_count = task.votes.count()
        if vote_count == len(task.voters):
            aggregate_voting_results.delay(str(task.id))
