# CHANGELOG - Audio Voice Service

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [Unreleased]

### 🔥 Fixed - CRITICAL

#### Engine Selection Bug (P0 - Critical)
- **CRITICAL BUG FIX:** Engine selection being completely ignored in `/voices/clone` AND `/jobs` endpoints
  - **Issue:** Frontend selection of F5-TTS was being ignored by backend
  - **Impact:** 100% failure rate - F5-TTS never worked since implementation
  - **Root Cause:** FastAPI `Form(TTSEngine.XTTS)` with Enum ignores user input, always defaults to XTTS
  - **Fix:** Changed to `str = Form('xtts')` with explicit validation
  - **Endpoints Fixed:**
    - ✅ `/voices/clone` - Fixed `tts_engine` parameter (SPRINT-01)
    - ✅ `/jobs` - Fixed `tts_engine`, `mode`, `voice_preset`, `rvc_f0_method` (SPRINT-06)
  - **Files Modified:**
    - `app/main.py` lines 697, 232-250: Changed Form parameters from Enum to str
    - Added explicit validation using `validate_enum_string()`
    - Added request logging with all parameters
    - Added job creation logging with all parameters
  - **References:** `RESULT.md`, `SPRINTS.md`, `docs/postmortems/2024-12-04-engine-selection-bug.md`
  - **Tested:** Manual validation + automated tests created
  - **Deployed:** 2024-12-04 23:17 UTC (SPRINT-01), 2024-12-04 23:50 UTC (SPRINT-06)

### ✅ Added

#### Testing
- **New Test Suite:** `tests/test_clone_voice_engine_selection.py` (SPRINT-02)
  - Comprehensive engine selection testing (XTTS + F5-TTS)
  - Invalid engine validation tests (400 error)
  - Backward compatibility tests (default engine)
  - Case-insensitive handling tests
  - **Regression Test:** Dedicated test to prevent bug from returning (`test_f5tts_selection_not_ignored`)
  - 6 test cases covering 100% of engine selection scenarios

#### Utilities & Infrastructure
- **Form Parser Utility:** `app/utils/form_parsers.py` (SPRINT-04)
  - `validate_enum_string()` - Validates and converts string to Enum
  - `parse_enum_form()` - Creates FastAPI Depends() parser for Enums
  - `validate_enum_list()` - Validates list of strings to Enum list
  - Case-insensitive by default
  - Reusable across all endpoints
  - Prevents future bugs

#### Logging & Observability
- **Structured Logging in Processor:** `app/processor.py` (SPRINT-03)
  - Initial processing log with full metadata:
    - `engine_requested` vs `engine_selected` (detect fallbacks)
    - `has_ref_text` flag
    - Job ID, voice name, language
  - Completion log with metrics:
    - Processing duration in seconds
    - Voice ID created
    - Engine actually used
  - All logs use structured `extra={}` format for easy parsing

- **Structured Logging in Endpoints:** `app/main.py`
  - `/voices/clone`: Logs engine, name, language on request
  - `/jobs`: Logs mode, engine, preset, RVC settings on request

### 📚 Documentation
- **Root Cause Analysis:** `RESULT.md` (SPRINT-01)
  - Complete investigation of engine selection bug
  - 5 WHYs analysis
  - Full flow tracing (frontend → backend → processor → engine)
  - 3 proposed solutions with pros/cons
  - Implementation outcomes section

- **Sprint Planning:** `SPRINTS.md` (SPRINT-01)
  - Detailed breakdown of 6 sprints
  - SPRINT-01: Hotfix (✅ completed)
  - SPRINT-02: Tests (✅ completed)
  - SPRINT-03: Logging (✅ completed)
  - SPRINT-04: Validation utility (✅ completed)
  - SPRINT-05: Postmortem docs (✅ completed)
  - SPRINT-06: Endpoint audit (✅ completed)

- **Pattern Documentation:** `docs/FORM_ENUM_PATTERN.md` (SPRINT-04)
  - Complete guide on how to use Enums with FastAPI Form()
  - Common pitfalls and solutions
  - Code examples and best practices
  - Testing checklist
  - Migration guide
  - Troubleshooting section

- **Postmortem:** `docs/postmortems/2024-12-04-engine-selection-bug.md` (SPRINT-05)
  - Complete incident timeline
  - Root cause analysis (5 WHYs)
  - Impact assessment
  - What worked well / what can improve
  - Action items and lessons learned
  - Metrics and resolution details

- **Endpoint Audit:** `docs/ENDPOINT_AUDIT.md` (SPRINT-06)
  - Audit of all endpoints using Form() + Enum
  - 4 additional bugs found in `/jobs` endpoint
  - Fixes applied to all parameters
  - Testing recommendations

---

## [2.0.0] - 2025-11-27

### 🚀 Major Release: XTTS v2 Migration + Complete Refactoring

