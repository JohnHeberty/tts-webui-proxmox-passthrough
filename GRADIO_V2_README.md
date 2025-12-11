# Audio Voice Service - Versão 2.0 (Pure Gradio)

## 🎯 Mudanças Importantes

Esta versão foi **completamente reestruturada** para ser mais simples e direta:

### ❌ Removido
- **RVC (Voice Conversion)** - Removido completamente para simplificar
- **FastAPI** - Substituído por Gradio puro
- **Celery** - Processamento direto, sem filas assíncronas
- **WebUI Bootstrap 5** - Interface antiga removida

### ✅ Mantido
- **XTTS v2** - Engine TTS multilingual
- **F5-TTS** - Engine otimizado PT-BR
- **Voice Cloning** - Clone de vozes com 5-300s de áudio
- **Quality Profiles** - Perfis de qualidade configuráveis
- **Redis** - Armazenamento de jobs e vozes
- **VoiceProcessor** - Orquestrador TTS

## 🚀 Como Usar

### Instalação

```bash
# Instalar dependências
pip install -r requirements.txt

# Iniciar Redis (necessário)
docker run -d -p 6379:6379 redis:latest

# Ou use Redis local
```

### Executar

```bash
python app_gradio.py
```

Acesse: **http://localhost:7860**

## 📱 Interface Gradio

A interface tem 4 tabs principais:

### 1. 🎤 Geração TTS
- Digite texto para converter em áudio
- Escolha engine (XTTS ou F5-TTS)
- Selecione modo: Voz Genérica (preset) ou Voz Clonada
- Configure idioma e perfil de qualidade
- Gera áudio instantaneamente

### 2. 🎙️ Clonagem de Voz
- Upload de áudio (5-300 segundos)
- Nome e descrição da voz
- Escolha idioma e engine
- Voice ID gerado para reutilização
- Lista de vozes clonadas

### 3. 📋 Jobs
- Lista todos os jobs TTS gerados
- Busca por Job ID
- Download de áudios por job
- Histórico completo

### 4. ℹ️ Sobre
- Informações do sistema
- Versão e features
- Documentação

## 🏗️ Arquitetura Simplificada

```
┌─────────────────┐
│   Gradio UI     │ ← Interface web única (porta 7860)
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  app_gradio.py  │ ← Aplicação principal (sync wrappers)
└────────┬────────┘
         │
         ├─────────► VoiceProcessor (app/processor.py)
         │                   │
         │                   ├─► XTTS Engine
         │                   └─► F5-TTS Engine
         │
         └─────────► RedisJobStore (app/redis_store.py)
                             │
                             └─► Redis (porta 6379)
```

## 📦 Arquivos Principais

- **app_gradio.py** - Aplicação Gradio standalone (670 linhas)
- **app/processor.py** - Orquestrador TTS
- **app/engines/** - Engines XTTS e F5-TTS
- **app/redis_store.py** - Persistência Redis
- **app/quality_profile_manager.py** - Gerenciamento de perfis

## 🔧 Configuração

Edite `app/config.py` ou use variáveis de ambiente:

```bash
# Redis
REDIS_URL=redis://localhost:6379/4

# Engine padrão
TTS_ENGINE_DEFAULT=xtts  # ou f5tts

# VRAM
LOW_VRAM=true  # Descarrega modelos após uso

# Devices
XTTS_DEVICE=cuda  # ou cpu
F5TTS_DEVICE=cuda
```

## 🎯 Diferenças da Versão Anterior

| Feature | v1.0 (FastAPI) | v2.0 (Gradio) |
|---------|----------------|---------------|
| Interface | Bootstrap 5 SPA | Gradio nativo |
| API REST | 42 endpoints | Nenhum |
| RVC | ✅ Incluído | ❌ Removido |
| Celery | ✅ Filas async | ❌ Processamento direto |
| Complexidade | Alta | Baixa |
| Setup | Docker + Redis + Celery | Redis apenas |

## 🐛 Troubleshooting

### Redis não conecta
```bash
# Iniciar Redis Docker
docker run -d -p 6379:6379 redis:latest

# Verificar se está rodando
docker ps | grep redis
```

### Gradio não carrega dados
- Verifique se Redis está rodando
- Verifique logs em `logs/info.log`
- Recarregue a página (F5)

### Engine não encontrado
- Verifique se modelos estão em `models/`
- Execute: `python scripts/download_models.py`

## 📚 Próximos Passos

Se você precisa de funcionalidades removidas:

- **API REST**: Use versão v1.0 com FastAPI
- **RVC**: Instale `tts-with-rvc` separadamente
- **Celery**: Adicione worker separado

## 🎓 Documentação Completa

- [README.md](README.md) - Overview geral
- [docs/getting-started.md](docs/getting-started.md) - Setup detalhado
- [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) - Arquitetura v1.0
- [GRADIO_MIGRATION.md](GRADIO_MIGRATION.md) - Histórico da migração

---

**Versão:** 2.0.0  
**Data:** Dezembro 2025  
**Licença:** MIT
