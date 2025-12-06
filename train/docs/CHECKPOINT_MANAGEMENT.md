# Checkpoint Management System

**Version:** 2.0  
**Sprint:** 2 - Checkpoint Consolidation  
**Date:** December 6, 2025

## Overview

The F5-TTS training pipeline includes an intelligent checkpoint management system that provides:

- **Automatic checkpoint resolution** with priority-based fallback
- **Validation and corruption detection**
- **Metadata tracking** for all checkpoints
- **Auto-resume** from interrupted training
- **PT-BR model patching** for compatibility

## Architecture

### Components

1. **`train/utils/checkpoint.py`** - Core utilities
   - `resolve_checkpoint_path()` - Intelligent resolution with priority fallback
   - `validate_checkpoint()` - Integrity validation
   - `CheckpointInfo` - Metadata dataclass
   - `save/load_checkpoint_metadata()` - Metadata persistence

2. **`app/engines/f5tts_engine.py`** - Engine integration
   - Uses `resolve_checkpoint_path()` for model loading
   - Automatic PT-BR checkpoint patching
   - Fallback to legacy resolution

3. **`train/run_training.py`** - Training integration
   - Auto-resume from last checkpoint
   - Background metadata monitor
   - Checkpoint validation before use

---

## Checkpoint Resolution

### Priority Order

The system resolves checkpoints in the following order:

1. **Custom Checkpoint** (`config.model.custom_checkpoint`)
   - Explicitly specified checkpoint path
   - Highest priority for specific model selection

2. **Specified Checkpoint Name** (if `checkpoint_name` provided)
   - Named checkpoint in output directory
   - E.g., `model_50000.pt`

3. **Best Model** (`output_dir/model_best.pt`)
   - Best performing checkpoint based on validation metrics
   - Created when validation loss improves

4. **Last Model** (`output_dir/model_last.pt`)
   - Most recent checkpoint from training
   - Updated at configured intervals

5. **Latest Update Checkpoint** (`output_dir/model_XXXXX.pt`)
   - Numbered checkpoints by update count
   - Sorted by update number (highest first)

6. **Pretrained Model** (`config.paths.pretrained_model_path`)
   - Base pretrained model for fine-tuning
   - Downloaded from HuggingFace if not found

7. **Auto-Download** (if enabled)
   - Downloads from `config.model.base_model`
   - Only if `config.model.auto_download_pretrained = True`

### Usage Example

```python
from train.config.loader import load_config
from train.utils.checkpoint import resolve_checkpoint_path

# Load config
config = load_config()

# Resolve checkpoint
checkpoint_path = resolve_checkpoint_path(
    config,
    checkpoint_name=None,       # Optional specific name
    auto_download=True,         # Enable HF download fallback
    verbose=True                # Print resolution process
)

if checkpoint_path:
    print(f"Using checkpoint: {checkpoint_path}")
else:
    print("No checkpoint found")
```

### CLI Usage

```bash
# Validate checkpoint
python -m train.utils.checkpoint validate /path/to/model.pt

# Resolve checkpoint (shows resolution process)
python -m train.utils.checkpoint resolve

# Resolve specific checkpoint
python -m train.utils.checkpoint resolve --name model_best.pt

# Disable auto-download
python -m train.utils.checkpoint resolve --no-download

# Show checkpoint info
python -m train.utils.checkpoint info /path/to/model.pt
```

---

## Checkpoint Validation

### Validation Checks

1. **Existence** - File exists on filesystem
2. **Size** - Minimum 1GB (configurable)
3. **Format** - Valid PyTorch checkpoint (torch.load succeeds)
4. **Structure** - Is a dict with expected keys
5. **Essential Keys** - Contains `model_state_dict`, `vocab_char_map`

### Corruption Handling

When a corrupted checkpoint is detected:

1. Validation fails with detailed error
2. File is renamed to `.corrupted` extension
3. Next checkpoint in priority order is tried
4. Process continues until valid checkpoint found

### Validation API

```python
from train.utils.checkpoint import validate_checkpoint

info = validate_checkpoint(
    '/path/to/checkpoint.pt',
    min_size_gb=1.0,      # Minimum size in GB
    check_keys=True,      # Validate essential keys
    verbose=True          # Print details
)

print(info)
# CheckpointInfo(✅ VALID, 2.34GB, 1247 keys + EMA, model_last.pt)

# Access validation results
if info.is_valid:
    print(f"Size: {info.size_gb}GB")
    print(f"Keys: {info.num_keys}")
    print(f"EMA: {info.has_ema}")
else:
    print(f"Error: {info.error}")
```

