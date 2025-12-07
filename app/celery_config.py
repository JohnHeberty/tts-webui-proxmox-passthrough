"""
Configuração do Celery para processamento assíncrono
"""
from celery import Celery
from .settings import get_settings

settings = get_settings()

# Cria instância Celery
celery_app = Celery(
    'audio_voice_worker',
    broker=settings.celery_broker_url,
    backend=settings.celery_result_backend
)

# Configurações
celery_app.conf.update(
    task_serializer='json',
    result_serializer='json',
    accept_content=['json'],
    timezone='America/Sao_Paulo',
    enable_utc=True,
    task_track_started=True,
    task_time_limit=settings.task_timeout,
    task_soft_time_limit=settings.task_timeout - 60,
    worker_prefetch_multiplier=1,
    worker_max_tasks_per_child=10,
    
    # Roteamento de tasks
    task_routes={
        'app.celery_tasks.dubbing_task': {'queue': 'audio_voice_queue'},
        'app.celery_tasks.clone_voice_task': {'queue': 'audio_voice_queue'},
    },
    
    # Retry policy
    task_autoretry_for=(Exception,),
    task_max_retries=3,
    task_default_retry_delay=60,  # 1 minuto
    
    # Conexão com broker
    broker_connection_retry_on_startup=True,
)

# ✅ IMPORTANTE: Importa tasks para registrá-las no Celery
# Isso garante que o worker reconheça as tasks ao inicializar
from . import celery_tasks  # noqa: F401
