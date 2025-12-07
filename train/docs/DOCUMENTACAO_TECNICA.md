# 🔧 Documentação Técnica - Training Pipeline XTTS-v2

## 📋 Índice

1. [Arquitetura](#arquitetura)
2. [Pydantic Settings](#pydantic-settings)
3. [Pipeline de Dataset](#pipeline-de-dataset)
4. [Script de Treinamento](#script-de-treinamento)
5. [Implementação XTTS Real](#implementação-xtts-real)
6. [API Reference](#api-reference)

---

## 🏗️ Arquitetura

### Visão Geral

```
┌─────────────────────────────────────────────────────────────┐
│                    Training Pipeline v2.0                    │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                  1. Dataset Preparation                      │
│  download_youtube → segment_audio → transcribe → build_ljs  │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                  2. Configuration (Pydantic)                 │
│      TrainingSettings → Type-safe, validated config          │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                  3. Model & Training                         │
│   load_model → setup_lora → train_loop → save_checkpoints   │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                  4. Inference & Deployment                   │
│      XTTSInference → API endpoints → Production deploy       │
└─────────────────────────────────────────────────────────────┘
```

### Componentes Principais

| Componente | Arquivo | Responsabilidade |
|------------|---------|------------------|
| **Settings** | `train/train_settings.py` | Configuração type-safe com Pydantic |
| **Training** | `train/scripts/train_xtts.py` | Loop de treinamento com LoRA |
| **Dataset** | `train/scripts/build_ljs_dataset.py` | Preparação LJSpeech format |
| **Inference** | `train/scripts/xtts_inference.py` | Síntese com checkpoints |
| **API** | `app/finetune_api.py` | REST endpoints |

---

## ⚙️ Pydantic Settings

### TrainingSettings Class

```python
# train/train_settings.py

from pydantic import BaseModel, Field, field_validator
from pathlib import Path

class TrainingSettings(BaseModel):
    """Type-safe training configuration"""
    
    # Hardware
    device: str = "cuda"
    cuda_device_id: int = 0
    
    # Model
    model_name: str = "tts_models/multilingual/multi-dataset/xtts_v2"
    use_lora: bool = True
    lora_rank: int = 8
    lora_alpha: int = 16
    lora_dropout: float = 0.1
    
    # Dataset
    dataset_dir: Path = Path("train/data/MyTTSDataset")
    sample_rate: int = 24000  # XTTS fixed
    batch_size: int = 2
    num_workers: int = 2
    
    # Training
    num_epochs: int = 1000
    learning_rate: float = 1e-5
    use_amp: bool = False
    
    # Logging
    checkpoint_dir: Path = Path("train/checkpoints")
    use_tensorboard: bool = True
    log_dir: Path = Path("train/runs")
    
    @field_validator("sample_rate")
    @classmethod
    def validate_sample_rate(cls, v):
        if v != 24000:
            raise ValueError("XTTS requires 24kHz")
        return v
```

### Uso

**Método 1: Defaults**
```python
from train.train_settings import get_train_settings
settings = get_train_settings()
```

**Método 2: Env Vars**
```bash
export TRAIN_NUM_EPOCHS=50
export TRAIN_BATCH_SIZE=4
```

**Método 3: .env File**
```bash
# train/.env
TRAIN_NUM_EPOCHS=1000
TRAIN_LEARNING_RATE=0.00001
```

**Método 4: Programático**
```python
settings = TrainingSettings(
    num_epochs=50,
    batch_size=4,
    learning_rate=5e-6
)
```

---

## 📊 Pipeline de Dataset

### 1. download_youtube.py

**Função:** Baixar vídeos/áudios do YouTube

```python
# Uso
python3 -m train.scripts.download_youtube

# Configuração: train/config/dataset_config.yaml
youtube:
  audio_quality: "best"  # best/128k/64k
  output_dir: "train/data/raw"
  max_duration: 7200  # 2h max
```

**Output:**
- `train/data/raw/*.mp3` - Áudios baixados

### 2. segment_audio.py

**Função:** Dividir áudios em chunks de 5-15s

```python
# Uso
python3 -m train.scripts.segment_audio

# Algoritmo:
# 1. Detecta silêncios (pydub.silence.detect_silence)
# 2. Split em boundaries de silêncio
# 3. Filtra por duração (5-15s)
# 4. Normaliza volume
# 5. Converte para mono 22050Hz WAV
```

**Configuração:**
```yaml
segmentation:
  min_duration: 5.0
  max_duration: 15.0
  silence_threshold: -40  # dBFS
  silence_duration: 500    # ms
  fade_duration: 10        # ms
```

**Output:**
- `train/data/processed/segments/*.wav`

### 3. transcribe_audio_parallel.py

**Função:** Transcrever com Whisper (parallel)

```python
# Uso
python3 -m train.scripts.transcribe_audio_parallel

# Features:
# - Parallel processing (6-8 workers)
# - VRAM auto-detection
# - Progress tracking
# - 15x faster que versão serial

# Algoritmo:
# 1. Detecta VRAM disponível
# 2. Calcula workers ótimo (VRAM / 1.5GB)
# 3. Distribui arquivos entre workers
# 4. Processa em parallel com torch.multiprocessing
# 5. Salva transcriptions JSON
```

**Configuração:**
```yaml
whisper:
  model: "medium"  # tiny/base/small/medium/large
  language: "pt"
  device: "cuda"
```

**Output:**
- `train/data/processed/transcriptions/*.json`

### 4. build_ljs_dataset.py

**Função:** Criar dataset formato LJSpeech

```python
# Uso
python3 -m train.scripts.build_ljs_dataset

# Algoritmo:
# 1. Ler todos transcriptions JSON
# 2. Copiar WAVs para dataset/wavs/
# 3. Criar metadata.csv (path|text)
# 4. Calcular estatísticas
# 5. Split 90/10 train/val
# 6. Quality filtering (duração, silêncios)
```

**Quality Filters:**
- Duração: 3-15s
- Text não vazio
- Confiança Whisper > threshold
- Remove silêncios excessivos

**Output:**
```
train/data/MyTTSDataset/
├── wavs/
│   ├── audio_001.wav
│   ├── audio_002.wav
│   └── ...
├── metadata.csv          # Todos samples
├── metadata_train.csv    # 90% treino
└── metadata_val.csv      # 10% validação
```

---

## 🎓 Script de Treinamento

### train_xtts.py Architecture

```python
"""
XTTS-v2 Training Script com LoRA
v2.0: Pydantic Settings, TEMPLATE MODE
"""

# 1. Setup
settings = get_train_settings()
device = setup_device(settings)

# 2. Load Model (TEMPLATE - placeholder)
model = load_pretrained_model(settings, device)

# 3. LoRA Config (TEMPLATE - skipped)
model = setup_lora(model, settings)

# 4. Dataset
train_dataset, val_dataset = create_dataset(settings)
train_loader = DataLoader(train_dataset, batch_size=settings.batch_size)

# 5. Optimizer & Scheduler
optimizer = create_optimizer(model, settings)
scheduler = create_scheduler(optimizer, settings)

# 6. Training Loop
for epoch in range(1, settings.num_epochs + 1):
    for batch_idx, batch in enumerate(train_loader):
        loss = train_step(model, batch, optimizer, scaler, settings, device)
        
        if batch_idx % settings.log_every_n_steps == 0:
            log_metrics(loss, lr, global_step)
    
    # Validation
    val_loss = validate(model, val_loader, device)
    
    # Checkpointing
    if epoch % settings.save_every_n_epochs == 0:
        save_checkpoint(model, optimizer, scheduler, epoch, settings)
        
        if val_loss < best_val_loss:
            save_checkpoint(model, epoch, settings, best=True)
```

### Funções Principais

#### setup_device()

```python
def setup_device(settings: TrainingSettings) -> torch.device:
    """
    Configura device (CUDA/CPU)
    
    Returns:
        torch.device: cuda:0 ou cpu
    
    Raises:
        SystemExit: Se CUDA requerido mas não disponível
    """
    if settings.device == "cuda":
        if not torch.cuda.is_available():
            logger.error("CUDA required but not available")
            sys.exit(1)
        
        device = torch.device(f"cuda:{settings.cuda_device_id}")
        vram_gb = torch.cuda.get_device_properties(0).total_memory / 1e9
        logger.info(f"Using CUDA: {torch.cuda.get_device_name(0)}")
        logger.info(f"VRAM: {vram_gb:.2f} GB")
    else:
        device = torch.device("cpu")
        logger.info("Using CPU")
    
    return device
```

#### load_pretrained_model() - TEMPLATE

```python
def load_pretrained_model(settings: TrainingSettings, device: torch.device):
    """
    TEMPLATE: Carrega modelo XTTS pré-treinado
    
    Para implementação real:
    
    from TTS.tts.models.xtts import Xtts
    from TTS.tts.configs.xtts_config import XttsConfig
    
    config = XttsConfig()
    model = Xtts.init_from_config(config)
    model.load_checkpoint(
        config,
        checkpoint_dir="models/xtts",
        use_deepspeed=False
    )
    
    Returns:
        None (template mode)
        nn.Module (quando implementado)
    """
    logger.warning("TEMPLATE MODE: Using placeholder")
    logger.info("To implement: Install TTS and adapt this function")
    return None
```

#### setup_lora() - TEMPLATE

```python
def setup_lora(model: nn.Module, settings: TrainingSettings) -> nn.Module:
    """
    TEMPLATE: Configura LoRA no modelo
    
    Para implementação real:
    
    from peft import LoraConfig, get_peft_model
    
    # Identificar target modules do XTTS
    # Ex: GPT layers, vocoder modules
    peft_config = LoraConfig(
        r=settings.lora_rank,
        lora_alpha=settings.lora_alpha,
        lora_dropout=settings.lora_dropout,
        target_modules=[
            "gpt.transformer.h.*.attn.c_attn",
            "gpt.transformer.h.*.attn.c_proj",
            "gpt.transformer.h.*.mlp.c_fc",
            "gpt.transformer.h.*.mlp.c_proj",
        ],
        bias="none",
        task_type="CAUSAL_LM"
    )
    
    model = get_peft_model(model, peft_config)
    model.print_trainable_parameters()
    
    Returns:
        model (unmodified in template mode)
    """
    if not settings.use_lora:
        return model
    
    logger.warning("TEMPLATE: LoRA skipped (needs real model)")
    return model
```

#### train_step() - TEMPLATE

```python
def train_step(
    model, batch, optimizer, scaler, 
    settings: TrainingSettings, device: torch.device
) -> float:
    """
    TEMPLATE: Executa um step de treinamento
    
    Para implementação real:
    
    # Forward pass XTTS
    outputs = model(
        text_input=batch["text_tokens"],
        mel_input=batch["mel_spec"],
        speaker_embedding=batch["speaker_emb"]
    )
    
    # Multi-task loss
    loss = (
        outputs.mel_loss +
        outputs.duration_loss +
        outputs.alignment_loss
    )
    
    # Backward com gradient clipping
    if settings.use_amp:
        scaler.scale(loss).backward()
        scaler.unscale_(optimizer)
        torch.nn.utils.clip_grad_norm_(
            model.parameters(),
            settings.max_grad_norm
        )
        scaler.step(optimizer)
        scaler.update()
    else:
        loss.backward()
        torch.nn.utils.clip_grad_norm_(
            model.parameters(),
            settings.max_grad_norm
        )
        optimizer.step()
    
    optimizer.zero_grad()
    
    Returns:
        loss.item()
    """
    model.train()
    
    # TEMPLATE: Random placeholder loss
    loss = torch.tensor(
        0.5 + torch.rand(1).item() * 0.1,
        device=device,
        requires_grad=True
    )
    
    # Backward pass simulado
    if settings.use_amp and scaler is not None:
        scaler.scale(loss).backward()
        scaler.step(optimizer)
        scaler.update()
    else:
        loss.backward()
        optimizer.step()
    
    optimizer.zero_grad()
    
    return loss.item()
```

---

## 🔨 Implementação XTTS Real

### Checklist de Implementação

- [ ] **1. Instalar TTS**
  ```bash
  pip install TTS transformers<4.40 peft<0.8
  ```

- [ ] **2. Adaptar load_pretrained_model()**
  - Importar `TTS.tts.models.xtts`
  - Carregar config XTTS
  - Download automático de checkpoint
  - Aceitar ToS: `os.environ['COQUI_TOS_AGREED'] = '1'`

- [ ] **3. Adaptar setup_lora()**
  - Identificar modules XTTS (GPT layers, vocoder)
  - Configurar `LoraConfig` com target_modules corretos
  - Usar `get_peft_model()` e `.print_trainable_parameters()`

- [ ] **4. Implementar create_dataset()**
  - Usar `TTS.tts.datasets.TTSDataset`
  - Configurar audio processor (24kHz, mel spectrograms)
  - Implementar collate_fn para batching

- [ ] **5. Implementar train_step()**
  - Forward pass XTTS completo
  - Calcular multi-task loss (mel, duration, alignment)
  - Backward com gradient accumulation (opcional)

- [ ] **6. Testar com Smoke Test**
  ```bash
  export TRAIN_NUM_EPOCHS=1
  export TRAIN_BATCH_SIZE=1
  python3 -m train.scripts.train_xtts
  ```

- [ ] **7. Validar Checkpoints**
  - Carregar checkpoint salvo
  - Testar síntese com `xtts_inference.py`
  - Comparar qualidade antes/depois fine-tuning

### Exemplo de Implementação

```python
# train/scripts/train_xtts.py

def load_pretrained_model(settings: TrainingSettings, device: torch.device):
    """Implementação REAL do carregamento XTTS"""
    
    # Imports
    from TTS.api import TTS
    from TTS.tts.models.xtts import Xtts
    from TTS.tts.configs.xtts_config import XttsConfig
    import os
    
    # Accept ToS
    os.environ['COQUI_TOS_AGREED'] = '1'
    
    logger.info(f"Loading XTTS model: {settings.model_name}")
    
    # Option 1: Via TTS API (easiest)
    tts = TTS(
        model_name=settings.model_name,
        gpu=(device.type == 'cuda'),
        progress_bar=True
    )
    model = tts.synthesizer.tts_model
    
    # Option 2: Direct load
    # config = XttsConfig()
    # config.load_json("path/to/config.json")
    # model = Xtts.init_from_config(config)
    # model.load_checkpoint(config, checkpoint_dir="models/xtts")
    
    model = model.to(device)
    model.train()  # Set to training mode
    
    logger.info(f"Model loaded: {model.__class__.__name__}")
    logger.info(f"Parameters: {sum(p.numel() for p in model.parameters())/1e6:.1f}M")
    
    return model


def setup_lora(model: nn.Module, settings: TrainingSettings) -> nn.Module:
    """Implementação REAL do LoRA setup"""
    
    if not settings.use_lora:
        return model
    
    from peft import LoraConfig, get_peft_model
    
    logger.info("Setting up LoRA...")
    
    # Target modules para XTTS-v2
    # GPT: Multi-head attention e feed-forward
    # Vocoder: HiFi-GAN modules
    peft_config = LoraConfig(
        r=settings.lora_rank,
        lora_alpha=settings.lora_alpha,
        lora_dropout=settings.lora_dropout,
        target_modules=[
            # GPT Attention
            "gpt.transformer.h.*.attn.c_attn",
            "gpt.transformer.h.*.attn.c_proj",
            # GPT MLP
            "gpt.transformer.h.*.mlp.c_fc",
            "gpt.transformer.h.*.mlp.c_proj",
            # Vocoder (opcional, se incluído)
            # "vocoder.*.conv.*",
        ],
        bias="none",
        task_type="CAUSAL_LM",
    )
    
    model = get_peft_model(model, peft_config)
    model.print_trainable_parameters()
    
    return model
```

---

## 📖 API Reference

### TrainingSettings

Ver `train/train_settings.py` para referência completa.

**Principais campos:**

| Campo | Tipo | Default | Descrição |
|-------|------|---------|-----------|
| `device` | str | "cuda" | Device (cuda/cpu) |
| `model_name` | str | "tts_models/..." | Nome modelo XTTS |
| `use_lora` | bool | True | Habilitar LoRA |
| `lora_rank` | int | 8 | LoRA rank (4-32) |
| `dataset_dir` | Path | "train/data/..." | Diretório dataset |
| `num_epochs` | int | 1000 | Número épocas |
| `learning_rate` | float | 1e-5 | Taxa aprendizado |
| `batch_size` | int | 2 | Batch size |
| `checkpoint_dir` | Path | "train/checkpoints" | Checkpoints |

### Funções Públicas

#### get_train_settings()

```python
def get_train_settings() -> TrainingSettings:
    """
    Retorna singleton TrainingSettings
    
    Returns:
        TrainingSettings configurado via:
        - Defaults
        - Variáveis ambiente (TRAIN_*)
        - Arquivo .env (train/.env)
    """
```

#### create_dataset()

```python
def create_dataset(settings: TrainingSettings) -> Tuple[Dataset, Dataset]:
    """
    Cria datasets treino/validação
    
    Args:
        settings: TrainingSettings configurado
    
    Returns:
        (train_dataset, val_dataset)
    
    Raises:
        FileNotFoundError: Se metadata não existe
    """
```

#### save_checkpoint()

```python
def save_checkpoint(
    model: nn.Module,
    optimizer,
    scheduler,
    step: int,
    settings: TrainingSettings,
    best: bool = False
):
    """
    Salva checkpoint
    
    Args:
        model: Modelo treinado
        optimizer: Optimizer state
        scheduler: Scheduler state
        step: Checkpoint step/epoch
        settings: TrainingSettings
        best: Se é best model
    
    Saves to:
        {checkpoint_dir}/checkpoint_epoch_{step}.pt
        {checkpoint_dir}/best_model.pt (se best=True)
    """
```

---

## 🔗 Referências Externas

- [Coqui TTS Documentation](https://docs.coqui.ai/)
- [PEFT GitHub](https://github.com/huggingface/peft)
- [LoRA Paper](https://arxiv.org/abs/2106.09685)
- [XTTS-v2 Architecture](https://github.com/coqui-ai/TTS/blob/dev/TTS/tts/models/xtts.py)

---

**Versão:** v2.0  
**Última Atualização:** 2025-12-07  
**Autor:** TTS WebUI Training Team
