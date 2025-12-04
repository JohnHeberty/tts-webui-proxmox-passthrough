# F5-TTS Training Pipeline - Documentação

**Última Atualização:** 04 de Dezembro de 2025  
**Versão:** 3.0 (Configuração via .env)

---

## 📚 Quick Links

| Documento | Descrição |
|-----------|-----------|
| 📖 **[SETUP.md](SETUP.md)** | Instalação e configuração inicial |
| ⚙️ **[CONFIGURATION.md](CONFIGURATION.md)** | Todos os parâmetros do `.env` explicados |
| 🚀 **[USAGE.md](USAGE.md)** | Uso, treinamento e troubleshooting |
| 🎯 **[FINETUNING.md](FINETUNING.md)** | Guia de fine-tuning do F5-TTS |
| 📦 **[DELIVERY.md](DELIVERY.md)** | Histórico de entregas e versões |
| 🔧 **[COMMAND_TRAIN.md](COMMAND_TRAIN.md)** | Atalhos e comandos úteis |

---

## 🎯 Overview

Pipeline completo e modular para fine-tuning do modelo F5-TTS em português brasileiro, otimizado para datasets grandes (15+ horas de áudio).

### ✨ Features Principais

- ✅ **100% Configurável via `.env`** - Zero hardcoding, tudo em variáveis
- ✅ **Auto-download de modelos** - HuggingFace integration
- ✅ **Auto-resume de checkpoints** - Nunca perca progresso
- ✅ **Early stopping inteligente** - Para quando não há mais melhoria
- ✅ **TensorBoard integrado** - Monitoramento em tempo real
- ✅ **Geração automática de samples** - Teste qualidade durante treino
- ✅ **Otimização de memória** - Processamento em chunks (5GB vs 19GB)
- ✅ **Pipeline completo** - Do YouTube ao modelo treinado

---

## 🚀 Quick Start (5 Minutos)

```bash
# 1. Clone e instale
git clone <repo>
cd tts-webui-proxmox-passthrough/train
pip install -r requirements_train.txt

# 2. Configure (IMPORTANTE!)
cp .env.example .env
nano .env  # Ajuste conforme necessário

# 3. Execute
python run_training.py

# 4. Monitore
# TensorBoard: http://localhost:6006
# Terminal: Progress bars em tempo real
```

**Primeiro Uso?** → Leia [SETUP.md](SETUP.md) primeiro!

---

## 📁 Estrutura do Projeto

```
train/
├── 📚 docs/                    # Documentação completa
│   ├── README.md              # Este arquivo
│   ├── SETUP.md               # Guia de instalação
│   ├── CONFIGURATION.md       # Referência do .env
│   ├── USAGE.md               # Como usar
│   ├── FINETUNING.md          # Guia de fine-tuning
│   └── COMMAND_TRAIN.md       # Comandos úteis
│
├── ⚙️ config/                  # Configurações YAML
│   ├── dataset_config.yaml    # Config do dataset
│   └── train_config.yaml      # Config de treinamento
│
├── 🔧 scripts/                 # Pipeline de preparação
│   ├── download_youtube.py          # Step 1: Download
│   ├── prepare_segments_optimized.py # Step 2: Segmentação
│   ├── transcribe_or_subtitles.py   # Step 3: Transcrição
│   ├── build_metadata_csv.py        # Step 4: Metadata
│   ├── prepare_f5_dataset.py        # Step 5: Dataset F5-TTS
│   ├── verify_ready.py              # Pré-flight check
│   ├── verify_structure.py          # Diagnóstico
│   └── test_model.py                # Análise pós-treino
│
├── 🛠️ utils/                   # Utilitários
│   ├── env_loader.py          # Carregador do .env
│   ├── text_normalizer.py     # Normalização de texto
│   └── early_stopping.py      # Early stopping logic
│
├── 📊 data/                    # Datasets (gitignored)
│   ├── raw/                   # Áudio bruto do YouTube
│   ├── processed/             # Segmentos processados
│   ├── f5_dataset/            # Dataset final F5-TTS
│   └── videos.csv             # Lista de vídeos
│
├── 💾 output/                  # Checkpoints (gitignored)
│   └── ptbr_finetuned/        # Checkpoints do modelo
│       ├── model_*.pt         # Checkpoints numerados
│       ├── model_last.pt      # Último checkpoint
│       └── samples/           # Samples de áudio gerados
│
├── 📈 runs/                    # TensorBoard logs (gitignored)
│   └── F5TTS_Base/            # Logs do experimento
│
├── 🎓 pretrained/              # Modelos pré-treinados (gitignored)
│   └── F5-TTS-pt-br/          # Auto-downloaded
│
├── 🚀 run_training.py          # Script principal de treinamento
├── 📝 .env                     # SUA CONFIGURAÇÃO (gitignored)
├── 📋 .env.example             # Template de configuração
├── 🗂️ SCRIPTS.md               # Relatório de scripts
└── 📖 README.md                # Quickstart
```

---

## 🔄 Pipeline Completo

