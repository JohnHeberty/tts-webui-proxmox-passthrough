# 📋 Análise Técnica & Melhorias - TTS WebUI (XTTS-v2)

**Data**: 2025-12-06  
**Status**: Pós-remoção F5-TTS, pré-implementação `train/` XTTS-v2  
**Tech Lead**: Claude Sonnet 4.5

---

## 🎯 Contexto

Este projeto é um serviço TTS (Text-to-Speech) baseado em **XTTS-v2** (Coqui TTS) com suporte a:
- Síntese de voz multilíngue (foco pt-BR)
- Clonagem de voz via reference audio
- Pipeline RVC para modificação de voz
- API REST (FastAPI) + workers Celery
- Deploy Docker com GPU NVIDIA (CUDA 11.8)

**Recentemente completado**:
- ✅ Remoção total de F5-TTS (157 arquivos, 44k linhas, 84GB liberados)
- ✅ Isolamento 100% Docker (Python VM limpo)
- ✅ API funcionando com XTTS apenas

**Objetivo atual**: Criar pipeline completo de fine-tuning XTTS-v2 para pt-BR.

---

## 📊 Categorias de Análise

### 1. 🏗️ Arquitetura & Organização

#### ✅ Pontos Fortes
- Separação clara backend (FastAPI) + workers (Celery) + cache (Redis)
- Engines abstraídos (`app/engines/base.py`, `xtts_engine.py`)
- Quality profiles configuráveis por engine
- Docker Compose com NVIDIA runtime
- Volume mounts para acesso direto aos modelos (sem cópia)

#### ❌ Problemas Identificados

1. **Falta pasta `train/` para fine-tuning XTTS-v2**
   - Severidade: **ALTA**
   - Não há estrutura para dataset preparation, training, checkpoints
   - Scripts úteis existem em `scripts/not_remove/` mas não estão integrados

2. **Paths hardcoded espalhados pelo código**
   - Severidade: MÉDIA
   - Exemplos: `/app/models/xtts/`, `/app/uploads/`, etc
   - Devem vir de `config.py` ou `.env`

3. **Documentação desatualizada**
   - Severidade: MÉDIA
   - `docs/LOW_VRAM.md`, `docs/QUALITY_PROFILES.md` ainda mencionam F5-TTS
   - Pode confundir novos desenvolvedores

4. **Falta namespace claro para scripts**
   - Severidade: BAIXA
   - `scripts/` mistura prod (`download_models.py`) com utils de manutenção
   - `scripts/not_remove/` é confuso (deveria ser `scripts/dataset/` ou similar)

#### 🔧 Melhorias Propostas

**P0 (Crítico)**:
- [ ] Criar estrutura `train/` completa (ver seção 2)
- [ ] Centralizar paths em `app/config.py` usando `pathlib.Path`

**P1 (Importante)**:
- [ ] Limpar docs desatualizadas ou marcar como "DEPRECATED - F5-TTS removed"
- [ ] Renomear `scripts/not_remove/` → `scripts/dataset/`
- [ ] Criar `scripts/training/` para scripts de treino XTTS

**P2 (Nice to have)**:
- [ ] Adicionar `pyproject.toml` completo (já existe stub)
- [ ] Migrar configs YAML para Pydantic Settings

---

### 2. 📦 Data Pipeline (YouTube → Dataset LJSpeech)

#### ✅ Pontos Fortes
- Scripts funcionais em `scripts/not_remove/`:
  - `download_youtube.py` (yt-dlp)
  - `prepare_segments_optimized.py` (VAD + segmentação)
  - `transcribe_or_subtitles.py` (Whisper + legendas)
  - `build_metadata_csv.py` (formato LJSpeech)
- Lógica de VAD baseada em RMS (memory-efficient)
- Suporte a legendas como fallback

#### ❌ Problemas Identificados

1. **Scripts isolados, sem pipeline unificado**
   - Severidade: **ALTA**
   - Cada script roda manualmente, sem orquestração
   - Falta validação entre etapas (ex: verificar se transcrição existe antes de build_metadata)

2. **Target de duração inadequado para XTTS-v2**
   - Severidade: MÉDIA
   - Scripts geram segmentos variados (3-30s)
   - XTTS-v2 ideal: **7-12s** (conforme docs oficiais)
   - Segmentos muito curtos (<5s) têm baixa qualidade; muito longos (>15s) OOM

3. **Sample rate inconsistente**
   - Severidade: MÉDIA
   - Alguns scripts usam 24kHz, outros 22.05kHz
   - XTTS-v2 requer **22050 Hz mono 16-bit**

4. **Normalização de texto pt-BR incompleta**
   - Severidade: BAIXA
   - `normalize_transcriptions.py` existe mas falta integração
   - Números, siglas, timestamps não são expandidos consistentemente

