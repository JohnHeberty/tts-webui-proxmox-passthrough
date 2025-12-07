# Audio Voice Service - Arquitetura

**Serviço:** Audio Voice Service  
**Versão:** 2.0.1  
**Data:** Dezembro 2025  
**Stack:** FastAPI + Celery + Redis + XTTS v2 (v2.0: F5-TTS and RVC removed)

---

## 🎯 OBJETIVO

Microserviço de **Text-to-Speech (TTS)** e **Voice Cloning** com suporte a múltiplos engines de IA e conversão de voz avançada.

### Capacidades Principais

1. **Text-to-Speech Multi-Engine**
   - **XTTS v2** (Coqui TTS): Motor principal, multilingual (16 idiomas)
   - **F5-TTS**: **REMOVED in v2.0** (Previously: specialized PT-BR engine)
   - Sistema de Quality Profiles (8 perfis configuráveis)
   - Vozes genéricas pré-configuradas (8 presets)
   - Vozes clonadas customizadas via zero-shot cloning

2. **Voice Cloning**
   - Clonagem zero-shot com 5-300s de áudio de referência
   - Suporte WAV, MP3, OGG
   - Armazenamento persistente em Redis
   - Gerenciamento completo via API REST

3. **RVC Voice Conversion**
   - Upload de modelos RVC (.pth + .index)
   - 7 parâmetros configuráveis (pitch, index_rate, protect, etc.)
   - 6 métodos F0 (rmvpe, fcpe, pm, harvest, dio, crepe)
   - Integração opcional no pipeline TTS
   - Fallback automático em caso de erro

---

## 📐 ARQUITETURA

### Estrutura do Projeto

```
tts-webui-proxmox-passthrough/
├── app/
│   ├── __init__.py
│   ├── main.py                    # FastAPI app (42 endpoints REST)
│   ├── models.py                  # Pydantic models (Job, VoiceProfile, RvcModel)
│   ├── config.py                  # Configurações via .env
│   ├── processor.py               # VoiceProcessor (orquestração TTS + RVC)
│   ├── redis_store.py             # RedisJobStore (cache de jobs/voices)
│   ├── celery_config.py           # Configuração Celery
│   ├── celery_tasks.py            # Tasks assíncronas (dubbing, cloning)
│   ├── quality_profiles.py        # Sistema de Quality Profiles
│   ├── quality_profile_manager.py # Manager de perfis (Redis)
│   ├── rvc_client.py              # RVC Voice Conversion client
│   ├── rvc_model_manager.py       # Gerenciador de modelos RVC
│   ├── xtts_client.py             # XTTS v2 client (Coqui TTS)
│   ├── logging_config.py          # Setup de logging
│   ├── exceptions.py              # Exceções customizadas
│   ├── validators.py              # Validadores de entrada
│   ├── vram_manager.py            # Gerenciador de VRAM (LOW_VRAM mode)
│   ├── resilience.py              # Circuit breaker
│   ├── engines/                   # Factory pattern para TTS engines
│   │   ├── __init__.py
│   │   ├── base.py                # TTSEngine (interface)
│   │   ├── factory.py             # create_engine() com caching
│   │   ├── xtts_engine.py         # XTTS v2 implementation
│   │   ├── f5tts_engine.py        # F5-TTS implementation
│   │   └── f5tts_ptbr_engine.py   # F5-TTS PT-BR otimizado
│   └── webui/                     # Interface web Bootstrap 5
│       ├── index.html             # SPA (2100+ linhas JS)
│       └── assets/
│           ├── js/app.js
│           └── css/styles.css
├── scripts/
│   ├── create_default_speaker.py
│   ├── create_voice_presets.py
│   ├── download_models.py
│   └── validate-*.sh              # Scripts de validação
├── tests/                         # Suite de testes (pytest)
│   ├── unit/
│   ├── integration/
│   └── e2e/
├── models/                        # Modelos ML (XTTS, F5-TTS, RVC)
├── voice_profiles/                # Perfis de voz clonados
├── uploads/                       # Uploads temporários
├── processed/                     # Áudios processados
├── temp/                          # Arquivos temporários
├── logs/                          # Logs da aplicação
├── Dockerfile                     # CUDA 11.8 + PyTorch 2.4
├── docker-compose.yml             # API + Celery Worker
├── requirements.txt               # Dependências Python
├── constraints.txt                # Versões fixadas
├── run.py                         # Entry point
└── Makefile                       # Comandos úteis (rebuild, logs, etc.)
```

