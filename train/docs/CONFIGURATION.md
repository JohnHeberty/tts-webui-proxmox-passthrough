# Configuration Reference

## Environment Variables (.env)

### Training Parameters

| Variable | Default | Description |
|----------|---------|-------------|
| `EPOCHS` | 1000 | Número máximo de epochs de treinamento |
| `BATCH_SIZE` | 4 | Tamanho do batch (ajustar conforme VRAM) |
| `LEARNING_RATE` | 0.0001 | Taxa de aprendizado (Adam optimizer) |
| `GRAD_ACCUMULATION_STEPS` | 4 | Acumular gradientes para simular batch maior |

### Early Stopping

| Variable | Default | Description |
|----------|---------|-------------|
| `EARLY_STOP_PATIENCE` | 1000 | Parar se não melhorar em N epochs |
| `EARLY_STOP_MIN_DELTA` | 0.001 | Melhoria mínima considerada significativa |

### Checkpointing

| Variable | Default | Description |
|----------|---------|-------------|
| `SAVE_PER_UPDATES` | 250 | Salvar checkpoint completo a cada N updates |
| `LAST_PER_UPDATES` | 50 | Salvar checkpoint_last a cada N updates |
| `KEEP_LAST_N_CHECKPOINTS` | 10 | Manter apenas N checkpoints mais recentes |
| `LOG_SAMPLES_PER_UPDATES` | 250 | Gerar samples de áudio a cada N updates |

### Paths

| Variable | Default | Description |
|----------|---------|-------------|
| `DATASET_NAME` | ptbr_youtube_custom | Nome do dataset |
| `DATASET_PATH` | train/data/f5_dataset | Path do dataset |
| `OUTPUT_DIR` | train/output/ptbr_finetuned | Onde salvar checkpoints |
| `TENSORBOARD_DIR` | train/runs | Logs do TensorBoard |

### Model

| Variable | Default | Description |
|----------|---------|-------------|
| `BASE_MODEL` | firstpixel/F5-TTS-pt-br | Modelo pré-treinado para fine-tuning |
| `CHECKPOINT_PATH` | ./models/f5tts/pt-br/model_last.safetensors | Checkpoint inicial |
| `VOCAB_FILE` | ./models/f5tts/pt-br/vocab.txt | Vocabulário (44 caracteres PT-BR) |

### Hardware

| Variable | Default | Description |
|----------|---------|-------------|
| `DEVICE` | cuda | Device PyTorch (cuda/cpu) |
| `NUM_WORKERS` | 4 | Workers para DataLoader |
| `MIXED_PRECISION` | fp16 | Precisão mista (fp16/fp32) |

### Logging

| Variable | Default | Description |
|----------|---------|-------------|
| `LOGGER` | tensorboard | Logger backend |
| `LOG_SAMPLES` | true | Gerar samples durante treinamento |
| `LOG_SAMPLES_PER_EPOCHS` | 1 | Samples por epoch |

### Advanced

| Variable | Default | Description |
|----------|---------|-------------|
| `SEED` | 666 | Random seed para reproducibilidade |
| `NUM_WARMUP_UPDATES` | 200 | Updates de warmup para learning rate |

## Configurações Recomendadas por GPU

### RTX 3090 (24GB VRAM)
```env
BATCH_SIZE=4
GRAD_ACCUMULATION_STEPS=4
MIXED_PRECISION=fp16
```

### RTX 4090 (24GB VRAM)
```env
BATCH_SIZE=6
GRAD_ACCUMULATION_STEPS=4
MIXED_PRECISION=fp16
```

### A100 (40GB VRAM)
```env
BATCH_SIZE=8
GRAD_ACCUMULATION_STEPS=2
MIXED_PRECISION=fp16
```

### RTX 3060 (12GB VRAM)
```env
BATCH_SIZE=2
GRAD_ACCUMULATION_STEPS=8
MIXED_PRECISION=fp16
```

## Ajustes para Convergência

**Treinamento muito lento:**
```env
LEARNING_RATE=0.0002          # Aumentar learning rate
NUM_WARMUP_UPDATES=100        # Reduzir warmup
```

**Overfitting:**
```env
LEARNING_RATE=0.00005         # Reduzir learning rate
EARLY_STOP_PATIENCE=5         # Early stop mais agressivo
```

**Underfitting:**
```env
EPOCHS=2000                   # Mais epochs
EARLY_STOP_PATIENCE=1000      # Permitir mais tempo
```

## Exemplo Completo

```env
# Configuração balanceada para RTX 3090
EPOCHS=1000
BATCH_SIZE=4
LEARNING_RATE=0.0001
GRAD_ACCUMULATION_STEPS=4

EARLY_STOP_PATIENCE=10
EARLY_STOP_MIN_DELTA=0.001

SAVE_PER_UPDATES=250
LAST_PER_UPDATES=50
KEEP_LAST_N_CHECKPOINTS=10
LOG_SAMPLES_PER_UPDATES=250

DATASET_NAME=ptbr_youtube_custom
DATASET_PATH=train/data/f5_dataset

BASE_MODEL=firstpixel/F5-TTS-pt-br
OUTPUT_DIR=train/output/ptbr_finetuned
TENSORBOARD_DIR=train/runs

DEVICE=cuda
NUM_WORKERS=4
MIXED_PRECISION=fp16

LOGGER=tensorboard
LOG_SAMPLES=true
LOG_SAMPLES_PER_EPOCHS=1

SEED=666
NUM_WARMUP_UPDATES=200
```
