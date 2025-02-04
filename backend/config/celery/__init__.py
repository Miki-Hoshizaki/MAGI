from __future__ import absolute_import, unicode_literals
import os
from celery import Celery

# Set the default Django settings module for the 'celery' program.
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')

# Create the celery application
app = Celery('magisys')

# Load task modules from all registered Django apps.
# app.config_from_object('django.conf:settings', namespace='CELERY')
app.config_from_object('config.celery.celeryconfig')

# Include tasks from non-Django apps
app.autodiscover_tasks([
    'tasks.agent_dispatcher',  # include specific task module
    'tasks.dispatcher',  
    'tasks.agent_tasks',
    'apps.core',
    'apps.users',
])

# Optional: Create a debug task
@app.task(bind=True, ignore_result=True)
def debug_task(self):
    print(f'Request: {self.request!r}')