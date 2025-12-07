# Changelog

All notable changes to the TTS WebUI Training System will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- Training API with 13 new endpoints for dataset management and model training
- WebUI Training page with 3 tabs (Dataset, Training, Inference)
- A/B comparison testing for model quality validation
- Real-time training status polling
- Checkpoint management system
- Background task processing for long-running operations
- Comprehensive API documentation (TRAINING_API.md)
- CI/CD pipeline with GitHub Actions
- 24 new unit tests for training API
- Python client example in API documentation

### Changed
- Reorganized test folder structure (train/tests → train/test)
- Unified test configuration in pyproject.toml
- Improved error handling across all endpoints
- Enhanced logging with structured output

### Fixed
- Type hints in training_api.py for better IDE support
- Validation errors now return proper 422 status codes
- Process monitoring in background tasks

## [1.0.0] - 2025-12-06

### Added
- Complete XTTS-v2 fine-tuning pipeline
- Voice cloning with 89.44% similarity validation
- Dataset preprocessing (download, segment, transcribe)
- WebUI with full API coverage
- Quality profile management
- RVC model integration
- Redis job store for scalability
- Docker support with GPU passthrough
- Comprehensive test suite (46 tests)
- Documentation suite (API, Architecture, Deployment)

### Features
- **Dataset Pipeline**
  - YouTube video download with yt-dlp
  - Voice Activity Detection (VAD) segmentation
  - Whisper-based transcription
  - 4922 samples processed (15.3 hours)

- **Training**
  - LoRA-based fine-tuning for XTTS-v2
  - Mixed precision training (FP16)
  - Gradient clipping and checkpointing
  - DeepSpeed support for multi-GPU

- **API**
  - FastAPI REST endpoints
  - Celery async task processing
  - Redis job queue
  - OpenAPI documentation

- **WebUI**
  - Bootstrap 5 responsive interface
  - Real-time job monitoring
  - Voice profile management
  - Quality profile presets
  - RVC model integration
  - Admin dashboard

### Performance
- Training: ~2-4 hours for 100 epochs (RTX 3090)
- Inference: <1s per sentence (GPU)
- Dataset processing: 15x speedup with parallel transcription

### Infrastructure
- Docker containerization
- Proxmox GPU passthrough support
- Nginx reverse proxy configuration
- Prometheus metrics
- ELK stack logging

---

## Version History

### Sprint Summary

| Sprint | Focus | Status | Tests | LOC |
|--------|-------|--------|-------|-----|
| Sprint 0 | Security & Cleanup | ✅ 100% | - | -500 |
| Sprint 1 | Dataset Pipeline | ✅ 100% | 6 | +2500 |
| Sprint 2 | Training Script | ✅ 100% | 8 | +3000 |
| Sprint 3 | API Integration | ✅ 100% | 11 | +1500 |
| Sprint 4 | Quality & Tests | ✅ 70% | 24 | +800 |
| Sprint 5 | Docs & DevOps | ✅ 90% | - | +500 |
| Sprint 6 | WebUI Training | ✅ 100% | 24 | +1718 |
| Sprint 7 | Advanced Features | 🔄 0% | - | - |

**Total**: 73 tests, ~10,000 lines of code

---

## Deprecated Features

### Removed in 1.0.0
- **F5-TTS Integration**: Removed due to instability and limited PT-BR support
  - Replaced with XTTS-v2 focus
  - Migration guide: Use XTTS-v2 quality profiles instead

---

## Migration Guides

### From 0.x to 1.0

**Configuration Changes**:
```bash
# Old
QUALITY_PROFILE=balanced

# New
QUALITY_PROFILE_ID=xtts-balanced
```

**API Changes**:
```python
# Old endpoint
POST /jobs/create

# New endpoint  
POST /jobs
```

**Database Schema**:
```sql
-- Run migration
python -m app.migrations.upgrade_to_1_0
```

---

## Known Issues

### Current Limitations
- Training requires minimum 16GB VRAM (can be reduced with DeepSpeed)
- WebUI JavaScript not yet modularized (planned for v1.1)
- No authentication layer (use reverse proxy for now)
- Dataset download limited to YouTube (more sources planned)

### Workarounds
- **Low VRAM**: Use `batch_size=2` and `use_deepspeed=true`
- **Slow inference**: Enable FP16 and reduce `temperature`
- **Out of disk**: Clean up temp files in `/temp/inference`

---

## Roadmap

### Version 1.1 (Planned)
- [ ] Modular JavaScript architecture
- [ ] WebSocket real-time updates
- [ ] Batch processing for multiple jobs
- [ ] Voice morphing/blending features
- [ ] Multi-language dataset support
- [ ] JWT authentication
- [ ] S3 storage integration

### Version 2.0 (Future)
- [ ] Multi-tenant support
- [ ] Kubernetes deployment
- [ ] Custom model architectures
- [ ] Fine-tuning scheduler
- [ ] Model compression/quantization
- [ ] Edge deployment support

---

## Contributors

- **Claude Sonnet 4.5** - AI Tech Lead, Architecture & Implementation
- **User** - Project Direction, Testing & Validation

---

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

## Acknowledgments

- **Coqui TTS** - XTTS-v2 base model
- **OpenAI Whisper** - Transcription engine
- **Bootstrap** - WebUI framework
- **FastAPI** - REST API framework
- **Redis** - Job queue system
