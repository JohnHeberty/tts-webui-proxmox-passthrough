"""
Prometheus Metrics for Monitoring
Sprint 7 - Monitoring & Observability
"""

from prometheus_client import Counter, Histogram, Gauge, generate_latest, CONTENT_TYPE_LATEST
from fastapi import APIRouter, Response
from functools import wraps
import time
from typing import Callable

router = APIRouter(tags=["monitoring"])

# ==================== METRICS DEFINITIONS ====================

# Request counters
http_requests_total = Counter(
    'http_requests_total',
    'Total HTTP requests',
    ['method', 'endpoint', 'status']
)

# TTS job counters
tts_jobs_created_total = Counter(
    'tts_jobs_created_total',
    'Total TTS jobs created',
    ['engine', 'language']
)

tts_jobs_completed_total = Counter(
    'tts_jobs_completed_total',
    'Total TTS jobs completed successfully',
    ['engine']
)

tts_jobs_failed_total = Counter(
    'tts_jobs_failed_total',
    'Total TTS jobs failed',
    ['engine', 'error_type']
)

# Training metrics
training_jobs_active = Gauge(
    'training_jobs_active',
    'Number of active training jobs'
)

training_epoch_duration_seconds = Histogram(
    'training_epoch_duration_seconds',
    'Training epoch duration in seconds',
    buckets=[10, 30, 60, 120, 300, 600, 1800, 3600]
)

# Voice cloning metrics
voice_clone_requests_total = Counter(
    'voice_clone_requests_total',
    'Total voice cloning requests'
)

voice_clone_duration_seconds = Histogram(
    'voice_clone_duration_seconds',
    'Voice cloning duration in seconds',
    buckets=[1, 2, 5, 10, 20, 30, 60]
)

# Audio processing metrics
audio_generation_duration_seconds = Histogram(
    'audio_generation_duration_seconds',
    'Audio generation duration in seconds',
    buckets=[0.5, 1, 2, 5, 10, 20, 30]
)

audio_file_size_bytes = Histogram(
    'audio_file_size_bytes',
    'Generated audio file size in bytes',
    buckets=[10000, 50000, 100000, 500000, 1000000, 5000000, 10000000]
)

# GPU metrics
gpu_memory_usage_bytes = Gauge(
    'gpu_memory_usage_bytes',
    'GPU memory usage in bytes',
    ['gpu_id']
)

gpu_utilization_percent = Gauge(
    'gpu_utilization_percent',
    'GPU utilization percentage',
    ['gpu_id']
)

# Cache metrics
cache_hits_total = Counter(
    'cache_hits_total',
    'Total cache hits',
    ['cache_type']
)

cache_misses_total = Counter(
    'cache_misses_total',
    'Total cache misses',
    ['cache_type']
)

# API latency
api_latency_seconds = Histogram(
    'api_latency_seconds',
    'API endpoint latency in seconds',
    ['method', 'endpoint'],
    buckets=[0.01, 0.05, 0.1, 0.5, 1, 2, 5, 10]
)

# ==================== HELPER FUNCTIONS ====================

def track_request(method: str, endpoint: str, status: int):
    """Track HTTP request"""
    http_requests_total.labels(method=method, endpoint=endpoint, status=status).inc()


def track_tts_job_created(engine: str, language: str):
    """Track TTS job creation"""
    tts_jobs_created_total.labels(engine=engine, language=language).inc()


def track_tts_job_completed(engine: str):
    """Track TTS job completion"""
    tts_jobs_completed_total.labels(engine=engine).inc()


def track_tts_job_failed(engine: str, error_type: str):
    """Track TTS job failure"""
    tts_jobs_failed_total.labels(engine=engine, error_type=error_type).inc()


def track_audio_generation(duration: float, file_size: int):
    """Track audio generation"""
    audio_generation_duration_seconds.observe(duration)
    audio_file_size_bytes.observe(file_size)


def track_cache_access(cache_type: str, hit: bool):
    """Track cache access"""
    if hit:
        cache_hits_total.labels(cache_type=cache_type).inc()
    else:
        cache_misses_total.labels(cache_type=cache_type).inc()


