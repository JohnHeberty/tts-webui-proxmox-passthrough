# Referência Completa de Configuração

**Última Atualização:** 04/12/2025  
**Arquivo:** `train/.env`

---

## 📋 Índice

1. [Parâmetros de Treinamento](#parâmetros-de-treinamento)
2. [Early Stopping](#early-stopping)
3. [Checkpoint Management](#checkpoint-management)
4. [Dataset](#dataset)
5. [Model (Fine-tuning)](#model-fine-tuning)
6. [Paths](#paths)
7. [Hardware](#hardware)
8. [Logging](#logging)
9. [Advanced](#advanced)
10. [F5-TTS Paths (Opcional)](#f5-tts-paths-opcional)
11. [Data Preparation](#data-preparation)
12. [Perfis por GPU](#perfis-por-gpu)

---

## 🎯 Parâmetros de Treinamento

Configurações principais que afetam o processo de treinamento.

| Variável | Padrão | Range | Descrição |
|----------|--------|-------|-----------|
| `EPOCHS` | 1000 | 1-10000 | Número máximo de épocas de treinamento |
| `BATCH_SIZE` | 2 | 1-16 | Amostras por GPU (ajustar conforme VRAM) |
| `BATCH_SIZE_TYPE` | sample | sample/frame | Tipo de batch (sample recomendado) |
| `LEARNING_RATE` | 0.0001 | 0.00001-0.001 | Taxa de aprendizado (Adam optimizer) |
| `GRAD_ACCUMULATION_STEPS` | 8 | 1-32 | Acumular gradientes para simular batch maior |
| `MAX_GRAD_NORM` | 1.0 | 0.1-10.0 | Gradient clipping para estabilidade |

**Dica:** `BATCH_SIZE * GRAD_ACCUMULATION_STEPS` = effective batch size

---

## 🛑 Early Stopping

Para automático quando não houver mais melhoria.

| Variável | Padrão | Descrição |
|----------|--------|-----------|
| `EARLY_STOP_PATIENCE` | 1000 | Parar se não melhorar em N épocas |
| `EARLY_STOP_MIN_DELTA` | 0.001 | Melhoria mínima considerada significativa |

**Exemplo:**
- Se loss não melhorar > 0.001 por 1000 épocas → para automaticamente

---

## 💾 Checkpoint Management

Controle de salvamento de checkpoints.

| Variável | Padrão | Descrição |
|----------|--------|-----------|
| `SAVE_PER_UPDATES` | 100 | Salvar checkpoint completo a cada N updates |
| `LAST_PER_UPDATES` | 50 | Atualizar `model_last.pt` a cada N updates |
| `KEEP_LAST_N_CHECKPOINTS` | 10 | Manter apenas N checkpoints (economiza espaço) |
| `LOG_SAMPLES_PER_UPDATES` | 100 | Gerar samples de áudio a cada N updates |

**Cálculo de Espaço:**
- 1 checkpoint = ~5GB
- 10 checkpoints = ~50GB

---

## 📊 Dataset

Configuração do dataset de treinamento.

| Variável | Padrão | Descrição |
|----------|--------|-----------|
| `DATASET_NAME` | f5_dataset | Nome do dataset (usado em symlinks) |
| `DATASET_PATH` | train/data/f5_dataset | Caminho completo do dataset |

**Estrutura Esperada:**
```
train/data/f5_dataset/
├── metadata.csv      # Metadados (path, text, speaker)
├── wavs/            # Arquivos de áudio
│   ├── audio_001.wav
│   ├── audio_002.wav
│   └── ...
├── vocab.txt        # Vocabulário (gerado automaticamente)
└── raw.arrow        # Dataset em formato Arrow
```

---

## 🎯 Model (Fine-tuning)

Configuração do modelo base para fine-tuning.

| Variável | Padrão | Descrição |
|----------|--------|-----------|
| `BASE_MODEL` | firstpixel/F5-TTS-pt-br | Repo do HuggingFace |
| `PRETRAIN_MODEL_PATH` | train/pretrained/.../model_200000_fixed.pt | Path do checkpoint pretrained |
| `AUTO_DOWNLOAD_PRETRAINED` | true | Baixar automaticamente se não existir |
| `USE_FINETUNE_FLAG` | true | Usar flag --finetune no treinamento |
| `MODEL_FILENAME` | pt-br/model_200000.pt | Arquivo a baixar do HuggingFace |

**Fluxo de Fine-tuning:**
1. Se `AUTO_DOWNLOAD_PRETRAINED=true` e modelo não existe → baixa
2. Inicia treinamento com `--finetune --pretrain <path>`
3. Continua do checkpoint mais recente se existir

---

## 📁 Paths

Diretórios principais do projeto.

| Variável | Padrão | Descrição |
|----------|--------|-----------|
| `OUTPUT_DIR` | train/output/ptbr_finetuned | Onde salvar checkpoints e samples |
| `TENSORBOARD_DIR` | train/runs | Logs do TensorBoard |
| `LOG_DIR` | train/logs | Logs de execução |

**Nota:** Todos os paths são relativos ao root do projeto.

---

## 💻 Hardware

Configurações de hardware e otimização.

| Variável | Padrão | Descrição |
|----------|--------|-----------|
| `DEVICE` | cuda | Device PyTorch (cuda/cpu/mps) |
| `NUM_WORKERS` | 2 | Workers para DataLoader (ajustar conforme CPU) |
| `MIXED_PRECISION` | fp16 | Precisão mista (fp16/fp32/bf16) |
| `MAX_SAMPLES` | 32 | Máximo de samples por batch |

**Otimização VRAM:**
- `fp16` reduz uso de VRAM em ~50%
- `NUM_WORKERS=0` se tiver problemas de memória RAM

---

## 📊 Logging

Configuração de logs e monitoramento.

| Variável | Padrão | Descrição |
|----------|--------|-----------|
| `LOGGER` | tensorboard | Backend de logging (tensorboard/wandb) |
| `LOG_SAMPLES` | true | Gerar samples de áudio durante treino |
| `LOG_SAMPLES_PER_EPOCHS` | 1 | Quantos samples gerar por época |
| `TENSORBOARD_PORT` | 6006 | Porta do TensorBoard |

**TensorBoard:**
```bash
# Auto-inicia em http://localhost:6006
# Métricas: loss, learning rate, gradient norm, samples
```

---

## 🔧 Advanced

Configurações avançadas.

| Variável | Padrão | Descrição |
|----------|--------|-----------|
| `SEED` | 666 | Random seed para reproducibilidade |
| `NUM_WARMUP_UPDATES` | 200 | Updates de warmup para learning rate |
| `EXP_NAME` | F5TTS_Base | Nome do experimento (usado em logs) |

---

## 🛠️ F5-TTS Paths (Opcional)

Paths internos do F5-TTS. **Só customizar se necessário!**

| Variável | Padrão | Descrição |
|----------|--------|-----------|
| `F5TTS_BASE_DIR` | /root/.local/lib/python3.11 | Diretório base do F5-TTS |
| `F5TTS_CKPTS_DIR` | /root/.local/lib/python3.11/ckpts | Diretório de checkpoints |
| `LOCAL_PRETRAINED_PATH` | models/f5tts/pt-br/model_last.pt | Path alternativo de modelo |

**⚠️ Aviso:** Deixe comentado a menos que tenha instalação customizada!

---

## 📦 Data Preparation

Paths para scripts de preparação de dados.

| Variável | Padrão | Descrição |
|----------|--------|-----------|
| `RAW_DATA_DIR` | train/data/raw | Áudio bruto do YouTube |
| `PROCESSED_DATA_DIR` | train/data/processed | Segmentos processados |
| `VIDEOS_CSV` | train/data/videos.csv | Lista de vídeos para download |
| `CONFIG_DIR` | train/config | Configs YAML |

**Pipeline:**
```
videos.csv → RAW_DATA_DIR → PROCESSED_DATA_DIR → DATASET_PATH
```

---

## 🎮 Perfis por GPU

### 🟢 RTX 3090 / RTX 4090 (24GB VRAM)
```env
BATCH_SIZE=4
GRAD_ACCUMULATION_STEPS=4
MIXED_PRECISION=fp16
NUM_WORKERS=4
MAX_SAMPLES=64
```
**Effective Batch:** 16 samples  
**VRAM Usage:** ~20GB

---

### 🟡 RTX 3080 / RTX 4080 (16GB VRAM)
```env
BATCH_SIZE=2
GRAD_ACCUMULATION_STEPS=8
MIXED_PRECISION=fp16
NUM_WORKERS=2
MAX_SAMPLES=32
```
**Effective Batch:** 16 samples  
**VRAM Usage:** ~14GB

---

### 🟠 RTX 3070 / RTX 4070 (12GB VRAM)
```env
BATCH_SIZE=1
GRAD_ACCUMULATION_STEPS=16
MIXED_PRECISION=fp16
NUM_WORKERS=2
MAX_SAMPLES=16
```
**Effective Batch:** 16 samples  
**VRAM Usage:** ~10GB

---

### 🔴 RTX 3060 / Outras (8GB VRAM)
```env
BATCH_SIZE=1
GRAD_ACCUMULATION_STEPS=8
MIXED_PRECISION=fp16
NUM_WORKERS=1
MAX_SAMPLES=8
```
**Effective Batch:** 8 samples  
**VRAM Usage:** ~7GB  
**⚠️ Pode ser muito lento!**

---

## 📝 Exemplo Completo (.env)

```env
# ========================================
# BASIC TRAINING
# ========================================
EPOCHS=1000
BATCH_SIZE=4
BATCH_SIZE_TYPE=sample
LEARNING_RATE=0.0001
GRAD_ACCUMULATION_STEPS=8
MAX_GRAD_NORM=1.0

# ========================================
# EARLY STOPPING
# ========================================
EARLY_STOP_PATIENCE=100
EARLY_STOP_MIN_DELTA=0.001

# ========================================
# CHECKPOINTS
# ========================================
SAVE_PER_UPDATES=1000
LAST_PER_UPDATES=100
KEEP_LAST_N_CHECKPOINTS=10
LOG_SAMPLES_PER_UPDATES=250

# ========================================
# DATASET
# ========================================
DATASET_NAME=f5_dataset
DATASET_PATH=train/data/f5_dataset

# ========================================
# MODEL (FINE-TUNING)
# ========================================
BASE_MODEL=firstpixel/F5-TTS-pt-br
PRETRAIN_MODEL_PATH=train/pretrained/F5-TTS-pt-br/pt-br/model_200000.pt
AUTO_DOWNLOAD_PRETRAINED=true
USE_FINETUNE_FLAG=true
MODEL_FILENAME=pt-br/model_200000.pt

# ========================================
# PATHS
# ========================================
OUTPUT_DIR=train/output/ptbr_finetuned
TENSORBOARD_DIR=train/runs
LOG_DIR=train/logs

# ========================================
# HARDWARE
# ========================================
DEVICE=cuda
NUM_WORKERS=4
MIXED_PRECISION=fp16
MAX_SAMPLES=32

# ========================================
# LOGGING
# ========================================
LOGGER=tensorboard
LOG_SAMPLES=true
LOG_SAMPLES_PER_EPOCHS=1
TENSORBOARD_PORT=6006

# ========================================
# ADVANCED
# ========================================
SEED=666
NUM_WARMUP_UPDATES=200
EXP_NAME=F5TTS_Base

# ========================================
# DATA PREPARATION
# ========================================
RAW_DATA_DIR=train/data/raw
PROCESSED_DATA_DIR=train/data/processed
VIDEOS_CSV=train/data/videos.csv
CONFIG_DIR=train/config
```

---

## 🔗 Links Relacionados

- [Setup Guide](SETUP.md) - Instalação
- [Usage Guide](USAGE.md) - Como usar
- [Fine-tuning Guide](FINETUNING.md) - Guia de fine-tuning

---

**Última Atualização:** 04/12/2025  
**Arquivo de Exemplo:** `train/.env.example`

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
