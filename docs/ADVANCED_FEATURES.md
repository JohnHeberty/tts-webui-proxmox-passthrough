# Advanced Features Guide - Sprint 7

## 📋 Overview

This guide covers the advanced features implemented in Sprint 7:

- ✅ **Batch Processing**: Process multiple TTS requests in one call
- ✅ **Authentication**: JWT tokens and API keys
- ✅ **Monitoring**: Prometheus metrics and health checks
- ⏳ **Voice Morphing**: Blend multiple voices (coming soon)

---

## 🔐 Authentication

### JWT Token Authentication

#### 1. Login to Get Token

```bash
curl -X POST http://localhost:8005/api/v1/advanced/auth/token \
  -H "Content-Type: application/json" \
  -d '{
    "username": "your_username",
    "password": "your_password"
  }'
```

**Response**:
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "expires_in": 86400
}
```

#### 2. Use Token in Requests

```bash
curl -X POST http://localhost:8005/api/v1/advanced/batch-tts \
  -H "Authorization: Bearer YOUR_TOKEN_HERE" \
  -H "Content-Type: application/json" \
  -d '{...}'
```

**Token expires in**: 24 hours (configurable via `JWT_EXPIRATION_HOURS`)

---

### API Key Authentication

#### 1. Create API Key (Requires JWT)

```bash
curl -X POST http://localhost:8005/api/v1/advanced/auth/api-key \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "My Production Key",
    "expires_days": 365
  }'
```

**Response**:
```json
{
  "api_key": "abc123def456...",
  "name": "My Production Key",
  "expires_at": "2025-12-06T10:00:00",
  "warning": "Store this key securely - it won't be shown again!"
}
```

**⚠️ Important**: Save the API key immediately! It cannot be retrieved later.

#### 2. Use API Key in Requests

```bash
curl -X POST http://localhost:8005/api/v1/advanced/batch-tts \
  -H "X-API-Key: YOUR_API_KEY_HERE" \
  -H "Content-Type: application/json" \
  -d '{...}'
```

---

## 🚀 Batch Processing

### Batch TTS from JSON

Process multiple texts in one request:

```bash
curl -X POST http://localhost:8005/api/v1/advanced/batch-tts \
  -H "X-API-Key: YOUR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "texts": [
      "Primeiro texto para síntese",
      "Segundo texto para síntese",
      "Terceiro texto para síntese"
    ],
    "voice_id": "cloned_voice_123",
    "language": "pt",
    "tts_engine": "xtts",
    "quality_profile": "ultra"
  }'
```

**Response**:
```json
{
  "job_id": "batch_a1b2c3d4",
  "total_jobs": 3,
  "estimated_time": 15,
  "status_url": "/api/v1/advanced/batch-tts/batch_a1b2c3d4/status"
}
```

**Limits**:
- Min texts: 1
- Max texts: 100
- Max text length: 5000 characters each

---

### Batch TTS from CSV

Upload a CSV file with multiple TTS requests:

**CSV Format**:
```csv
text,voice_id,language
"Olá mundo",voice1,pt
"Hello world",voice1,en
"Bonjour monde",voice2,fr
```

**Request**:
```bash
curl -X POST http://localhost:8005/api/v1/advanced/batch-csv \
  -H "X-API-Key: YOUR_API_KEY" \
  -F "file=@batch_requests.csv"
```

**Response**: Same as batch TTS

---

### Check Batch Status

```bash
curl -X GET http://localhost:8005/api/v1/advanced/batch-tts/batch_a1b2c3d4/status \
  -H "X-API-Key: YOUR_API_KEY"
```

**Response**:
```json
{
  "batch_id": "batch_a1b2c3d4",
  "total_jobs": 3,
  "completed": 2,
  "failed": 0,
  "pending": 1,
  "progress": 66,
  "status": "processing"
}
```

---

### Download Batch Results

Once all jobs are completed, download ZIP with all audio files:

```bash
curl -X GET http://localhost:8005/api/v1/advanced/batch-tts/batch_a1b2c3d4/download \
  -H "X-API-Key: YOUR_API_KEY" \
  -o results.zip
