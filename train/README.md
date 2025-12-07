# XTTS-v2 Fine-Tuning Pipeline

Pipeline completo para fine-tuning de modelos XTTS-v2 com LoRA.

## 📊 Status

**Progresso**: 67% (4/6 sprints completos)

- ✅ Sprint 0: Segurança (100%)
- ✅ Sprint 1: Dataset Pipeline (100%)  
- ✅ Sprint 2: Training Script (100%)
- ✅ Sprint 3: API Integration (100%)
- ⏳ Sprint 4-5: Testes e Docs

Ver `IMPLEMENTATION_STATUS.md` para detalhes.

## 🚀 Quick Start

### 1. Criar Dataset

```bash
# Download de vídeos do YouTube
python3 -m train.scripts.download_youtube

# Segmentar áudio em chunks
python3 -m train.scripts.segment_audio

# Transcrever com Whisper (parallel processing, 15x faster)
python3 -m train.scripts.transcribe_audio_parallel

# Gerar metadata LJSpeech
python3 -m train.scripts.build_ljs_dataset
```

**Resultado**: Dataset em `train/data/MyTTSDataset/` (4922 samples, 15.3h)

### 2. Training

```bash
# Smoke test (10 steps)
python3 -m train.scripts.train_xtts --config train/config/smoke_test.yaml

# Full training (50 epochs)
python3 -m train.scripts.train_xtts --config train/config/train_config.yaml
```

**Checkpoints**: Salvos em `train/checkpoints/`

### 3. Inference

```python
from train.scripts.xtts_inference import XTTSInference

# Carregar modelo fine-tunado
inference = XTTSInference(checkpoint_path="train/checkpoints/best_model.pt")

# Sintetizar áudio
audio = inference.synthesize("Texto custom", language="pt", speaker_wav="reference.wav")

# Salvar em arquivo
inference.synthesize_to_file("Outro texto", "output.wav", language="pt")
```

### 4. API Endpoints

```bash
# Listar checkpoints
curl http://localhost:8000/v1/finetune/checkpoints

# Sintetizar com checkpoint
curl -X POST http://localhost:8000/v1/finetune/synthesize \
  -H "Content-Type: application/json" \
  -d '{
    "text": "Olá, teste de síntese",
    "language": "pt",
    "checkpoint": "best_model.pt"
  }'

# Info do modelo
curl http://localhost:8000/v1/finetune/model/info?checkpoint=best_model.pt
```

## 📂 Estrutura

```
train/
├── config/
│   ├── dataset_config.yaml      # XTTS-v2 dataset specs
│   ├── train_config.yaml         # LoRA training config
│   └── smoke_test.yaml           # Quick validation
├── scripts/
│   ├── download_youtube.py       # YouTube downloader
│   ├── segment_audio.py          # Audio segmentation
│   ├── transcribe_audio_parallel.py  # Parallel Whisper (15x faster)
│   ├── build_ljs_dataset.py      # LJSpeech metadata builder
│   ├── train_xtts.py             # Training script (517 linhas)
│   └── xtts_inference.py         # Inference engine (376 linhas)
├── data/
│   ├── raw/                      # YouTube videos (~30-40h)
│   ├── processed/                # Segments + transcriptions
│   └── MyTTSDataset/             # Final dataset (4922 samples)
├── checkpoints/                  # Saved models
└── env_config.py                 # VRAM auto-detection
```

## 🎯 Features

- **Pipeline Completo**: Download → Segment → Transcribe → Build → Train
- **Parallel Processing**: 15x speedup (6-8 workers com VRAM auto-detection)
- **LoRA Training**: Efficient fine-tuning (PEFT)
- **Checkpoint Management**: Auto-save, best model tracking
- **Inference Engine**: Load custom checkpoints, voice cloning
- **REST API**: 6 endpoints (`/v1/finetune/*`)
- **Quality Filtering**: 14.2% low-quality samples removed
- **Incremental Save**: Resume from crash (zero data loss)

## 📊 Dataset Stats

- **Total samples**: 4922
- **Duration**: 15.3 hours (13.76h train, 1.54h val)
- **Split**: 90/10 train/val
- **Average length**: 11.19s per sample
- **Format**: 22050Hz mono 16-bit WAV
- **Metadata**: LJSpeech format (`path|text`)

## 🔧 Configuração

### Environment Variables

```bash
# train/.env
MAX_WORKERS=6           # Parallel transcription workers
VRAM_GB=24              # Available VRAM (auto-detected)
CHUNK_SIZE=10           # Save checkpoint every N segments
```

### Training Config

```yaml
# train/config/train_config.yaml
model:
  name: "tts_models/multilingual/multi-dataset/xtts_v2"
  use_lora: true
  lora:
    rank: 8
    alpha: 16
    target_modules:
      - "gpt.transformer.h.*.attn.c_attn"
      - "gpt.transformer.h.*.mlp.c_fc"

training:
  max_steps: 10000
  learning_rate: 1e-5
  use_amp: true
  lr_scheduler: "cosine_with_warmup"
```

## 📚 Documentação

- `IMPLEMENTATION_STATUS.md` - Overview geral do projeto
- `SPRINT0_REPORT.md` - Segurança e cleanup
- `IMPLEMENTATION_COMPLETE.md` - Dataset pipeline (Sprint 1)
- `SPRINT2_REPORT.md` - Training script (Sprint 2)
- `SPRINT3_REPORT.md` - API integration (Sprint 3)
- `SPRINTS.md` - Plano completo de desenvolvimento

## 🐛 Troubleshooting

### PyTorch 2.6 UnpicklingError

**Problema**: `weights_only=True` causa erro ao carregar TTS.

**Solução**: Aplicado fix em `xtts_inference.py`:
```python
import torch.serialization
from TTS.tts.configs.xtts_config import XttsConfig
torch.serialization.add_safe_globals([XttsConfig])
```

### Transformers Incompatibility

**Problema**: `BeamSearchScorer` não encontrado.

**Solução**: Downgrade para versão compatível:
```bash
pip install 'transformers<4.40' 'peft<0.8'
```

### VRAM Out of Memory

**Problema**: CUDA OOM durante training.

**Solução**:
- Reduzir `batch_size` em `train_config.yaml`
- Desabilitar `use_amp`
- Usar `gradient_checkpointing`

## 🎓 Referências

- [Coqui TTS](https://github.com/coqui-ai/TTS)
- [XTTS-v2](https://huggingface.co/coqui/XTTS-v2)
- [PEFT/LoRA](https://github.com/huggingface/peft)
- [Whisper](https://github.com/openai/whisper)

---

**Última atualização**: 2025-12-06