5. **Falta validação de qualidade de áudio**
   - Severidade: BAIXA
   - Não verifica SNR, clipping, silêncios internos
   - Pode poluir dataset com amostras ruins

#### 🔧 Melhorias Propostas

**P0 (Crítico)**:
- [ ] Criar `train/scripts/pipeline.py` orquestrando:
  1. Download YouTube
  2. Segmentação VAD (target 7-12s, 22050Hz)
  3. Transcrição Whisper
  4. Normalização texto pt-BR
  5. Build LJSpeech dataset
  6. Validação qualidade
- [ ] Garantir **22050 Hz mono 16-bit** em todas as etapas
- [ ] Implementar filtros de duração: `min_duration=5s`, `max_duration=12s`

**P1 (Importante)**:
- [ ] Adicionar validação de SNR (threshold ~20dB)
- [ ] Detectar e remover segmentos com silêncios longos internos (>1s)
- [ ] Expandir números para texto (`"123" → "cento e vinte e três"`)

**P2 (Nice to have)**:
- [ ] Suporte a múltiplas vozes (speaker ID no metadata.csv)
- [ ] Deduplicação de frases repetidas (comum em podcasts)
- [ ] Data augmentation (pitch shift, tempo, reverb leve)

---

### 3. 🎓 Treinamento XTTS-v2

#### ✅ Pontos Fortes
- Infraestrutura Docker com CUDA 11.8 + RTX 3090
- torch 2.4.0+cu118 funcionando
- coqui-tts instalado no container

#### ❌ Problemas Identificados

1. **Não existe script de treinamento**
   - Severidade: **CRÍTICA**
   - Projeto não tem `xtts_train.py` ou similar
   - Sem configuração de hiperparâmetros

2. **Falta modelo pretrained XTTS-v2**
   - Severidade: **ALTA**
   - Não há `models/xtts_pretrained/` com checkpoint base
   - Precisa baixar ou carregar via HuggingFace

3. **Sem suporte a LoRA**
   - Severidade: MÉDIA
   - Full fine-tune é pesado (23GB VRAM)
   - LoRA permite treinar com 8-12GB

4. **Falta monitoramento de treino**
   - Severidade: BAIXA
   - Sem TensorBoard, WandB ou logs estruturados
   - Difícil debugar convergência

5. **Configurações hardcoded**
   - Severidade: BAIXA
   - Batch size, epochs, LR deveriam vir de YAML/env

#### 🔧 Melhorias Propostas

**P0 (Crítico)**:
- [ ] Criar `train/scripts/xtts_train.py` com:
  - Carregamento modelo base XTTS-v2
  - LJSpeechDataset loader
  - Training loop com checkpoints
  - Validação samples a cada N epochs
- [ ] Criar `train/config/train_config.yaml`:
  ```yaml
  model:
    name: xtts_v2
    checkpoint: ./models/xtts_pretrained/model.pth
  training:
    batch_size: 4
    epochs: 50
    learning_rate: 1e-5
    max_text_length: 200
    max_audio_length: 12  # seconds
  dataset:
    path: ./train/data/MyTTSDataset
    language: pt-BR
    sample_rate: 22050
  ```
- [ ] Baixar modelo pretrained XTTS-v2:
  ```bash
  # Via Coqui TTS
  tts --model_name tts_models/multilingual/multi-dataset/xtts_v2 --list_models
  ```

**P1 (Importante)**:
- [ ] Implementar LoRA fine-tuning (parâmetro `use_lora=True`)
- [ ] Adicionar TensorBoard logging
- [ ] Gerar áudio samples a cada epoch (validação manual)
- [ ] Early stopping baseado em validation loss

**P2 (Nice to have)**:
- [ ] Mixed precision training (FP16)
- [ ] Gradient accumulation para batch_size efetivo maior
- [ ] Multi-GPU training (DataParallel)
- [ ] Curriculum learning (começar com frases curtas)

---

### 4. 🎤 API de Inferência & Clonagem

#### ✅ Pontos Fortes
- API FastAPI funcionando (`app/main.py`)
- Engine factory pattern (`app/engines/factory.py`)
- Quality profiles configuráveis
- Endpoint `/jobs` para TTS assíncrono
- Celery workers para processamento

#### ❌ Problemas Identificados

1. **Modelo fine-tunado não integrado**
   - Severidade: **ALTA**
   - `xtts_engine.py` carrega apenas modelo base
   - Precisa suportar checkpoint custom em `train/output/checkpoints/`

2. **Voice cloning sem interface clara**
   - Severidade: MÉDIA
   - Endpoint `/voices/clone` existe mas docs não explicam uso
   - Falta exemplo de curl com upload de reference.wav