```mermaid
graph LR
    A[YouTube URLs] --> B[download_youtube.py]
    B --> C[prepare_segments_optimized.py]
    C --> D[transcribe_or_subtitles.py]
    D --> E[build_metadata_csv.py]
    E --> F[prepare_f5_dataset.py]
    F --> G[run_training.py]
    G --> H[Modelo Treinado]
```

**5 Steps de Preparação + 1 Treinamento**

1. **Download** → `download_youtube.py` - Baixa áudio do YouTube
2. **Segmentação** → `prepare_segments_optimized.py` - Divide em segmentos
3. **Transcrição** → `transcribe_or_subtitles.py` - Gera texto com Whisper
4. **Metadata** → `build_metadata_csv.py` - Cria metadata.csv
5. **Dataset** → `prepare_f5_dataset.py` - Converte para Arrow
6. **Treinamento** → `run_training.py` - Fine-tuning do modelo

**Detalhes:** Veja [USAGE.md](USAGE.md#pipeline-completo)

---

## 📊 Informações do Modelo

| Característica | Valor |
|----------------|-------|
| **Arquitetura** | F5-TTS (DiT-based) |
| **Parâmetros** | 335.8M |
| **Base Model** | firstpixel/F5-TTS-pt-br |
| **Vocabulário** | 2545 caracteres (multilíngue) |
| **Sample Rate** | 24kHz mono WAV |
| **Precisão** | Mixed FP16 |
| **Checkpoint Size** | ~5GB |

---

## 💻 Requisitos do Sistema

### Mínimo (Produção)
- **GPU:** NVIDIA 16GB+ VRAM (RTX 3090, A100, etc)
- **RAM:** 32GB+ (64GB recomendado)
- **CPU:** 8+ cores
- **Storage:** 100GB+ SSD
- **Python:** 3.11+
- **CUDA:** 12.1+
- **OS:** Linux (Ubuntu 22.04+)

### Desenvolvimento
- **GPU:** 8GB+ VRAM (para testes pequenos)
- **RAM:** 16GB+
- **Storage:** 50GB+

**Nota:** Para datasets grandes (15+ horas), recomenda-se 64GB RAM e GPU 24GB+

---

## ⚙️ Configuração Rápida (.env)

```bash
# Principais parâmetros para ajustar

# Treinamento
EPOCHS=1000                    # Número de épocas
BATCH_SIZE=4                   # Amostras por GPU
LEARNING_RATE=0.0001          # Taxa de aprendizado

# Early Stopping
EARLY_STOP_PATIENCE=50        # Parar após N épocas sem melhoria

# Checkpoints
SAVE_PER_UPDATES=1000         # Salvar a cada N updates
KEEP_LAST_N_CHECKPOINTS=10    # Manter últimos N checkpoints

# Paths
OUTPUT_DIR=train/output/ptbr_finetuned
DATASET_PATH=train/data/f5_dataset
```

**Documentação Completa:** [CONFIGURATION.md](CONFIGURATION.md)

---

## 🆘 Precisa de Ajuda?

| Problema | Solução |
|----------|---------|
| ❌ Erro de instalação | [SETUP.md](SETUP.md#troubleshooting) |
| ⚙️ Dúvida de configuração | [CONFIGURATION.md](CONFIGURATION.md) |
| 🐛 Bug durante treinamento | [USAGE.md](USAGE.md#troubleshooting) |
| 🎯 Como fazer fine-tuning | [FINETUNING.md](FINETUNING.md) |
| 📜 Histórico de mudanças | [DELIVERY.md](DELIVERY.md) |

---

## 📊 Monitoramento

### TensorBoard
```bash
# Auto-inicia em http://localhost:6006
# Métricas disponíveis:
- Loss (training)
- Learning rate
- Gradient norm
- Samples de áudio gerados
```

### Terminal
```bash
# Progress bars em tempo real
Epoch 1/1000 |████████░░░| 80% - Loss: 0.245
Update 5000 - Checkpoint saved
```

### Logs
```bash
train/logs/training.log        # Log detalhado
train/runs/F5TTS_Base/         # TensorBoard events
```

---

## 🔧 Scripts Úteis

```bash
# Verificar ambiente
python -m train.scripts.verify_ready

# Verificar estrutura
python -m train.scripts.verify_structure

# Analisar treinamento
python -m train.scripts.test_model

# Ver relatório de scripts
cat train/SCRIPTS.md
```

**Mais comandos:** [COMMAND_TRAIN.md](COMMAND_TRAIN.md)

---

## 📝 Changelog

**v3.0 (04/12/2025)**
- ✅ 100% configurável via .env
- ✅ Auto-download de modelos pretrained
- ✅ Otimização de memória (5GB vs 19GB)
- ✅ Scripts atualizados para .env
- ✅ Documentação reorganizada

**v2.0**
- Symlinks automáticos
- Early stopping
- TensorBoard integrado

**v1.0**
- Pipeline básico funcional

**Histórico completo:** [DELIVERY.md](DELIVERY.md)

---

## 📜 Licença

Este projeto é parte do TTS WebUI Proxmox Passthrough.  
Consulte o LICENSE no repositório principal.

---

**Última Atualização:** 04/12/2025  
**Maintainer:** @JohnHeberty  
**Status:** 🟢 Produção Ativa

