# F5-TTS Inference API Documentation

**Version:** 1.0  
**Date:** 2025-12-06  
**Author:** F5-TTS Training Pipeline

## Overview

The F5-TTS Inference API provides a unified, production-ready interface for F5-TTS speech synthesis. This API consolidates all inference logic into a single, consistent interface used across:

- ✅ REST API endpoints (`app/engines/f5tts_engine.py`)
- ✅ Training/evaluation scripts (`train/scripts/*`)
- ✅ CLI tools (`train/cli/infer.py`)

## Architecture

```
┌─────────────────────────────────────────────┐
│          Application Layer                   │
│  (REST API, CLI, Training Scripts)          │
└─────────────────┬───────────────────────────┘
                  │
                  ▼
┌─────────────────────────────────────────────┐
│     F5TTSInferenceService (Singleton)       │
│  • Model caching                            │
│  • Lazy loading                             │
│  • Memory management                        │
└─────────────────┬───────────────────────────┘
                  │
                  ▼
┌─────────────────────────────────────────────┐
│         F5TTSInference (Core API)           │
│  • Model loading                            │
│  • Speech generation                        │
│  • Audio I/O                                │
└─────────────────┬───────────────────────────┘
                  │
                  ▼
┌─────────────────────────────────────────────┐
│          F5-TTS Library                     │
│  (f5_tts.infer.utils_infer)                 │
└─────────────────────────────────────────────┘
```

## API Components

### 1. F5TTSInference (Core API)

**Location:** `train/inference/api.py`

The core inference class that encapsulates F5-TTS model loading and generation.

#### Initialization

```python
from train.inference.api import F5TTSInference

inference = F5TTSInference(
    checkpoint_path="models/f5tts/model_last.pt",
    vocab_file="train/config/vocab.txt",
    device="cuda",
    config=None,  # Optional model config
    sample_rate=24000,
    hop_length=256,
    target_rms=0.1,
)
```

**Parameters:**

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `checkpoint_path` | `str \| Path` | *required* | Path to model checkpoint (`.pt` or `.safetensors`) |
| `vocab_file` | `str \| Path` | *required* | Path to vocabulary file (`vocab.txt`) |
| `device` | `str` | `"cuda"` | Device to run inference on (`cuda`, `cpu`, `mps`) |
| `config` | `dict \| None` | `None` | Optional model configuration dict |
| `sample_rate` | `int` | `24000` | Audio sample rate (Hz) |
| `hop_length` | `int` | `256` | Mel spectrogram hop length |
| `target_rms` | `float` | `0.1` | Target RMS for audio normalization |

#### Methods

##### `generate()`

Generate speech from text using reference audio.

```python
audio = inference.generate(
    text="Olá, mundo! Como você está?",
    ref_audio="reference.wav",
    ref_text="Texto de referência para voice cloning",
    nfe_step=32,
    cfg_strength=2.0,
    sway_sampling_coef=-1.0,
    speed=1.0,
    fix_duration=None,
    remove_silence=False,
)
```

**Parameters:**

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `text` | `str` | *required* | Text to synthesize |
| `ref_audio` | `str \| Path` | *required* | Path to reference audio file |
| `ref_text` | `str` | `""` | Transcription of reference audio (auto-transcribed if empty) |
| `nfe_step` | `int` | `32` | Number of function evaluations (1-128, higher = better quality) |
| `cfg_strength` | `float` | `2.0` | Classifier-free guidance strength (1.0-3.0) |
| `sway_sampling_coef` | `float` | `-1.0` | Sway sampling coefficient (-1.0 = auto) |
| `speed` | `float` | `1.0` | Speech speed multiplier (0.5-2.0) |
| `fix_duration` | `float \| None` | `None` | Fix output duration in seconds (None = auto) |
| `remove_silence` | `bool` | `False` | Remove leading/trailing silence |

**Returns:** `np.ndarray` - Generated audio array (shape: `[samples,]`)

**Raises:**
- `FileNotFoundError`: If reference audio not found
- `ValueError`: If text is empty or parameters invalid
- `RuntimeError`: If speech generation fails

##### `save_audio()`

Save generated audio to file.

```python
inference.save_audio(
    audio=audio_array,
    output_path="output.wav",
    sample_rate=None,  # Uses self.sample_rate if None
)
```

##### `unload()`

Unload model from memory to free GPU/RAM.

```python
inference.unload()
```

---

### 2. F5TTSInferenceService (Singleton Layer)

**Location:** `train/inference/service.py`

A singleton service that provides model caching and lifecycle management for efficient production use.

#### Getting Instance

```python
from train.inference.service import get_inference_service

service = get_inference_service()
```

#### Configuration

```python
service.configure(
    checkpoint_path="models/f5tts/model_last.pt",
    vocab_file="train/config/vocab.txt",
    device="cuda",
)
```

#### Usage

```python
# Model loaded automatically on first generate()
audio1 = service.generate(
    text="Primeira frase",
    ref_audio="ref.wav",
    ref_text="Referência",
)

# Subsequent calls reuse loaded model (fast!)
audio2 = service.generate(
    text="Segunda frase",
    ref_audio="ref.wav",
    ref_text="Referência",
)

# Unload when done
service.unload_model()
```