3. **Falta endpoint de inferência direta (síncrono)**
   - Severidade: BAIXA
   - `/jobs` é sempre assíncrono
   - Útil ter `/tts/synthesize` para requests rápidos (<5s)

4. **Quality profiles ainda referenciam F5-TTS**
   - Severidade: BAIXA (já removido do código, só docs)
   - Ver `docs/QUALITY_PROFILES.md`

#### 🔧 Melhorias Propostas

**P0 (Crítico)**:
- [ ] Modificar `app/engines/xtts_engine.py`:
  ```python
  def __init__(self, checkpoint_path: str = None):
      if checkpoint_path:
          self.model = self._load_custom_checkpoint(checkpoint_path)
      else:
          self.model = TTS("tts_models/multilingual/multi-dataset/xtts_v2")
  ```
- [ ] Adicionar env var:
  ```bash
  XTTS_CUSTOM_CHECKPOINT=/app/train/output/checkpoints/best_model.pth
  ```

**P1 (Importante)**:
- [ ] Criar endpoint síncrono:
  ```python
  @app.post("/tts/synthesize")
  async def synthesize(text: str, reference_audio: UploadFile = None):
      # Inferência direta, retorna WAV
  ```
- [ ] Documentar voice cloning no README:
  ```bash
  curl -X POST http://localhost:8005/voices/clone \
    -F "text=Olá, sou sua voz clonada" \
    -F "reference_audio=@speaker.wav" \
    -F "language=pt-BR"
  ```

**P2 (Nice to have)**:
- [ ] Batch inference (múltiplos textos de uma vez)
- [ ] Streaming TTS (retornar chunks de áudio)
- [ ] Cache de embeddings de speaker (acelerar cloning)

---

### 5. 🔧 Ambiente & DevOps

#### ✅ Pontos Fortes
- Docker Compose funcional
- Imagens otimizadas (9.8GB)
- NVIDIA runtime configurado
- Volume mounts (sem duplicação de modelos)
- Healthchecks nos containers

#### ❌ Problemas Identificados

1. **Venv não criada no projeto**
   - Severidade: MÉDIA
   - Desenvolvimento direto no sistema ou em Docker apenas
   - Sem `.venv/` local para IDEs

2. **Falta CI/CD**
   - Severidade: BAIXA
   - Sem GitHub Actions / GitLab CI
   - Testes manuais

3. **Logs não estruturados**
   - Severidade: BAIXA
   - Logging via `print()` em alguns lugares
   - Falta JSON logging para parsing

4. **Secrets em `.env` commitado**
   - Severidade: **CRÍTICA (SEGURANÇA)**
   - `.env` está no repositório (verificar `.gitignore`)
   - API keys expostas?

#### 🔧 Melhorias Propostas

**P0 (Crítico)**:
- [ ] Verificar se `.env` está no `.gitignore`
- [ ] Criar `.env.example` sem secrets
- [ ] Rotacionar qualquer API key que esteja commitada

**P1 (Importante)**:
- [ ] Criar `ENV_SETUP.md` com:
  ```bash
  # Criar venv
  python3 -m venv .venv
  source .venv/bin/activate
  pip install -r requirements.txt
  
  # VSCode: Ctrl+Shift+P > "Python: Select Interpreter" > .venv
  ```
- [ ] Adicionar `pytest` em requirements-dev.txt
- [ ] Configurar logging estruturado (JSON) em produção

**P2 (Nice to have)**:
- [ ] GitHub Actions para testes
- [ ] Pre-commit hooks (black, isort, mypy)
- [ ] Docker registry privado (AWS ECR / GCP Artifact Registry)

---

### 6. ✅ Qualidade de Código & Testes

#### ✅ Pontos Fortes
- Type hints em alguns módulos
- Docstrings em funções críticas
- Pytest configurado (`pytest.ini`)
- Alguns testes existem (`test_voice_cloning.py`)

#### ❌ Problemas Identificados

1. **Cobertura de testes baixa**
   - Severidade: MÉDIA
   - Maioria do código sem testes
   - Falta testes de integração (API endpoints)

2. **Type hints incompletos**
   - Severidade: BAIXA
   - Muitas funções sem hints
   - Mypy não configurado

3. **Duplicação de código**
   - Severidade: BAIXA
   - Lógica de paths repetida
   - Validações similares em múltiplos lugares

4. **Falta linting automático**
   - Severidade: BAIXA
   - Sem black, flake8, isort no projeto

#### 🔧 Melhorias Propostas

**P0 (Crítico)**:
- [ ] Adicionar testes para `train/scripts/`:
  - `test_download_youtube.py`
  - `test_segment_audio.py`
  - `test_transcribe.py`
  - `test_build_metadata.py`