### CheckpointInfo Dataclass

```python
@dataclass
class CheckpointInfo:
    path: Path                          # Checkpoint path
    exists: bool                        # File exists
    size_bytes: int                     # Size in bytes
    size_gb: float                      # Size in GB
    is_valid: bool                      # Validation passed
    has_ema: bool                       # Has EMA weights
    num_keys: int                       # Number of keys
    metadata: Optional[Dict]            # Metadata if available
    error: Optional[str]                # Error message if invalid
```

---

## Checkpoint Metadata

### Metadata Format

Each checkpoint can have an associated `.metadata.json` file:

```json
{
  "checkpoint_name": "model_last.pt",
  "created_at": "2025-12-06T14:30:45",
  "size_bytes": 2516582400,
  "size_gb": 2.34,
  "hash_partial": "a3f8c9d2e1b4f7a9",
  "config": {
    "exp_name": "F5TTS_Base",
    "dataset_name": "f5_dataset",
    "learning_rate": 0.0002,
    "batch_size": 4,
    "epochs": 500
  },
  "training": {
    "num_warmup_updates": 200,
    "max_grad_norm": 1.0,
    "grad_accumulation_steps": 1
  },
  "metadata_version": "1.0"
}
```

### Automatic Metadata Generation

During training, a background monitor automatically adds metadata to checkpoints:

- Runs every 10 seconds
- Detects new/modified checkpoints
- Generates metadata JSON
- Updates when checkpoint is modified

### Metadata API

```python
from train.utils.checkpoint import (
    save_checkpoint_metadata,
    load_checkpoint_metadata
)

# Save metadata
metadata = {
    'checkpoint_name': 'model_50000.pt',
    'created_at': datetime.now().isoformat(),
    'config': {...},
    'training': {...}
}
save_checkpoint_metadata('/path/to/model.pt', metadata)

# Load metadata
metadata = load_checkpoint_metadata('/path/to/model.pt')
if metadata:
    print(f"Created: {metadata['created_at']}")
    print(f"LR: {metadata['config']['learning_rate']}")
```

---

## Auto-Resume Training

### How It Works

1. **On Training Start:**
   - System checks for existing checkpoints
   - Uses intelligent resolution to find latest valid checkpoint
   - Automatically resumes if found

2. **Resume vs Fine-tune:**
   - **Resume:** Checkpoint from `output_dir` → Continue same training run
   - **Fine-tune:** Checkpoint from elsewhere → Start new training from pretrained

3. **Validation:**
   - All checkpoints validated before use
   - Corrupted checkpoints automatically skipped
   - User notified of resolution decision

### Configuration

```yaml
# train/config/base_config.yaml

model:
  custom_checkpoint: ''                    # Explicit checkpoint (highest priority)
  auto_download_pretrained: true           # Download if no checkpoint found
  base_model: 'firstpixel/F5-TTS-pt-br'   # Model to download
  model_filename: 'pt-br/model_last.safetensors'

paths:
  output_dir: 'train/output/F5TTS_Base'   # Training checkpoints saved here
  pretrained_model_path: ''                # Pretrained model path (if local)
```

### Manual Resume

```bash
# Resume from specific checkpoint
python -m train.run_training --checkpoint /path/to/model.pt

# Resume from model_best.pt
python -m train.run_training --checkpoint model_best.pt

# Force fresh start (ignore existing checkpoints)
python -m train.run_training --no-resume
```

---

## PT-BR Model Compatibility

### The Problem

PT-BR checkpoints from `firstpixel/F5-TTS-pt-br` have incompatible key names:

- Keys use `ema.` prefix instead of `ema_model.`
- Keys have extra `model.` wrapper: `ema.model.transformer.xxx`
- Expected format: `ema_model.transformer.xxx`

### The Solution

Automatic patching applied transparently:

1. **Detection:**
   - Checks if checkpoint is `.safetensors` from `firstpixel`
   - Skips if already patched (`_patched` suffix)

2. **Patching:**
   - Replace `ema.` → `ema_model.`
   - Remove `model.` wrapper from transformer keys
   - Save to `<name>_patched.safetensors`

3. **Caching:**
   - Patched version saved for reuse
   - One-time operation per checkpoint

### Patch Details

```python
# Before patching
"ema.model.transformer.input_embed.proj.weight"

# After patching  
"ema_model.transformer.input_embed.proj.weight"
```

### Verification

```python
from train.utils.checkpoint import validate_checkpoint

# Validate PT-BR checkpoint (auto-patches if needed)
info = validate_checkpoint('model_last.safetensors')

if info.is_valid:
    print("✅ Checkpoint ready (patched if needed)")
```

