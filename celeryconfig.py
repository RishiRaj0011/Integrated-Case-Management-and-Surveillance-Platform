"""
Celery Configuration - Scalable Video Processing
Max 4 concurrent videos, memory-aware queueing
"""
from kombu import Queue

# Broker and backend
broker_url = 'redis://localhost:6379/0'
result_backend = 'redis://localhost:6379/0'

# Task routing
task_routes = {
    'tasks.analyze_footage_match': {'queue': 'video_analysis'},
    'tasks.analyze_batch_parallel': {'queue': 'batch_processing'},
    'tasks.process_batch_with_progress': {'queue': 'batch_processing'},
    'tasks.process_footage_high_precision': {'queue': 'high_precision'},
    'tasks.process_batch_high_precision': {'queue': 'high_precision'},
}

# Queue definitions
task_queues = (
    Queue('video_analysis', routing_key='video.#'),
    Queue('batch_processing', routing_key='batch.#'),
    Queue('high_precision', routing_key='precision.#'),
)

# CRITICAL: Max 4 concurrent workers to prevent RAM exhaustion
worker_concurrency = 4
worker_prefetch_multiplier = 1  # Process one task at a time per worker

# Task settings
task_serializer = 'json'
result_serializer = 'json'
accept_content = ['json']
timezone = 'UTC'
enable_utc = True

# Task time limits
task_soft_time_limit = 3600  # 1 hour
task_time_limit = 7200  # 2 hours hard limit

# Result expiration
result_expires = 86400  # 24 hours

# Task acknowledgment
task_acks_late = True
task_reject_on_worker_lost = True

# Memory management
worker_max_tasks_per_child = 10  # Restart worker after 10 tasks to prevent memory leaks
worker_max_memory_per_child = 2000000  # 2GB per worker max

# Logging
worker_log_format = '[%(asctime)s: %(levelname)s/%(processName)s] %(message)s'
worker_task_log_format = '[%(asctime)s: %(levelname)s/%(processName)s][%(task_name)s(%(task_id)s)] %(message)s'
