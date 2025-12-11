# Audio Voice Service - XTTS v2 Only (Standalone)

## ✅ Limpeza Completa Realizada

### 🗑️ Removido do Projeto

**Engines Removidos:**
- ❌ F5-TTS (engines e configs)
- ❌ F5-TTS PT-BR engine

**Features Removidas:**
- ❌ RVC Voice Conversion (todos arquivos)
- ❌ FastAPI (main.py deletado)
- ❌ Celery (processamento direto)
- ❌ WebUI Bootstrap 5 (index.html e assets)
- ❌ Redis (armazenamento local)
- ❌ Pasta /train (scripts F5-TTS)

**Arquivos Deletados:**
```
app/engines/f5tts_engine.py
app/engines/f5tts_ptbr_engine.py
app/rvc_client.py
app/rvc_dependencies.py
app/rvc_model_manager.py
app/main.py
app/webui/index.html
app/webui/README.md
app/webui/gradio_ui.py
app/webui/assets/
test_gradio.py
train/
```

### ✅ Sistema Atual

**Engine Único:**
- ✅ **XTTS v2** (Coqui TTS) - Multilingual (16 idiomas)

**Arquitetura Simplificada:**
```
app_standalone.py (700 linhas)
├── Gradio UI (4 tabs)
├── VoiceProcessor (XTTS only)
├── Storage local (./storage/)
└── Sem dependências externas (Redis/Celery)
```

## 🚀 Como Usar

### Instalação

```bash
# Instalar dependências
pip install gradio pydub

# Executar
python app_standalone.py
```

### Acesso
**http://localhost:7860**

### Interface

**🎤 Tab 1: Geração TTS**
- Digite texto para converter
- Escolha modo: Preset (female/male) ou Voz Clonada
- Selecione idiomas (16 disponíveis)
- Gera áudio XTTS instantaneamente

**🎙️ Tab 2: Clonagem de Voz**
- Upload áudio 5-300s
- Nome e descrição da voz
- Gera Voice ID para reutilização

**📋 Tab 3: Jobs**
- Histórico de gerações
- Download por Job ID
- Status e duração

**ℹ️ Tab 4: Sobre**
- Informações do sistema
- Documentação

## 💾 Armazenamento

Todos os dados são salvos localmente:

```
storage/
├── jobs/          # JSON dos jobs
│   └── {job_id}.json
└── voices/        # JSON + áudios clonados
    ├── {voice_id}.json
    └── {voice_id}.wav

processed/         # Áudios gerados
└── {job_id}_output.wav
```

## 🎯 Funcionalidades

### TTS Generation
- ✅ XTTS v2 multilingual
- ✅ 16 idiomas suportados
- ✅ Voice presets (female/male)
- ✅ Vozes clonadas customizadas
- ✅ Processamento assíncrono

### Voice Cloning
- ✅ Clone com 5-300s de áudio
- ✅ Zero-shot learning
- ✅ Armazenamento persistente
- ✅ Reutilização via Voice ID

### Jobs Management
- ✅ Histórico completo
- ✅ Status tracking
- ✅ Download de áudios
- ✅ Metadata (duração, texto, etc)

## 📝 Idiomas Suportados

XTTS v2 suporta 16 idiomas:
- Português (Brasil/Portugal)
- English
- Español
- Français
- Deutsch
- Italiano
- Polski
- Türkçe
- Русский
- Nederlands
- Čeština
- العربية (Árabe)
- 中文 (Chinês)
- 日本語 (Japonês)
- 한국어 (Coreano)
- Magyar (Húngaro)

## ⚙️ Configuração

Edite `app/config.py` para ajustar:

```python
# XTTS Device
XTTS_DEVICE = "cuda"  # ou "cpu"

# VRAM Management
LOW_VRAM = True  # Descarrega modelo após uso

# Output Directory
OUTPUT_DIR = "./processed"
```

## 🔧 Desenvolvimento

### Estrutura do Código

```
app_standalone.py        # Aplicação principal (700 linhas)
├── Storage Functions    # save_job, get_job, list_jobs
├── TTS Generation       # generate_tts_async + sync wrapper
├── Voice Cloning        # clone_voice_async
├── Jobs Management      # list_jobs_html, get_job_audio
└── Gradio UI            # create_app() com 4 tabs

app/
├── processor.py         # VoiceProcessor (orquestrador)
├── engines/
│   ├── base.py         # TTSEngine interface
│   ├── xtts_engine.py  # XTTS implementation
│   └── factory.py      # Engine factory
├── models.py           # Pydantic models
├── config.py           # Settings
└── logging_config.py   # Logging setup
```

### Adicionar Novos Recursos

Para adicionar features:
1. Modifique `app_standalone.py`
2. Adicione tab no Gradio UI
3. Implemente função sync + async
4. Conecte ao VoiceProcessor

## 🐛 Troubleshooting

### Interface não carrega
- Verifique se porta 7860 está livre
- Restart: `Ctrl+C` e execute novamente

### Erro ao gerar TTS
- Verifique se modelo XTTS está em `models/`
- Baixe com: `python scripts/download_models.py`
- Check GPU: `nvidia-smi` (se usando CUDA)

### Vozes clonadas não aparecem
- Verifique `./storage/voices/`
- Clique em "🔄 Atualizar Lista"

## 📚 Referências

- **XTTS v2**: https://github.com/coqui-ai/TTS
- **Gradio**: https://gradio.app
- **Documentação**: [README.md](README.md)

---

**Versão:** 2.0.0 Standalone  
**Engine:** XTTS v2 Only  
**Status:** ✅ Pronto para uso
