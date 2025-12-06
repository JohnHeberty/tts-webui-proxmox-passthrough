# Configuration System - New Unified Approach

**Status:** ✅ Implemented (Sprint 1, Task 2)  
**Date:** 2025-12-06  
**Old Doc:** `CONFIGURATION.md` (deprecated - kept for reference)

---

## 🎯 What Changed?

### Before (Old System)
- ❌ Config fragmented across 5+ files
- ❌ No type safety or validation
- ❌ Manual merging prone to errors
- ❌ Hardcoded paths everywhere
- ❌ Difficult to override values

### After (New System)
- ✅ Single source of truth (`base_config.yaml`)
- ✅ Type-safe with Pydantic validation
- ✅ Hierarchical overrides (YAML → ENV → CLI)
- ✅ Centralized path management
- ✅ Easy CLI overrides

---

## 📁 File Structure

```
train/config/
├── base_config.yaml        # ⭐ Single source of truth
├── schemas.py              # Pydantic validation models
├── loader.py               # Config loading logic
├── example_usage.py        # Usage examples
└── vocab.txt               # Vocabulary (SOURCE OF TRUTH)
```

---

## 🚀 Quick Start

### Load Configuration

```python
from train.config.loader import load_config

# Load default config (base + .env overrides)
config = load_config()

# Access values (type-safe!)
lr = config.training.learning_rate  # 0.0001
batch = config.training.batch_size_per_gpu  # 2
device = config.hardware.device  # "cuda"
```

### Override with CLI

```python
# Override specific values
config = load_config(cli_overrides={
    "training": {
        "learning_rate": 2e-4,
        "epochs": 500
    },
    "hardware": {
        "device": "cpu"
    }
})
```

---

## 🔄 Configuration Hierarchy

```
1. base_config.yaml     (defaults)
   ↓
2. .env files           (environment overrides)
   ↓  
3. CLI arguments        (highest priority)
   ↓
4. Final validated config
```

**Example:**
```yaml
# base_config.yaml
training:
  learning_rate: 1.0e-4
```

```bash
# train/.env
LEARNING_RATE=2.0e-4
```

```python
# CLI
cli_overrides = {"training": {"learning_rate": 3e-4}}
```

**Result:** `3e-4` (CLI wins)

---

## 📚 Main Sections

### 1. Paths

All project paths centralized:

```python
config.paths.dataset_path          # "train/data/f5_dataset"
config.paths.vocab_file            # "train/config/vocab.txt"
config.paths.pretrained_model_path # "train/pretrained/..."
config.paths.output_dir            # "train/output/..."
```

### 2. Model

Architecture and checkpoints:

```python
config.model.base_model   # "firstpixel/F5-TTS-pt-br"
config.model.model_type   # "DiT"
config.model.dim          # 1024
config.model.depth        # 22
config.model.use_ema      # True
```

### 3. Training

Hyperparameters:

```python
config.training.learning_rate          # 1e-4
config.training.batch_size_per_gpu     # 2
config.training.grad_accumulation_steps # 8
config.training.epochs                 # 1000
config.training.num_warmup_updates     # 200
```

### 4. Hardware

Device and parallelization:

```python
config.hardware.device             # "cuda"
config.hardware.num_gpus           # 1
config.hardware.dataloader_workers # 8
config.hardware.pin_memory         # True
```

### 5. Checkpoints

Save strategy:

```python
config.checkpoints.save_per_updates       # 500
config.checkpoints.keep_last_n_checkpoints # 3
config.checkpoints.log_samples            # True
```

### 6. Logging

TensorBoard / W&B:

```python
config.logging.logger               # "tensorboard"
config.logging.log_every_n_steps    # 10
config.logging.wandb.enabled        # False
config.logging.wandb.project        # "f5tts-ptbr-finetune"
```

### 7. Mixed Precision

AMP settings:

```python
config.mixed_precision.enabled  # False
config.mixed_precision.dtype    # "fp16"
```

### 8. Audio Processing

Dataset preparation:

```python
config.audio.target_sample_rate  # 24000
config.audio.normalize_audio     # True
config.audio.target_lufs         # -23.0
```

### 9. Segmentation

Audio chunking:

