# Audio Voice Service - Copilot Instructions

## Architecture Overview

This is a **production-ready TTS & Voice Cloning microservice** with XTTS v2 engine and Gradio WebUI. Simplified architecture focused on XTTS-only for better maintainability.

### Core Components
- **Gradio WebUI** ([app_gradio.py](app_gradio.py)): Pure Gradio application with TTS generation, voice cloning, and training UI
- **VoiceProcessor** ([app/processor.py](app/processor.py)): Orchestrates TTS generation pipeline
- **XTTS Engine** ([app/engines/xtts_engine.py](app/engines/xtts_engine.py)): Factory pattern with lazy loading for XTTS v2 only
- **Redis Store** ([app/redis_store.py](app/redis_store.py)): Jobs, voice profiles, quality profiles (optional - can work without)
- **Standalone Mode** ([app_standalone.py](app_standalone.py)): Simplified version without Redis/Celery dependencies

### Critical Data Flows
1. **Job Creation**: Gradio UI → Direct processing (no queue) → Updates storage → Returns audio
2. **TTS Pipeline**: Text → VoiceProcessor → XTTS Engine → Audio file
3. **Voice Cloning**: Upload → Validation → Engine.clone_voice() → Stored in disk/Redis

## Key Patterns & Conventions

### Lazy Loading & VRAM Management
The system uses **aggressive lazy loading** to minimize VRAM usage (critical for 8GB GPUs):

```python
# API: lazy_load=True (NO models loaded)
processor = VoiceProcessor(lazy_load=True)

# Worker: lazy_load=False (loads default engine)
processor = VoiceProcessor(lazy_load=False)
```

**LOW_VRAM mode** ([app/vram_manager.py](app/vram_manager.py)) automatically unloads models after use. When `LOW_VRAM=true`, models are loaded/unloaded per-request instead of cached.

### Factory Pattern for Engines
[app/engines/factory.py](app/engines/factory.py) implements singleton caching:
```python
# Engines cached after first creation
engine = create_engine('xtts', settings)  # Creates & caches
engine = create_engine('xtts', settings)  # Returns cached
```

**Never** instantiate engines directly - always use `create_engine()` or `create_engine_with_fallback()`.

### Quality Profiles System
[app/quality_profiles.py](app/quality_profiles.py) + [app/quality_profile_manager.py](app/quality_profile_manager.py) manage TTS generation parameters:
- 3 built-in XTTS profiles (balanced, expressive, stable)
- Can be stored in Redis with 30-day TTL (optional)
- Include temperature, speed, repetition penalty, etc.

When adding features, check if parameters belong in Quality Profiles vs Job/Request models.

### Pydantic Models & Redis Serialization
All data classes ([app/models.py](app/models.py)) inherit from `BaseModel` with:
- `.model_dump()` for Redis storage (handles datetime → ISO strings)
- Custom serialization for enums (use `.value`)
- Reconstruction via `Job(**job_dict)` or `Job.from_redis_dict()`

**Always** use `.model_dump()` before storing in Redis, never `dict(model)`.

### Exception Hierarchy
[app/exceptions.py](app/exceptions.py) defines custom exceptions:
- `VoiceServiceException` (base)
- `DubbingException`, `VoiceCloneException`
- `TTSEngineException` (with fallback triggers)

Use specific exceptions for proper error handling and circuit breaker integration.

### Celery Async Bridge Pattern
Celery tasks are **synchronous by default**, but our TTS engines use async/await. Use the `run_async_task()` helper in [app/celery_tasks.py](app/celery_tasks.py):

```python
def run_async_task(coro):
    """Helper to execute async coroutine in sync Celery task"""
    try:
        loop = asyncio.get_event_loop()
        if loop.is_running():
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
    return loop.run_until_complete(coro)

@celery_app.task
def dubbing_task(self, job_dict: dict):
    async def _process():
        processor = get_processor()
        job = await processor.process_dubbing_job(job)
        return job
    return run_async_task(_process())
```

**Critical**: Never use `asyncio.run()` in Celery tasks - it creates a new event loop that conflicts with Celery's own loop. Always use the pattern above.

## Development Workflows

