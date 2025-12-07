# Migration Guide: v1.x → v2.0

**Data**: December 2025  
**Breaking Changes**: Yes (RVC and F5-TTS removed)

---

## 🔥 Breaking Changes Summary

### Removed Features

#### 1. **RVC Voice Conversion** ❌
**Status**: Completely removed in v2.0

**What was removed**:
- All RVC models and processing
- `/rvc-models` API endpoints
- RVC parameters in `/jobs` endpoint
- 15+ dependencies (faiss-cpu, praat-parselmouth, pyworld, etc.)
- ~1500 lines of code

**Migration path**:
```diff
# v1.x - RVC was optional
POST /jobs
{
  "text": "Hello world",
  "voice": "speaker.wav",
- "enable_rvc": true,
- "rvc_model_id": "model123"
}

# v2.0 - Use XTTS native voice cloning
POST /jobs
{
  "text": "Hello world",
  "voice": "speaker.wav"
}
```

**Recommendation**: Use XTTS-v2 native voice cloning instead. Quality is comparable for most use cases.

#### 2. **F5-TTS Engine** ❌
**Status**: Completely removed in v2.0

**What was removed**:
- F5-TTS engine implementation
- F5-TTS quality profiles
- `engine: "f5tts"` parameter
- Dependencies: pyarrow, f5-tts-pytorch

**Migration path**:
```diff
# v1.x - F5-TTS was available
POST /jobs
{
  "text": "Olá mundo",
- "engine": "f5tts",
- "ref_text": "Reference transcription"
}

# v2.0 - Use XTTS only
POST /jobs
{
  "text": "Olá mundo",
  "engine": "xtts"  # or omit (xtts is default)
}
```

**Recommendation**: XTTS-v2 has excellent Portuguese (PT-BR) support. F5-TTS was experimental.

---

## ✨ New Features in v2.0

### 1. **Eager Loading Architecture**
**Before (v1.x)**:
- First request: ~10s (lazy loading)
- Subsequent requests: ~2s

**After (v2.0)**:
- Startup: 10-20s (eager loading)
- **All requests**: <2s ✅
- **Improvement**: -80% latency on first request

### 2. **SOLID Architecture**
**New service layer**:
```python
# app/services/xtts_service.py
from app.services import XTTSService
from app.dependencies import get_xtts_service

# Dependency Injection in endpoints
@app.post("/synthesize-direct")
async def synthesize(
    xtts: XTTSService = Depends(get_xtts_service)
):
    audio, sr = await xtts.synthesize(...)
```

**Benefits**:
- Testable (mock dependencies)
- Maintainable (SRP)
- Type-safe (IDE autocomplete)

### 3. **Quality Profiles**
**New profiles**:
```json
{
  "xtts_profiles": [
    {
      "id": "fast",
      "temperature": 0.7,
      "speed": 1.2,
      "latency": "~2s"
    },
    {
      "id": "balanced",
      "temperature": 0.75,
      "speed": 1.0,
      "latency": "~3s"
    },
    {
      "id": "high_quality",
      "temperature": 0.6,
      "speed": 0.95,
      "denoise": true,
      "latency": "~5s"
    }
  ]
}
```

**Usage**:
```bash
POST /synthesize-direct
{
  "text": "Test",
  "speaker_wav": file,
  "quality_profile": "high_quality"
}
```

### 4. **Enhanced Health Check**
**New endpoint**: `GET /health`

```json
{
  "status": "healthy",
  "checks": {
    "redis": {"status": "ok"},
    "disk_space": {"free_gb": 45.2},
    "xtts": {
      "status": "ok",
      "device": "cuda",
      "gpu": {
        "device_name": "RTX 3090",
        "vram_allocated_gb": 3.2
      }
    }
  },
  "uptime_seconds": 3847
}
```

### 5. **New Direct Synthesis Endpoint**
**Endpoint**: `POST /synthesize-direct`

**Purpose**: Synchronous synthesis without job queue

**Performance**:
- Latency: 2-5s (vs 10-30s with `/jobs`)
- Use case: Real-time applications, chatbots

**Example**:
```bash
curl -X POST http://localhost:8005/synthesize-direct \
  -F "text=Hello world" \
  -F "speaker_wav=@voice.wav" \
  -F "language=en" \
  -F "quality_profile=balanced"
```

---

## 📋 Migration Checklist

### Before Migration

- [ ] **Backup data**: `voice_profiles/`, `models/`, processed jobs
- [ ] **Export RVC models** (if needed for archival)
- [ ] **Document current API usage** (especially RVC parameters)
- [ ] **Notify users** about breaking changes

### Migration Steps

#### 1. Update Docker Compose (if customized)
```diff
# docker-compose.yml
volumes:
  - ./models/xtts:/app/models/xtts
- - ./models/rvc:/app/models/rvc  # REMOVE
- - ./models/f5tts:/app/models/f5tts  # REMOVE
```

#### 2. Update API Calls
**Remove RVC parameters**:
```diff
POST /jobs
{
  "text": "...",
  "voice": "...",
- "enable_rvc": false,
- "rvc_model_id": null,
- "rvc_pitch": 0
}
```