```python
config.segmentation.min_duration  # 3.0
config.segmentation.max_duration  # 10.0
config.segmentation.use_vad       # True
```

### 10. Transcription

Whisper ASR:

```python
config.transcription.asr.model      # "base"
config.transcription.asr.language   # "pt"
config.transcription.asr.beam_size  # 5
```

---

## ✅ Validation

Pydantic automatically validates:

### Type Safety

```python
# ✅ Valid
config = load_config(cli_overrides={
    "training": {"learning_rate": 2e-4}  # float
})

# ❌ Invalid - ValidationError!
config = load_config(cli_overrides={
    "training": {"learning_rate": "fast"}  # str - wrong type!
})
```

### Range Constraints

```python
# ❌ learning_rate must be > 0
config = load_config(cli_overrides={
    "training": {"learning_rate": -0.001}
})

# ❌ batch_size must be >= 1
config = load_config(cli_overrides={
    "training": {"batch_size_per_gpu": 0}
})
```

### Custom Validations

```python
# ❌ train_ratio + val_ratio must equal 1.0
config = load_config(cli_overrides={
    "split": {
        "train_ratio": 0.8,
        "val_ratio": 0.3  # 0.8 + 0.3 = 1.1 != 1.0
    }
})
```

---

## 🌍 Environment Variables

Map to config structure:

```bash
# train/.env

# Training
LEARNING_RATE=2.0e-4
BATCH_SIZE_PER_GPU=4
EPOCHS=500
GRAD_ACCUMULATION_STEPS=8

# Hardware
NUM_WORKERS=2
DATALOADER_WORKERS=8

# Mixed Precision
MIXED_PRECISION=true
MIXED_PRECISION_DTYPE=fp16

# Logging
LOGGER=tensorboard
WANDB_ENABLED=true
WANDB_PROJECT=my-project

# Paths
DATASET_NAME=f5_dataset
OUTPUT_DIR=train/output/my_exp

# Advanced
SEED=666
GRADIENT_CHECKPOINTING=true
```

Full mapping in `train/config/loader.py::load_env_overrides()`.

---

## 🖥️ CLI Integration

### Argparse Example

```python
import argparse
from train.config.loader import load_config

parser = argparse.ArgumentParser()
parser.add_argument('--lr', type=float)
parser.add_argument('--batch-size', type=int)
parser.add_argument('--device', type=str)
parser.add_argument('--exp-name', type=str)
args = parser.parse_args()

# Convert to config overrides
cli_overrides = {}
if args.lr:
    cli_overrides.setdefault('training', {})['learning_rate'] = args.lr
if args.batch_size:
    cli_overrides.setdefault('training', {})['batch_size_per_gpu'] = args.batch_size
if args.device:
    cli_overrides.setdefault('hardware', {})['device'] = args.device
if args.exp_name:
    cli_overrides.setdefault('training', {})['exp_name'] = args.exp_name

# Load validated config
config = load_config(cli_overrides=cli_overrides)
```

**Usage:**
```bash
python run_training.py --lr 3e-4 --batch-size 8 --exp-name my_exp
```

---

## 🛠️ Utilities

### Print Summary

```python
from train.config.loader import print_config_summary

config = load_config()
print_config_summary(config)
```

**Output:**
```
================================================================================
F5-TTS TRAINING CONFIGURATION
================================================================================

📁 PATHS:
  Dataset: train/data/f5_dataset
  Pretrained: train/pretrained/F5-TTS-pt-br/pt-br/model_200000_fixed.pt
  Output: train/output/ptbr_finetuned2

🧠 MODEL:
  Type: DiT, Dim: 1024, Depth: 22, Heads: 16

🎓 TRAINING:
  LR: 0.0001, Batch: 2, Epochs: 1000
...
```

### Save for Reproducibility

```python
from train.config.loader import save_config_to_yaml

config = load_config(cli_overrides={...})
save_config_to_yaml(config, "train/output/experiment_config.yaml")
```

---

## 🧪 Testing

```bash
# Test basic loading
python3 -m train.config.loader

# Test with save
python3 -m train.config.loader --save train/output/test_config.yaml

# Run examples
python3 -m train.config.example_usage
```

---

## 🔄 Migration from Old System

### Before

