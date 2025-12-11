# TTS WebUI v2.0.1 Release Notes

**Release Date**: December 10, 2025  
**Previous Release**: v2.0.0 (December 7, 2025)  
**Status**: Production Ready ✅

## 🎯 Overview

TTS WebUI v2.0 represents a complete architectural overhaul focused on:
- **Simplicity**: Single TTS engine (XTTS-v2 only)
- **Performance**: Eager loading eliminates first-request latency
- **Maintainability**: SOLID principles and dependency injection
- **Type Safety**: Pydantic Settings with validation
- **Production Ready**: Stable Docker deployment with health monitoring

## 🚀 Major Changes

### Architecture

**SOLID Principles Implemented:**
- ✅ **Single Responsibility**: XTTSService handles only TTS synthesis
- ✅ **Dependency Injection**: Services injected via FastAPI dependencies
- ✅ **Type Safety**: Pydantic models throughout

**Performance Improvements:**
- **Eager Loading**: XTTS model loads at startup (~36s)
- **First Request**: Instant (vs 15-20s in v1.x)
- **Memory**: Predictable VRAM usage (1.6GB for XTTS)

### Removed Features

- ❌ **RVC (Voice Conversion)**: Removed entirely
- ❌ **F5-TTS Engine**: Removed (XTTS-only in v2.0)
- ❌ **Multi-Engine Fallback**: Simplified to single engine
- ❌ **Lazy Loading**: Replaced with eager loading

### New Features

**Centralized Configuration:**
- `app/settings.py`: Pydantic Settings with field validation
- Environment variable support via `.env`
- Type-safe configuration access
- Automatic path creation and validation

**Improved Health Monitoring:**
- Enhanced `/health` endpoint
- GPU stats in health response
- Startup time tracking
- Service readiness checks

**Direct Synthesis Endpoint:**
- `/synthesize-direct`: Synchronous synthesis without job queue
- Quality profile support
- Immediate audio response

## 📊 Technical Details

### File Changes

**Created:**
- `app/settings.py` (220 lines) - Centralized Pydantic Settings
- `app/services/xtts_service.py` (271 lines) - XTTS service layer
- `app/dependencies.py` (50 lines) - FastAPI dependency injection
- `docs/MIGRATION_v1_to_v2.md` (400 lines) - Migration guide
- `docs/V2_RELEASE_NOTES.md` (this file)

**Modified:**
- `app/main.py`: Startup event with eager loading
- `app/processor.py`: Uses XTTSService via DI (-150 lines complexity)
- `app/celery_tasks.py`: Injects XTTSService for workers
- `run.py`: Uses new Settings fields

**Removed:**
- `app/config.py` (replaced by settings.py)
- 6 obsolete documentation files
- All RVC-related code (~2000+ lines)
- F5-TTS engine code (~800 lines)

### Dependencies

**Unchanged:**
- PyTorch 2.4.0+cu118
- FastAPI 0.120.0
- Pydantic 2.7.0-2.11.0
- Coqui TTS 0.27.0

**Key Configuration:**
- Sample Rate: 24kHz (aligned across training/inference)
- Default Device: CUDA (auto-fallback to CPU)
- Task Timeout: 300s

## 🐳 Docker Deployment

### Startup Sequence

1. **Environment Setup** (~2s)
   - Directory permissions
   - CUDA detection
   - GPU validation

2. **Model Loading** (~36s)
   - XTTS-v2 download/cache (first run)
   - GPU allocation
   - Model initialization

3. **Service Ready** (~38s total)
   - Health endpoint available
   - Synthesis ready
   - Job queue active

### Resource Usage

- **VRAM**: ~1.6GB (XTTS model)
- **RAM**: ~3GB (Python + FastAPI)
- **Disk**: ~2GB (XTTS model cache)

### Health Check

```bash
curl http://localhost:8005/health
```

Response:
```json
{
  "status": "healthy",
  "timestamp": "2025-12-07T04:06:09.225810",
  "service": "tts-webui"
}
```

## 📚 Migration Guide

See [MIGRATION_v1_to_v2.md](./MIGRATION_v1_to_v2.md) for detailed migration instructions.

### Quick Migration Checklist

1. ✅ Update environment variables (use new Settings fields)
2. ✅ Remove RVC-related configuration
3. ✅ Remove F5-TTS references in code
4. ✅ Update API calls to use `engine: "xtts"` only
5. ✅ Test with `/synthesize-direct` endpoint
6. ✅ Verify health endpoint returns healthy
7. ✅ Update documentation/scripts referencing removed features

## 🔧 Configuration

### Environment Variables

```bash
# API Settings
HOST=0.0.0.0
PORT=8005
DEBUG=false
LOG_LEVEL=INFO

# XTTS Settings
XTTS_DEVICE=cuda
XTTS_SAMPLE_RATE=24000
XTTS_MODEL_NAME=tts_models/multilingual/multi-dataset/xtts_v2

# Redis & Celery
REDIS_HOST=redis
REDIS_PORT=6379
CELERY_BROKER_URL=redis://redis:6379/0

# Training
TRAIN_SAMPLE_RATE=24000  # Must match XTTS
TRAIN_BATCH_SIZE=2
TRAIN_EPOCHS=20
```

### Pydantic Settings Features

- **Type Validation**: Automatic type checking at startup
- **Field Validators**: Custom validation (paths, CUDA, sample rates)
- **Auto .env Loading**: No manual env parsing needed
- **IDE Autocomplete**: Full IntelliSense support

## 🎬 Next Steps

### Planned Sprints (v2.1+)

**Sprint TRAIN-3**: Pipeline Consolidation
- Unify training scripts
- Remove duplicate code
- Improve dataset management

**Sprint QUALITY-4**: Quality Enhancements
- Add audio denoising
- Update WebUI for quality profiles
- Improve synthesis quality metrics

**Sprint RESIL-5**: Observability
- Structured logging
- Distributed tracing
- Performance metrics

**Sprint FINAL-6**: Polish
- Clean WebUI
- Improve error messages
- Documentation updates

## 🐛 Known Issues

None currently identified in v2.0 core.

## 📞 Support

For issues, feature requests, or questions:
- Check `docs/MIGRATION_v1_to_v2.md` for migration help
- Review `docs/ARCHITECTURE.md` for technical details
- See `docs/API_PARAMETERS.md` for API usage

## 🏆 Credits

v2.0 Architecture: Complete refactoring with SOLID principles  
Performance: Eager loading strategy  
Type Safety: Pydantic Settings implementation  
Documentation: Comprehensive migration guide

---

**v2.0 - Simple, Fast, Production-Ready** 🚀