### Stack Tecnológica

- **Backend:** FastAPI 0.120.0 + Uvicorn
- **Job Queue:** Celery 5.3.4 + Redis 5.0.1
- **Storage:** Redis (jobs, voice profiles, quality profiles, RVC models)
- **TTS Engines:**
  - **XTTS v2** (Coqui TTS 0.27.0+): Multilingual, 16 idiomas
  - **F5-TTS** (1.1.9): Especializado em PT-BR
- **Voice Conversion:** RVC (tts-with-rvc)
- **Audio Processing:** soundfile, numpy, torch, torchaudio
- **ML/DL:** PyTorch 2.4.0+cu118, CUDA 11.8
- **Frontend:** Vanilla JS + Bootstrap 5
- **Container:** Docker + Docker Compose + NVIDIA Runtime
- **Testing:** pytest + httpx

---

## 🔌 INTEGRAÇÃO COM ORCHESTRATOR

### Endpoints Obrigatórios

O serviço implementa os endpoints esperados pelo orchestrator:

1. **`GET /health`** - Health check profundo
2. **`POST /jobs`** - Criar job de dublagem/clonagem
3. **`GET /jobs/{job_id}`** - Status do job
4. **`GET /jobs/{job_id}/download`** - Download do áudio gerado
5. **`DELETE /jobs/{job_id}`** - Remover job

### Endpoints Adicionais de Gerenciamento

6. **`POST /voices/clone`** - Clonar voz (criar perfil)
7. **`GET /voices`** - Listar vozes clonadas
8. **`GET /voices/{voice_id}`** - Detalhes de voz
9. **`DELETE /voices/{voice_id}`** - Remover voz clonada
10. **`POST /admin/cleanup`** - Limpeza manual (deep/basic)
11. **`GET /admin/stats`** - Estatísticas do sistema

### Formato de Requisição

#### Dublagem Simples (Voz Genérica)
```json
POST /jobs
{
  "mode": "dubbing",
  "text": "Hello, this is a test",
  "source_language": "en",
  "target_language": "pt-BR",
  "voice_preset": "female_generic"
}
```

#### Dublagem com Voz Clonada
```json
POST /jobs
{
  "mode": "dubbing_with_clone",
  "text": "Olá, este é um teste",
  "source_language": "pt-BR",
  "target_language": "en",
  "voice_id": "voice_abc123"
}
```

#### Clonagem de Voz
```json
POST /voices/clone
Content-Type: multipart/form-data

file: <audio_sample.wav>
name: "João Silva"
description: "Voz masculina brasileira"
language: "pt-BR"
```

### Formato de Resposta

```json
{
  "id": "job_xyz789",
  "status": "queued|processing|completed|failed",
  "progress": 75.5,
  "mode": "dubbing_with_clone",
  "text": "Olá, este é um teste",
  "voice_id": "voice_abc123",
  "output_file": "./processed/job_xyz789.wav",
  "audio_url": "/jobs/job_xyz789/download",
  "duration": 3.5,
  "created_at": "2025-11-24T10:00:00Z",
  "completed_at": "2025-11-24T10:01:30Z"
}
```

---

## 🧱 COMPONENTES PRINCIPAIS

### 1. OpenVoice Client (`openvoice_client.py`)

