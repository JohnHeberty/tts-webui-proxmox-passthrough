# 🎓 Guia Completo de Treinamento XTTS-v2

**Versão:** v2.0.1  
**Data:** 10 de Dezembro de 2025

## 📋 Índice

1. [Introdução](#introdução)
2. [Pré-requisitos](#pré-requisitos)
3. [Preparação do Dataset](#preparação-do-dataset)
4. [Configuração](#configuração)
5. [Treinamento](#treinamento)
6. [Problemas Comuns](#problemas-comuns)
7. [Referências](#referências)

---

## 🎯 Introdução

Este guia explica como treinar (fine-tune) um modelo XTTS-v2 para sua própria voz usando LoRA (Low-Rank Adaptation), uma técnica eficiente que requer menos recursos.

### O que você vai precisar?

- **GPU NVIDIA** com no mínimo 8GB VRAM (recomendado 12GB+)
- **Áudio de referência**: 30-60 minutos de áudio limpo da voz alvo
- **Tempo**: 2-4 horas para preparar dataset + 6-12 horas de treinamento
- **Conhecimento básico**: Linha de comando Linux/Terminal

### ⚠️ IMPORTANTE - Estado Atual (v2.0)

O script `train_xtts.py` está em **modo TEMPLATE**:
- ✅ Estrutura completa implementada
- ✅ Configuração via Pydantic Settings
- ⚠️ Modelo XTTS placeholder (não carrega modelo real)
- ⚠️ Dataset dummy (não treina com dados reais)

**Para treinar modelo XTTS REAL**, você precisa:
1. Instalar biblioteca TTS: `pip install TTS`
2. Implementar `load_pretrained_model()` com TTS API
3. Implementar `create_dataset()` com TTS.tts.datasets
4. Implementar `train_step()` com XTTS forward pass

---

## 🔧 Pré-requisitos

### Hardware

```bash
# Verificar GPU
nvidia-smi

# Verificar VRAM (mínimo 8GB)
nvidia-smi --query-gpu=memory.total --format=csv
```

**Recomendações:**
- **8GB VRAM**: Batch size 1-2, epochs curtos
- **12GB VRAM**: Batch size 2-4, treinamento completo
- **24GB+ VRAM**: Batch size 8+, parallel training

### Software

```bash
# Python 3.11+
python3 --version

# CUDA 11.8+
nvcc --version

# PyTorch com CUDA
python3 -c "import torch; print(torch.cuda.is_available())"
```

### Dependências

```bash
cd /home/tts-webui-proxmox-passthrough

# Instalar dependências base
pip install -r requirements.txt

# Para treinamento REAL (ainda não implementado)
# pip install TTS peft transformers<4.40
```

---

## 📊 Preparação do Dataset

### Opção 1: Baixar do YouTube (Mais Fácil)

```bash
# 1. Baixar vídeos/áudios
python3 -m train.scripts.download_youtube

# Siga as instruções:
# - Cole URLs de vídeos do YouTube
# - Escolha qualidade de áudio (best/128k/64k)
# - Áudios salvos em: train/data/raw/
```

**Dicas:**
- Use vídeos com **boa qualidade de áudio**
- Evite música de fundo ou ruídos
- Prefira **conteúdo falado**: podcasts, entrevistas, aulas
- Baixe **30-60 minutos** de áudio total

### Opção 2: Usar Seus Próprios Áudios

```bash
# Copiar áudios para pasta raw
mkdir -p train/data/raw
cp /caminho/seus/audios/*.mp3 train/data/raw/

# Formatos aceitos: MP3, WAV, M4A, OGG, FLAC
```

### 2. Segmentar Áudio em Chunks

```bash
# Dividir áudio longo em chunks de 5-15 segundos
python3 -m train.scripts.segment_audio

# Configurações em: train/config/dataset_config.yaml
# - min_duration: 5.0 (mínimo 5s)
# - max_duration: 15.0 (máximo 15s)
# - silence_threshold: -40dB (ajustar se necessário)

# Resultado: train/data/processed/segments/
```

**O que acontece:**
- Detecta silêncios para dividir naturalmente
- Remove segmentos muito curtos ou longos
- Normaliza volume
- Converte para WAV mono 22050Hz

### 3. Transcrever com Whisper

```bash
# Opção A: Parallel (15x mais rápido - RECOMENDADO)
python3 -m train.scripts.transcribe_audio_parallel

# Opção B: Serial (mais lento)
python3 -m train.scripts.transcribe_audio

# Configurações:
# - Modelo: medium (padrão) ou large
# - Workers: auto-detect baseado em VRAM
# - Resultado: train/data/processed/transcriptions/
```

**Tempo estimado:**
- 1 hora de áudio com `medium` parallel: ~4-6 minutos
- 1 hora de áudio com `large` parallel: ~8-12 minutos

### 4. Gerar Metadata LJSpeech

```bash
# Criar dataset final formato LJSpeech
python3 -m train.scripts.build_ljs_dataset

# Saída: train/data/MyTTSDataset/
# ├── wavs/                    # Áudios processados
# ├── metadata.csv             # Todos samples
# ├── metadata_train.csv       # 90% treino
# └── metadata_val.csv         # 10% validação
```

**Formato metadata.csv:**
```
wavs/audio_001.wav|Texto transcrito aqui
wavs/audio_002.wav|Outro texto transcrito
```

### 5. Validar Dataset

```bash
# Verificar estatísticas
cd train/data/MyTTSDataset
wc -l metadata*.csv

# Esperado:
# - 500-5000 samples (mínimo 100)
# - 15-60 minutos total
# - Taxa 90/10 train/val
```

---

## ⚙️ Configuração

### v2.0: Pydantic Settings (Sem YAML!)

**Método 1: Usar Defaults**

```bash
# Simplesmente rode - usa configurações otimizadas
python3 -m train.scripts.train_xtts
```

**Método 2: Variáveis de Ambiente**

```bash
# Customizar via export
export TRAIN_NUM_EPOCHS=50
export TRAIN_LEARNING_RATE=0.00001
export TRAIN_BATCH_SIZE=4
export TRAIN_USE_LORA=true

python3 -m train.scripts.train_xtts
```

**Método 3: Arquivo .env**

```bash
# Criar train/.env
cat > train/.env << 'EOF'
# Hardware
TRAIN_DEVICE=cuda
TRAIN_CUDA_DEVICE_ID=0

# Dataset
TRAIN_DATASET_DIR=train/data/MyTTSDataset
TRAIN_BATCH_SIZE=2
TRAIN_NUM_WORKERS=4

# Model & LoRA
TRAIN_USE_LORA=true
TRAIN_LORA_RANK=8
TRAIN_LORA_ALPHA=16

# Training
TRAIN_NUM_EPOCHS=1000
TRAIN_LEARNING_RATE=0.00001
TRAIN_USE_AMP=false

# Logging
TRAIN_SAVE_EVERY_N_EPOCHS=10
TRAIN_USE_TENSORBOARD=true
EOF

# Rodar com .env
python3 -m train.scripts.train_xtts
```

### Parâmetros Principais

| Parâmetro | Default | Descrição | Quando Ajustar |
|-----------|---------|-----------|----------------|
| `num_epochs` | 1000 | Número de épocas | Reduzir para testes (10-50) |
| `batch_size` | 2 | Samples por batch | Aumentar se VRAM > 12GB |
| `learning_rate` | 1e-5 | Taxa de aprendizado | Reduzir se loss instável |
| `use_lora` | true | Usar LoRA | Manter true (mais eficiente) |
| `lora_rank` | 8 | LoRA rank | Aumentar para 16-32 se VRAM permite |
| `use_amp` | false | Mixed precision | Ativar para economizar VRAM |
| `save_every_n_epochs` | 10 | Frequência checkpoint | Reduzir para 1-5 |

---

## 🚀 Treinamento

### Modo Template (Atual)

```bash
# Rodar script em modo demonstração
python3 -m train.scripts.train_xtts

# Saída:
# - ⚠️  TEMPLATE MODE warnings
# - Dummy model criado
# - Dummy dataset (10 samples)
# - Loop de treinamento simulado
# - Não salva checkpoints reais
```

### Treinamento Real (Requer Implementação)

**Quando implementado, você verá:**

```bash
python3 -m train.scripts.train_xtts

# Output esperado:
# ================================================================================
# XTTS-v2 FINE-TUNING com LoRA
# ================================================================================
# 📝 Settings carregadas via Pydantic
# ✅ Using CUDA device: NVIDIA GeForce RTX 3090
# 📦 Carregando modelo XTTS-v2...
# ✅ Modelo carregado: XttsModel (340M params)
# 🔧 Configurando LoRA...
#    Trainable params: 2.5M (0.73%)
# 📊 Carregando dataset...
#    Train: 4,429 samples (13.76h)
#    Val: 493 samples (1.54h)
# 
# 🚀 Iniciando treinamento...
#    Epochs: 1000
#    Batch size: 2
#    Learning rate: 1e-05
# 
# ============================================================
# EPOCH 1/1000
# ============================================================
# Epoch 1/1000 | Step 1/2215 | Loss: 0.8542 | Avg: 0.8542 | LR: 1.00e-05
# Epoch 1/1000 | Step 10/2215 | Loss: 0.7234 | Avg: 0.7891 | LR: 1.00e-05
# ...
```

### Monitorar Treinamento

#### TensorBoard

```bash
# Em outro terminal
tensorboard --logdir train/runs --port 6006

# Abrir navegador: http://localhost:6006
# Ver:
# - train/loss, train/avg_loss
# - epoch/train_loss, epoch/val_loss
# - train/lr (learning rate)
```

#### Logs

```bash
# Ver logs em tempo real
tail -f logs/info.log

# Buscar erros
grep "ERROR" logs/error.log
```

#### Checkpoints

```bash
# Listar checkpoints salvos
ls -lh train/checkpoints/

# Estrutura:
# checkpoint_epoch_10.pt
# checkpoint_epoch_20.pt
# best_model.pt  # Melhor modelo (menor val_loss)
```

---

## 🐛 Problemas Comuns

### 1. CUDA Out of Memory (OOM)

**Erro:**
```
RuntimeError: CUDA out of memory. Tried to allocate X.XX GiB
```

**Soluções:**

```bash
# Reduzir batch size
export TRAIN_BATCH_SIZE=1

# Ativar mixed precision (economiza VRAM)
export TRAIN_USE_AMP=true

# Reduzir num_workers
export TRAIN_NUM_WORKERS=0

# Limpar cache CUDA
python3 -c "import torch; torch.cuda.empty_cache()"
```

### 2. Dataset Não Encontrado

**Erro:**
```
WARNING - ⚠️  Dataset não encontrado - usando modo TEMPLATE
```

**Solução:**

```bash
# Verificar se dataset existe
ls -la train/data/MyTTSDataset/

# Deve conter:
# - metadata_train.csv
# - metadata_val.csv
# - wavs/

# Se não existe, rodar pipeline completo:
python3 -m train.scripts.download_youtube
python3 -m train.scripts.segment_audio
python3 -m train.scripts.transcribe_audio_parallel
python3 -m train.scripts.build_ljs_dataset
```

### 3. Modelo Não Carrega (Template Mode)

**Warning:**
```
⚠️  SMOKE TEST MODE: Using dummy model (not loading full XTTS)
```

**Explicação:**
- v2.0 está em modo TEMPLATE
- Não carrega modelo XTTS real
- Para implementação real, ver comentários no código

**Para Implementar:**

```python
# Em train/scripts/train_xtts.py, função load_pretrained_model():

# Descomentar e adaptar:
# from TTS.tts.models.xtts import Xtts
# from TTS.tts.configs.xtts_config import XttsConfig
# 
# config = XttsConfig()
# model = Xtts.init_from_config(config)
# model.load_checkpoint(config, checkpoint_path)
```

### 4. LoRA Não Funciona

**Error:**
```
AttributeError: 'DummyModel' object has no attribute 'prepare_inputs_for_generation'
```

**Causa:**
- PEFT/LoRA precisa de modelo real com métodos específicos
- Dummy model em template mode não tem esses métodos

**Solução:**
- Implementar modelo XTTS real
- LoRA funcionará automaticamente após implementação

### 5. Transcription Muito Lenta

**Problema:** Whisper transcribe muito devagar

**Soluções:**

```bash
# Usar versão parallel (15x faster)
python3 -m train.scripts.transcribe_audio_parallel

# Ou usar modelo menor
# Editar train/config/dataset_config.yaml:
whisper:
  model: "base"  # ou "small" ao invés de "medium"
```

### 6. Segmentos Muito Curtos/Longos

**Problema:** Muitos segmentos rejeitados

**Solução:**

```bash
# Editar train/config/dataset_config.yaml
segmentation:
  min_duration: 3.0  # Reduzir mínimo
  max_duration: 20.0  # Aumentar máximo
  silence_threshold: -35  # Ajustar threshold
```

---

## 📖 Referências

### Documentação Oficial

- [Coqui TTS GitHub](https://github.com/coqui-ai/TTS)
- [XTTS-v2 Model Card](https://huggingface.co/coqui/XTTS-v2)
- [PEFT/LoRA Documentation](https://huggingface.co/docs/peft)
- [Whisper AI](https://github.com/openai/whisper)

### Tutoriais

- [XTTS Fine-tuning Guide](https://docs.coqui.ai/en/latest/tutorial_for_nervous_beginners.html)
- [LoRA Paper](https://arxiv.org/abs/2106.09685)
- [Dataset Preparation Best Practices](https://docs.coqui.ai/en/latest/formatting_your_dataset.html)

### Este Projeto

- `README.md` - Visão geral do pipeline
- `train/train_settings.py` - Configuração Pydantic
- `/docs/SESSION_SUMMARY.md` - Sprint TRAIN-3 completion

---

## 🎯 Próximos Passos

1. ✅ **Prepare Dataset**: Rode pipeline completo
2. ⏳ **Implemente Modelo XTTS**: Adapte `load_pretrained_model()`
3. ⏳ **Teste Treinamento**: Rode epoch 1-10 para validar
4. ⏳ **Treinamento Completo**: 1000 epochs (6-12h)
5. ⏳ **Avalie Modelo**: Teste síntese com checkpoint
6. ⏳ **Fine-tune Hiperparâmetros**: Ajuste LR, batch size, etc.

**Status v2.0:** Template implementado ✅ | Modelo XTTS real ⏳

---

**Última atualização:** 2025-12-07  
**Versão:** v2.0 (Pydantic Settings)