def track_gpu_metrics(gpu_id: int, memory_used: int, utilization: float):
    """Track GPU metrics"""
    gpu_memory_usage_bytes.labels(gpu_id=str(gpu_id)).set(memory_used)
    gpu_utilization_percent.labels(gpu_id=str(gpu_id)).set(utilization)


# ==================== DECORATORS ====================

def track_latency(endpoint: str):
    """Decorator to track endpoint latency"""
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args, **kwargs):
            start_time = time.time()
            try:
                result = await func(*args, **kwargs)
                duration = time.time() - start_time
                api_latency_seconds.labels(method="POST", endpoint=endpoint).observe(duration)
                return result
            except Exception as e:
                duration = time.time() - start_time
                api_latency_seconds.labels(method="POST", endpoint=endpoint).observe(duration)
                raise
        return wrapper
    return decorator


# ==================== ENDPOINTS ====================

@router.get("/metrics")
async def metrics():
    """
    Prometheus metrics endpoint
    
    This endpoint exposes metrics in Prometheus format for scraping.
    
    Configure Prometheus to scrape this endpoint:
    ```yaml
    scrape_configs:
      - job_name: 'tts-webui'
        static_configs:
          - targets: ['localhost:8005']
        metrics_path: '/metrics'
        scrape_interval: 15s
    ```
    """
    return Response(content=generate_latest(), media_type=CONTENT_TYPE_LATEST)


@router.get("/health")
async def health():
    """
    Health check endpoint for load balancers
    
    Returns 200 OK if service is healthy.
    """
    from datetime import datetime
    
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "service": "tts-webui"
    }


@router.get("/ready")
async def readiness():
    """
    Readiness check endpoint for Kubernetes
    
    Returns 200 OK if service is ready to accept traffic.
    Checks:
    - GPU availability
    - Redis connection
    - Model loading status
    """
    import torch
    from app.main import job_store
    
    checks = {
        "gpu": torch.cuda.is_available(),
        "redis": False,
        "models": True  # TODO: Check if models are loaded
    }
    
    try:
        job_store.redis.ping()
        checks["redis"] = True
    except Exception:
        pass
    
    all_ready = all(checks.values())
    
    return {
        "ready": all_ready,
        "checks": checks
    }, 200 if all_ready else 503


# ==================== BACKGROUND GPU MONITORING ====================

async def monitor_gpu_metrics():
    """
    Background task to monitor GPU metrics
    
    Call this periodically (e.g., every 10 seconds) to update GPU metrics.
    """
    try:
        import torch
        if torch.cuda.is_available():
            for i in range(torch.cuda.device_count()):
                memory_allocated = torch.cuda.memory_allocated(i)
                memory_reserved = torch.cuda.memory_reserved(i)
                utilization = torch.cuda.utilization(i) if hasattr(torch.cuda, 'utilization') else 0
                
                track_gpu_metrics(i, memory_allocated, utilization)
    except Exception as e:
        print(f"Error monitoring GPU metrics: {e}")


# ==================== MIDDLEWARE ====================

class PrometheusMiddleware:
    """
    Middleware to automatically track all HTTP requests
    
    Usage in main.py:
    ```python
    from app.metrics import PrometheusMiddleware
    app.add_middleware(PrometheusMiddleware)
    ```
    """
    def __init__(self, app):
        self.app = app
    
    async def __call__(self, scope, receive, send):
        if scope["type"] == "http":
            start_time = time.time()
            
            async def send_wrapper(message):
                if message["type"] == "http.response.start":
                    duration = time.time() - start_time
                    method = scope["method"]
                    path = scope["path"]
                    status = message["status"]
                    
                    # Track request
                    track_request(method, path, status)
                    api_latency_seconds.labels(method=method, endpoint=path).observe(duration)
                
                await send(message)
            
            await self.app(scope, receive, send_wrapper)
        else:
            await self.app(scope, receive, send)