**Responsabilidade:** Adapter para OpenVoice, esconde complexidade da lib.

```python
class OpenVoiceClient:
    """Cliente para OpenVoice - Dublagem e Clonagem de Voz"""
    
    async def generate_dubbing(
        self, 
        text: str, 
        language: str,
        voice_preset: str = None,
        voice_profile: VoiceProfile = None
    ) -> bytes:
        """Gera áudio dublado a partir de texto"""
        pass
    
    async def clone_voice(
        self, 
        audio_path: str,
        language: str
    ) -> VoiceProfile:
        """Clona voz a partir de amostra de áudio"""
        pass
    
    async def synthesize_with_voice(
        self,
        text: str,
        voice_profile: VoiceProfile
    ) -> bytes:
        """Sintetiza fala usando voz clonada"""
        pass
```

### 2. Voice Processor (`processor.py`)

**Responsabilidade:** Orquestra processamento de jobs e clonagem.

```python
class VoiceProcessor:
    """Processa jobs de dublagem e clonagem de voz"""
    
    async def process_dubbing_job(self, job: Job) -> Job:
        """Processa job de dublagem"""
        pass
    
    async def process_clone_job(self, job: Job) -> Job:
        """Processa job de clonagem de voz"""
        pass
```

### 3. Redis Store (`redis_store.py`)

**Responsabilidade:** Persistência de jobs e perfis de voz.

```python
class RedisJobStore:
    """Store Redis para jobs e perfis de voz"""
    
    def save_job(self, job: Job) -> None:
        """Salva job no Redis"""
        pass
    
    def save_voice_profile(self, profile: VoiceProfile) -> None:
        """Salva perfil de voz no Redis"""
        pass
    
    def list_voice_profiles(self) -> List[VoiceProfile]:
        """Lista todos os perfis de voz"""
        pass
```

### 4. Models (`models.py`)

**Modelos Pydantic:**

- `Job` - Job de dublagem/clonagem
- `VoiceProfile` - Perfil de voz clonada
- `DubbingRequest` - Request de dublagem
- `VoiceCloneRequest` - Request de clonagem
- `JobStatus` - Enum de status

---

## 🔧 OPENVOICE - INTEGRAÇÃO TÉCNICA

### Repositório de Referência
https://github.com/myshell-ai/OpenVoice.git

### Modos de Integração

**Opção 1: OpenVoice como Dependência Python (Escolhida)**
- Instalar OpenVoice via pip no container
- Chamar diretamente APIs Python
- Mais simples e direto

**Opção 2: OpenVoice como Serviço Separado**
- OpenVoice rodando em container separado
- Comunicação via HTTP/gRPC
- Mais escalável, mas mais complexo

### Workflow OpenVoice

#### Dublagem (Text-to-Speech)
```python
from openvoice import api as openvoice_api

# 1. Configurar modelo
model = openvoice_api.BaseSpeakerTTS(
    model_path="./checkpoints/base_speakers",
    device="cpu"  # ou "cuda"
)

# 2. Gerar áudio
audio = model.tts(
    text="Hello world",
    speaker="female_generic",
    language="en"
)

# 3. Salvar arquivo
audio.save("output.wav")
```

#### Clonagem de Voz
```python
from openvoice import api as openvoice_api

# 1. Carregar modelo de clonagem
tone_color_converter = openvoice_api.ToneColorConverter(
    model_path="./checkpoints/converter",
    device="cpu"
)

# 2. Extrair características da voz
voice_profile = tone_color_converter.extract_se(
    audio_path="sample_voice.wav",
    language="en"
)

# 3. Salvar perfil
voice_profile.save("voice_profile_xyz.pkl")

# 4. Usar voz clonada na síntese
audio = model.tts_with_voice(
    text="New text with cloned voice",
    voice_profile=voice_profile
)
```

---

## 🚀 FLUXO DE EXECUÇÃO

