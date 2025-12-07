# MORE – Análise Profunda: Problemas e Oportunidades

## 0. Visão Geral

**API Principal:** FastAPI rodando em `/app/main.py`
- XTTS-v2 (inferência + clonagem)
- RVC (voice conversion) **← REMOVER**
- Sistema de jobs assíncrono (Redis + Celery)
- WebUI em `/app/webui`

**Tecnologias TTS:**
- ✅ XTTS-v2: principal engine (lazy load)
- ❌ F5-TTS: removido
- ❌ RVC: **DEVE SER REMOVIDO**

**Pastas Principais:**
- `/app`: API FastAPI + engines + serviços
- `/train`: mini-projeto de treinamento XTTS
- `/models`: checkpoints (xtts, rvc, whisper)
- `/scripts`: validação, deployment, setup

---

## 1. RVC – Inventário Completo

### 1.1 Artefatos Encontrados

**Código Python:**
- `app/rvc_client.py` (327 linhas) - client completo RVC
- `app/rvc_model_manager.py` (330 linhas) - gerenciamento modelos
- `app/rvc_dependencies.py` - validação deps
- `app/models.py`: `RvcModel`, `RvcParameters` dataclasses
- `app/exceptions.py`: 6 classes de exceção RVC
- `app/metrics.py`: métricas Prometheus RVC
- `app/engines/xtts_engine.py`: integração RVC (linhas 147-621)

**Endpoints API:**
- `/rvc-models` (GET, POST, DELETE)
- `/rvc-models/{id}` (GET, DELETE)
- Jobs com parâmetros RVC (`enable_rvc`, `rvc_model_id`, etc.)

**Configuração:**
- `app/config.py`: seção completa RVC (linhas 135-151)
- `.env`: variáveis `RVC_DEVICE`, `RVC_MODELS_DIR`, etc.
- Diretório `/models/rvc`

**Scripts:**
- `scripts/validate-deps.sh` - validação deps RVC
- `scripts/validate-sprint4.sh` - integração XTTS+RVC
- `scripts/validate-gpu.sh` - reqs GPU para RVC

**Testes:**
- `tests/test_rvc_*.py` (7 arquivos)
- `tests/test_xtts_rvc_integration.py`

**Dependencies:**
- `requirements.txt`: `tts-with-rvc`, `fairseq`, `praat-parselmouth`
- Libs específicas: `pyworld`, `torchcrepe`

### 1.2 Problemas e Riscos (RVC)

**Configuração:**
- Configs duplicadas (`.env` + `config.py`)
- Paths hardcoded (`/app/models/rvc`)
- Variáveis não usadas occupando memória

**Arquitetura:**
- Lazy-load no meio do engine XTTS (acoplamento forte)
- 2-4GB VRAM desperdiçados quando não usado
- Lógica RVC misturada em `xtts_engine.py` (violação SRP)

**Dependências:**
- ~15 packages só para RVC
- Conflitos potenciais (fairseq vs outros)
- Build time aumentado

**Dados/Modelos:**
- Modelos RVC não usados ocupando disco
- Metadata JSON pode estar corrompido
- Symlinks para `/models/rvc`

**Segurança:**
- Upload de .pth sem validação profunda
- Risco de arbitrary code execution via torch.load

---

## 2. Arquitetura & Organização

**Problemas:**
- XTTS-v2 com lazy-load (atraso no 1º request)
- Engines em `/app/engines` mas só XTTS usado
- Lógica RVC dentro de `xtts_engine.py` (acoplamento)
- `main.py` tem 1771 linhas (monolito)
- Falta camada de serviço coesa (tudo misturado)

**Melhorias:**
- Extrair `XTTSService` com eager-load
- Remover pasta `/app/engines` (só XTTS existe)
- Separar routers em `/app/api/` (tts, jobs, voices)
- Criar `/app/services/` (xtts_service, voice_service, job_service)
- Aplicar dependency injection (FastAPI Depends)

---

## 3. Configuração & Paths

**Problemas:**
- Duplicidade: `.env`, `config.py`, YAMLs em `/train/config`
- Paths mistos (`./models` vs `/app/models`)
- Validação fraca (paths podem não existir)
- Configs imutáveis (sem hot-reload)

**Melhorias:**
- Config único via `pydantic.BaseSettings`
- Validar paths no startup
- Usar `pathlib.Path` everywhere
- Consolidar YAMLs do `/train` com config principal

---

## 4. XTTS-v2 Treinamento (/train)

**Problemas:**
- Scripts dispersos (pipeline.py, pipeline_v2.py, ambos)
- Configs duplicados (dataset_config.yaml + train_config.yaml + .env)
- Sample rate inconsistente (16kHz vs 22kHz vs 24kHz)
- Normalização não padronizada
- Falta guia de hyperparams (epochs, batch_size)

**Melhorias:**
- Consolidar em `scripts/train_pipeline.py` único
- Alinhar com guia XTTS avançado:
  - 24kHz sample rate fixo
  - Segmentos 6-12s
  - Normalização -20 LUFS
  - Epochs: 10-40 (dependendo de dataset)
  - Batch size: 2-4 com grad accumulation
- Remover scripts obsoletos (backup, v1)

---

## 5. XTTS-v2 Inferência & Clonagem

**Problemas:**
- **Lazy-load**: modelo carrega no 1º request (5-10s delay)
- Falta perfis de qualidade (fast/balanced/high)
- Parâmetros hardcoded (`temperature=0.75`)
- Vocabulário/tokenizador não validado
- Sem cache de embeddings de voz
- Sem retry logic para CUDA OOM

**Melhorias:**
- **Eager-load** no startup:
  ```python
  @app.on_event("startup")
  async def load_models():
      xtts_service.initialize()
  ```
- Implementar perfis:
  - `fast`: temp=0.7, speed=1.2, top_p=0.85
  - `balanced`: temp=0.75, speed=1.0, top_p=0.9
  - `high_quality`: temp=0.6, speed=0.95, top_p=0.95, denoise=True
- Refatorar para `XTTSService` (SOLID):
  - Single Responsibility: só TTS
  - Open/Closed: novos perfis sem alterar core
  - Dependency Inversion: API depende de interface

---

## 6. Resiliência & Observabilidade

**Problemas:**
- Tratamento de erro inconsistente
- Logs pouco estruturados (falta request_id)
- Métricas RVC poluindo Prometheus
- Sem circuit breaker para GPU
- Timeout hardcoded (60s)

**Melhorias:**
- Middleware de exceções padronizado
- Logs estruturados (JSON) com:
  - `request_id`, `user_agent`, `duration_ms`
  - Parâmetros principais (text_length, voice_id, quality_profile)
- Métricas limpas (só XTTS):
  - `xtts_synthesis_duration_seconds`
  - `xtts_synthesis_total{status, quality_profile}`
  - `xtts_gpu_memory_bytes`
- Circuit breaker para CUDA OOM
- Healthcheck detalhado:
  ```json
  {
    "status": "healthy",
    "xtts": {"loaded": true, "device": "cuda:0"},
    "gpu": {"vram_free_gb": 18.5}
  }
  ```

---

## 7. Outros Pontos Relevantes

**Docker:**
- Entrypoint usa `gosu` (correto)
- Mas ainda tem refs RVC em comentários
- Build time alto (RVC deps)

**WebUI:**
- Limpo de F5-TTS ✅
- Ainda tem refs RVC em forms

**Testes:**
- 99 testes, 91% coverage (bom)
- Mas metade é RVC (remover)
- Falta testes de carga para XTTS

**Docs:**
- Bem documentado
- Precisa atualizar pós-remoção RVC