---

## Best Practices

### During Training

1. **Regular Saves:**
   ```yaml
   training:
     save_per_updates: 10000    # Save numbered checkpoint every 10k updates
     last_per_updates: 1000     # Update model_last.pt every 1k updates
   ```

2. **Keep Multiple Checkpoints:**
   ```yaml
   training:
     keep_last_n_checkpoints: 5  # Keep 5 most recent numbered checkpoints
   ```

3. **Monitor Metadata:**
   - Metadata automatically added every 10 seconds
   - Check `.metadata.json` files to verify training config

### For Inference

1. **Use Intelligent Resolution:**
   ```python
   from train.utils.checkpoint import resolve_checkpoint_path
   checkpoint = resolve_checkpoint_path(config)
   ```

2. **Validate Before Loading:**
   ```python
   from train.utils.checkpoint import validate_checkpoint
   info = validate_checkpoint(checkpoint)
   if not info.is_valid:
       raise ValueError(f"Invalid checkpoint: {info.error}")
   ```

3. **Specify Custom Checkpoints:**
   ```yaml
   model:
     custom_checkpoint: '/app/train/output/model_best.pt'
   ```

### For Production

1. **Always Validate:**
   - Run validation before deploying checkpoint
   - Check metadata matches expected config

2. **Use model_best.pt:**
   - Best performing checkpoint for production
   - Created automatically when validation loss improves

3. **Keep Backups:**
   - Archive important checkpoints
   - Store with metadata for reproducibility

---

## Troubleshooting

### "No valid checkpoint found"

**Cause:** No checkpoints in resolution priority order

**Solution:**
1. Check `config.paths.output_dir` exists
2. Enable auto-download: `config.model.auto_download_pretrained = true`
3. Specify pretrained model: `config.paths.pretrained_model_path`

### "Checkpoint too small"

**Cause:** File < 1GB (likely incomplete download)

**Solution:**
1. Delete corrupted checkpoint
2. Re-download or re-train
3. Adjust minimum size: `validate_checkpoint(path, min_size_gb=0.5)`

### "Missing essential keys"

**Cause:** Checkpoint missing required state dict keys

**Solution:**
1. Check if checkpoint is from compatible F5-TTS version
2. For PT-BR: Ensure patching succeeded
3. Re-download pretrained model

### "PT-BR patching failed"

**Cause:** Error during key patching process

**Solution:**
1. Check disk space (patched checkpoint = 2x size)
2. Install safetensors: `pip install safetensors`
3. Download patched version manually from HuggingFace

### "Checkpoint corrupted after save"

**Cause:** Training interrupted during checkpoint save

**Solution:**
1. System auto-renames to `.corrupted`
2. Previous checkpoint used automatically
3. Increase `last_per_updates` to reduce save frequency

---

## Integration Examples

### Training Script

```python
from train.config.loader import load_config
from train.utils.checkpoint import resolve_checkpoint_path, validate_checkpoint

config = load_config()

# Resolve checkpoint for resume/fine-tune
checkpoint = resolve_checkpoint_path(config, auto_download=True, verbose=True)

if checkpoint:
    # Validate before use
    info = validate_checkpoint(checkpoint)
    if info.is_valid:
        print(f"✅ Resuming from: {checkpoint}")
        print(f"   Size: {info.size_gb}GB")
        print(f"   EMA: {'Yes' if info.has_ema else 'No'}")
    else:
        print(f"❌ Invalid checkpoint: {info.error}")
        checkpoint = None

# Start training
if checkpoint:
    train(pretrain=checkpoint)  # Resume or fine-tune
else:
    train()  # Train from scratch
```

### Inference Engine

```python
from train.config.loader import load_config
from train.utils.checkpoint import resolve_checkpoint_path
from app.engines.f5tts_engine import F5TtsEngine

config = load_config()

# Resolve best checkpoint
checkpoint = resolve_checkpoint_path(
    config,
    checkpoint_name='model_best.pt',  # Prefer best model
    auto_download=False,              # Don't download for inference
    verbose=True
)

# Initialize engine
engine = F5TtsEngine(
    custom_ckpt_path=checkpoint,
    device='cuda'
)

# Generate audio
audio = engine.synthesize("Olá, como vai?", ref_audio="reference.wav")
```

### CI/CD Pipeline

