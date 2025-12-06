# 🎙️ Audio Voice Service

> **Microserviço profissional de Text-to-Speech (TTS) e Voice Cloning com suporte multi-engine e Voice Conversion avançada**

Sistema completo de geração de voz sintética usando **XTTS v2** (Coqui TTS), **F5-TTS** especializado em PT-BR, e **RVC** (Retrieval-based Voice Conversion) para conversão de voz de alta qualidade.

[![FastAPI](https://img.shields.io/badge/FastAPI-0.120.0-009688?logo=fastapi)](https://fastapi.tiangolo.com/)
[![Python](https://img.shields.io/badge/Python-3.11-3776AB?logo=python&logoColor=white)](https://www.python.org/)
[![Docker](https://img.shields.io/badge/Docker-Ready-2496ED?logo=docker&logoColor=white)](https://www.docker.com/)
[![CUDA](https://img.shields.io/badge/CUDA-11.8-76B900?logo=nvidia&logoColor=white)](https://developer.nvidia.com/cuda-toolkit)
[![License](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)

---

## ✨ Destaques

🎯 **Multi-Engine TTS**  
Suporte a XTTS v2 (16 idiomas) e F5-TTS (otimizado PT-BR) com troca dinâmica de engines

🎤 **Voice Cloning Zero-Shot**  
Clone qualquer voz com apenas 5-300 segundos de áudio de referência

🎭 **RVC Voice Conversion**  
Transforme vozes geradas com modelos RVC para qualidade premium

⚙️ **Quality Profiles**  
8 perfis pré-configurados (3 XTTS + 5 F5-TTS) + criação de perfis customizados

🌐 **WebUI Completa**  
Interface Bootstrap 5 responsiva com 6 abas e gerenciamento completo

📦 **Produção-Ready**  
Docker + Celery + Redis + Circuit Breaker + Health Checks

---

## 📋 Índice

- [Funcionalidades](#-funcionalidades)
- [Arquitetura](#-arquitetura-de-alto-nível)
- [Pré-requisitos](#-pré-requisitos)
- [Instalação Rápida](#-instalação-rápida)
- [Uso Básico](#-uso-básico)
- [API](#-api-endpoints)
- [Estrutura do Projeto](#-estrutura-do-projeto)
- [Testes](#-testes)
- [Comandos Úteis](#-comandos-úteis-makefile)
- [**Treinamento F5-TTS**](#-treinamento-f5-tts) ⭐ **NOVO**
- [Documentação](#-documentação)
- [Contribuindo](#-contribuindo)
- [Licença](#-licença)

---

## 🚀 Funcionalidades

### Text-to-Speech (TTS)

- ✅ **XTTS v2** (Coqui TTS): Multilingual, 16 idiomas suportados
- ✅ **F5-TTS**: Especializado em português brasileiro de alta qualidade
- ✅ **Voice Presets**: 8 vozes genéricas pré-configuradas
- ✅ **Voice Cloning**: Clone vozes customizadas com zero-shot learning
- ✅ **Quality Profiles**: Sistema de perfis de qualidade configuráveis
- ✅ **Multi-formato**: Download em WAV, MP3, OGG, FLAC, M4A, OPUS

### Voice Cloning

- ✅ Upload de áudio de referência (WAV, MP3, OGG)
- ✅ Processamento assíncrono via Celery
- ✅ Validação automática de duração (5s - 300s)
- ✅ Armazenamento persistente em Redis
- ✅ Gerenciamento completo via API REST

### RVC Voice Conversion

- ✅ Upload de modelos RVC (.pth + .index)
- ✅ 7 parâmetros configuráveis (pitch, index_rate, protect, etc.)
- ✅ 6 métodos F0 (pm, harvest, crepe, dio, fcpe, rmvpe)
- ✅ Integração opcional no pipeline TTS (XTTS → RVC)
- ✅ Fallback automático em caso de erro

### Sistema de Jobs

- ✅ Criação de jobs TTS via API REST
- ✅ Listagem com paginação e filtros avançados
- ✅ Status tracking em tempo real (queued, processing, completed, failed)
- ✅ Progress tracking (0.0 - 100.0%)
- ✅ Download multi-formato com conversão automática
- ✅ Busca por Job ID com download direto

### WebUI

- ✅ Interface Bootstrap 5 responsiva e moderna
- ✅ 6 abas: Jobs, F5-TTS, Voices, RVC Models, Quality Profiles, About
- ✅ Formulários validados com feedback em tempo real
- ✅ Toast notifications (sucesso/erro/warning)
- ✅ Progress bars para jobs em processamento
- ✅ Modals para operações complexas
- ✅ Acesso direto: http://localhost:8005/webui

---

## 🏗️ Arquitetura de Alto Nível

```
┌─────────────────┐
│   WebUI / API   │  ← FastAPI (port 8005)
│   (Bootstrap 5) │
└────────┬────────┘
         │
    ┌────▼─────┐
    │  Redis   │  ← Jobs, Voices, Quality Profiles, RVC Models
    └────┬─────┘
         │
┌────────▼────────────┐
│  Celery Worker      │
│  ┌──────────────┐   │
│  │ VoiceProcessor│  │ ← Orquestra TTS + RVC
│  └──────┬────────┘  │
│         │           │
│  ┌──────▼──────┐    │
│  │TTS Engines  │    │
│  │ ├─ XTTS     │    │ ← Coqui TTS v2
│  │ └─ F5-TTS   │    │ ← F5-TTS PT-BR
│  └─────────────┘    │
│         │           │
│  ┌──────▼──────┐    │
│  │ RVC Client  │    │ ← Voice Conversion (opcional)
│  └─────────────┘    │
└─────────────────────┘
         │
    ┌────▼─────┐
    │  NVIDIA  │  ← CUDA 11.8 + PyTorch 2.4
    │   GPU    │
    └──────────┘
```

**Componentes principais:**

- **FastAPI:** API REST + WebUI estática
- **Celery:** Processamento assíncrono de jobs
- **Redis:** Cache de jobs, voice profiles, quality profiles
- **TTS Engines:** Factory pattern com XTTS v2 e F5-TTS
- **RVC Client:** Voice conversion opcional
- **VRAM Manager:** Gerenciamento inteligente de memória GPU

📖 **Documentação detalhada:** [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md)

---

## 📦 Pré-requisitos

### Hardware

**Mínimo (CPU):**
- CPU: 4 cores
- RAM: 8GB
- Disco: 20GB livres

**Recomendado (GPU):**
- CPU: 8+ cores
- RAM: 16GB+
- Disco: 50GB+ SSD
- GPU: NVIDIA RTX 3060+ (6GB+ VRAM)
- CUDA: 11.8+

### Software

- [Docker](https://docs.docker.com/get-docker/) 24.0+
- [Docker Compose](https://docs.docker.com/compose/install/) 2.20+
- [NVIDIA Container Toolkit](https://docs.nvidia.com/datacenter/cloud-native/container-toolkit/install-guide.html) (se usar GPU)
- Git

**Verificar instalação:**

```powershell
docker --version
docker compose version
nvidia-smi  # Se usar GPU
```

---

## ⚡ Instalação Rápida

### 1. Clonar Repositório

```bash
git clone https://github.com/JohnHeberty/tts-webui-proxmox-passthrough.git
cd tts-webui-proxmox-passthrough
```

### 2. Configurar Ambiente

Crie arquivo `.env` na raiz:

```env
# ===== APLICAÇÃO =====
PORT=8005
DEBUG=false

# ===== REDIS =====
REDIS_URL=redis://localhost:6379/0

# ===== TTS ENGINES =====
TTS_ENGINE_DEFAULT=xtts

# XTTS (GPU)
XTTS_ENABLED=true
XTTS_DEVICE=cuda
XTTS_FALLBACK_CPU=true

# F5-TTS (GPU)
F5TTS_ENABLED=true
F5TTS_DEVICE=cuda
F5TTS_FALLBACK_CPU=true

# ===== LOW VRAM MODE =====
LOW_VRAM=false  # true se VRAM < 8GB
```

**💡 Dica:** Para usar somente CPU, configure `XTTS_DEVICE=cpu` e `F5TTS_DEVICE=cpu`

### 3. Iniciar Serviços

```bash
# Build e iniciar containers
docker compose up -d

# Verificar logs
docker compose logs -f

# Aguardar health check (30-90s)
curl http://localhost:8005/health
```

### 4. Acessar Serviços

- **WebUI:** http://localhost:8005/webui
- **API Docs:** http://localhost:8005/docs (Swagger)
- **Health:** http://localhost:8005/health

---

## 🎯 Uso Básico

### Via WebUI (Recomendado)

1. Acesse http://localhost:8005/webui
2. Aba **"Jobs"** → Preencha formulário:
   - Texto: "Olá, este é um teste de voz."
   - Engine: XTTS
   - Preset: female_generic
3. Clique **"Criar Job"**
4. Aguarde processamento (barra de progresso)
5. Download: Clique no botão de download (WAV, MP3, etc.)

### Via API (cURL)

**Criar job TTS:**

```bash
curl -X POST http://localhost:8005/jobs \
  -H "Content-Type: application/json" \
  -d '{
    "text": "Olá, este é um teste de voz.",
    "engine": "xtts",
    "mode": "preset",
    "preset": "female_generic",
    "source_language": "pt-BR"
  }'
```

**Resposta:**
```json
{
  "id": "job_abc123",
  "status": "queued",
  "text": "Olá, este é um teste de voz.",
  "created_at": "2025-12-01T10:00:00Z"
}
```

**Verificar status:**

```bash
curl http://localhost:8005/jobs/job_abc123
```

**Download áudio:**

```bash
# WAV (padrão)
curl http://localhost:8005/jobs/job_abc123/download?format=wav -o output.wav

# MP3
curl http://localhost:8005/jobs/job_abc123/download?format=mp3 -o output.mp3
```

### Clonar Voz

**Upload de áudio de referência:**

```bash
curl -X POST http://localhost:8005/voices/clone \
  -F "file=@my_voice.wav" \
  -F "name=Minha Voz" \
  -F "language=pt-BR" \
  -F "description=Voz clonada para testes"
```

**Usar voz clonada em job:**

```bash
curl -X POST http://localhost:8005/jobs \
  -H "Content-Type: application/json" \
  -d '{
    "text": "Testando minha voz clonada.",
    "engine": "xtts",
    "mode": "voice",
    "voice_id": "voice_xyz789"
  }'
```

---

## 📡 API Endpoints

O serviço expõe **42 endpoints REST**. Principais:

| Categoria | Endpoint | Método | Descrição |
|-----------|----------|--------|-----------|
| **Jobs** | `/jobs` | POST | Criar job TTS |
| | `/jobs` | GET | Listar jobs (paginado) |
| | `/jobs/{id}` | GET | Buscar job específico |
| | `/jobs/{id}/download` | GET | Download áudio (WAV/MP3/OGG/FLAC/M4A) |
| | `/jobs/{id}` | DELETE | Deletar job |
| **Voices** | `/voices/clone` | POST | Clonar voz |
| | `/voices` | GET | Listar vozes clonadas |
| | `/voices/{id}` | GET | Detalhes de voz |
| | `/voices/{id}` | DELETE | Deletar voz |
| **RVC** | `/rvc-models` | POST | Upload modelo RVC |
| | `/rvc-models` | GET | Listar modelos RVC |
| | `/rvc-models/{id}` | DELETE | Deletar modelo RVC |
| **Profiles** | `/quality-profiles` | GET | Listar quality profiles |
| | `/quality-profiles` | POST | Criar perfil customizado |
| | `/quality-profiles/{id}/set-default` | POST | Definir perfil padrão |
| **System** | `/health` | GET | Health check |
| | `/languages` | GET | Idiomas suportados |
| | `/presets` | GET | Voice presets |
| | `/admin/stats` | GET | Estatísticas do sistema |

📖 **Documentação completa:** [docs/api-reference.md](docs/api-reference.md)  
🔗 **Swagger UI:** http://localhost:8005/docs

---

## 📁 Estrutura do Projeto

```
tts-webui-proxmox-passthrough/
├── app/                        # Código fonte principal
│   ├── main.py                 # FastAPI app (42 endpoints)
│   ├── models.py               # Pydantic models
│   ├── processor.py            # VoiceProcessor (orquestração)
│   ├── engines/                # TTS engines (Factory pattern)
│   │   ├── xtts_engine.py      # XTTS v2
│   │   └── f5tts_engine.py     # F5-TTS
│   ├── rvc_client.py           # RVC Voice Conversion
│   ├── quality_profiles.py     # Sistema de Quality Profiles
│   └── webui/                  # Interface web
│       └── index.html          # SPA Bootstrap 5
├── docs/                       # Documentação
│   ├── getting-started.md      # Setup inicial
│   ├── ARCHITECTURE.md         # Arquitetura detalhada
│   ├── api-reference.md        # Referência completa da API
│   ├── QUALITY_PROFILES.md     # Guia de perfis
│   └── LOW_VRAM.md             # Otimizações para GPU
├── tests/                      # Testes automatizados
│   ├── unit/
│   ├── integration/
│   └── e2e/
├── scripts/                    # Scripts utilitários
│   └── validate-*.sh           # Validações
├── Dockerfile                  # CUDA 11.8 + PyTorch 2.4
├── docker-compose.yml          # API + Celery Worker
├── requirements.txt            # Dependências Python
├── Makefile                    # Comandos úteis
└── README.md                   # Este arquivo
```

---

## 🧪 Testes

### Executar Testes

```bash
# Todos os testes
docker exec -it audio-voice-api pytest tests/

# Testes unitários
pytest tests/unit/

# Testes de integração
pytest tests/integration/

# Testes E2E
pytest tests/e2e/

# Com coverage
pytest tests/ --cov=app --cov-report=html
```

### Suite de Testes

- ✅ **Unit Tests:** Componentes isolados (engines, RVC, validators)
- ✅ **Integration Tests:** API endpoints, Celery tasks
- ✅ **E2E Tests:** Fluxos completos (clone → TTS → RVC → download)
- ✅ **Quality Tests:** Análise acústica de voice cloning

---

## 🛠️ Comandos Úteis (Makefile)

```bash
# Ver comandos disponíveis
make help

# Rebuild completo (sem cache)
make rebuild

# Rebuild rápido (com cache)
make rebuild-fast

# Ver logs
make logs               # Todos
make logs-api           # API
make logs-celery        # Worker

# Gerenciar containers
make up                 # Iniciar
make down               # Parar
make restart            # Reiniciar

# Monitoramento
make status             # Status dos containers
make health             # Health checks
make vram-stats         # Estatísticas de VRAM

# Debug
make shell-api          # Shell no container da API
make shell-celery       # Shell no worker
make env-check          # Verificar variáveis de ambiente
```

---

## 📚 Documentação

### Guias Essenciais

- 🚀 **[Getting Started](docs/getting-started.md)** - Setup inicial e primeiro uso
- 🏗️ **[ARCHITECTURE.md](docs/ARCHITECTURE.md)** - Arquitetura detalhada do sistema
- 📡 **[API Reference](docs/api-reference.md)** - Referência completa dos 42 endpoints
- 🎛️ **[QUALITY_PROFILES.md](docs/QUALITY_PROFILES.md)** - Guia de perfis de qualidade
- ⚙️ **[LOW_VRAM.md](docs/LOW_VRAM.md)** - Otimizações para GPUs com pouca VRAM

### Documentação Adicional

- 🚢 **[DEPLOYMENT.md](docs/DEPLOYMENT.md)** - Deploy em produção
- 📝 **[CHANGELOG.md](docs/CHANGELOG.md)** - Histórico de versões
- 🔧 **[INFRASTRUCTURE_SETUP.md](docs/INFRASTRUCTURE_SETUP.md)** - Setup de infraestrutura

### Documentação Interativa

- **Swagger UI:** http://localhost:8005/docs
- **ReDoc:** http://localhost:8005/redoc

---

## 🤝 Contribuindo

Contribuições são bem-vindas! Siga os passos:

### 1. Fork e Clone

```bash
git clone https://github.com/SEU-USUARIO/tts-webui-proxmox-passthrough.git
cd tts-webui-proxmox-passthrough
```

### 2. Criar Branch

```bash
git checkout -b feature/minha-feature
# ou
git checkout -b fix/meu-bugfix
```

### 3. Desenvolver

- Siga o estilo de código existente
- Adicione testes para novas features
- Atualize documentação se necessário
- Execute testes: `pytest tests/`

### 4. Commit

```bash
git add .
git commit -m "feat: adiciona suporte a novo engine"
# ou
git commit -m "fix: corrige erro em RVC conversion"
```

**Convenção de commits:**
- `feat:` Nova feature
- `fix:` Correção de bug
- `docs:` Mudanças na documentação
- `refactor:` Refatoração de código
- `test:` Adição/modificação de testes
- `chore:` Tarefas de manutenção

### 5. Push e Pull Request

```bash
git push origin feature/minha-feature
```

Abra Pull Request no GitHub com descrição detalhada.

### Diretrizes

- ✅ Código bem documentado (docstrings)
- ✅ Testes unitários para novas features
- ✅ Type hints em funções Python
- ✅ Logs informativos (não excessivos)
- ✅ Tratamento de erros adequado

---

## 🐛 Reportar Bugs

Encontrou um bug? Abra uma [issue](https://github.com/JohnHeberty/tts-webui-proxmox-passthrough/issues) com:

1. **Descrição clara do problema**
2. **Passos para reproduzir**
3. **Comportamento esperado vs atual**
4. **Logs relevantes** (use `make logs`)
5. **Ambiente:**
   - OS: Windows/Linux/macOS
   - Docker version
   - GPU (se aplicável): modelo e VRAM
   - Versão do projeto

---

## 📝 Licença

Este projeto está licenciado sob a [MIT License](LICENSE).

```
MIT License

Copyright (c) 2025 João Freitas (JohnHeberty)

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

[... texto completo da MIT License ...]
```

---

## 🎓 Treinamento F5-TTS

Pipeline completo de **treinamento personalizado de modelos F5-TTS** para criar vozes customizadas de alta qualidade.

### 🚀 Quick Start

```bash
# 1. Setup do ambiente de treinamento
python train/scripts/health_check.py

# 2. Prepare seu dataset (YouTube, áudio local, etc.)
python train/examples/03_custom_dataset.py --audio-dir /path/to/audio

# 3. Configure o treinamento
vim train/config/config.yaml

# 4. Inicie o treinamento
python -m train.run_training --config train/config/config.yaml

# 5. Teste o modelo treinado
python train/examples/02_inference_simple.py
```

### 📚 Documentação Completa

**Para iniciantes:**
- 📖 **[Tutorial Passo-a-Passo](train/docs/TUTORIAL.md)** ⭐ **COMECE AQUI**
  - Setup completo do ambiente
  - Preparação de datasets
  - Configuração e execução
  - Monitoramento e deploy

**Referências técnicas:**
- 🔧 **[Inference API](train/docs/INFERENCE_API.md)** - API unificada de inferência
- ⚙️ **[Config Schema](train/config/README.md)** - Configuração detalhada
- 📊 **[Quality Profiles](docs/QUALITY_PROFILES.md)** - Perfis de qualidade

**Módulos:**
- 🎵 **[Audio Processing](train/audio/README.md)** - Processamento de áudio
- 📝 **[Text Processing](train/text/README.md)** - Normalização de texto
- 🛠️ **[Scripts](train/scripts/README.md)** - Ferramentas utilitárias

**Exemplos práticos:**
- 💡 **[Examples](train/examples/README.md)** - 4 exemplos comentados
  - Quick training test (1 epoch)
  - Simple inference
  - Custom dataset creation
  - Resume training

**Índice completo:**
- 📑 **[Documentation Index](train/docs/INDEX.md)** - Navegação completa

### ✨ Principais Features

✅ **Dataset Processing**
- Download automático do YouTube com legendas
- Segmentação inteligente de áudio (VAD)
- Normalização e quality checks
- Suporte a áudios longos (>30s)

✅ **Training Pipeline**
- Configuração via YAML type-safe (Pydantic)
- Reproducibilidade completa (seed fixo)
- TensorBoard integration
- Best model tracking
- Checkpoint management

✅ **Inference API**
- API unificada com singleton pattern
- CLI tool (typer + rich)
- Batch processing
- Voice cloning
- Multi-device (CUDA/CPU)

✅ **Code Quality**
- Ruff + Black + Mypy configurados
- 11 testes unitários (100% passing)
- Type hints completos
- Documentação extensiva

### 📦 Estrutura

```
train/
├── docs/               # Documentação completa
│   ├── TUTORIAL.md    # Tutorial passo-a-passo ⭐
│   ├── INDEX.md       # Índice de navegação
│   └── INFERENCE_API.md  # API reference
├── examples/          # Exemplos práticos
│   ├── 01_quick_train.py      # Teste rápido
│   ├── 02_inference_simple.py # Inferência básica
│   ├── 03_custom_dataset.py   # Criar dataset
│   └── 04_resume_training.py  # Retomar treino
├── config/            # Configuração
│   ├── schemas.py     # Pydantic models
│   ├── loader.py      # Config loading
│   └── config.yaml    # Arquivo de config
├── audio/             # Processamento de áudio
├── text/              # Processamento de texto
├── inference/         # API de inferência
├── scripts/           # Utilitários
└── tests/             # Testes unitários
```

### 🎯 Casos de Uso

**1. Treinar modelo personalizado:**
```bash
# Prepare dataset de 1-10 horas de áudio
python train/examples/03_custom_dataset.py --audio-dir /audio

# Configure e treine
python -m train.run_training --config train/config/config.yaml
```

**2. Fine-tuning de modelo existente:**
```bash
# Retome de checkpoint com dataset menor (30min-2h)
python train/examples/04_resume_training.py \
    --checkpoint models/f5tts/model_best.pt \
    --additional-epochs 20
```

**3. Testar modelo treinado:**
```bash
# Inference CLI
python -m train.cli.infer \
    --checkpoint model.pt \
    --vocab vocab.txt \
    --text "Olá, mundo!" \
    --ref-audio ref.wav \
    --output out.wav
```

### 🔬 Recursos Avançados

- **MLOps:** TensorBoard, checkpoint management, best model tracking
- **Reproducibilidade:** Seed fixo, deterministic algorithms
- **VRAM Optimization:** Gradient accumulation, mixed precision
- **Data Augmentation:** Audio effects, speed variation
- **Quality Assurance:** Text validation, audio checks

### 📊 Performance

| Dataset | VRAM | Batch Size | Tempo/Epoch |
|---------|------|------------|-------------|
| 1h | 8GB | 4 | ~15 min |
| 5h | 12GB | 8 | ~45 min |
| 10h | 24GB | 16 | ~90 min |

### 🆘 Troubleshooting

**OOM (Out of Memory)?**
```yaml
# Reduza batch size no config.yaml
training:
  batch_size_per_gpu: 2  # Ou 1
  gradient_accumulation_steps: 4
```

**Loss não diminui?**
- Verifique learning rate (1e-4 a 1e-5)
- Valide qualidade do dataset
- Aumente número de épocas

**Mais problemas?**
- [Tutorial - Seção Troubleshooting](train/docs/TUTORIAL.md#7-troubleshooting)
- [Health Check](train/scripts/health_check.py)

---

## 💬 Suporte e Comunidade

### Documentação

- 📖 **[Docs completa](/docs)** - Toda a documentação técnica
- 🚀 **[Getting Started](docs/getting-started.md)** - Guia de início rápido
- 🏗️ **[Arquitetura](docs/ARCHITECTURE.md)** - Entenda o sistema
- 📡 **[API Reference](docs/api-reference.md)** - Referência completa

### Suporte

- 🐛 **[Issues](https://github.com/JohnHeberty/tts-webui-proxmox-passthrough/issues)** - Reportar bugs ou solicitar features
- 💬 **[Discussions](https://github.com/JohnHeberty/tts-webui-proxmox-passthrough/discussions)** - Perguntas e discussões gerais

### Contato

- **Autor:** João Freitas (JohnHeberty)
- **GitHub:** [@JohnHeberty](https://github.com/JohnHeberty)
- **Repositório:** [tts-webui-proxmox-passthrough](https://github.com/JohnHeberty/tts-webui-proxmox-passthrough)

---

## 🙏 Agradecimentos

Este projeto utiliza as seguintes tecnologias open-source:

- **[Coqui TTS](https://github.com/coqui-ai/TTS)** - XTTS v2 engine
- **[F5-TTS](https://github.com/SWivid/F5-TTS)** - F5-TTS engine para PT-BR
- **[RVC](https://github.com/RVC-Project/Retrieval-based-Voice-Conversion-WebUI)** - Voice conversion
- **[FastAPI](https://fastapi.tiangolo.com/)** - Framework web moderno
- **[Celery](https://docs.celeryq.dev/)** - Task queue assíncrona
- **[Redis](https://redis.io/)** - Cache e message broker
- **[PyTorch](https://pytorch.org/)** - Deep learning framework
- **[Bootstrap](https://getbootstrap.com/)** - Framework CSS

---

## 🔗 Links Relacionados

- **[Coqui TTS Documentation](https://tts.readthedocs.io/)**
- **[F5-TTS Paper](https://arxiv.org/abs/2410.06885)**
- **[RVC Documentation](https://docs.ai-hub.wtf/rvc/)**
- **[FastAPI Documentation](https://fastapi.tiangolo.com/)**
- **[Docker Best Practices](https://docs.docker.com/develop/dev-best-practices/)**

---

## 📊 Status do Projeto

🟢 **Ativo e em desenvolvimento**

- Última atualização: Dezembro 2025
- Versão estável: 2.0.1
- Ambiente de produção: ✅ Testado e validado

### Roadmap Futuro

- [ ] Suporte a mais engines TTS (Bark, Tortoise, etc.)
- [ ] API de streaming (WebSockets)
- [ ] Dashboard de analytics
- [ ] Autenticação e autorização (JWT)
- [ ] Multi-tenant support
- [ ] Kubernetes deployment manifests

---

<p align="center">
  <strong>Desenvolvido com ❤️ por <a href="https://github.com/JohnHeberty">João Freitas</a></strong>
</p>

<p align="center">
  <a href="#-audio-voice-service">↑ Voltar ao topo</a>
</p>