#### Benefits

- ✅ **Lazy Loading**: Model loaded only when needed
- ✅ **Singleton Pattern**: Single instance across application
- ✅ **Memory Efficient**: Explicit load/unload controls
- ✅ **Thread-Safe**: Uses locking for concurrent access
- ✅ **Fast Batch Processing**: Reuses loaded model

---

### 3. CLI Tool

**Location:** `train/cli/infer.py`

A command-line tool for quick testing and batch processing.

#### Basic Usage

```bash
python -m train.cli.infer \
    --checkpoint models/f5tts/model_last.pt \
    --vocab train/config/vocab.txt \
    --text "Olá, mundo!" \
    --ref-audio reference.wav \
    --output output.wav
```

#### Advanced Usage

```bash
python -m train.cli.infer \
    --checkpoint models/f5tts/model_last.pt \
    --vocab train/config/vocab.txt \
    --text "Texto longo com múltiplas frases." \
    --ref-audio reference.wav \
    --ref-text "Transcrição do áudio de referência" \
    --nfe-step 64 \
    --cfg-strength 2.5 \
    --speed 1.0 \
    --remove-silence \
    --output output.wav
```

#### Service Mode (Model Caching)

Use `--use-service` for batch processing with model caching:

```bash
# First call loads model
python -m train.cli.infer \
    --checkpoint models/f5tts/model_last.pt \
    --vocab train/config/vocab.txt \
    --text "Primeira frase" \
    --ref-audio ref.wav \
    --output output1.wav \
    --use-service

# Second call reuses loaded model (faster!)
python -m train.cli.infer \
    --checkpoint models/f5tts/model_last.pt \
    --vocab train/config/vocab.txt \
    --text "Segunda frase" \
    --ref-audio ref.wav \
    --output output2.wav \
    --use-service
```

#### Checkpoint Info

Display checkpoint information:

```bash
python -m train.cli.infer info --checkpoint models/f5tts/model_last.pt
```

---

## Usage Examples

### Example 1: Simple Speech Generation

```python
from train.inference.api import F5TTSInference

# Initialize
inference = F5TTSInference(
    checkpoint_path="models/f5tts/model_last.pt",
    vocab_file="train/config/vocab.txt",
    device="cuda"
)

# Generate
audio = inference.generate(
    text="Olá! Este é um teste de síntese de voz.",
    ref_audio="reference.wav",
)

# Save
inference.save_audio(audio, "output.wav")
```

### Example 2: High-Quality Synthesis

```python
# Use more NFE steps for better quality
audio = inference.generate(
    text="Texto com alta qualidade e expressividade.",
    ref_audio="reference.wav",
    ref_text="Transcrição precisa do áudio de referência",
    nfe_step=64,  # Higher quality (slower)
    cfg_strength=2.5,  # More expressive
    remove_silence=True,
)
```

### Example 3: Batch Processing with Service

```python
from train.inference.service import get_inference_service

# Get singleton service
service = get_inference_service()
service.configure(
    checkpoint_path="models/f5tts/model_last.pt",
    vocab_file="train/config/vocab.txt",
    device="cuda"
)

# Process multiple texts
texts = [
    "Primeira frase a sintetizar.",
    "Segunda frase com mais detalhes.",
    "Terceira frase para completar.",
]

for i, text in enumerate(texts):
    audio = service.generate(
        text=text,
        ref_audio="reference.wav",
        ref_text="Referência",
    )
    service.save_audio(audio, f"output_{i}.wav")

# Unload model
service.unload_model()
```

### Example 4: Custom Speed and Duration

```python
# Faster speech (1.5x speed)
audio_fast = inference.generate(
    text="Fala rápida para urgência.",
    ref_audio="reference.wav",
    speed=1.5,
)

# Slower speech (0.7x speed)
audio_slow = inference.generate(
    text="Fala lenta e clara para narração.",
    ref_audio="reference.wav",
    speed=0.7,
)
```

---

## Quality Parameters

### NFE Steps (`nfe_step`)

Number of function evaluations in the diffusion process.

- **Low (16-32)**: Fast, acceptable quality
- **Medium (32-64)**: Balanced quality/speed ⭐ **Recommended**
- **High (64-128)**: Maximum quality, slow

### CFG Strength (`cfg_strength`)

Classifier-free guidance strength controls expressiveness.

- **Low (1.0-1.5)**: Stable, less expressive
- **Medium (2.0-2.5)**: Balanced ⭐ **Recommended**
- **High (2.5-3.0)**: Very expressive, may introduce artifacts

### Speed (`speed`)

Speech speed multiplier.

- **Slow (0.5-0.8)**: Careful narration, audiobooks
- **Normal (1.0)**: Natural speech ⭐ **Recommended**
- **Fast (1.2-2.0)**: Quick updates, notifications

---

## Performance

### Real-Time Factor (RTF)

Typical RTF values on RTX 3090:

| NFE Steps | RTF | Use Case |
|-----------|-----|----------|
| 16 | 0.3-0.5 | Quick tests, drafts |
| 32 | 0.5-1.0 | Production (balanced) ⭐ |
| 64 | 1.0-2.0 | High quality, final outputs |
| 128 | 2.0-4.0 | Maximum quality, research |

