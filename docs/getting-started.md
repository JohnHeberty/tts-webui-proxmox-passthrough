# Getting Started - Audio Voice Service

Guia rápido para configurar e executar o Audio Voice Service localmente.

---

## 📋 Pré-requisitos

### Hardware Mínimo

**Desenvolvimento (CPU mode):**
- CPU: 4 cores
- RAM: 8GB
- Disco: 20GB livres

**Produção (GPU recomendado):**
- CPU: 8+ cores
- RAM: 16GB+
- Disco: 50GB+ SSD
- GPU: NVIDIA RTX 3060+ (6GB+ VRAM)
- CUDA: 11.8+

### Software Necessário

- **Docker:** 24.0+ 
- **Docker Compose:** 2.20+
- **Git:** Para clonar o repositório
- **NVIDIA Container Toolkit:** Se usar GPU ([guia de instalação](https://docs.nvidia.com/datacenter/cloud-native/container-toolkit/install-guide.html))

**Verificar instalação:**

```powershell
# Docker
docker --version
docker compose version

# GPU (se aplicável)
nvidia-smi
```

---

## 🚀 Instalação Rápida

### Passo 1: Clonar Repositório

```powershell
git clone https://github.com/JohnHeberty/tts-webui-proxmox-passthrough.git
cd tts-webui-proxmox-passthrough
```

### Passo 2: Configurar Variáveis de Ambiente

Crie arquivo `.env` na raiz do projeto:

```powershell
# Copiar exemplo (se existir)
# cp .env.example .env

# Ou criar manualmente
@"
# ===== APLICAÇÃO =====
APP_NAME=Audio Voice Service
PORT=8005
HOST=0.0.0.0
DEBUG=false
ENVIRONMENT=production

# ===== REDIS =====
REDIS_URL=redis://localhost:6379/0

# ===== TTS ENGINES =====
TTS_ENGINE_DEFAULT=xtts

# XTTS Configuration
XTTS_ENABLED=true
XTTS_DEVICE=cuda
XTTS_FALLBACK_CPU=true
XTTS_MODEL=tts_models/multilingual/multi-dataset/xtts_v2

# F5-TTS Configuration
F5TTS_ENABLED=true
F5TTS_DEVICE=cuda
F5TTS_FALLBACK_CPU=true
F5TTS_MODEL=firstpixel/F5-TTS-pt-br

# ===== LOW VRAM MODE =====
# Ativa carregamento/descarregamento automático de modelos
LOW_VRAM=false

# ===== LIMITS =====
MAX_FILE_SIZE_MB=100
MAX_TEXT_LENGTH=10000
MAX_CONCURRENT_JOBS=3
JOB_TIMEOUT_MINUTES=15
"@ | Out-File -FilePath .env -Encoding utf8
```

**Configurações importantes:**

- `XTTS_DEVICE=cuda` / `F5TTS_DEVICE=cuda`: Use GPU (mude para `cpu` se não tiver GPU)
- `LOW_VRAM=true`: Ative se tiver menos de 8GB VRAM
- `TTS_ENGINE_DEFAULT=xtts`: Engine padrão (pode ser `f5tts`)

### Passo 3: Iniciar Serviços

```powershell
# Build e iniciar containers
docker compose up -d

# Verificar status
docker compose ps

# Acompanhar logs
docker compose logs -f
```

**Containers criados:**
- `audio-voice-api`: FastAPI server (porta 8005)
- `audio-voice-celery`: Celery worker (processamento assíncrono)

### Passo 4: Verificar Saúde

```powershell
# Health check da API
curl http://localhost:8005/health

# Ou abrir no navegador:
# http://localhost:8005/
```

**Resposta esperada:**
```json
{
  "status": "healthy",
  "service": "Audio Voice Service",
  "version": "2.0.1",
  "timestamp": "2025-12-01T10:00:00Z"
}
```

---

## 🎯 Primeiro Uso

### Acessar a WebUI

Abra no navegador: **http://localhost:8005/webui**

A interface permite:
- ✅ Criar jobs de TTS
- ✅ Gerenciar vozes clonadas
- ✅ Configurar Quality Profiles
- ✅ Upload de modelos RVC
- ✅ Monitorar jobs em tempo real

### Teste via API (cURL)

**Criar job de dublagem simples:**

```powershell
# PowerShell
$body = @{
    text = "Olá, este é um teste de voz."
    engine = "xtts"
    source_language = "pt"
    mode = "preset"
    preset = "female_generic"
} | ConvertTo-Json

Invoke-RestMethod -Method Post -Uri "http://localhost:8005/jobs" -Body $body -ContentType "application/json"
```

**Resposta:**
```json
{
  "id": "job_abc123",
  "status": "queued",
  "text": "Olá, este é um teste de voz.",
  "engine": "xtts",
  "created_at": "2025-12-01T10:00:00Z"
}
```

**Verificar status do job:**

```powershell
curl http://localhost:8005/jobs/job_abc123
```

**Download do áudio (quando completed):**

```powershell
# Download WAV
curl http://localhost:8005/jobs/job_abc123/download?format=wav -o output.wav

# Download MP3
curl http://localhost:8005/jobs/job_abc123/download?format=mp3 -o output.mp3
```

### Teste de Clonagem de Voz

**1. Preparar áudio de referência** (WAV, MP3 ou OGG com 5-300s de duração)

**2. Upload via API:**

```powershell
# PowerShell (multipart/form-data)
$filePath = "C:\caminho\para\voz_referencia.wav"

$form = @{
    file = Get-Item -Path $filePath
    name = "Minha Voz Clonada"
    description = "Voz criada a partir da referência"
    language = "pt-BR"
}

Invoke-RestMethod -Method Post -Uri "http://localhost:8005/voices/clone" -Form $form
```

**3. Usar voz clonada em job:**

```powershell
$body = @{
    text = "Testando com minha voz clonada."
    engine = "xtts"
    mode = "voice"
    voice_id = "voice_xyz789"
} | ConvertTo-Json

Invoke-RestMethod -Method Post -Uri "http://localhost:8005/jobs" -Body $body -ContentType "application/json"
```

---

## 🛠️ Comandos Úteis (Makefile)

O projeto inclui um `Makefile` com atalhos:

```powershell
# Ver todos os comandos disponíveis
make help

# Rebuild completo (limpa cache)
make rebuild

# Rebuild rápido (com cache)
make rebuild-fast

# Ver logs
make logs              # Todos os containers
make logs-api          # Apenas API
make logs-celery       # Apenas Celery worker

# Gerenciar containers
make up                # Iniciar
make down              # Parar
make restart           # Reiniciar

# Monitoramento
make status            # Status dos containers
make health            # Health checks
make vram-stats        # Estatísticas de VRAM (se GPU)

# Debug
make shell-api         # Shell no container da API
make shell-celery      # Shell no worker
make env-check         # Verificar variáveis de ambiente
```

---

## 📚 Próximos Passos

- 📖 **[ARCHITECTURE.md](./ARCHITECTURE.md)** - Entenda a arquitetura do sistema
- 🎛️ **[QUALITY_PROFILES.md](./QUALITY_PROFILES.md)** - Configurar perfis de qualidade
- ⚙️ **[LOW_VRAM.md](./LOW_VRAM.md)** - Otimizações para GPU com pouca VRAM
- 🚀 **[DEPLOYMENT.md](./DEPLOYMENT.md)** - Deploy em produção
- 📡 **API Docs:** http://localhost:8005/docs (Swagger UI)

---

## 🆘 Troubleshooting

### Erro: "CUDA not available"

**Solução 1:** Fallback para CPU (temporário)
```env
XTTS_DEVICE=cpu
F5TTS_DEVICE=cpu
```

**Solução 2:** Verificar NVIDIA Container Toolkit
```powershell
docker run --rm --gpus all nvidia/cuda:11.8.0-base-ubuntu22.04 nvidia-smi
```

### Erro: "Out of memory" (VRAM)

Ative LOW_VRAM mode:
```env
LOW_VRAM=true
```

Veja mais detalhes em [LOW_VRAM.md](./LOW_VRAM.md).

### Containers não iniciam

```powershell
# Ver logs detalhados
docker compose logs

# Rebuild do zero
make cleanup
make rebuild
```

### Porta 8005 já em uso

Altere no `.env`:
```env
PORT=8006
```

E atualize `docker-compose.yml`:
```yaml
ports:
  - "${PORT:-8006}:8006"
```

---

## 💡 Dicas de Desenvolvimento

### Modo Debug

Para desenvolvimento com reload automático:

```env
DEBUG=true
```

### Acessar logs em tempo real

```powershell
# Filtrar por tipo
docker compose logs -f | Select-String "ERROR"
docker compose logs -f | Select-String "VRAM"
```

### Executar testes

```powershell
# Dentro do container
docker exec -it audio-voice-api pytest tests/

# Ou localmente (se tiver venv)
pytest tests/
```

---

## 📞 Suporte

- **Issues:** https://github.com/JohnHeberty/tts-webui-proxmox-passthrough/issues
- **Discussions:** https://github.com/JohnHeberty/tts-webui-proxmox-passthrough/discussions
- **Documentação completa:** `/docs` folder