### Dublagem com Voz Genérica

```
Cliente → POST /jobs (mode=dubbing)
    ↓
FastAPI cria Job → Salva Redis
    ↓
Celery Worker recebe task
    ↓
OpenVoiceClient.generate_dubbing()
    ↓
Áudio gerado → Salva em ./processed
    ↓
Job status = completed
    ↓
Cliente → GET /jobs/{id}/download
```

### Clonagem de Voz + Dublagem

```
Cliente → POST /voices/clone (multipart)
    ↓
Salva amostra em ./uploads
    ↓
OpenVoiceClient.clone_voice()
    ↓
VoiceProfile criado → Salva Redis
    ↓
voice_id retornado ao cliente
    ↓
Cliente → POST /jobs (mode=dubbing_with_clone, voice_id)
    ↓
OpenVoiceClient.synthesize_with_voice()
    ↓
Áudio dublado com voz clonada
```

---

## 💾 ARMAZENAMENTO

### Redis Keys

```
voice_job:{job_id}              # Jobs de dublagem/clonagem
voice_profile:{voice_id}        # Perfis de voz clonados
voice_jobs_index                # Índice de jobs
voice_profiles_index            # Índice de perfis
```

### Sistema de Arquivos

```
./uploads/          # Amostras de áudio enviadas
./processed/        # Áudios dublados gerados
./temp/             # Arquivos temporários
./models/           # Modelos OpenVoice baixados
./voice_profiles/   # Perfis de voz serializados (.pkl)
./logs/             # Logs do serviço
```

---

## 🔒 SEGURANÇA E LIMITES

### Limites de Processamento

- **Tamanho máx. de arquivo:** 100MB (`.env` configurável)
- **Duração máx. de áudio:** 10 minutos
- **Tamanho máx. de texto:** 10.000 caracteres
- **Max concurrent jobs:** 3 (Celery)
- **Job timeout:** 15 minutos
- **Cache TTL:** 24 horas

### Validações

- Formato de áudio: `.wav`, `.mp3`, `.m4a`, `.ogg`
- Sample rate mínimo: 16kHz
- Idiomas suportados: verificação contra lista OpenVoice
- Texto não-vazio, sem caracteres inválidos

---

## 📊 MONITORAMENTO

### Health Check Profundo

```json
GET /health
{
  "status": "healthy",
  "service": "audio-voice",
  "version": "1.0.0",
  "checks": {
    "redis": {"status": "ok"},
    "disk_space": {"status": "ok", "free_gb": 50.2},
    "openvoice": {"status": "ok", "model_loaded": true},
    "celery_workers": {"status": "ok", "active": 2}
  }
}
```

### Estatísticas

```json
GET /admin/stats
{
  "jobs": {
    "total": 150,
    "queued": 2,
    "processing": 3,
    "completed": 140,
    "failed": 5
  },
  "voices": {
    "total_profiles": 12,
    "storage_mb": 45.3
  },
  "cache": {
    "files_count": 150,
    "total_size_mb": 1250.5
  }
}
```

---

## 🐳 DOCKER E DEPLOYMENT

### Dockerfile

- Base: `python:3.10-slim`
- FFmpeg para processamento de áudio
- PyTorch CPU (ou CUDA se GPU disponível)
- OpenVoice instalado via pip
- User não-root para segurança

### Docker Compose

```yaml
services:
  audio-voice:
    build: .
    ports:
      - "8004:8004"
    environment:
      - REDIS_URL=redis://redis:6379/4
    volumes:
      - ./uploads:/app/uploads
      - ./processed:/app/processed
      - ./voice_profiles:/app/voice_profiles
    depends_on:
      - redis
  
  audio-voice-worker:
    build: .
    command: celery -A app.celery_tasks worker --loglevel=info
    depends_on:
      - redis
```

---

## 🧪 TESTES

### Cobertura de Testes