**P1 (Importante)**:
- [ ] Configurar mypy:
  ```ini
  [mypy]
  python_version = 3.11
  warn_return_any = True
  warn_unused_configs = True
  disallow_untyped_defs = True
  ```
- [ ] Adicionar pre-commit:
  ```yaml
  repos:
    - repo: https://github.com/psf/black
      hooks:
        - id: black
    - repo: https://github.com/pycqa/isort
      hooks:
        - id: isort
  ```

**P2 (Nice to have)**:
- [ ] Coverage report (pytest-cov)
- [ ] Mutation testing (mutmut)
- [ ] Property-based testing (hypothesis)

---

### 7. 📚 Documentação & DX (Developer Experience)

#### ✅ Pontos Fortes
- README.md existente
- Docs em `docs/` (arquitetura, API, deployment)
- Changelog mantido
- Comentários inline em código complexo

#### ❌ Problemas Identificados

1. **Docs desatualizadas após remoção F5-TTS**
   - Severidade: MÉDIA
   - `docs/LOW_VRAM.md` - ainda menciona F5-TTS
   - `docs/QUALITY_PROFILES.md` - perfis F5-TTS documentados
   - `docs/CHANGELOG.md` - correto, mas confuso para novos devs

2. **Falta guia de contribuição**
   - Severidade: BAIXA
   - Sem `CONTRIBUTING.md`
   - Novos devs não sabem como setup ambiente

3. **API docs não geradas automaticamente**
   - Severidade: BAIXA
   - FastAPI tem Swagger, mas não documentado
   - Falta link no README para `http://localhost:8005/docs`

4. **Falta diagramas de arquitetura**
   - Severidade: BAIXA
   - Nenhuma imagem explicando fluxo de dados
   - Dificuldade para entender sistema rapidamente

#### 🔧 Melhorias Propostas

**P0 (Crítico)**:
- [ ] Atualizar docs com remoção F5-TTS:
  - Marcar seções obsoletas com "⚠️ DEPRECATED"
  - Adicionar nota: "F5-TTS removed in v2.0 - XTTS-only project"

**P1 (Importante)**:
- [ ] Criar `CONTRIBUTING.md`:
  ```markdown
  # Contributing
  
  ## Setup
  1. Clone repo
  2. Create venv: `python3 -m venv .venv`
  3. Install deps: `pip install -r requirements.txt -r requirements-dev.txt`
  4. Run tests: `pytest`
  
  ## Code Style
  - Black (line length 100)
  - isort
  - Type hints obrigatórios
  
  ## Commit Messages
  - Conventional Commits: `feat:`, `fix:`, `docs:`, etc
  ```
- [ ] Adicionar no README:
  ```markdown
  ## API Documentation
  
  Acesse http://localhost:8005/docs (Swagger UI)
  ```

**P2 (Nice to have)**:
- [ ] Gerar diagramas com Mermaid:
  ```mermaid
  graph TD
    A[YouTube URL] --> B[download_youtube.py]
    B --> C[segment_audio.py]
    C --> D[transcribe_whisper.py]
    D --> E[build_metadata.py]
    E --> F[LJSpeech Dataset]
    F --> G[xtts_train.py]
    G --> H[Checkpoint]
    H --> I[API Inference]
  ```
- [ ] Gravar screencast de setup (Asciinema)
- [ ] Adicionar badges no README (build status, coverage, license)

---

## 🎯 Resumo Executivo

### Problemas Críticos (P0)

1. **Falta estrutura `train/` completa** → Bloqueia fine-tuning
2. **Sem script de treinamento XTTS-v2** → Core feature inexistente
3. **Modelo fine-tunado não integrável** → Sem path para usar checkpoint custom
4. **Pipeline de dados desintegrado** → Scripts isolados, sem orquestração
5. **Secrets em `.env` commitado** → Risco de segurança

### Melhorias de Alto Impacto (P1)

1. Documentação atualizada (remover F5-TTS)
2. Validação de qualidade de áudio (SNR, duração)
3. Suporte a LoRA fine-tuning
4. Endpoint síncrono de TTS
5. Setup de venv + CI básico

### Quick Wins (P2)

1. Linting automático (black, isort)
2. Diagramas de arquitetura
3. Batch inference
4. Data augmentation

---

## 📋 Próximos Passos

Ver `SPRINTS.md` para plano detalhado de implementação em sprints.

**Recomendação**: Começar pela **Sprint 1** (estrutura `train/` + pipeline dados).

---

**Última atualização**: 2025-12-06  
**Mantido por**: Tech Lead (Claude Sonnet 4.5)
