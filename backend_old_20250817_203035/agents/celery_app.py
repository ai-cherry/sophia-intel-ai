"""
Celery Application for SOPHIA Intel Micro-Agent Ecosystem
Orchestrates background processing agents for continuous learning and intelligence
"""

import os
from celery import Celery
from kombu import Queue

# Initialize Celery app
celery_app = Celery('sophia_agents')

# Configuration
celery_app.conf.update(
    # Broker settings (Redis)
    broker_url=os.getenv('REDIS_URL', 'redis://localhost:6379/0'),
    result_backend=os.getenv('REDIS_URL', 'redis://localhost:6379/0'),
    
    # Task settings
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='UTC',
    enable_utc=True,
    
    # Worker settings
    worker_prefetch_multiplier=1,
    task_acks_late=True,
    worker_max_tasks_per_child=1000,
    
    # Queue configuration
    task_routes={
        'sophia_agents.entity_recognition.*': {'queue': 'entity_processing'},
        'sophia_agents.relationship_mapping.*': {'queue': 'graph_updates'},
        'sophia_agents.cross_platform_correlation.*': {'queue': 'data_correlation'},
        'sophia_agents.quality_assurance.*': {'queue': 'quality_control'},
        'sophia_agents.ai_fine_tuning.*': {'queue': 'model_evolution'},
        'sophia_agents.knowledge_extraction.*': {'queue': 'learning'},
        'sophia_agents.insight_generation.*': {'queue': 'insights'},
    },
    
    # Queue definitions
    task_queues=(
        Queue('entity_processing', routing_key='entity_processing'),
        Queue('graph_updates', routing_key='graph_updates'),
        Queue('data_correlation', routing_key='data_correlation'),
        Queue('quality_control', routing_key='quality_control'),
        Queue('model_evolution', routing_key='model_evolution'),
        Queue('learning', routing_key='learning'),
        Queue('insights', routing_key='insights'),
        Queue('default', routing_key='default'),
    ),
    
    # Monitoring
    worker_send_task_events=True,
    task_send_sent_event=True,
    
    # Beat schedule for periodic tasks
    beat_schedule={
        'process-pending-entities': {
            'task': 'sophia_agents.entity_recognition.process_pending_entities',
            'schedule': 300.0,  # Every 5 minutes
        },
        'update-relationship-graph': {
            'task': 'sophia_agents.relationship_mapping.update_relationship_graph',
            'schedule': 600.0,  # Every 10 minutes
        },
        'correlate-cross-platform-data': {
            'task': 'sophia_agents.cross_platform_correlation.correlate_data_sources',
            'schedule': 900.0,  # Every 15 minutes
        },
        'validate-knowledge-quality': {
            'task': 'sophia_agents.quality_assurance.validate_knowledge_quality',
            'schedule': 1800.0,  # Every 30 minutes
        },
        'generate-proactive-insights': {
            'task': 'sophia_agents.insight_generation.generate_proactive_insights',
            'schedule': 3600.0,  # Every hour
        },
        'optimize-model-performance': {
            'task': 'sophia_agents.ai_fine_tuning.optimize_model_performance',
            'schedule': 86400.0,  # Daily
        },
    },
)

# Auto-discover tasks
celery_app.autodiscover_tasks([
    'backend.agents.entity_recognition',
    'backend.agents.relationship_mapping',
    'backend.agents.cross_platform_correlation',
    'backend.agents.quality_assurance',
    'backend.agents.ai_fine_tuning',
    'backend.agents.knowledge_extraction',
    'backend.agents.insight_generation',
])

if __name__ == '__main__':
    celery_app.start()