This release represents a complete architectural refactoring of the audio-voice microservice, migrating from F5-TTS to XTTS v2 as the primary TTS engine, with significant improvements in code quality, resilience, and maintainability.

### ✅ Added

#### Core Features
- **XTTS v2 Integration** - Migrated to Coqui TTS XTTS v2 as primary engine
  - Zero-shot voice cloning (3-30s audio samples)
  - 16 languages supported including PT-BR
  - 24kHz sample rate (high quality)
  - GPU-first with automatic CPU fallback
  
- **Quality Profiles System** (`app/models.py`)
  - `BALANCED` - Equilíbrio entre emoção e estabilidade (recomendado)
  - `EXPRESSIVE` - Máxima emoção e naturalidade
  - `STABLE` - Conservador, produção segura
  - Customizable XTTS parameters per profile

- **Resilience Module** (`app/resilience.py`)
  - `@retry_async` decorator - Exponential backoff retry (3 attempts)
  - `CircuitBreaker` class - Prevents cascade failures
  - `with_timeout` utility - Timeout protection (300s default)
  - Applied to all XTTS inference calls

- **Input Validation Module** (`app/validators.py`)
  - `sanitize_text()` - Text sanitization for TTS
  - `validate_audio_mime()` - MIME type validation
  - `validate_audio_file()` - File size and existence checks
  - `validate_language_code()` - ISO 639-1 validation
  - `validate_voice_name()` - Voice profile name validation
  - `validate_speed()` / `validate_temperature()` - Parameter validation

- **Quality Profiles API Endpoints** (`app/main.py`)
  - `POST /quality-profiles` - Create custom profile
  - `GET /quality-profiles` - List all profiles (defaults + custom)
  - `DELETE /quality-profiles/{name}` - Remove custom profile (protects defaults)

- **Default Speaker Generation** (`scripts/create_default_speaker.py`)
  - Generates synthetic speaker for generic dubbing
  - Executed automatically during Docker build
  - Eliminates dependency on external audio files

#### Documentation
- **TTS_RESEARCH_PTBR.md** - Comprehensive TTS model research
  - Comparison: XTTS v2 vs YourTTS vs Bark vs VITS vs Fairseq MMS
  - Analysis of 102 HuggingFace models for PT-BR
  - Recommendation: Keep XTTS v2 (best for cloning PT-BR)
  
- **IMPLEMENTATION_SUMMARY.md** - Complete implementation summary
  - All phases documented (1-7)
  - Metrics: -6200 lines (25% reduction)
  - Dependencies: 48% reduction (31→16 packages)
  
- **CHANGELOG.md** - This file

### 🔄 Changed

#### Architecture
- **Removed Factory Pattern** - Simplified to direct XTTS instantiation
  - Deleted `_get_tts_engine()` from `processor.py`
  - Removed abstract interface (unnecessary for single engine)
  - Simplified code complexity

- **VoiceProcessor Refactoring** (`app/processor.py`)
  - Added circuit breaker initialization
  - Lazy loading support for API (saves 2GB VRAM)
  - Improved error handling and logging

- **XTTSClient Enhancements** (`app/xtts_client.py`)
  - Added `@retry_async` decorators on `generate_dubbing()` and `clone_voice()`
  - Timeout protection (300s) on all XTTS inference calls
  - Fixed parameter restoration bug (original_params scope)
  - Improved pt-BR language normalization
  
- **Configuration Cleanup** (`app/config.py`)
  - Removed F5-TTS section entirely
  - Removed OpenVoice section entirely
  - Added resilience settings section
  - Reduced environment variables from 50+ to ~15

- **Models Simplification** (`app/models.py`)
  - Removed `VoicePreset` Enum (was incorrect concept - not quality profiles)
  - Enhanced `XTTSParameters` dataclass with `from_profile()` factory
  - Improved `VoiceProfile` field documentation

#### Docker & Dependencies
- **Dockerfile Optimization**
  - Removed F5-TTS git clone (lines 44-49)
  - Removed blinker workaround (line 56)
  - Added default speaker generation step
  - Image size: 5GB (vs 7GB before - 28% reduction)

- **docker-compose.yml Cleanup**
  - Removed 20+ F5-TTS environment variables
  - Only XTTS variables maintained
  - Simplified configuration

- **requirements.txt Reduction**
  - Removed 15+ F5-TTS dependencies
  - From 31 packages to 16 packages (48% reduction)
  - Cleaner dependency tree

#### Documentation
- **README.md Complete Rewrite**
  - Removed all F5-TTS references (20+ occurrences)
  - Updated examples to XTTS v2
  - Fixed cloning duration recommendations (3-30s vs 2-10s)
  - Updated troubleshooting sections
  - Added validators.py to architecture diagram
  - Updated environment variables section

### ❌ Removed

