# Usage Guide

## Starting Training

### Option 1: Simple Script (Recommended)
```bash
./run.sh
```
This will:
- ✅ Start TensorBoard automatically at http://192.168.18.134:6006
- ✅ Load configuration from `train/.env`
- ✅ Auto-resume from last checkpoint if exists
- ✅ Show live progress bars
- ✅ Handle cleanup on exit

### Option 2: Direct Python
```bash
cd train
python3 run_training.py
```

## Monitoring Training

### TensorBoard (Real-time Metrics)
```bash
# Auto-started by run.sh
# Access: http://192.168.18.134:6006

# Manual start if needed:
tensorboard --logdir=train/runs --host=0.0.0.0 --port=6006
```

**Available metrics:**
- `loss/train` - Training loss over time
- `learning_rate` - Learning rate schedule
- `samples/audio` - Generated audio samples

### Terminal Output
```
Epoch 16/1000:  68%|██████▊   | 51/75 [02:17<00:58,  2.44s/update, loss=0.82, update=1173]
```

- **Epoch**: Current epoch / total epochs
- **Progress**: Percentage through current epoch
- **Update**: Total training updates (steps)
- **Loss**: Current batch loss

## Understanding Outputs

### Checkpoints
```
train/output/ptbr_finetuned/
├── model_last.pt           # Latest checkpoint (auto-resume)
├── model_250.pt            # Full checkpoint @ update 250
├── model_500.pt            # Full checkpoint @ update 500
├── model_750.pt            # Full checkpoint @ update 750
└── ...
```

**Checkpoint types:**
- `model_last.pt` - Updated every 50 updates, used for resuming
- `model_N.pt` - Full checkpoints every 250 updates (configurable)

### Audio Samples
```
train/output/ptbr_finetuned/samples/
├── sample_250_0.wav
├── sample_250_1.wav
├── sample_500_0.wav
└── ...
```

Generated every 250 updates to monitor voice quality improvement.

### TensorBoard Logs
```
train/runs/
└── None/                   # Run directory
    ├── events.out.tfevents.*
    └── ...
```

## Resuming Training

Training automatically resumes if `model_last.pt` exists:

```bash
# Just run again, it will continue from last checkpoint
./run.sh
```

**Manual checkpoint selection:**
```bash
# Edit train/.env
CHECKPOINT_PATH=train/output/ptbr_finetuned/model_500.pt
```

## Stopping Training

### Graceful Stop
```bash
Ctrl+C  # Press once, waits for current epoch to finish
```

### Force Stop
```bash
Ctrl+C  # Press twice to force immediate stop
```

## Early Stopping

Training automatically stops when:
1. **Max epochs reached**: `EPOCHS=1000` (configurable)
2. **No improvement**: Loss doesn't improve for N epochs (`EARLY_STOP_PATIENCE`)

Example:
```
Epoch 45: loss=0.420
Epoch 46: loss=0.422
Epoch 47: loss=0.423
...
Epoch 55: loss=0.425
⚠️  Early stopping triggered: no improvement for 10 epochs
✅ Best model: epoch 45 (loss=0.420)
```

## Analyzing Results

### Check Training Metrics
```bash
# View TensorBoard
tensorboard --logdir=train/runs --port=6006

# Check logs
tail -f train/logs/tensorboard.log
```

### Listen to Samples
```bash
# Play latest sample
mpv train/output/ptbr_finetuned/samples/sample_latest.wav

# Compare samples over time
ls -lh train/output/ptbr_finetuned/samples/
```

### Checkpoint Info
```python
import torch
ckpt = torch.load('train/output/ptbr_finetuned/model_last.pt')
print(f"Epoch: {ckpt['epoch']}")
print(f"Updates: {ckpt['updates']}")
print(f"Loss: {ckpt['loss']:.4f}")
```

## Common Workflows

### Quick Test (10 epochs)
```bash
# Edit .env
EPOCHS=10
EARLY_STOP_PATIENCE=1000  # Disable early stop

# Run
./run.sh
```

### Full Training
```bash
# Edit .env
EPOCHS=1000
EARLY_STOP_PATIENCE=10

# Run
./run.sh
```

### Continue Interrupted Training
```bash
# Just run again - auto-resumes from model_last.pt
./run.sh
```

### Compare Different Configurations
```bash
# Run 1
cp train/.env train/.env.backup
# Edit .env with config A
./run.sh
mv train/output/ptbr_finetuned train/output/run_config_a

# Run 2
# Edit .env with config B
./run.sh
mv train/output/ptbr_finetuned train/output/run_config_b

# Compare in TensorBoard
tensorboard --logdir=train/output --port=6006
```

## Performance Tips

**Faster training:**
- Increase `BATCH_SIZE` (if VRAM allows)
- Reduce `GRAD_ACCUMULATION_STEPS`
- Use `MIXED_PRECISION=fp16`

**Better quality:**
- More `EPOCHS`
- Lower `LEARNING_RATE`
- Larger dataset

**Less disk usage:**
- Reduce `KEEP_LAST_N_CHECKPOINTS`
- Increase `SAVE_PER_UPDATES`
- Disable `LOG_SAMPLES=false`

## Troubleshooting

**Training not starting:**
```bash
# Check dataset
ls train/data/f5_dataset/audio/ | wc -l
head train/data/f5_dataset/metadata.csv

# Check GPU
nvidia-smi
```

**Loss not decreasing:**
- Try lower learning rate
- Check dataset quality
- Increase warmup steps
- Verify checkpoint loaded correctly

**TensorBoard not accessible:**
```bash
# Check if running
ps aux | grep tensorboard

# Check port
lsof -i :6006

# Restart manually
pkill -f tensorboard
tensorboard --logdir=train/runs --host=0.0.0.0 --port=6006 &
```

**Out of memory:**
```bash
# Reduce batch size
BATCH_SIZE=2
GRAD_ACCUMULATION_STEPS=8

# Or use smaller precision
MIXED_PRECISION=fp16
```
