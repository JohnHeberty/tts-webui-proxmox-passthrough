# API Reference - Audio Voice Service

Documentação completa dos 42 endpoints REST do Audio Voice Service.

**Base URL:** `http://localhost:8005`  
**OpenAPI/Swagger:** http://localhost:8005/docs  
**ReDoc:** http://localhost:8005/redoc

---

## 📋 Índice

1. [Jobs (TTS)](#jobs-tts) - 7 endpoints
2. [Voice Cloning](#voice-cloning) - 4 endpoints
3. [RVC Models](#rvc-models) - 5 endpoints
4. [Quality Profiles](#quality-profiles) - 9 endpoints
5. [System](#system) - 5 endpoints
6. [WebUI](#webui) - 1 endpoint

---

## 🎙️ Jobs (TTS)

### POST /jobs

Cria novo job de Text-to-Speech.

**Request Body:**

```json
{
  "text": "string (required, max 10000 chars)",
  "engine": "xtts (only engine available in v2.0)",
  "mode": "preset | voice (required)",
  "preset": "female_generic | male_generic | ... (se mode=preset)",
  "voice_id": "string (se mode=voice)",
  "source_language": "pt | pt-BR | en | ... (optional)",
  "quality_profile": "balanced | expressive | stable | ... (optional)",
  "enable_rvc": false,
  "rvc_model_id": "string (se enable_rvc=true)",
  "rvc_pitch": 0,
  "rvc_index_rate": 0.75,
  "rvc_protect": 0.33,
  "rvc_f0_method": "rmvpe | fcpe | pm | harvest | dio | crepe"
}
```

**Voice Presets disponíveis:**
- `female_generic`
- `male_generic`
- `female_young`
- `male_deep`
- `female_warm`
- `male_warm`
- `female_soft`
- `male_soft`

**Response (202 Accepted):**

```json
{
  "id": "job_abc123",
  "status": "queued | processing | completed | failed",
  "progress": 0.0,
  "text": "...",
  "engine": "xtts",
  "tts_engine_used": "xtts",
  "mode": "preset",
  "preset": "female_generic",
  "output_file": null,
  "audio_url": null,
  "duration": null,
  "error_message": null,
  "created_at": "2025-12-01T10:00:00Z",
  "started_at": null,
  "completed_at": null
}
```

**Exemplo (PowerShell):**

```powershell
$body = @{
    text = "Olá, este é um teste."
    engine = "xtts"
    mode = "preset"
    preset = "female_generic"
    source_language = "pt-BR"
} | ConvertTo-Json

Invoke-RestMethod -Method Post -Uri "http://localhost:8005/jobs" `
    -Body $body -ContentType "application/json"
```

---

### GET /jobs

Lista jobs com paginação e filtros.

**Query Parameters:**

- `page` (int, default: 1)
- `page_size` (int, default: 20, max: 100)
- `status` (string): `queued`, `processing`, `completed`, `failed`
- `mode` (string): `preset`, `voice`

**Response:**

```json
{
  "jobs": [
    {
      "id": "job_abc123",
      "status": "completed",
      "text": "...",
      "duration": 3.5,
      "created_at": "2025-12-01T10:00:00Z"
    }
  ],
  "total": 100,
  "page": 1,
  "page_size": 20,
  "total_pages": 5
}
```

**Exemplo:**

```powershell
# Listar apenas jobs completados, página 2
curl "http://localhost:8005/jobs?status=completed&page=2&page_size=10"
```

---

### GET /jobs/{job_id}

Busca job específico por ID.

**Response:**

```json
{
  "id": "job_abc123",
  "status": "completed",
  "progress": 100.0,
  "text": "Olá, este é um teste.",
  "output_file": "./processed/job_abc123.wav",
  "audio_url": "/jobs/job_abc123/download",
  "duration": 3.5,
  "created_at": "2025-12-01T10:00:00Z",
  "completed_at": "2025-12-01T10:00:15Z"
}
```

**Errors:**
- `404`: Job não encontrado

---

### GET /jobs/{job_id}/formats

Lista formatos de áudio disponíveis para download.

**Response:**

```json
{
  "job_id": "job_abc123",
  "available_formats": [
    {
      "format": "wav",
      "mime_type": "audio/wav",
      "download_url": "/jobs/job_abc123/download?format=wav"
    },
    {
      "format": "mp3",
      "mime_type": "audio/mpeg",
      "download_url": "/jobs/job_abc123/download?format=mp3"
    },
    {
      "format": "ogg",
      "mime_type": "audio/ogg",
      "download_url": "/jobs/job_abc123/download?format=ogg"
    },
    {
      "format": "flac",
      "mime_type": "audio/flac",
      "download_url": "/jobs/job_abc123/download?format=flac"
    },
    {
      "format": "m4a",
      "mime_type": "audio/mp4",
      "download_url": "/jobs/job_abc123/download?format=m4a"
    }
  ]
}
```

---

### GET /jobs/{job_id}/download

Faz download do áudio gerado.

**Query Parameters:**

- `format` (string, default: `wav`): `wav`, `mp3`, `ogg`, `flac`, `m4a`, `opus`

**Response:**

- **Content-Type:** `audio/wav`, `audio/mpeg`, etc.
- **Content-Disposition:** `attachment; filename="job_abc123.wav"`

**Exemplo:**

```powershell
# Download WAV
curl "http://localhost:8005/jobs/job_abc123/download?format=wav" -o output.wav

# Download MP3
curl "http://localhost:8005/jobs/job_abc123/download?format=mp3" -o output.mp3
```

**Errors:**
- `404`: Job não encontrado ou sem output
- `400`: Formato não suportado
- `500`: Erro na conversão de formato

---

### DELETE /jobs/{job_id}

Deleta job e arquivos associados.

**Response (204 No Content):**

```json
{
  "message": "Job deletado com sucesso"
}
```

**Errors:**
- `404`: Job não encontrado

---

### GET /admin/stats

Retorna estatísticas do sistema.

**Response:**

```json
{
  "total_jobs": 150,
  "queued_jobs": 2,
  "processing_jobs": 1,
  "completed_jobs": 140,
  "failed_jobs": 7,
  "total_voices": 15,
  "total_rvc_models": 3,
  "total_quality_profiles": 8,
  "uptime_seconds": 86400,
  "cache_size_mb": 1024
}
```

---

## 🎤 Voice Cloning

### POST /voices/clone

Clona voz a partir de áudio de referência.

**Request (multipart/form-data):**

- `file` (file, required): WAV, MP3 ou OGG (5s - 300s)
- `name` (string, required): Nome da voz
- `language` (string, required): `pt-BR`, `en`, etc.
- `description` (string, optional): Descrição
- `ref_text` (string, optional): **DEPRECATED** - Was used for F5-TTS (removed in v2.0)

**Response (202 Accepted):**

```json
{
  "job_id": "clone_job_xyz789",
  "status": "queued",
  "message": "Clonagem de voz iniciada"
}
```

**Exemplo (PowerShell):**

```powershell
$form = @{
    file = Get-Item "C:\path\to\audio.wav"
    name = "João Silva"
    language = "pt-BR"
    description = "Voz masculina brasileira"
}

Invoke-RestMethod -Method Post -Uri "http://localhost:8005/voices/clone" -Form $form
```

**Errors:**
- `400`: Arquivo inválido (tamanho, formato, duração)
- `413`: Arquivo muito grande (> MAX_FILE_SIZE_MB)

---

### GET /voices

Lista vozes clonadas.

**Query Parameters:**

- `page` (int, default: 1)
- `page_size` (int, default: 20)
- `language` (string): Filtrar por idioma

**Response:**

```json
{
  "voices": [
    {
      "id": "voice_abc123",
      "name": "João Silva",
      "language": "pt-BR",
      "duration": 15.5,
      "created_at": "2025-12-01T10:00:00Z",
      "usage_count": 42
    }
  ],
  "total": 15,
  "page": 1,
  "page_size": 20
}
```

---

### GET /voices/{voice_id}

Retorna detalhes de voz específica.

**Response:**

```json
{
  "id": "voice_abc123",
  "name": "João Silva",
  "description": "Voz masculina brasileira",
  "language": "pt-BR",
  "source_audio_path": "./voice_profiles/voice_abc123_source.wav",
  "profile_path": "./voice_profiles/voice_abc123.wav",
  "duration": 15.5,
  "sample_rate": 24000,
  "quality_score": 0.95,
  "created_at": "2025-12-01T10:00:00Z",
  "usage_count": 42
}
```

**Errors:**
- `404`: Voz não encontrada

---

### DELETE /voices/{voice_id}

Deleta voz clonada.

**Response (204 No Content):**

```json
{
  "message": "Voz deletada com sucesso"
}
```

---

## 🎭 RVC Models

### POST /rvc-models

Faz upload de modelo RVC.

**Request (multipart/form-data):**

- `pth_file` (file, required): Arquivo `.pth` (modelo RVC)
- `index_file` (file, optional): Arquivo `.index` (índice FAISS)
- `name` (string, required): Nome do modelo
- `description` (string, optional)
- `target_sr` (int, default: 40000): Sample rate alvo
- `f0_method` (string, default: `rmvpe`): Método F0

**Response (201 Created):**

```json
{
  "id": "rvc_model_xyz789",
  "name": "Modelo RVC PT-BR",
  "pth_path": "./models/rvc/rvc_model_xyz789.pth",
  "index_path": "./models/rvc/rvc_model_xyz789.index",
  "created_at": "2025-12-01T10:00:00Z"
}
```

---

### GET /rvc-models

Lista modelos RVC.

**Response:**

```json
{
  "models": [
    {
      "id": "rvc_model_xyz789",
      "name": "Modelo RVC PT-BR",
      "target_sr": 40000,
      "f0_method": "rmvpe",
      "usage_count": 10,
      "created_at": "2025-12-01T10:00:00Z"
    }
  ],
  "total": 3
}
```

---

### GET /rvc-models/{model_id}

Retorna detalhes de modelo RVC.

---

### GET /rvc-models/stats

Estatísticas de uso de modelos RVC.

**Response:**

```json
{
  "total_models": 3,
  "total_usage": 127,
  "most_used_model": {
    "id": "rvc_model_xyz789",
    "name": "Modelo RVC PT-BR",
    "usage_count": 100
  }
}
```

---

### DELETE /rvc-models/{model_id}

Deleta modelo RVC.

---

## 🎛️ Quality Profiles

Sistema completo de gerenciamento de perfis de qualidade por engine.

### GET /quality-profiles

Lista perfis de qualidade.

**Query Parameters:**

- `engine` (string): `xtts`, `f5tts`

**Response:**

```json
{
  "profiles": [
    {
      "id": "xtts_balanced",
      "name": "Balanced",
      "engine": "xtts",
      "is_default": true,
      "description": "Equilíbrio entre qualidade e velocidade"
    },
    {
      "id": "f5tts_high_quality",
      "name": "High Quality",
      "engine": "f5tts",
      "is_default": false,
      "description": "Máxima qualidade (NFE=64)"
    }
  ],
  "total": 8
}
```

---

### POST /quality-profiles

Cria novo perfil de qualidade.

**Request Body (XTTS):**

```json
{
  "name": "My Custom Profile",
  "description": "Perfil customizado",
  "engine": "xtts",
  "temperature": 0.75,
  "repetition_penalty": 1.5,
  "top_p": 0.9,
  "top_k": 60,
  "speed": 1.0
}
```

**Request Body (F5-TTS):**

```json
{
  "name": "Ultra Quality PT-BR",
  "engine": "f5tts",
  "nfe_step": 64,
  "cfg_strength": 2.5,
  "speed": 0.8,
  "denoise_strength": 0.9
}
```

---

### GET /quality-profiles/{profile_id}

Retorna perfil específico.

---

### PUT /quality-profiles/{profile_id}

Atualiza perfil existente.

---

### DELETE /quality-profiles/{profile_id}

Deleta perfil.

**Errors:**
- `400`: Não é possível deletar perfil padrão

---

### POST /quality-profiles/{profile_id}/set-default

Define perfil como padrão do engine.

---

### POST /quality-profiles/{profile_id}/duplicate

Duplica perfil existente.

**Request:**

```json
{
  "new_name": "Copy of Balanced"
}
```

---

### GET /quality-profiles/defaults

Retorna perfis padrão por engine.

**Response:**

```json
{
  "xtts": {
    "id": "xtts_balanced",
    "name": "Balanced"
  },
  "f5tts": {
    "id": "f5tts_balanced",
    "name": "Balanced"
  }
}
```

---

## 🔧 System

### GET /

Página inicial (redireciona para /webui ou retorna info básica).

---

### GET /health

Health check completo.

**Response:**

```json
{
  "status": "healthy",
  "service": "Audio Voice Service",
  "version": "2.0.1",
  "timestamp": "2025-12-01T10:00:00Z",
  "redis": "connected",
  "celery": "running",
  "gpu": {
    "available": true,
    "device": "NVIDIA RTX 3090",
    "memory_total": 24576,
    "memory_used": 8192,
    "memory_free": 16384
  }
}
```

---

### GET /presets

Lista voice presets disponíveis.

**Response:**

```json
{
  "presets": [
    "female_generic",
    "male_generic",
    "female_young",
    "male_deep",
    "female_warm",
    "male_warm",
    "female_soft",
    "male_soft"
  ]
}
```

---

### GET /languages

Lista idiomas suportados.

**Response:**

```json
{
  "languages": {
    "xtts": ["en", "es", "fr", "de", "it", "pt", "pl", "tr", "ru", "nl", "cs", "ar", "zh-cn", "ja", "hu", "ko"],
    "f5tts": ["pt", "pt-BR", "en"]
  }
}
```

---

### POST /admin/cleanup

Limpeza de cache e arquivos antigos.

**Request:**

```json
{
  "mode": "basic | deep",
  "max_age_hours": 24
}
```

**Response:**

```json
{
  "deleted_jobs": 10,
  "deleted_files": 25,
  "freed_space_mb": 512
}
```

---

## 🌐 WebUI

### GET /webui/*

Serve interface web estática (Bootstrap 5 SPA).

**URL:** http://localhost:8005/webui

**Features:**
- 4 abas: Jobs, Voices, Quality Profiles, About (v2.0: F5-TTS and RVC removed)
- Formulários validados
- Toast notifications
- Progress tracking em tempo real
- Download multi-formato

---

## 📊 Códigos de Status HTTP

| Código | Significado |
|--------|-------------|
| 200 | OK - Requisição bem-sucedida |
| 201 | Created - Recurso criado |
| 202 | Accepted - Job aceito (processamento assíncrono) |
| 204 | No Content - Deletado com sucesso |
| 400 | Bad Request - Parâmetros inválidos |
| 404 | Not Found - Recurso não encontrado |
| 413 | Payload Too Large - Arquivo muito grande |
| 422 | Unprocessable Entity - Validação falhou |
| 500 | Internal Server Error - Erro no servidor |

---

## 🔐 Autenticação

Atualmente o serviço **não possui autenticação**.

Para ambientes de produção, recomenda-se:
- Configurar reverse proxy (nginx) com autenticação básica
- Usar API Gateway com OAuth2/JWT
- Restringir acesso por firewall/rede

---

## 📝 Exemplos de Uso

### Workflow Completo: Clonar Voz + Gerar TTS + RVC

```powershell
# 1. Clonar voz
$cloneForm = @{
    file = Get-Item "reference.wav"
    name = "Minha Voz"
    language = "pt-BR"
}
$voice = Invoke-RestMethod -Method Post -Uri "http://localhost:8005/voices/clone" -Form $cloneForm

# 2. Aguardar conclusão (poll status)
Start-Sleep -Seconds 10

# 3. Listar vozes para pegar ID
$voices = Invoke-RestMethod "http://localhost:8005/voices"
$voiceId = $voices.voices[0].id

# 4. Criar job TTS com voz clonada + RVC
$jobBody = @{
    text = "Olá, testando minha voz clonada com RVC."
    engine = "xtts"
    mode = "voice"
    voice_id = $voiceId
    enable_rvc = $true
    rvc_model_id = "rvc_model_xyz789"
    rvc_pitch = 0
} | ConvertTo-Json

$job = Invoke-RestMethod -Method Post -Uri "http://localhost:8005/jobs" -Body $jobBody -ContentType "application/json"

# 5. Aguardar processamento
Start-Sleep -Seconds 15

# 6. Download MP3
curl "http://localhost:8005/jobs/$($job.id)/download?format=mp3" -o final_output.mp3
```

---

## 📚 Documentação Adicional

- **[Getting Started](./getting-started.md)** - Setup inicial
- **[ARCHITECTURE.md](./ARCHITECTURE.md)** - Arquitetura do sistema
- **[QUALITY_PROFILES.md](./QUALITY_PROFILES.md)** - Guia de perfis de qualidade
- **Swagger UI:** http://localhost:8005/docs (documentação interativa)