```

**ZIP Contents**:
```
results.zip
├── audio_001.wav
├── audio_002.wav
└── audio_003.wav
```

---

## 📊 Monitoring & Metrics

### Prometheus Metrics Endpoint

Expose metrics for Prometheus scraping:

```bash
curl http://localhost:8005/metrics
```

**Sample Output**:
```prometheus
# HELP http_requests_total Total HTTP requests
# TYPE http_requests_total counter
http_requests_total{method="POST",endpoint="/api/v1/advanced/batch-tts",status="200"} 42.0

# HELP tts_jobs_created_total Total TTS jobs created
# TYPE tts_jobs_created_total counter
tts_jobs_created_total{engine="xtts",language="pt"} 128.0

# HELP api_latency_seconds API endpoint latency in seconds
# TYPE api_latency_seconds histogram
api_latency_seconds_bucket{method="POST",endpoint="/clone-voice",le="0.5"} 95.0
api_latency_seconds_bucket{method="POST",endpoint="/clone-voice",le="1.0"} 120.0
```

---

### Configure Prometheus

**prometheus.yml**:
```yaml
scrape_configs:
  - job_name: 'tts-webui'
    static_configs:
      - targets: ['localhost:8005']
    metrics_path: '/metrics'
    scrape_interval: 15s
```

**Start Prometheus**:
```bash
docker run -d \
  -p 9090:9090 \
  -v $(pwd)/prometheus.yml:/etc/prometheus/prometheus.yml \
  prom/prometheus
```

Access Prometheus UI: `http://localhost:9090`

---

### Available Metrics

| Metric | Type | Description |
|--------|------|-------------|
| `http_requests_total` | Counter | Total HTTP requests |
| `tts_jobs_created_total` | Counter | Total TTS jobs created |
| `tts_jobs_completed_total` | Counter | Total TTS jobs completed |
| `tts_jobs_failed_total` | Counter | Total TTS jobs failed |
| `api_latency_seconds` | Histogram | API endpoint latency |
| `audio_generation_duration_seconds` | Histogram | Audio generation time |
| `audio_file_size_bytes` | Histogram | Generated audio file size |
| `gpu_memory_usage_bytes` | Gauge | GPU memory usage |
| `gpu_utilization_percent` | Gauge | GPU utilization |
| `rvc_conversion_total` | Counter | Total RVC conversions |
| `cache_hits_total` | Counter | Cache hits |
| `cache_misses_total` | Counter | Cache misses |

---

### Health Checks

#### Basic Health Check

```bash
curl http://localhost:8005/health
```

**Response**:
```json
{
  "status": "healthy",
  "timestamp": "2025-12-06T10:30:00",
  "service": "tts-webui"
}
```

#### Readiness Check (Kubernetes)

```bash
curl http://localhost:8005/ready
```

**Response (Healthy)**:
```json
{
  "ready": true,
  "checks": {
    "gpu": true,
    "redis": true,
    "models": true
  }
}
```

**Response (Not Ready)**:
```json
{
  "ready": false,
  "checks": {
    "gpu": true,
    "redis": false,
    "models": true
  }
}
```

**HTTP Status**:
- `200 OK` - Service ready
- `503 Service Unavailable` - Service not ready

---

## 🎨 Voice Morphing (Coming Soon)

Voice morphing allows blending multiple voices to create unique voice characteristics.

**Status**: ⏳ Not yet implemented (returns 501)

**Planned API**:
```bash
curl -X POST http://localhost:8005/api/v1/advanced/voice-morphing \
  -H "X-API-Key: YOUR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "voice_ids": ["voice1", "voice2", "voice3"],
    "weights": [0.5, 0.3, 0.2],
    "text": "Hello, this is a morphed voice",
    "language": "en"
  }'
```

**How it works** (planned):
1. Load speaker embeddings for each voice
2. Compute weighted average of embeddings
3. Generate audio with blended embedding

**Use cases**:
- Create unique voice styles
- Blend professional and casual tones
- Mix characteristics from multiple speakers

---

## 🔒 Security Best Practices

### 1. Environment Variables

Store secrets in environment variables:

```bash
# .env
JWT_SECRET_KEY=your-super-secret-key-change-this
API_KEYS_FILE=/secure/path/api_keys.txt
```

**Load in app**:
```python
import os
JWT_SECRET = os.getenv("JWT_SECRET_KEY", "change-me-in-production")
```

### 2. API Key Storage

API keys are stored **hashed** (SHA256) in `data/api_keys.txt`:

