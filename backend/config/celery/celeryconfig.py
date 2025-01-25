import os

# Broker settings
broker_url = os.getenv('REDIS_URL', 'redis://redis:6379/0')
result_backend = os.getenv('REDIS_URL', 'redis://redis:6379/0')

# Task settings
task_serializer = 'json'
result_serializer = 'json'
accept_content = ['json']
timezone = 'UTC'
enable_utc = True

# Task execution settings
task_always_eager = False
task_eager_propagates = True
task_ignore_result = False
task_store_errors_even_if_ignored = True

# Queue settings
task_default_queue = 'default'
task_queues = {
    'default': {
        'exchange': 'default',
        'routing_key': 'default',
    },
    'high_priority': {
        'exchange': 'high_priority',
        'routing_key': 'high_priority',
    },
    'low_priority': {
        'exchange': 'low_priority',
        'routing_key': 'low_priority',
    },
}

# Task routing
task_routes = {
    'core.tasks.*': {'queue': 'default'},
}

# Task result settings
task_ignore_result = False
task_track_started = True
task_time_limit = 5 * 60  # 5 minutes
task_soft_time_limit = 60  # 1 minute

# Worker settings
worker_prefetch_multiplier = 1
worker_max_tasks_per_child = 100
worker_max_memory_per_child = 200000  # 200MB

# Beat settings
beat_schedule = {}