# F5-TTS Training Tutorial

Guia passo-a-passo completo para treinar um modelo F5-TTS customizado.

**Tempo estimado:** 2-4 horas (preparação) + tempo de treino variável

---

## 📋 Índice

1. [Setup do Ambiente](#1-setup-do-ambiente)
2. [Preparar Dataset](#2-preparar-dataset)
3. [Configurar Treino](#3-configurar-treino)
4. [Iniciar Treino](#4-iniciar-treino)
5. [Monitorar Progresso](#5-monitorar-progresso)
6. [Testar Checkpoint](#6-testar-checkpoint)
7. [Deploy em Produção](#7-deploy-em-produção)

---

## 1. Setup do Ambiente

### 1.1 Requisitos

**Hardware:**
- GPU NVIDIA com 8GB+ VRAM (RTX 3060 ou superior)
- 32GB+ RAM recomendado
- 100GB+ espaço em disco

**Software:**
- Python 3.11+
- CUDA 12.1+
- Git

### 1.2 Instalar Dependências

```bash
# Clone o repositório
git clone https://github.com/JohnHeberty/tts-webui-proxmox-passthrough.git
cd tts-webui-proxmox-passthrough

# Instalar dependências de treinamento
pip install -r train/requirements-train-lock.txt

# Ou usar Makefile
make train-setup
```

### 1.3 Verificar Ambiente

```bash
# Executar health check
python train/scripts/health_check.py
```

**Saída esperada:**
```
✅ Python: 3.11.2
✅ PyTorch: 2.5.1+cu121
✅ CUDA: 12.1 available
✅ GPU: NVIDIA RTX 3090 (23.7 GB VRAM)
✅ Environment is healthy!
```

Se houver erros, consulte [Troubleshooting](#troubleshooting).

---

## 2. Preparar Dataset

### 2.1 Estrutura de Diretórios

Seu dataset deve ter esta estrutura:

```
train/data/
├── raw/                    # Áudio bruto
│   ├── video1.mp4
│   ├── audio1.wav
│   └── ...
├── processed/              # Áudio processado
│   └── wavs/
│       ├── segment_0001.wav
│       ├── segment_0002.wav
│       └── ...
└── f5_dataset/            # Dataset final
    ├── metadata.csv
    └── wavs/
```

### 2.2 Opção A: Usar Dataset Existente

Se você já tem áudio + transcrições:

```bash
# Copiar áudios para train/data/raw/
cp /caminho/para/audios/*.wav train/data/raw/

# Copiar transcrições (formato: audio.txt com mesmo nome)
cp /caminho/para/textos/*.txt train/data/raw/
```

### 2.3 Opção B: Download de YouTube

Para criar dataset a partir de vídeos do YouTube:

**2.3.1 Criar lista de vídeos:**

```bash
# Criar arquivo com URLs
cat > train/data/videos.csv << EOF
video_id,title,url
pt_sample1,Tutorial Python,https://youtube.com/watch?v=xxxxx
pt_sample2,Palestra TED,https://youtube.com/watch?v=yyyyy
EOF
```

**2.3.2 Download:**

```python
from train.io import download_youtube_videos

download_youtube_videos(
    videos_csv="train/data/videos.csv",
    output_dir="train/data/raw/",
    download_audio=True,
    download_subtitles=True,
)
```

### 2.4 Processamento e Segmentação

```bash
# Processar áudio bruto → segmentos limpos
python train/scripts/prepare_segments_optimized.py \
    --input-dir train/data/raw/ \
    --output-dir train/data/processed/ \
    --config train/config/config.yaml
```

**O que acontece:**
1. ✅ Segmenta áudio em chunks de 3-10s
2. ✅ Remove silêncios (VAD)
3. ✅ Normaliza volume (-23 LUFS)
4. ✅ Valida qualidade
5. ✅ Transcreve com Whisper (se necessário)
6. ✅ Gera `metadata.csv`

**Saída:**
```
🎵 Processing 50 audio files...
✅ Segmented: 450 chunks (3-10s each)
✅ Transcribed: 450 segments
✅ Valid: 420 segments (30 rejected)
💾 Saved to: train/data/processed/
```

### 2.5 Verificar Dataset

```bash
# Ver estatísticas
python -c "
import pandas as pd
df = pd.read_csv('train/data/processed/metadata.csv', sep='|')
print(f'Total samples: {len(df)}')
print(f'Total duration: {df[\"duration\"].sum() / 3600:.1f}h')
print(f'Avg duration: {df[\"duration\"].mean():.1f}s')
"
```

**Mínimo recomendado:**
- 100+ samples para fine-tuning
- 1000+ samples para treino completo
- 1h+ de áudio total

---

## 3. Configurar Treino

### 3.1 Editar config.yaml

```bash
# Abrir configuração
nano train/config/config.yaml
```

### 3.2 Parâmetros Essenciais

```yaml
# Dataset
paths:
  dataset_name: "meu_dataset"
  output_dir: "train/output/meu_modelo"

# Training
training:
  exp_name: "F5TTS_CustomVoice"
  epochs: 100                    # Ajustar conforme dataset
  batch_size_per_gpu: 2          # Reduzir se OOM
  learning_rate: 1e-4
  grad_accumulation_steps: 8     # Aumenta batch efetivo

# Model
model:
  base_model: "firstpixel/F5-TTS-pt-br"
  use_ema: true                  # Melhora qualidade

# Checkpoints
checkpoints:
  save_per_updates: 500
  keep_last_n_checkpoints: 3
  log_samples: true              # Gera samples a cada epoch

# Hardware
hardware:
  device: "cuda"
  num_workers: 4
  dataloader_workers: 8
```

### 3.3 Ajustar para VRAM Disponível

**8GB VRAM (RTX 3060):**
```yaml
training:
  batch_size_per_gpu: 1
  grad_accumulation_steps: 16
advanced:
  gradient_checkpointing: true
```

**12GB VRAM (RTX 3080):**
```yaml
training:
  batch_size_per_gpu: 2
  grad_accumulation_steps: 8
```

**24GB VRAM (RTX 3090/4090):**
```yaml
training:
  batch_size_per_gpu: 4
  grad_accumulation_steps: 4
```

---

## 4. Iniciar Treino

### 4.1 Treino Completo

```bash
# Iniciar treino
python -m train.run_training \
    --config train/config/config.yaml \
    --epochs 100

# Ou via Makefile
make train-run
```

### 4.2 Resume de Checkpoint

Se o treino foi interrompido:

```bash
# Retomar do último checkpoint
python -m train.run_training \
    --config train/config/config.yaml \
    --resume

# Ou de checkpoint específico
python -m train.run_training \
    --config train/config/config.yaml \
    --resume-from train/output/meu_modelo/model_epoch_50.pt
```

### 4.3 Quick Test (1 epoch)

Para testar o pipeline:

```bash
# Treino rápido (1 epoch)
python -m train.run_training \
    --config train/config/config.yaml \
    --epochs 1

# Ou via Makefile
make train-quick
```

---

## 5. Monitorar Progresso

### 5.1 TensorBoard

```bash
# Em outro terminal, iniciar TensorBoard
tensorboard --logdir train/runs/ --port 6006
```

Abrir no navegador: http://localhost:6006

**Métricas importantes:**
- `train/loss` - deve diminuir consistentemente
- `train/lr` - learning rate (warmup → decay)
- `samples/epoch_X` - amostras de áudio geradas

### 5.2 Logs

```bash
# Ver logs em tempo real
tail -f train/logs/training.log

# Filtrar erros
grep "ERROR" train/logs/training.log

# Ver checkpoints salvos
ls -lh train/output/meu_modelo/*.pt
```

### 5.3 Monitoramento de GPU

```bash
# Uso de GPU em tempo real
watch -n 1 nvidia-smi

# Ou com formatação melhor
gpustat -i 1
```

---

## 6. Testar Checkpoint

### 6.1 Inferência via CLI

```bash
# Testar modelo treinado
python -m train.cli.infer \
    --checkpoint train/output/meu_modelo/model_best.pt \
    --vocab train/config/vocab.txt \
    --text "Olá! Este é um teste do meu modelo customizado." \
    --ref-audio train/data/processed/wavs/segment_0001.wav \
    --ref-text "Transcrição do áudio de referência" \
    --output test_output.wav
```

### 6.2 Comparar Checkpoints

```bash
# Testar múltiplos checkpoints
for ckpt in train/output/meu_modelo/model_epoch_*.pt; do
    echo "Testing: $ckpt"
    python -m train.cli.infer \
        --checkpoint "$ckpt" \
        --vocab train/config/vocab.txt \
        --text "Texto de teste" \
        --ref-audio ref.wav \
        --output "output_$(basename $ckpt .pt).wav"
done
```

### 6.3 Avaliar Qualidade

Ouça os áudios gerados e avalie:
- ✅ Naturalidade
- ✅ Clareza
- ✅ Prosódia (entonação)
- ✅ Ausência de artefatos

Para métricas objetivas:
```bash
# Calcular MCD (Mel Cepstral Distortion)
python train/scripts/benchmark.py \
    --checkpoint model_best.pt \
    --test-samples test_samples.txt
```

---

## 7. Deploy em Produção

### 7.1 Copiar Checkpoint

```bash
# Copiar melhor checkpoint para API
cp train/output/meu_modelo/model_best.pt models/f5tts/model_custom.pt

# Copiar vocab
cp train/config/vocab.txt models/f5tts/vocab.txt
```

### 7.2 Atualizar API Config

Editar `.env`:
```bash
# Usar modelo customizado
F5TTS_CUSTOM_CHECKPOINT=models/f5tts/model_custom.pt
```

### 7.3 Testar na API

```bash
# Restart API
docker-compose restart

# Testar endpoint
curl -X POST http://localhost:8005/tts/generate \
  -H "Content-Type: application/json" \
  -d '{
    "text": "Teste do modelo customizado",
    "engine": "f5tts",
    "language": "pt-BR"
  }' \
  --output test_api.wav
```

### 7.4 Criar Backup

```bash
# Backup completo
tar -czf modelo_$(date +%Y%m%d).tar.gz \
    train/output/meu_modelo/ \
    train/config/config.yaml \
    train/data/processed/metadata.csv

# Upload para cloud (opcional)
aws s3 cp modelo_*.tar.gz s3://meu-bucket/backups/
```

---

## Troubleshooting

### Erro: CUDA Out of Memory (OOM)

**Solução 1 - Reduzir batch size:**
```yaml
training:
  batch_size_per_gpu: 1
  grad_accumulation_steps: 16
```

**Solução 2 - Gradient checkpointing:**
```yaml
advanced:
  gradient_checkpointing: true
```

**Solução 3 - Mixed precision:**
```yaml
mixed_precision:
  enabled: true
  dtype: "fp16"
```

### Loss não diminui

**Causas comuns:**
1. Learning rate muito alto → reduzir para 5e-5
2. Dataset muito pequeno → adicionar mais dados
3. Bad samples → revisar qualidade do dataset

**Solução:**
```yaml
training:
  learning_rate: 5e-5
  early_stop_patience: 20  # Parar se não melhorar
```

### Qualidade ruim

**Checklist:**
- [ ] Dataset tem 1h+ de áudio?
- [ ] Áudios estão limpos (sem ruído)?
- [ ] Transcrições estão corretas?
- [ ] Treinou por 50+ epochs?
- [ ] Usou modelo pré-treinado (fine-tuning)?

---

## Dicas Avançadas

### 1. Data Augmentation

Aumentar variedade do dataset:
```python
from train.audio.effects import apply_eq, add_noise

# Gerar variações
audio_eq = apply_eq(audio, sr, low_shelf=-2.0, high_shelf=1.0)
audio_noise = add_noise(audio, snr_db=30)
```

### 2. Curriculum Learning

Começar com exemplos fáceis:
```yaml
# Epoch 1-10: apenas samples curtos (3-5s)
# Epoch 11-50: samples médios (5-7s)
# Epoch 51+: todos os samples (3-10s)
```

### 3. Transfer Learning

Fine-tune de modelo específico:
```yaml
model:
  base_model: "suno/bark-small"  # Outro modelo base
  custom_checkpoint: "pretrained/other_model.pt"
```

---

## Recursos Adicionais

- [Inference API Documentation](INFERENCE_API.md)
- [Configuration Reference](../config/README.md)
- [Audio Processing Guide](../audio/README.md)
- [Sprint Plan](../../SPRINTS_PLAN.md)

---

## Checklist Final

- [ ] Ambiente validado (health check OK)
- [ ] Dataset preparado (100+ samples)
- [ ] Config.yaml ajustado
- [ ] Treino executado (50+ epochs)
- [ ] Checkpoints testados
- [ ] Melhor modelo selecionado
- [ ] Backup criado
- [ ] Deploy em produção

---

**🎉 Parabéns! Você treinou seu modelo F5-TTS customizado!**

Para suporte, abra uma issue no GitHub ou consulte a documentação completa.

---

**Autor:** F5-TTS Training Pipeline  
**Versão:** 1.0  
**Data:** 2025-12-06