#### Legacy Code
- `app/openvoice_client.py` (548 lines) - Unused OpenVoice integration
- `app/tts_interface.py` (42 lines) - Unnecessary abstraction layer

#### Legacy Tests
- `test_model_compatibility.py` - F5-TTS model compatibility tests
- `test_final_compatibility.py` - F5-TTS final validation
- `test_voice_clone.py` - F5-TTS voice cloning tests

#### Legacy Documentation
- `SPRINT*.md` (4 files, 6500+ lines) - Consolidated into `SPRINT_NOT.md`
- `FEITO.md` - Replaced by `IMPLEMENTATION_SUMMARY.md`
- `OPTIMIZER.md` - Merged into implementation docs
- `AUDIT.md` - Completed, archived
- `FIX_2.md` - Implemented, archived
- `NAOFEITO.md` - Consolidated into pending tasks

#### Legacy Artifacts
- `models/f5tts/` (~500MB) - Old architecture models
- `venv_xtts_test/` (16MB) - Duplicate venv

### 🐛 Fixed

#### Critical Fixes
- **Default Speaker Path** - Fixed hardcoded paths to `/app/uploads/default_speaker.wav`
  - Removed fallback to non-existent paths
  - Ensured default speaker exists via build script

- **Exception Naming** - Renamed `OpenVoiceException` → `TTSEngineException`
  - Consistent exception handling across codebase
  - Updated all imports

- **Logging Issues**
  - Removed emojis from logs (more professional)
  - Converted f-strings to lazy % formatting (performance)
  - Improved log levels (DEBUG for auditing)

#### Quality Improvements
- **Parameter Scope Bug** - Fixed `original_params` unbound variable in `xtts_client.py`
- **Language Normalization** - Improved pt-BR → pt conversion logic
- **Error Messages** - More descriptive error messages with context

### 📊 Metrics

#### Code Reduction
- **Lines Deleted**: ~7000 lines
  - Code: ~590 lines (openvoice_client + tts_interface)
  - Documentation: ~6500 lines (old sprint docs)
- **Lines Added**: ~800 lines
  - resilience.py + validators.py + quality profiles: ~200 lines
  - New documentation: ~600 lines
- **Net Result**: -6200 lines (25% reduction)

#### Dependencies
- **Before**: 31 packages (F5-TTS deps included)
- **After**: 16 packages (XTTS + core only)
- **Reduction**: 48% fewer dependencies

#### Configuration
- **Before**: 50+ environment variables (3 engines)
- **After**: ~15 variables (1 engine XTTS)
- **Reduction**: 70% simpler configuration

#### Artifacts
- **Docker Image**: 5GB (vs 7GB before - 28% reduction)
- **Models Storage**: 0MB in project (vs 500MB f5tts - 100% reduction)
- **Venv Size**: 19MB (vs 35MB with duplicates - 46% reduction)

### 🔒 Security

- Input validation via `validators.py` module
- MIME type validation for audio uploads
- Text sanitization to prevent injection
- File size limits enforced
- Audio duration limits enforced

### ⚡ Performance

#### XTTS v2 Benchmarks (GPU RTX 4090)
- Dubbing (3-7s audio): 10-30s generation time
- Voice cloning: 15-30s processing time
- CPU fallback: 3-6x slower (60-180s) but viable

#### Resilience Improvements
- Retry on transient failures (CUDA OOM, network)
- Circuit breaker prevents cascade failures
- Timeout protection prevents infinite hangs
- Lazy loading saves 2GB VRAM on API

### 📝 Technical Notes

#### Migration Path
- F5-TTS → XTTS v2 migration completed
- No breaking changes in API endpoints
- Backward compatible (same JSON schema)
- Quality profiles enhance existing API

#### Future Enhancements (See SPRINT_NOT.md)
- YourTTS fallback for low VRAM scenarios
- Fairseq MMS for generic dubbing (no cloning)
- Fine-tuning XTTS v2 with Common Voice PT-BR dataset
- Monitoring and metrics dashboard

### 🙏 Credits

**Refactoring executed by**: Senior Audio & Backend Engineer specialist  
**Date**: 2025-11-27  
**Review**: v2.0.0  
**Based on**: AUDIT.md + FIX_2.md + QUALITY.md + TTS_RESEARCH_PTBR.md

---

## [1.0.0] - 2024-11-24

### Initial Release (F5-TTS)

- F5-TTS v1 Base integration
- Basic dubbing functionality
- Voice cloning via Whisper
- Redis job queue
- Celery async processing
- Docker containerization

---

**Legend:**
- ✅ Added - New features
- 🔄 Changed - Changes to existing functionality
- ❌ Removed - Removed features/code
- 🐛 Fixed - Bug fixes
- 🔒 Security - Security improvements
- ⚡ Performance - Performance improvements
- 📝 Technical Notes - Implementation details