**RTF < 1.0** = Faster than real-time  
**RTF = 1.0** = Real-time  
**RTF > 1.0** = Slower than real-time

### VRAM Usage

| Configuration | VRAM |
|---------------|------|
| Base model (24kHz) | 3-5 GB |
| Base + caching | 4-6 GB |
| Large model | 8-12 GB |

---

## Troubleshooting

### FileNotFoundError: Checkpoint not found

**Solution:** Verify checkpoint path exists:

```python
from pathlib import Path
ckpt = Path("models/f5tts/model_last.pt")
print(f"Exists: {ckpt.exists()}")
```

### CUDA Out of Memory

**Solutions:**
1. Reduce batch size (process shorter texts)
2. Use fewer NFE steps (`nfe_step=16`)
3. Switch to CPU (`device="cpu"`)
4. Use LOW_VRAM mode in REST API

### Poor Quality Output

**Solutions:**
1. Provide accurate `ref_text` transcription
2. Increase NFE steps (`nfe_step=64`)
3. Adjust CFG strength (`cfg_strength=2.5`)
4. Use higher quality reference audio (clear, 3-30s)

### Slow Inference

**Solutions:**
1. Reduce NFE steps (`nfe_step=16-32`)
2. Use service layer for batch processing
3. Ensure GPU is being used (`device="cuda"`)
4. Check VRAM availability

---

## API Reference Summary

### Classes

| Class | Location | Purpose |
|-------|----------|---------|
| `F5TTSInference` | `train/inference/api.py` | Core inference API |
| `F5TTSInferenceService` | `train/inference/service.py` | Singleton service with caching |

### Key Methods

| Method | Class | Description |
|--------|-------|-------------|
| `generate()` | `F5TTSInference` | Generate speech from text |
| `save_audio()` | `F5TTSInference` | Save audio to file |
| `unload()` | `F5TTSInference` | Unload model from memory |
| `configure()` | `F5TTSInferenceService` | Configure service parameters |
| `load_model()` | `F5TTSInferenceService` | Explicitly load model |
| `unload_model()` | `F5TTSInferenceService` | Unload model from cache |

### CLI Commands

| Command | Description |
|---------|-------------|
| `infer` | Generate speech from text |
| `info` | Display checkpoint information |

---

## Integration Examples

### REST API Integration

```python
from train.inference.service import get_inference_service

# In FastAPI endpoint
@app.post("/tts/generate")
async def generate_tts(request: TTSRequest):
    service = get_inference_service()
    
    if not service.is_configured():
        service.configure(
            checkpoint_path=settings.f5tts_checkpoint,
            vocab_file=settings.f5tts_vocab,
            device=settings.device,
        )
    
    audio = service.generate(
        text=request.text,
        ref_audio=request.ref_audio,
        ref_text=request.ref_text,
        nfe_step=request.quality_params.get('nfe_step', 32),
    )
    
    return audio
```

### Training Script Integration

```python
from train.inference.api import F5TTSInference

# In training script
def evaluate_checkpoint(checkpoint_path, test_cases):
    inference = F5TTSInference(
        checkpoint_path=checkpoint_path,
        vocab_file="train/config/vocab.txt",
        device="cuda"
    )
    
    for text, ref_audio in test_cases:
        audio = inference.generate(
            text=text,
            ref_audio=ref_audio,
            nfe_step=32,
        )
        # Evaluate quality...
    
    inference.unload()
```

---

## Migration Guide

### From Old f5tts_engine.py

**Before:**
```python
from app.engines.f5tts_engine import F5TtsEngine

engine = F5TtsEngine(device="cuda", model_name="model.pt")
audio_bytes, duration = await engine.generate_dubbing(
    text="Hello",
    language="en",
    voice_profile=profile,
)
```

**After:**
```python
from train.inference.api import F5TTSInference

inference = F5TTSInference(
    checkpoint_path="model.pt",
    vocab_file="vocab.txt",
    device="cuda"
)

audio_array = inference.generate(
    text="Hello",
    ref_audio=profile.source_audio_path,
    ref_text=profile.ref_text,
)

# Convert to bytes if needed
import soundfile as sf
import io
buffer = io.BytesIO()
sf.write(buffer, audio_array, 24000, format='WAV')
audio_bytes = buffer.getvalue()
```

---

## Changelog

### Version 1.0 (2025-12-06)

**Initial Release:**
- ✅ Core F5TTSInference API
- ✅ Singleton service layer with caching
- ✅ CLI tool with typer + rich
- ✅ Comprehensive documentation
- ✅ Production-ready error handling
- ✅ Memory management (load/unload)
- ✅ Thread-safe service

---

## Support

For issues, questions, or feature requests, please refer to:
- **Documentation:** `train/docs/`
- **Examples:** This document
- **Source Code:** `train/inference/`
- **Tests:** `tests/test_f5tts_*.py`

---

**Last Updated:** 2025-12-06  
**Version:** 1.0  
**Author:** F5-TTS Training Pipeline