**Remove F5-TTS parameters**:
```diff
POST /jobs
{
  "text": "...",
- "engine": "f5tts",
- "ref_text": "..."
}
```

#### 3. Update Environment Variables
```diff
# .env
DEVICE=cuda
- RVC_DEVICE=cuda  # REMOVE
- RVC_MODELS_DIR=/app/models/rvc  # REMOVE
- F5TTS_ENABLE=false  # REMOVE
```

#### 4. Deploy v2.0
```bash
# Pull latest
git pull origin main

# Rebuild (no cache to ensure clean build)
docker compose down
docker compose build --no-cache

# Start
docker compose up -d

# Validate
curl http://localhost:8005/health
```

#### 5. Validate Functionality
```bash
# Test synthesis
curl -X POST http://localhost:8005/synthesize-direct \
  -F "text=Migration test" \
  -F "speaker_wav=@test_voice.wav" \
  -F "quality_profile=balanced"

# Check quality profiles
curl http://localhost:8005/quality-profiles

# Check logs
docker compose logs api | tail -50
```

### After Migration

- [ ] **Monitor performance**: Check latency metrics
- [ ] **Validate quality**: Compare XTTS output with previous RVC/F5-TTS
- [ ] **Update documentation**: Internal API guides
- [ ] **Clean up old data** (optional):
  ```bash
  rm -rf models/rvc/
  rm -rf models/f5tts/
  ```

---

## 🐛 Troubleshooting

### Issue: "XTTS service not initialized"
**Cause**: Service still loading (startup takes 10-20s)

**Solution**: Wait for startup to complete
```bash
# Check logs
docker compose logs api | grep "Audio Voice Service started"

# Check health
curl http://localhost:8005/health
```

### Issue: "Module 'RvcClient' not found"
**Cause**: Old code still referencing RVC

**Solution**: Pull latest code and rebuild
```bash
git pull origin main
docker compose down
docker compose build --no-cache
docker compose up -d
```

### Issue: First request still slow
**Cause**: Warm-up may have failed

**Solution**: Check logs for warm-up errors
```bash
docker compose logs api | grep -i warm
```

### Issue: Quality worse than v1.x with RVC
**Cause**: RVC was doing voice conversion post-processing

**Solution**: 
1. Use `quality_profile: "high_quality"` (includes denoise)
2. Adjust XTTS parameters in quality profile
3. Use better reference audio (clear, 5-10s)

---

## 📊 Performance Comparison

| Metric | v1.x | v2.0 | Change |
|--------|------|------|--------|
| **Startup time** | ~5s | 10-20s | +10-15s ⚠️ |
| **First request** | ~10s | <2s | **-80%** ✅ |
| **Nth request** | ~2s | ~2s | Same ✅ |
| **VRAM usage** | 6-8GB | 3-4GB | **-50%** ✅ |
| **Dependencies** | 80+ | ~65 | -18% ✅ |
| **Code LOC** | 15000 | 13500 | -10% ✅ |

**Trade-off analysis**:
- ✅ **Worth it**: Startup happens once, requests happen thousands of times
- ✅ **Better UX**: Consistent low latency for all users
- ✅ **Simpler**: Less code = easier maintenance

---

## 💡 Best Practices v2.0

### 1. Use Direct Endpoint for Real-time
```python
# For chatbots, interactive apps
response = requests.post("/synthesize-direct", ...)
# Returns WAV in 2-5s
```

### 2. Use Jobs Endpoint for Batch
```python
# For long texts, multiple synthesis
job = requests.post("/jobs", ...)
# Poll /jobs/{id} for completion
```

### 3. Choose Quality Profile Wisely
- **fast**: Chatbots, demos (2s)
- **balanced**: Default, good quality (3s)
- **high_quality**: Production, podcasts (5s)

### 4. Monitor Health
```python
import requests

health = requests.get("/health").json()
if health["status"] != "healthy":
    # Alert or fallback
```

---

## 📚 Additional Resources

- **Changelog**: [CHANGELOG.md](./CHANGELOG.md)
- **API Reference**: [api-reference.md](./api-reference.md)
- **Architecture**: [ARCHITECTURE.md](./ARCHITECTURE.md)
- **Sprint Progress**: [../SPRINT_PROGRESS.md](../SPRINT_PROGRESS.md)

---

## ❓ FAQ

**Q: Can I still use RVC for voice conversion?**  
A: No, RVC was removed. Use XTTS native voice cloning, which produces similar quality.

**Q: What about F5-TTS for Portuguese?**  
A: XTTS-v2 has excellent Portuguese support. F5-TTS was experimental and had stability issues.

**Q: Will v1.x still work?**  
A: Yes, but it's deprecated. No new features or bug fixes. Migrate to v2.0.

**Q: Can I rollback to v1.x?**  
A: Yes: `git checkout <v1.x-tag> && docker compose up -d --build`

**Q: Is the API compatible?**  
A: Mostly yes. Remove RVC/F5-TTS parameters and you're good.

---

**Last Updated**: December 7, 2025  
**Version**: v2.0.0
