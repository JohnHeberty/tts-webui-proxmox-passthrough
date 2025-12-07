# 🚀 Quick Reference - Advanced Features

## Authentication

### Get JWT Token
```bash
curl -X POST http://localhost:8005/api/v1/advanced/auth/token \
  -d '{"username":"test","password":"test"}'
```

### Create API Key
```bash
curl -X POST http://localhost:8005/api/v1/advanced/auth/api-key \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -d '{"name":"My Key","expires_days":365}'
```

### Use Authentication
```bash
# Option 1: JWT
-H "Authorization: Bearer YOUR_TOKEN"

# Option 2: API Key
-H "X-API-Key: YOUR_API_KEY"
```

---

## Batch Processing

### Batch TTS (JSON)
```bash
curl -X POST http://localhost:8005/api/v1/advanced/batch-tts \
  -H "X-API-Key: YOUR_KEY" \
  -d '{
    "texts": ["Text 1", "Text 2"],
    "voice_id": "my_voice",
    "language": "pt"
  }'
```

### Batch TTS (CSV)
```bash
curl -X POST http://localhost:8005/api/v1/advanced/batch-csv \
  -H "X-API-Key: YOUR_KEY" \
  -F "file=@batch.csv"
```

### Check Status
```bash
curl http://localhost:8005/api/v1/advanced/batch-tts/BATCH_ID/status \
  -H "X-API-Key: YOUR_KEY"
```

### Download Results
```bash
curl http://localhost:8005/api/v1/advanced/batch-tts/BATCH_ID/download \
  -H "X-API-Key: YOUR_KEY" -o results.zip
```

---

## Training

### Start Training
```bash
curl -X POST http://localhost:8005/training/start \
  -d '{
    "model_name": "my_model",
    "dataset_folder": "datasets/my_voice",
    "epochs": 100,
    "batch_size": 8
  }'
```

### Check Status
```bash
curl http://localhost:8005/training/status
```

### List Checkpoints
```bash
curl http://localhost:8005/training/checkpoints
```

### Run Inference
```bash
curl -X POST http://localhost:8005/training/inference/synthesize \
  -d '{
    "checkpoint": "path/to/checkpoint.pth",
    "text": "Hello world",
    "temperature": 0.7
  }'
```

---

## Monitoring

### Prometheus Metrics
```bash
curl http://localhost:8005/metrics
```

### Health Check
```bash
curl http://localhost:8005/health
```

### Readiness Check
```bash
curl http://localhost:8005/ready
```

---

## Endpoints Summary

### Training (13)
- `POST /training/dataset/download`
- `POST /training/dataset/segment`
- `POST /training/dataset/transcribe`
- `GET  /training/dataset/stats`
- `GET  /training/dataset/files`
- `POST /training/start`
- `POST /training/stop`
- `GET  /training/status`
- `GET  /training/logs`
- `GET  /training/checkpoints`
- `POST /training/checkpoints/load`
- `POST /training/inference/synthesize`
- `POST /training/inference/ab-test`

### Advanced (7)
- `POST /api/v1/advanced/auth/token`
- `POST /api/v1/advanced/auth/api-key`
- `POST /api/v1/advanced/batch-tts`
- `POST /api/v1/advanced/batch-csv`
- `GET  /api/v1/advanced/batch-tts/{id}/status`
- `GET  /api/v1/advanced/batch-tts/{id}/download`
- `POST /api/v1/advanced/voice-morphing` (501)

### Monitoring (3)
- `GET /metrics`
- `GET /health`
- `GET /ready`

---

## Python Client Example

```python
import requests

# 1. Authentication
auth_response = requests.post(
    "http://localhost:8005/api/v1/advanced/auth/token",
    json={"username": "test", "password": "test"}
)
token = auth_response.json()["access_token"]

# 2. Batch TTS
headers = {"Authorization": f"Bearer {token}"}
batch_response = requests.post(
    "http://localhost:8005/api/v1/advanced/batch-tts",
    headers=headers,
    json={
        "texts": ["Hello", "World"],
        "voice_id": "my_voice",
        "language": "en"
    }
)
batch_id = batch_response.json()["job_id"]

# 3. Check status
status_response = requests.get(
    f"http://localhost:8005/api/v1/advanced/batch-tts/{batch_id}/status",
    headers=headers
)
print(status_response.json())

# 4. Download results
download_response = requests.get(
    f"http://localhost:8005/api/v1/advanced/batch-tts/{batch_id}/download",
    headers=headers
)
with open("results.zip", "wb") as f:
    f.write(download_response.content)
```

---

## Testing

```bash
# Run all tests
pytest tests/ -v

# Run specific tests
pytest tests/test_advanced_features.py -v
pytest tests/test_training_api.py -v

# With coverage
pytest --cov=app --cov-report=html
```

---

## Documentation

- `docs/TRAINING_API.md` - Training API reference
- `docs/ADVANCED_FEATURES.md` - Advanced features guide
- `docs/SPRINT_6.2_MODULARIZATION.md` - JS modularization
- `IMPLEMENTATION_COMPLETE.md` - Project summary
- `CHANGELOG.md` - Version history
