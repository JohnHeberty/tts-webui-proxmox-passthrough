# 🎙️ Audio Voice Service v2.0

> **Microserviço profissional de Text-to-Speech (TTS) e Voice Cloning com XTTS-v2**

Sistema completo de geração de voz sintética usando **XTTS v2** (Coqui TTS) com voice cloning zero-shot e quality profiles.

[![FastAPI](https://img.shields.io/badge/FastAPI-0.120.0-009688?logo=fastapi)](https://fastapi.tiangolo.com/)
[![Python](https://img.shields.io/badge/Python-3.11-3776AB?logo=python&logoColor=white)](https://www.python.org/)
[![Docker](https://img.shields.io/badge/Docker-Ready-2496ED?logo=docker&logoColor=white)](https://www.docker.com/)
[![CUDA](https://img.shields.io/badge/CUDA-11.8-76B900?logo=nvidia&logoColor=white)](https://developer.nvidia.com/cuda-toolkit)
[![License](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)

---

## ✨ v2.0 Highlights

🎯 **XTTS-v2 Only** ⭐ **UPDATED**  
Streamlined to use only XTTS-v2 engine for better performance and maintainability

🗑️ **RVC Removed** ⭐ **BREAKING**  
RVC voice conversion removed - use XTTS-v2 native voice cloning instead

🚀 **Faster Startup** ⭐ **NEW**  
No more lazy loading - models load on startup (~5-15s)

⚡ **Better Performance** ⭐ **NEW**  
Reduced dependencies, lower VRAM usage (8GB minimum, 12GB+ recommended)

🎨 **Quality Profiles** ⭐ **ENHANCED**  
3 built-in profiles: fast, balanced, high_quality

📦 **Production-Ready**  
Docker + Celery + Redis + Circuit Breaker + Health Checks

---

## 📋 Índice

- [Funcionalidades](#-funcionalidades)
- [Arquitetura](#-arquitetura)
- [Pré-requisitos](#-pré-requisitos)
- [Instalação Rápida](#-instalação-rápida)
- [Uso Básico](#-uso-básico)
- [API](#-api-endpoints)
- [Migração v1→v2](#-migração-v1v2)
- [Documentação](#-documentação)

---

## 🚀 Funcionalidades

### Text-to-Speech (TTS)

- ✅ **XTTS v2** (Coqui TTS): Multilingual, 16 idiomas suportados
- ✅ **Voice Presets**: 8 vozes genéricas pré-configuradas
- ✅ **Voice Cloning**: Clone vozes customizadas com zero-shot learning
- ✅ **Quality Profiles**: fast, balanced, high_quality
- ✅ **Multi-format Output**: WAV, MP3, OGG, FLAC, M4A, OPUS

### API

- ✅ **REST API**: FastAPI com OpenAPI docs automático
- ✅ **Async Jobs**: Celery + Redis para processamento em background
- ✅ **Health Checks**: Endpoint `/health` com métricas de GPU/VRAM
- ✅ **Metrics**: Prometheus `/metrics` endpoint

### DevOps

- ✅ **Docker**: Imagem otimizada com CUDA 11.8
- ✅ **GPU Support**: NVIDIA Container Toolkit
- ✅ **Logging**: Logs estruturados JSON
- ✅ **Error Handling**: Circuit breaker para CUDA OOM

---

## 🏗️ Arquitetura

```
┌─────────────┐     ┌──────────────┐
│   WebUI     │────▶│  FastAPI     │
│  Bootstrap  │     │  /jobs       │
└─────────────┘     └──────┬───────┘
                           │
                           ▼
                    ┌──────────────┐      ┌─────────────┐
                    │    Redis     │◀────▶│   Celery    │
                    │  Job Store   │      │   Worker    │
                    └──────────────┘      └──────┬──────┘
                                                 │
                                                 ▼
                                          ┌─────────────┐
                                          │  XTTS-v2    │
                                          │   Engine    │
                                          └─────────────┘
```

**Key Components:**
- **FastAPI**: API RESTful assíncrona
- **XTTS-v2**: Engine TTS principal (única engine)
- **Celery**: Processamento assíncrono de jobs
- **Redis**: Job store + Celery broker
- **Docker**: Containerização com GPU support

---

## 📦 Pré-requisitos

### Hardware
- **GPU**: NVIDIA com ≥8GB VRAM (12GB+ recomendado)
- **Compute Capability**: ≥7.0 (RTX 2000+, Tesla T4+)
- **CPU**: 4+ cores
- **RAM**: 16GB+
- **Disk**: 20GB+ (para modelos)

### Software
- **Docker**: ≥20.10
- **Docker Compose**: ≥1.29  
- **NVIDIA Driver**: ≥525.x
- **NVIDIA Container Toolkit**

---

## 🚀 Instalação Rápida

### 1. Clonar Repositório

```bash
git clone https://github.com/seu-usuario/tts-webui-proxmox-passthrough.git
cd tts-webui-proxmox-passthrough
```

### 2. Configurar Ambiente

```bash
cp .env.example .env
# Editar .env conforme necessário
```

### 3. Build & Start

```bash
docker compose up -d --build
```

### 4. Verificar Saúde

```bash
curl http://localhost:8005/health
```

**Resposta esperada:**
```json
{
  "status": "healthy",
  "components": {
    "xtts": {"loaded": true, "device": "cuda:0"},
    "gpu": {"vram_free_gb": 18.5, "vram_total_gb": 24},
    "redis": {"connected": true}
  },
  "uptime_seconds": 3600
}
```

### 5. Acessar WebUI

```
http://localhost:8005
```

---

## 💻 Uso Básico

### Via WebUI

1. Acesse `http://localhost:8005`
2. Digite o texto
3. Selecione qualidade (fast/balanced/high_quality)
4. Clique em "Gerar Áudio"

### Via API

```bash
# Criar job
curl -X POST "http://localhost:8005/jobs" \
  -H "Content-Type: application/json" \
  -d '{
    "text": "Olá, eu sou o XTTS-v2!",
    "mode": "dubbing",
    "voice_preset": "female_generic",
    "tts_engine": "xtts",
    "quality_profile_id": "xtts_balanced"
  }'

# Resposta
{
  "id": "abc123",
  "status": "processing",
  ...
}

# Consultar status
curl "http://localhost:8005/jobs/abc123"

# Download (quando completo)
curl "http://localhost:8005/jobs/abc123/download?format=mp3" -o output.mp3
```

---

## 🌐 API Endpoints

### Core Endpoints

| Método | Endpoint | Descrição |
|--------|----------|-----------|
| `POST` | `/jobs` | Criar job de síntese TTS |
| `GET` | `/jobs/{id}` | Consultar status do job |
| `GET` | `/jobs/{id}/download` | Download do áudio |
| `GET` | `/health` | Healthcheck detalhado |
| `GET` | `/metrics` | Prometheus metrics |

### Quality Profiles

| Método | Endpoint | Descrição |
|--------|----------|-----------|
| `GET` | `/quality-profiles` | Listar perfis de qualidade |

**Perfis Disponíveis:**
- `xtts_fast`: Menor latência (~2s), qualidade adequada
- `xtts_balanced`: Equilíbrio (~3s), **recomendado**
- `xtts_high_quality`: Máxima qualidade (~5s), com denoise

### Voice Profiles

| Método | Endpoint | Descrição |
|--------|----------|-----------|
| `POST` | `/voices/clone` | Clone voz customizada |
| `GET` | `/voices` | Listar vozes disponíveis |

**Docs Completa:** `http://localhost:8005/docs`

---

## 🔄 Migração v1→v2

### Breaking Changes

**1. RVC Removido**
```bash
# ❌ v1.x (com RVC)
curl -X POST /jobs \
  -d '{"enable_rvc": true, "rvc_model_id": "..."}'

# ✅ v2.0 (sem RVC, use voice cloning nativo)
curl -X POST /voices/clone \
  -F "audio=@reference.wav" \
  -F "name=minha_voz"

curl -X POST /jobs \
  -d '{"voice_id": "...", "mode": "dubbing_with_clone"}'
```

**2. F5-TTS Removido**
```bash
# ❌ v1.x
{"tts_engine": "f5tts"}  # Error 400

# ✅ v2.0
{"tts_engine": "xtts"}   # Única opção
```

**3. Quality Profiles Consolidados**
```bash
# ❌ v1.x (profiles diversos)
{"quality_profile": "balanced"}

# ✅ v2.0 (profiles com prefixo engine)
{"quality_profile_id": "xtts_balanced"}
```

### Migration Checklist

- [ ] Remover `enable_rvc`, `rvc_model_id` de requests
- [ ] Substituir `tts_engine: f5tts` por `tts_engine: xtts`
- [ ] Atualizar quality profiles: `balanced` → `xtts_balanced`
- [ ] Migrar workflows RVC para voice cloning XTTS nativo
- [ ] Deletar modelos RVC antigos (`/models/rvc`)
- [ ] Atualizar dependências (rebuild Docker)

---

## 📚 Documentação

| Documento | Descrição |
|-----------|-----------|
| [ARCHITECTURE.md](docs/ARCHITECTURE.md) | Arquitetura do sistema |
| [API Reference](docs/api-reference.md) | Referência completa da API |
| [CHANGELOG.md](docs/CHANGELOG.md) | Histórico de mudanças |
| [DEPLOYMENT.md](docs/DEPLOYMENT.md) | Guia de deployment |
| [QUALITY_PROFILES.md](docs/QUALITY_PROFILES.md) | Guia de quality profiles |
| [MORE.md](MORE.md) | Análise completa do projeto |
| [SPRINTS_RVC_REMOVAL.md](SPRINTS_RVC_REMOVAL.md) | Plano de remoção RVC |

---

## 🧪 Testes

```bash
# Rodar todos os testes
pytest tests/ -v

# Com coverage
pytest tests/ --cov=app --cov-report=term-missing

# Smoke test
curl http://localhost:8005/health
```

---

## 🛠️ Comandos Úteis

```bash
# Ver logs
docker compose logs -f api

# Restart
docker compose restart

# Stop
docker compose down

# Rebuild
docker compose down && docker compose up -d --build

# GPU status
nvidia-smi

# Validar GPU
bash scripts/validate-gpu.sh
```

---

## 📈 Performance

| Métrica | v1.x (RVC + XTTS + F5) | v2.0 (XTTS only) |
|---------|------------------------|------------------|
| Startup | ~30-60s | ~5-15s |
| First Request | ~10-15s | <2s |
| VRAM Usage | 12-16GB | 8-12GB |
| Dependencies | 80+ | ~50 |
| Code Lines | 15000+ | <12000 |

---

## 🤝 Contribuindo

1. Fork o projeto
2. Crie uma branch (`git checkout -b feature/minha-feature`)
3. Commit (`git commit -m 'Add: minha feature'`)
4. Push (`git push origin feature/minha-feature`)
5. Abra um Pull Request

---

## 📄 Licença

Este projeto está sob a licença MIT. Ver [LICENSE](LICENSE) para mais detalhes.

---

## 🙏 Agradecimentos

- [Coqui TTS](https://github.com/coqui-ai/TTS) - XTTS-v2 engine
- [FastAPI](https://fastapi.tiangolo.com/) - Web framework
- [Celery](https://docs.celeryq.dev/) - Async task queue

---

## 📞 Suporte

- **Issues**: [GitHub Issues](https://github.com/seu-usuario/tts-webui-proxmox-passthrough/issues)
- **Docs**: Ver pasta `docs/`
- **API Docs**: `http://localhost:8005/docs`

---

**Versão**: 2.0.0  
**Data**: 2025-12-07  
**Status**: ✅ Production Ready