1. **Unitários:**
   - Models (Job, VoiceProfile)
   - Config loading
   - OpenVoice client (mocked)

2. **Integração:**
   - Endpoints FastAPI
   - Redis store
   - Celery tasks

3. **E2E:**
   - Fluxo completo de dublagem
   - Fluxo completo de clonagem + uso

### Comandos de Teste

```bash
# Testes unitários
pytest tests/unit/

# Testes de integração
pytest tests/integration/

# Todos os testes
pytest
```

---

## 📚 DEPENDÊNCIAS PRINCIPAIS

```
fastapi==0.120.0
uvicorn[standard]==0.38.0
celery==5.3.4
redis==5.0.1
pydantic==2.12.3
openvoice==1.0.0
torch==2.1.2
torchaudio==2.1.2
pydub==0.25.1
soundfile==0.12.1
librosa==0.10.1
```

---

## 🔄 ROADMAP E MELHORIAS FUTURAS

### Versão 1.0 (MVP) ✅
- Dublagem com vozes genéricas
- Clonagem de voz básica
- Integração com orchestrator
- Cache Redis de 24h

### Versão 2.0 (Futuro)
- Suporte a GPU para processamento mais rápido
- Streaming de áudio em tempo real
- Vozes multi-idioma avançadas
- Fine-tuning de vozes clonadas
- API de qualidade de voz (scoring)
- Mixagem de múltiplas vozes

---

## 🐛 DEBUGGING E TROUBLESHOOTING

### Logs Importantes

```bash
# Logs do serviço
tail -f ./logs/audio-voice.log

# Logs Celery
tail -f ./logs/celery-worker.log

# Logs Docker
docker logs audio-voice-service
```

### Problemas Comuns

1. **OpenVoice não carrega modelo**
   - Verificar se modelos foram baixados em `./models/`
   - Verificar permissões de diretório
   - Verificar memória disponível (min 2GB RAM)

2. **Jobs ficam em "processing" eternamente**
   - Verificar se Celery worker está rodando
   - Verificar logs de erro no worker
   - Executar `/admin/cleanup` para limpar jobs órfãos

3. **Clonagem de voz falha**
   - Verificar qualidade da amostra de áudio (min 16kHz, 5s)
   - Verificar formato de áudio suportado
   - Verificar se idioma está correto

---

## 📝 NOTAS DE IMPLEMENTAÇÃO

### Decisões de Design

1. **Por que Redis para armazenar perfis de voz?**
   - Consistência com outros serviços
   - TTL automático (expira perfis não usados)
   - Rápido acesso para síntese

2. **Por que Celery para processamento assíncrono?**
   - Padrão dos outros serviços
   - Permite escalar workers horizontalmente
   - Timeout e retry nativos

3. **Por que OpenVoice em Python direto?**
   - Mais simples que serviço HTTP separado
   - Menos overhead de rede
   - Facilita debugging

### Padrões Seguidos

- ✅ Mesma estrutura de pastas dos outros serviços
- ✅ Endpoints compatíveis com orchestrator
- ✅ Redis como store compartilhado
- ✅ Celery para processamento assíncrono
- ✅ FastAPI como framework web
- ✅ Pydantic para validação
- ✅ Logging estruturado (JSON)
- ✅ Health check profundo
- ✅ Admin endpoints (/admin/cleanup, /admin/stats)
- ✅ Docker e Docker Compose

---

## 👥 CONTRIBUINDO

Para adicionar novas features:

1. Seguir padrão arquitetural existente
2. Adicionar testes (unitários + integração)
3. Atualizar README.md
4. Atualizar ARCHITECTURE.md (este arquivo)

---

## 📄 LICENÇA

Same as parent project: YTCaption-Easy-Youtube-API

---

**Status:** ✅ Arquitetura Aprovada e Pronta para Implementação  
**Próximo Passo:** Implementação dos componentes seguindo este blueprint