```
abc123...hash|My Production Key|2025-12-06T10:00:00
def456...hash|Mobile App Key|2026-01-15T08:30:00
```

**⚠️ Never commit this file to version control!**

Add to `.gitignore`:
```gitignore
data/api_keys.txt
temp/batch_*.json
```

### 3. HTTPS in Production

**Always use HTTPS in production!**

**Option 1: Nginx Reverse Proxy**
```nginx
server {
    listen 443 ssl;
    server_name tts.example.com;
    
    ssl_certificate /etc/letsencrypt/live/tts.example.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/tts.example.com/privkey.pem;
    
    location / {
        proxy_pass http://localhost:8005;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

**Option 2: Let's Encrypt (Certbot)**
```bash
certbot --nginx -d tts.example.com
```

### 4. Rate Limiting

Add rate limiting to prevent abuse:

**Install**:
```bash
pip install slowapi
```

**Configure**:
```python
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

@app.post("/api/v1/advanced/batch-tts")
@limiter.limit("10/minute")
async def batch_tts(...):
    ...
```

---

## 📈 Performance Optimization

### 1. Model Caching

Cache loaded models in memory:

```python
from functools import lru_cache

@lru_cache(maxsize=5)
def load_tts_model(engine: str):
    # Model stays in memory
    return load_model(engine)
```

### 2. Batch Inference

Process multiple requests in one GPU call:

```python
# Instead of:
for text in texts:
    audio = model.synthesize(text)

# Do:
audios = model.synthesize_batch(texts)  # Single GPU call
```

### 3. Async Processing

Use async for I/O operations:

```python
async def process_batch(texts):
    tasks = [synthesize_async(text) for text in texts]
    return await asyncio.gather(*tasks)
```

---

## 🧪 Testing

Run advanced features tests:

```bash
# Run all tests
pytest tests/test_advanced_features.py -v

# Run specific test category
pytest tests/test_advanced_features.py -k "auth" -v
pytest tests/test_advanced_features.py -k "batch" -v
pytest tests/test_advanced_features.py -k "metrics" -v

# With coverage
pytest tests/test_advanced_features.py --cov=app.advanced_features --cov-report=html
```

**Test Coverage**: 26 tests covering authentication, batch processing, metrics, and health checks.

---

## 🐛 Troubleshooting

### Issue: "Authentication required" Error

**Cause**: Missing or invalid authentication header

**Solution**:
```bash
# Check token is valid
curl -X POST http://localhost:8005/api/v1/advanced/auth/token \
  -d '{"username":"test","password":"test"}'

# Use token in header
curl -H "Authorization: Bearer YOUR_TOKEN" ...
```

---

### Issue: Batch Status Returns 404

**Cause**: Batch metadata file not found

**Check**:
```bash
ls -la temp/batch_*.json
```

**Solution**: Ensure `temp/` directory exists and is writable:
```bash
mkdir -p temp
chmod 755 temp
```

---

### Issue: Metrics Endpoint Empty

**Cause**: prometheus-client not installed

**Solution**:
```bash
pip install prometheus-client==0.19.0
```

---

## 📚 Additional Resources

- [JWT.io](https://jwt.io/) - JWT token debugger
- [Prometheus Documentation](https://prometheus.io/docs/)
- [Grafana Dashboards](https://grafana.com/grafana/dashboards/)
- [FastAPI Security](https://fastapi.tiangolo.com/tutorial/security/)

---

## 🎯 Next Steps

1. ✅ **Production deployment** with HTTPS
2. ⏳ **Implement voice morphing** (Sprint 7.2)
3. ⏳ **Add rate limiting** (prevent abuse)
4. ⏳ **Set up Grafana dashboards** (visualize metrics)
5. ⏳ **Implement model caching** (improve performance)

---

## 📝 Changelog

### v1.0.0 - Sprint 7 (2025-12-06)
- ✅ JWT authentication
- ✅ API key management
- ✅ Batch TTS processing
- ✅ CSV batch upload
- ✅ Prometheus metrics
- ✅ Health/readiness checks
- ✅ 26 comprehensive tests

### Upcoming - Sprint 7.2
- ⏳ Voice morphing implementation
- ⏳ Model caching (LRU)
- ⏳ Audio streaming
- ⏳ Rate limiting