```bash
#!/bin/bash
# Validate checkpoint before deployment

python -m train.utils.checkpoint validate /app/checkpoints/model_best.pt

if [ $? -eq 0 ]; then
    echo "✅ Checkpoint valid, deploying..."
    cp /app/checkpoints/model_best.pt /production/model.pt
else
    echo "❌ Checkpoint validation failed, aborting deployment"
    exit 1
fi
```

---

## API Reference

### resolve_checkpoint_path()

```python
def resolve_checkpoint_path(
    config: F5TTSConfig,
    checkpoint_name: Optional[str] = None,
    auto_download: bool = True,
    verbose: bool = True
) -> Optional[str]
```

**Parameters:**
- `config` - F5TTSConfig object with model/path settings
- `checkpoint_name` - Specific checkpoint filename (optional)
- `auto_download` - Download from HF if no checkpoint found
- `verbose` - Print resolution process

**Returns:**
- Absolute path to checkpoint, or None if not found

**Raises:**
- No exceptions (returns None on failure)

---

### validate_checkpoint()

```python
def validate_checkpoint(
    checkpoint_path: str,
    min_size_gb: float = 1.0,
    check_keys: bool = True,
    verbose: bool = True
) -> CheckpointInfo
```

**Parameters:**
- `checkpoint_path` - Path to checkpoint file
- `min_size_gb` - Minimum expected size in GB
- `check_keys` - Check for essential keys
- `verbose` - Print validation details

**Returns:**
- `CheckpointInfo` object with validation results

**Raises:**
- No exceptions (returns info with `is_valid=False`)

---

### save_checkpoint_metadata()

```python
def save_checkpoint_metadata(
    checkpoint_path: str,
    metadata: Dict[str, Any],
    verbose: bool = True
) -> bool
```

**Parameters:**
- `checkpoint_path` - Path to checkpoint file
- `metadata` - Dictionary with metadata to save
- `verbose` - Print details

**Returns:**
- True if successfully saved, False otherwise

---

### load_checkpoint_metadata()

```python
def load_checkpoint_metadata(
    checkpoint_path: str
) -> Optional[Dict[str, Any]]
```

**Parameters:**
- `checkpoint_path` - Path to checkpoint file

**Returns:**
- Metadata dict, or None if not found

---

## Migration Guide

### From Legacy to New System

**Before (Legacy):**
```python
# Manual checkpoint resolution
checkpoint = 'train/output/model_last.pt'
if not os.path.exists(checkpoint):
    checkpoint = 'models/f5tts/pt-br/model_last.pt'

# Load without validation
model = load_model(checkpoint)
```

**After (New System):**
```python
from train.config.loader import load_config
from train.utils.checkpoint import resolve_checkpoint_path, validate_checkpoint

config = load_config()

# Intelligent resolution
checkpoint = resolve_checkpoint_path(config, verbose=True)

# Validation
info = validate_checkpoint(checkpoint)
if info.is_valid:
    model = load_model(checkpoint)
else:
    raise ValueError(f"Invalid checkpoint: {info.error}")
```

### Benefits

- ✅ **Automatic priority fallback** - No manual path checking
- ✅ **Validation** - Detect corruption early
- ✅ **Metadata** - Track training config with checkpoint
- ✅ **Auto-resume** - Seamless training continuation
- ✅ **PT-BR compatibility** - Automatic patching

---

## Performance

### Resolution Time

- **Cache hit:** <1ms (existing checkpoint)
- **Validation:** ~100ms (2GB checkpoint)
- **Download:** ~30s (2GB from HuggingFace)
- **PT-BR patch:** ~5s (one-time, cached)

### Storage

- **Checkpoint:** ~2GB
- **Metadata:** ~2KB
- **Patched PT-BR:** +2GB (one-time)

### Memory

- **Validation:** <100MB (checkpoint loaded to CPU)
- **Training:** No overhead (metadata runs in background thread)

---

## Version History

### v2.0 (Sprint 2 - December 2025)
- Intelligent checkpoint resolution with priority fallback
- Automatic validation and corruption detection
- Metadata tracking and persistence
- PT-BR checkpoint patching
- Auto-resume training
- CLI utilities

### v1.0 (Sprint 1 - November 2025)
- Basic checkpoint loading
- Manual path specification
- No validation or metadata

---

## See Also

- **[CONFIG_NEW.md](CONFIG_NEW.md)** - Configuration system documentation
- **[VOCAB.md](VOCAB.md)** - Vocabulary management
- **[SPRINTS_PLAN.md](../SPRINTS_PLAN.md)** - Sprint roadmap

---

**Questions or Issues?**

Check logs for detailed checkpoint resolution process. All operations print verbose output when `verbose=True`.