### Testing
```bash
# Run specific test suites (pytest organized by type)
pytest tests/unit/          # Fast unit tests
pytest tests/integration/   # API + Redis tests
pytest tests/e2e/           # Full pipeline tests

# Common patterns in tests/conftest.py
@pytest.fixture
def sample_audio_3s():  # Synthetic audio for tests
```

Test files follow naming: `test_<component>_<aspect>.py` (e.g., `test_audio_quality.py`)

### Docker Development
```bash
# From project root (has Makefile)
make rebuild         # Full rebuild (cleanup + build + up)
make logs-celery     # View worker logs (where models load)
make vram-stats      # Check GPU memory usage
make shell-celery    # Debug inside worker container

# Key files:
# - docker-compose.yml: CPU/light GPU (default)
# - docker-compose-gpu.yml: Full GPU with NVIDIA runtime
```

**Important**: Changes to `.env` require `make rebuild`, NOT `make restart` (containers cache env vars).

### XTTS-Only Architecture
This project now uses **XTTS v2 exclusively** for simplified maintenance and better reliability:
- Single engine to maintain and optimize
- No RVC (voice conversion) - direct XTTS output only
- No F5-TTS - removed for simplification
- Focus on training and fine-tuning XTTS models

See [app/engines/xtts_engine.py](app/engines/xtts_engine.py) for the implementation.

### Gradio WebUI
The project uses **Gradio** (https://www.gradio.app/docs) for a Python-native UI:

```python
import gradio as gr

# Gradio blocks for audio generation
with gr.Blocks() as demo:
    with gr.Tab("TTS Generation"):
        text_input = gr.Textbox(label="Text to speak")
        audio_output = gr.Audio(label="Generated Audio")
        generate_btn = gr.Button("Generate")
        
        generate_btn.click(
            fn=tts_wrapper,
            inputs=[text_input],
            outputs=audio_output
        )
```

**Key patterns for Gradio**:
- Use async wrappers for async functions (Gradio expects sync)
- Use `gr.Blocks()` for multi-tab layouts
- Leverage `gr.Audio()` for playback and upload
- Use `gr.State()` for tracking state across interactions
- Can run standalone or mounted in FastAPI: `gr.mount_gradio_app(app, demo, path="/gradio")`

## Configuration & Environment

### Critical ENV Vars
- `LOW_VRAM=true/false`: Enables model unloading (see [docs/LOW_VRAM.md](docs/LOW_VRAM.md))
- `TTS_ENGINE_DEFAULT=xtts`: Default engine (only XTTS available)
- `XTTS_DEVICE`: `cuda`, `cpu`, or `None` (auto-detect)
- `REDIS_URL`: Job/profile storage (default: `redis://localhost:6379/4`) - optional

Full reference: [app/config.py](app/config.py) `get_settings()`

### Proxmox GPU Passthrough
For deployment on Proxmox VMs with GPU passthrough, see:
- [docs/PROXMOX_GPU_SETUP.md](docs/PROXMOX_GPU_SETUP.md): Complete setup guide
- [docs/PROXMOX_FIX_RAPIDO.md](docs/PROXMOX_FIX_RAPIDO.md): Quick troubleshooting
- [scripts/proxmox-bind-nvidia-complete.sh](scripts/proxmox-bind-nvidia-complete.sh): Automated GPU binding

Common issues involve `nvidia-smi` access and device persistence in containers.

## Common Pitfalls

1. **Model caching**: XTTS engine is singleton. Use `force_recreate=True` in tests or after config changes.
2. **CUDA OOM**: Check `LOW_VRAM` mode. XTTS uses ~2-4GB VRAM.
3. **Async/Sync bridge**: Gradio expects sync functions. Use sync wrappers with `asyncio.new_event_loop()` pattern.
4. **File cleanup**: Always clean temp files in try/finally blocks.
5. **Voice profiles TTL**: Default 30 days in Redis. Can also store in filesystem only (standalone mode).

## Documentation

- [README.md](README.md): Quick start, features, API overview
- [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md): Detailed architecture (670 lines)
- [docs/getting-started.md](docs/getting-started.md): Step-by-step setup
- [docs/api-reference.md](docs/api-reference.md): All 42 API endpoints
- [docs/QUALITY_PROFILES.md](docs/QUALITY_PROFILES.md): Profile system details
- [memory-bank/](memory-bank/): Project context for AI agents (experimental)