```python
# ❌ Old fragmented approach
import yaml
from train.utils.env_loader import load_env_config

with open("train_config.yaml") as f:
    train_cfg = yaml.safe_load(f)

env = load_env_config("train/.env")

# Manual merge (error-prone)
lr = float(env.get("LEARNING_RATE", train_cfg["learning_rate"]))
batch = int(env.get("BATCH_SIZE", train_cfg["batch_size"]))

# No validation
if lr < 0:
    raise ValueError("Invalid learning rate")
```

### After

```python
# ✅ New unified approach
from train.config.loader import load_config

# Everything validated automatically
config = load_config()

# Type-safe access
lr = config.training.learning_rate  # float, validated > 0
batch = config.training.batch_size_per_gpu  # int, validated >= 1
```

---

## ✨ Best Practices

1. **Never hardcode** → Always use `config.*`
2. **Load once** → At script start, pass config object around
3. **CLI overrides** → For quick experiments
4. **Save config** → For reproducibility (`save_config_to_yaml`)
5. **Validate early** → Let Pydantic catch errors immediately
6. **Immutable** → Don't try to modify config after loading

---

## 🐛 Troubleshooting

### ModuleNotFoundError

```bash
# ❌ Wrong
python train/config/loader.py

# ✅ Correct
python -m train.config.loader
```

### ValidationError

Read the error message:

```
ValidationError: 1 validation error for F5TTSConfig
training.learning_rate
  Input should be greater than 0 [type=greater_than, input_value=-0.001]
```

**Fix:** Adjust value to meet constraint (`> 0`).

---

## 📋 Complete Example

```python
#!/usr/bin/env python3
"""Training script with unified config."""

import argparse
from train.config.loader import load_config, print_config_summary, save_config_to_yaml

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--lr', type=float)
    parser.add_argument('--batch-size', type=int)
    parser.add_argument('--epochs', type=int)
    parser.add_argument('--exp-name', type=str, default='experiment')
    args = parser.parse_args()
    
    # Convert to overrides
    cli_overrides = {"training": {"exp_name": args.exp_name}}
    if args.lr:
        cli_overrides["training"]["learning_rate"] = args.lr
    if args.batch_size:
        cli_overrides["training"]["batch_size_per_gpu"] = args.batch_size
    if args.epochs:
        cli_overrides["training"]["epochs"] = args.epochs
    
    # Load validated config
    config = load_config(cli_overrides=cli_overrides)
    
    # Print summary
    print_config_summary(config)
    
    # Save for reproducibility
    save_path = f"{config.paths.output_dir}/config.yaml"
    save_config_to_yaml(config, save_path)
    
    # Use config
    print(f"\n🚀 Training:")
    print(f"   LR: {config.training.learning_rate}")
    print(f"   Batch: {config.training.batch_size_per_gpu}")
    print(f"   Epochs: {config.training.epochs}")
    
    # Train model...

if __name__ == '__main__':
    main()
```

---

## 📊 Migration Status

| Component | Old System | New System | Status |
|-----------|-----------|------------|--------|
| Base Config | train_config.yaml, dataset_config.yaml | base_config.yaml | ✅ Done |
| Schemas | None | schemas.py | ✅ Done |
| Loader | Manual | loader.py | ✅ Done |
| Validation | Manual checks | Pydantic | ✅ Done |
| Examples | None | example_usage.py | ✅ Done |
| Documentation | CONFIGURATION.md | CONFIG_NEW.md | ✅ Done |
| run_training.py | Old config | New config | ⬜ Todo (S1-T4) |
| Inference scripts | Old config | New config | ⬜ Todo (S1-T5) |

---

## 🎯 Next Steps (Sprint 1)

- ⬜ **S1-T3:** Consolidate vocabulary with hash validation
- ⬜ **S1-T4:** Refactor `run_training.py` to use new config
- ⬜ **S1-T5:** Refactor inference scripts (`AgentF5TTSChunk.py`, `test.py`)
- ⬜ **S1-T6:** Deprecate old config files

---

## 📖 See Also

- `base_config.yaml` - Complete config reference
- `schemas.py` - Pydantic models and validation rules
- `loader.py` - Loading logic and env mapping
- `example_usage.py` - 7 usage examples
- `CONFIGURATION.md` (old) - Legacy docs (kept for reference)
