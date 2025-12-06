# F5-TTS Training Examples

Example scripts demonstrating common F5-TTS training and inference tasks.

---

## 📋 Examples Overview

### Quick Reference

| Example | Description | Difficulty | Time |
|---------|-------------|------------|------|
| [01_quick_train.py](#1-quick-training-test) | 1-epoch training test | ⭐ Beginner | 5-30 min |
| [02_inference_simple.py](#2-simple-inference) | Basic voice synthesis | ⭐ Beginner | <1 min |
| [03_custom_dataset.py](#3-custom-dataset-creation) | Create dataset from audio files | ⭐⭐ Intermediate | 10-60 min |
| [04_resume_training.py](#4-resume-training) | Resume from checkpoint | ⭐⭐ Intermediate | Variable |

---

## 1. Quick Training Test

**File:** `01_quick_train.py`

Test the training pipeline with a single epoch. Useful for:
- Validating environment setup
- Testing configuration
- Debugging training issues

### Usage

```bash
# Simple run
python train/examples/01_quick_train.py

# What it does:
# 1. Checks environment (GPU, dependencies, VRAM)
# 2. Loads config.yaml
# 3. Validates dataset
# 4. Trains for 1 epoch
# 5. Reports results
```

### Requirements

- Dataset prepared in `train/data/processed/`
- Config file at `train/config/config.yaml`
- GPU with CUDA (recommended)

### Expected Output

```
📋 Step 1: Environment check
✅ CUDA available: 12.1
✅ GPU: NVIDIA RTX 3090 (24GB)
✅ Python: 3.11.2
...
🚀 Step 5: Start training (1 epoch)
...
✅ Quick training test complete!
```

---

## 2. Simple Inference

**File:** `02_inference_simple.py`

Generate speech from text using a trained model.

### Usage

```bash
# Run with defaults
python train/examples/02_inference_simple.py

# Output: output_example.wav
```

### Customization

Edit the file to change:

```python
# Input
text = "Seu texto aqui"
ref_audio = "path/to/reference.wav"  # 3-30s audio
ref_text = "Transcrição do áudio de referência"

# Quality settings
nfe_step = 32  # 16=fast, 32=balanced, 64=high
cfg_strength = 2.0  # 1.0=stable, 3.0=expressive
speed = 1.0  # 0.5-2.0

# Output
output_path = "my_output.wav"
```

### Requirements

- Trained checkpoint: `models/f5tts/model_last.pt`
- Vocab file: `train/config/vocab.txt`
- Reference audio (any 3-30s voice sample)

### Tips

**Quality vs Speed:**
- Fast: `nfe_step=16` (~2s generation)
- Balanced: `nfe_step=32` (~4s generation)
- High: `nfe_step=64` (~8s generation)

**Voice Cloning:**
- Use clean reference audio (no background noise)
- 5-15 seconds is optimal
- Provide accurate `ref_text` for best results

---

## 3. Custom Dataset Creation

**File:** `03_custom_dataset.py`

Process your own audio files into a training dataset.

### Usage

```bash
# Process audio directory
python train/examples/03_custom_dataset.py \
    --audio-dir /path/to/audio \
    --output-dir train/data/my_dataset

# With custom extensions
python train/examples/03_custom_dataset.py \
    --audio-dir /path/to/audio \
    --output-dir train/data/my_dataset \
    --audio-extensions .wav .mp3 .flac .m4a
```

### Input Structure

Your audio directory should contain:

```
audio_dir/
├── recording1.wav
├── recording1.txt  # Same name as audio
├── recording2.wav
├── recording2.txt
└── ...
```

Each `.txt` file contains the transcription for the corresponding audio.

### What It Does

1. **Loads audio files** (.wav, .mp3, .flac)
2. **Normalizes audio** (volume, sample rate)
3. **Detects voice** (removes silence)
4. **Splits into chunks** (max 30s per segment)
5. **Normalizes text** (numbers, punctuation, etc.)
6. **Quality checks** (length, special chars, etc.)
7. **Creates metadata.csv** (ready for training)

### Output

```
output_dir/
├── wavs/
│   ├── recording1_0000.wav
│   ├── recording1_0001.wav
│   ├── recording2_0000.wav
│   └── ...
└── metadata.csv  # audio_path|text|duration|speaker_id
```

### Next Steps

After creating dataset:

```bash
# 1. Review metadata
head train/data/my_dataset/metadata.csv

# 2. Update config.yaml
# paths:
#   dataset_path: "train/data/my_dataset"
#   dataset_name: "my_dataset"

# 3. Start training
python -m train.run_training --config train/config/config.yaml
```

### Requirements

- Audio files with transcriptions
- ~1GB disk space per hour of audio
- Silero VAD model (auto-downloaded)

---

## 4. Resume Training

**File:** `04_resume_training.py`

Continue training from a saved checkpoint.

### Usage

```bash
# Resume from specific checkpoint
python train/examples/04_resume_training.py \
    --checkpoint models/f5tts/model_100.pt

# Train for 10 additional epochs
python train/examples/04_resume_training.py \
    --checkpoint models/f5tts/model_100.pt \
    --additional-epochs 10

# Use different config
python train/examples/04_resume_training.py \
    --checkpoint models/f5tts/model_100.pt \
    --config train/config/config_finetuning.yaml
```

### When to Use

**Resume interrupted training:**
- Training crashed/stopped
- Power outage
- Out of memory error

**Fine-tuning:**
- Start from pretrained model
- Adapt to new speaker
- Improve specific quality

**Experimentation:**
- Test different learning rates
- Try different batch sizes
- Adjust training settings

### Checkpoint Info

The script shows checkpoint details:

```
📦 Checkpoint Info:
  File: models/f5tts/model_100.pt
  Epoch: 100
  Step: 50000
  Best loss: 0.0234
```

### Tips

**Learning Rate Adjustment:**

When resuming, consider reducing learning rate:

```yaml
# config.yaml
training:
  learning_rate: 1e-5  # Lower than initial 1e-4
```

**Fine-tuning Best Practices:**

1. **Start from good checkpoint:** Use `model_best.pt` or late epoch
2. **Use smaller dataset:** 30min-2h for voice adaptation
3. **Reduce learning rate:** 10x lower than initial
4. **Train fewer epochs:** 10-50 epochs usually enough
5. **Monitor quality:** Generate samples every few epochs

---

## 🎓 Learning Path

### For Beginners

1. **Start here:** [01_quick_train.py](#1-quick-training-test)
   - Test environment
   - Understand training flow
   - See if everything works

2. **Try inference:** [02_inference_simple.py](#2-simple-inference)
   - Generate speech
   - Test voice cloning
   - Experiment with parameters

### For Advanced Users

3. **Create dataset:** [03_custom_dataset.py](#3-custom-dataset-creation)
   - Process your audio
   - Build custom voice
   - Understand data pipeline

4. **Fine-tune:** [04_resume_training.py](#4-resume-training)
   - Resume training
   - Adapt models
   - Optimize quality

---

## 🔧 Troubleshooting

### Common Issues

**"Dataset not found"**
```bash
# Check dataset path
ls train/data/processed/metadata.csv

# Or create custom dataset
python train/examples/03_custom_dataset.py --audio-dir /path/to/audio
```

**"Checkpoint not found"**
```bash
# Check available checkpoints
ls models/f5tts/*.pt

# Or train new model first
python train/examples/01_quick_train.py
```

**"CUDA out of memory"**
```bash
# Reduce batch size in config.yaml
training:
  batch_size_per_gpu: 4  # Try 2 or 1

# Or use gradient accumulation
training:
  gradient_accumulation_steps: 4
```

**"Vocab file not found"**
```bash
# Check vocab location
ls train/config/vocab.txt

# Or specify custom vocab in code:
vocab_file = "path/to/custom_vocab.txt"
```

---

## 📚 Additional Resources

### Documentation

- [Complete Tutorial](../docs/TUTORIAL.md) - Step-by-step training guide
- [Inference API](../docs/INFERENCE_API.md) - Full API reference
- [Config Schema](../config/README.md) - Configuration options

### Scripts

- [Health Check](../scripts/health_check.py) - Validate environment
- [Download Models](../../scripts/download_models.py) - Get pretrained models
- [Batch Inference](../scripts/AgentF5TTSChunk.py) - Process multiple files

### Tests

- [Config Tests](../../tests/train/config/) - Test configuration
- [Inference Tests](../../tests/train/inference/) - Test inference API

---

## 🎯 Quick Commands

```bash
# Run all examples in sequence
python train/examples/01_quick_train.py
python train/examples/02_inference_simple.py
python train/examples/03_custom_dataset.py --audio-dir /path/to/audio
python train/examples/04_resume_training.py --checkpoint models/f5tts/model_last.pt

# Make examples executable
chmod +x train/examples/*.py

# Run with shebang
./train/examples/01_quick_train.py
```

---

## 📞 Support

**Issues?** Check:
1. [Troubleshooting](#troubleshooting)
2. [Tutorial](../docs/TUTORIAL.md) - Section 7: Troubleshooting
3. Logs in `train/logs/`

**Questions?** See:
- [Documentation Index](../docs/INDEX.md)
- [GitHub Issues](https://github.com/JohnHeberty/tts-webui-proxmox-passthrough/issues)

---

**Last Updated:** 2025-12-06  
**Version:** 1.0
