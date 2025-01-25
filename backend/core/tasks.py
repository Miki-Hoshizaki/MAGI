from celery import shared_task
from django.db import transaction
from .models import Task


@shared_task
def distribute_task_to_voters(task_id):
    """
    Distribute task to voters
    """
    try:
        task = Task.objects.get(id=task_id)
        task.status = 'processing'
        task.save()
        
        # TODO: Implement specific voter distribution logic
        # 1. Notify voters through WebSocket gateway
        # 2. Wait for voter response
        
        return True
    except Task.DoesNotExist:
        return False
    except Exception as e:
        # Record error and set task status to failed
        task.status = 'failed'
        task.save()
        raise e


@shared_task
def aggregate_voting_results(task_id):
    """
    Aggregate voting results
    """
    try:
        with transaction.atomic():
            task = Task.objects.select_for_update().get(id=task_id)
            votes = task.votes.all()
            
            # Calculate voting results
            pass_votes = votes.filter(result='pass').count()
            fail_votes = votes.filter(result='fail').count()
            
            # Determine final result based on minority obeying majority principle
            total_votes = pass_votes + fail_votes
            if total_votes > 0:
                if fail_votes > pass_votes:
                    task.status = 'failed'
                else:
                    task.status = 'completed'
                task.save()
            
            # TODO: Notify result through WebSocket gateway
            
            return {
                'task_id': str(task.id),
                'status': task.status,
                'pass_votes': pass_votes,
                'fail_votes': fail_votes
            }
    except Task.DoesNotExist:
        return None
    except Exception as e:
        raise e
