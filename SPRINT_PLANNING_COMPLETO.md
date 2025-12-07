# 🎯 Planejamento Completo - Sprints Pendentes

**Data**: 2025-12-06  
**Tech Lead**: Claude Sonnet 4.5  
**Escopo**: Finalizar Sprints 4-5 + Melhorias WebUI + Integrações

---

## 📊 Status Atual do Projeto

### ✅ Sprints Completos (Sprints 0-3)
- **Sprint 0**: Segurança & Cleanup (100%)
- **Sprint 1**: Pipeline de Dataset (100%) - 4922 samples, 15.3h
- **Sprint 2**: Training Script (100%) - XTTS-v2 fine-tuning
- **Sprint 3**: API Integration (100%) - 6 endpoints REST

### ⏳ Sprints Pendentes
- **Sprint 4**: Qualidade & Testes (0%)
- **Sprint 5**: Docs & DevOps (0%)
- **Sprint 6**: WebUI Integration (NOVO - 0%)
- **Sprint 7**: Advanced Features (NOVO - 0%)

---

## 🎯 Sprint 4: Qualidade & Testes (P1)

**Objetivo**: Garantir qualidade de código e cobertura de testes  
**Duração estimada**: 6-8 horas  
**Prioridade**: P1 (ALTA - validação crítica)

### 4.1 Testes de Voice Cloning (✅ FEITO)
- [x] `train/test/test_voice_cloning.py` - 6 testes
- [x] Validação Whisper (89.44% similaridade)
- [x] Pipeline completo: Original → Transcrição → Clone → Validação
- [x] Métricas MFCC (98.98%)

**Status**: ✅ COMPLETO

### 4.2 Testes do Pipeline de Dados
- [ ] `train/test/test_download_youtube.py`
  - Validar download de vídeos
  - Verificar sample rate (22050Hz)
  - Testar retry logic
  - Mock yt-dlp para CI
  
- [ ] `train/test/test_segment_audio.py`
  - Testar VAD streaming
  - Validar duração (7-12s)
  - Verificar fade in/out
  - Testar normalização RMS
  
- [ ] `train/test/test_transcribe_audio_parallel.py`
  - Testar paralelização (15x speedup)
  - Validar Whisper base + HP fallback
  - Verificar OOV detection
  - Testar normalização pt-BR
  
- [ ] `train/test/test_build_ljs_dataset.py`
  - Validar formato LJSpeech
  - Verificar metadata.csv
  - Testar splits (train/val)
  
- [ ] `train/test/test_pipeline_integration.py`
  - Pipeline end-to-end
  - Validar 4922 samples finais
  - Verificar tempo de execução

**Critérios de Aceitação**:
- ✅ Coverage > 75% nos scripts de pipeline
- ✅ Testes passam com pytest
- ✅ Mocks para APIs externas (YouTube, Whisper)

---

### 4.3 Testes de Treinamento
- [ ] `train/test/test_train_xtts.py`
  - Smoke test (10 steps)
  - Validar checkpoint saving
  - Testar LoRA weights
  - Verificar gradient clipping
  - Testar mixed precision
  
- [ ] `train/test/test_xtts_inference.py` (✅ JÁ EXISTE - integrar)
  - 16 testes já implementados
  - Mover de `train/tests/` para `train/test/` ✅ FEITO
  - Atualizar imports se necessário

**Critérios de Aceitação**:
- ✅ Smoke test passa em < 5min
- ✅ Checkpoint loading funcional
- ✅ Inferência com modelo fine-tuned

---

### 4.4 Testes de API Fine-tuning
- [ ] `train/test/test_finetune_api.py` (✅ JÁ EXISTE - integrar)
  - 11 testes já implementados
  - Validar 6 endpoints REST
  - Testar error handling
  
- [ ] `train/test/test_integration.py` (✅ JÁ EXISTE - integrar)
  - 9 testes já implementados
  - Pipeline completo API

**Status**: ✅ Arquivos já existem, apenas validar integração

---

### 4.5 Configurar Linting & Formatação
- [ ] Adicionar `.pre-commit-config.yaml`:
  ```yaml
  repos:
    - repo: https://github.com/psf/black
      rev: 24.10.0
      hooks:
        - id: black
          language_version: python3.11
    
    - repo: https://github.com/pycqa/isort
      rev: 5.13.2
      hooks:
        - id: isort
          args: ["--profile", "black"]
    
    - repo: https://github.com/pycqa/flake8
      rev: 7.0.0
      hooks:
        - id: flake8
          args: ["--max-line-length=120", "--extend-ignore=E203,W503"]
    
    - repo: https://github.com/pre-commit/pre-commit-hooks
      rev: v4.5.0
      hooks:
        - id: trailing-whitespace
        - id: end-of-file-fixer
        - id: check-yaml
        - id: check-json
        - id: check-added-large-files
          args: ['--maxkb=10000']
  ```

- [ ] Criar `pyproject.toml`:
  ```toml
  [tool.black]
  line-length = 120
  target-version = ['py311']
  include = '\.pyi?$'
  extend-exclude = '''
  /(
    \.eggs
    | \.git
    | \.hg
    | \.mypy_cache
    | \.tox
    | \.venv
    | _build
    | buck-out
    | build
    | dist
    | models
    | voice_profiles
  )/
  '''
  
  [tool.isort]
  profile = "black"
  line_length = 120
  skip_gitignore = true
  
  [tool.pytest.ini_options]
  testpaths = ["tests", "train/test"]
  python_files = "test_*.py"
  python_classes = "Test*"
  python_functions = "test_*"
  addopts = "-v --tb=short --strict-markers"
  ```

- [ ] Rodar formatação inicial:
  ```bash
  pip install black isort flake8 pre-commit
  black app/ train/ tests/
  isort app/ train/ tests/
  pre-commit install
  pre-commit run --all-files
  ```

**Critérios de Aceitação**:
- ✅ Pre-commit hooks instalados
- ✅ Código formatado (black + isort)
- ✅ Zero warnings do flake8

---

### 4.6 Type Hints & mypy
- [ ] Adicionar type hints em `train/scripts/*.py`
- [ ] Adicionar type hints em `app/*.py` (principais)
- [ ] Configurar `mypy.ini`:
  ```ini
  [mypy]
  python_version = 3.11
  warn_return_any = True
  warn_unused_configs = True
  warn_redundant_casts = True
  warn_unused_ignores = True
  
  # Strict mode (opcional, começar com False)
  disallow_untyped_defs = False
  disallow_any_generics = False
  check_untyped_defs = True
  
  # Ignore missing imports de third-party
  [mypy-celery.*]
  ignore_missing_imports = True
  [mypy-redis.*]
  ignore_missing_imports = True
  [mypy-TTS.*]
  ignore_missing_imports = True
  ```

- [ ] Rodar mypy:
  ```bash
  pip install mypy
  mypy app/ train/
  ```

**Critérios de Aceitação**:
- ✅ Type hints em funções públicas principais
- ✅ mypy sem erros críticos
- ✅ Documentação atualizada

---

### Sprint 4 - Deliverables

- [ ] 25+ testes implementados (pipeline + training + API)
- [ ] Coverage > 75% em `train/`
- [ ] Linting configurado (black, isort, flake8)
- [ ] Pre-commit hooks funcionando
- [ ] Type hints básicos adicionados
- [ ] CI local validado

---

## 📚 Sprint 5: Documentação & DevOps (P2)

**Objetivo**: Documentação completa e automação CI/CD  
**Duração estimada**: 4-5 horas  
**Prioridade**: P2 (MÉDIA - necessário para produção)

### 5.1 Documentação Técnica

#### 5.1.1 Criar `docs/TRAINING_GUIDE.md`
- [ ] **Seção 1: Setup Inicial**
  - Requisitos de hardware (GPU VRAM, storage)
  - Instalação de dependências
  - Download de modelos base
  - Configuração de variáveis de ambiente
  
- [ ] **Seção 2: Preparação de Dataset**
  - Como criar `videos.csv`
  - Executar pipeline completo
  - Validar qualidade do dataset
  - Troubleshooting comum
  
- [ ] **Seção 3: Fine-tuning**
  - Configurar `train_config.yaml`
  - Executar smoke test
  - Executar training completo
  - Monitorar TensorBoard
  - Ajustar hiperparâmetros
  
- [ ] **Seção 4: Inferência**
  - Testar modelo fine-tuned
  - Integrar com API
  - Validar qualidade de áudio
  - A/B testing com modelo base

**Formato**: Markdown com exemplos de código e screenshots

---

#### 5.1.2 Atualizar `train/docs/GUIA_USUARIO_TREINAMENTO.md`
- [ ] Adicionar seção de fine-tuning XTTS-v2
- [ ] Remover referências a F5-TTS (deprecated)
- [ ] Atualizar FAQs com casos reais
- [ ] Adicionar troubleshooting de VRAM

---

#### 5.1.3 Criar `docs/WEBUI_INTEGRATION.md`
- [ ] Arquitetura da WebUI (HTML5 + Bootstrap 5)
- [ ] Endpoints utilizados
- [ ] Fluxo de dados (Frontend ↔ API)
- [ ] Customização de temas
- [ ] Adicionar novas funcionalidades

---

### 5.2 Diagramas de Arquitetura

- [ ] **Pipeline de Dados** (Mermaid):
  ```mermaid
  graph LR
    A[videos.csv] --> B[download_youtube.py]
    B --> C[raw/*.wav]
    C --> D[segment_audio.py]
    D --> E[processed/wavs/*.wav]
    E --> F[transcribe_audio_parallel.py]
    F --> G[transcriptions.json]
    G --> H[build_ljs_dataset.py]
    H --> I[MyTTSDataset/metadata.csv]
  ```

- [ ] **Fluxo de Treinamento** (Mermaid):
  ```mermaid
  graph TD
    A[Dataset LJSpeech] --> B[train_xtts.py]
    B --> C{Epoch Loop}
    C --> D[Train Step]
    D --> E[Validation]
    E --> F{Best Model?}
    F -->|Yes| G[Save Checkpoint]
    F -->|No| C
    G --> H[Fine-tuned Model]
  ```

- [ ] **Arquitetura API** (Mermaid):
  ```mermaid
  graph TB
    subgraph "Frontend"
      A[WebUI]
      B[Postman/Curl]
    end
    
    subgraph "Backend"
      C[FastAPI]
      D[Celery Worker]
      E[Redis]
    end
    
    subgraph "ML Engines"
      F[XTTS v2]
      G[F5-TTS]
      H[RVC]
    end
    
    A --> C
    B --> C
    C --> D
    D --> E
    D --> F
    D --> G
    D --> H
  ```

---

### 5.3 README Updates

- [ ] **`README.md` (root)**:
  - Atualizar badges (build status, coverage)
  - Seção "Quick Start" com comandos principais
  - Link para docs de training
  - Link para Swagger (`/docs`)
  - Seção de contribuição
  
- [ ] **`train/README.md`**:
  - Atualizar status (67% → 85%+)
  - Adicionar exemplos de uso
  - Link para guia de training
  
- [ ] **`app/webui/README.md`**:
  - Atualizar screenshots
  - Adicionar seção de features
  - Link para API reference

---

### 5.4 GitHub Actions CI/CD

#### 5.4.1 Criar `.github/workflows/ci.yml`
```yaml
name: CI - Lint & Test

on:
  push:
    branches: [ main, develop ]
  pull_request:
    branches: [ main ]

jobs:
  lint:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      
      - name: Set up Python 3.11
        uses: actions/setup-python@v5
        with:
          python-version: '3.11'
          cache: 'pip'
      
      - name: Install dependencies
        run: |
          pip install black isort flake8 mypy
      
      - name: Run Black
        run: black --check app/ train/ tests/
      
      - name: Run isort
        run: isort --check-only app/ train/ tests/
      
      - name: Run flake8
        run: flake8 app/ train/ tests/ --max-line-length=120

  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      
      - name: Set up Python 3.11
        uses: actions/setup-python@v5
        with:
          python-version: '3.11'
          cache: 'pip'
      
      - name: Install dependencies
        run: |
          pip install -r requirements.txt
          pip install pytest pytest-cov pytest-asyncio
      
      - name: Run tests
        run: |
          pytest train/test/ -v --cov=train --cov-report=xml
      
      - name: Upload coverage
        uses: codecov/codecov-action@v4
        with:
          file: ./coverage.xml
          fail_ci_if_error: false
```

#### 5.4.2 Criar `.github/workflows/docker.yml`
```yaml
name: Docker Build

on:
  push:
    branches: [ main ]
    tags: [ 'v*' ]

jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      
      - name: Set up Docker Buildx
        uses: docker/setup-buildx-action@v3
      
      - name: Login to Docker Hub
        uses: docker/login-action@v3
        with:
          username: ${{ secrets.DOCKER_USERNAME }}
          password: ${{ secrets.DOCKER_PASSWORD }}
      
      - name: Build and push
        uses: docker/build-push-action@v5
        with:
          context: .
          push: ${{ github.event_name != 'pull_request' }}
          tags: |
            ${{ secrets.DOCKER_USERNAME }}/tts-webui:latest
            ${{ secrets.DOCKER_USERNAME }}/tts-webui:${{ github.sha }}
          cache-from: type=gha
          cache-to: type=gha,mode=max
```

---

### 5.5 Contributing Guidelines

- [ ] Criar `CONTRIBUTING.md`:
  - Code of Conduct
  - Como reportar bugs
  - Como sugerir features
  - Processo de PR
  - Commit conventions (Conventional Commits)
  - Code style (Black + isort)
  
- [ ] Criar `SECURITY.md`:
  - Como reportar vulnerabilidades
  - Política de disclosure
  - Versões suportadas

---

### Sprint 5 - Deliverables

- [ ] `docs/TRAINING_GUIDE.md` completo (20+ páginas)
- [ ] 3 diagramas Mermaid criados
- [ ] READMEs atualizados (root + train + webui)
- [ ] GitHub Actions CI funcionando
- [ ] `CONTRIBUTING.md` e `SECURITY.md` criados
- [ ] Badges no README (build status, coverage)

---

## 🎨 Sprint 6: WebUI Integration & Improvements (NOVO)

**Objetivo**: Integrar WebUI com funcionalidades de training e melhorias UX  
**Duração estimada**: 8-10 horas  
**Prioridade**: P1 (ALTA - user-facing)

### 6.1 Nova Seção: Training & Fine-tuning

#### 6.1.1 Criar Página "Training" na WebUI
- [ ] **Adicionar no navbar**:
  ```html
  <li class="nav-item">
      <a class="nav-link" href="#" onclick="app.navigate('training')">
          <i class="bi bi-cpu-fill"></i> Training
      </a>
  </li>
  ```

- [ ] **Seção HTML** (`app/webui/index.html`):
  ```html
  <section id="section-training" class="content-section" style="display:none;">
      <h1><i class="bi bi-cpu-fill"></i> Fine-tuning XTTS-v2</h1>
      
      <!-- Tabs: Dataset | Training | Inference -->
      <ul class="nav nav-tabs" id="trainingTabs">
          <li class="nav-item">
              <a class="nav-tab active" data-bs-toggle="tab" href="#tab-dataset">
                  <i class="bi bi-database"></i> Dataset
              </a>
          </li>
          <li class="nav-item">
              <a class="nav-tab" data-bs-toggle="tab" href="#tab-training">
                  <i class="bi bi-play-circle"></i> Training
              </a>
          </li>
          <li class="nav-item">
              <a class="nav-tab" data-bs-toggle="tab" href="#tab-inference">
                  <i class="bi bi-mic"></i> Inference
              </a>
          </li>
      </ul>
      
      <div class="tab-content">
          <!-- Tab 1: Dataset -->
          <!-- Tab 2: Training -->
          <!-- Tab 3: Inference -->
      </div>
  </section>
  ```

---

#### 6.1.2 Tab "Dataset" - Gerenciamento de Dataset
- [ ] **Upload de vídeos** (alternativa ao `videos.csv`):
  - Formulário com inputs: YouTube URL, Nome, Descrição
  - Botão "Add to Queue"
  - Lista de vídeos na fila
  - Botão "Download All" → chama API
  
- [ ] **Status do Dataset**:
  - Total de vídeos baixados
  - Total de segmentos gerados
  - Total de transcrições
  - Samples finais (metadata.csv)
  - Duração total (horas)
  
- [ ] **Visualizar Samples**:
  - Tabela paginada com samples
  - Colunas: ID, Texto, Duração, Player
  - Filtros por duração, texto
  
- [ ] **Ações**:
  - "Download Videos" → POST `/training/dataset/download`
  - "Segment Audio" → POST `/training/dataset/segment`
  - "Transcribe" → POST `/training/dataset/transcribe`
  - "Build Metadata" → POST `/training/dataset/build`
  - "View Stats" → GET `/training/dataset/stats`

**Endpoints necessários** (criar em `app/main.py`):
```python
@app.post("/training/dataset/download")
async def start_dataset_download():
    """Inicia download de vídeos do videos.csv"""
    pass

@app.post("/training/dataset/segment")
async def start_segmentation():
    """Inicia segmentação de áudio"""
    pass

@app.post("/training/dataset/transcribe")
async def start_transcription():
    """Inicia transcrição com Whisper"""
    pass

@app.post("/training/dataset/build")
async def build_metadata():
    """Gera metadata.csv LJSpeech"""
    pass

@app.get("/training/dataset/stats")
async def get_dataset_stats():
    """Retorna estatísticas do dataset"""
    pass
```

---

#### 6.1.3 Tab "Training" - Controle de Treinamento
- [ ] **Formulário de Configuração**:
  - Seletor de dataset (MyTTSDataset)
  - Epochs (slider 1-100, default 50)
  - Batch size (slider 1-16, default 2)
  - Learning rate (input, default 1e-5)
  - Gradient accumulation steps (slider 1-8, default 4)
  - Save frequency (slider 1-10, default 5)
  - Checkbox: Use mixed precision
  - Checkbox: Use LoRA
  
- [ ] **Botões de Controle**:
  - "Start Training" → POST `/training/start`
  - "Pause Training" → POST `/training/pause`
  - "Resume Training" → POST `/training/resume`
  - "Stop Training" → POST `/training/stop`
  
- [ ] **Status em Tempo Real**:
  - Progress bar (epoch atual / total)
  - Loss gráfico (Chart.js)
  - Métricas: Train Loss, Val Loss, Learning Rate
  - Tempo estimado restante
  - GPU usage (VRAM, Temp)
  
- [ ] **Logs ao Vivo**:
  - Terminal-style log viewer
  - Auto-scroll
  - Filtros: INFO, WARNING, ERROR
  
- [ ] **Checkpoints**:
  - Lista de checkpoints salvos
  - Colunas: Epoch, Val Loss, Tamanho, Data
  - Ações: Download, Load for Inference, Delete

**Endpoints necessários**:
```python
@app.post("/training/start")
async def start_training(config: TrainingConfig):
    """Inicia training em background (Celery task)"""
    pass

@app.get("/training/status")
async def get_training_status():
    """Retorna status atual do training (real-time)"""
    pass

@app.get("/training/logs")
async def get_training_logs(lines: int = 100):
    """Retorna últimas N linhas de log"""
    pass

@app.get("/training/checkpoints")
async def list_checkpoints():
    """Lista checkpoints disponíveis"""
    pass

@app.post("/training/pause")
async def pause_training():
    pass

@app.post("/training/stop")
async def stop_training():
    pass
```

---

#### 6.1.4 Tab "Inference" - Testar Modelo Fine-tuned
- [ ] **Seletor de Checkpoint**:
  - Dropdown com checkpoints disponíveis
  - Botão "Load Model"
  
- [ ] **Formulário de Síntese**:
  - Textarea para texto
  - Upload de áudio de referência (voice cloning)
  - Botão "Generate" → POST `/training/synthesize`
  
- [ ] **Player de Áudio**:
  - Tocar áudio gerado
  - Download
  - Compartilhar
  
- [ ] **Comparação A/B**:
  - Player lado a lado: Modelo Base vs Fine-tuned
  - Votar: Qual é melhor?
  - Salvar feedback

**Endpoints necessários**:
```python
@app.post("/training/inference/load")
async def load_checkpoint(checkpoint_path: str):
    """Carrega checkpoint para inferência"""
    pass

@app.post("/training/inference/synthesize")
async def synthesize_with_checkpoint(text: str, checkpoint: str, speaker_wav: Optional[bytes]):
    """Gera áudio com modelo fine-tuned"""
    pass
```

---

### 6.2 Melhorias Gerais da WebUI

#### 6.2.1 Dashboard Enhancements
- [ ] **Adicionar Gráficos**:
  - Jobs por dia (Chart.js line chart)
  - Engines mais usados (pie chart)
  - Vozes clonadas por idioma (bar chart)
  - RVC models usage stats
  
- [ ] **Notificações Push**:
  - WebSocket para updates em tempo real
  - Notificar quando job completo
  - Notificar quando training epoch completo
  
- [ ] **Quick Actions**:
  - Botões rápidos: "New TTS Job", "Clone Voice", "Upload RVC Model"
  - Recent items: Últimos 5 jobs, últimas 5 vozes

---

#### 6.2.2 Jobs & Downloads Improvements
- [ ] **Filtros Avançados**:
  - Por status (pending, processing, completed, failed)
  - Por engine (XTTS, F5-TTS)
  - Por data (range picker)
  - Por idioma
  
- [ ] **Bulk Actions**:
  - Selecionar múltiplos jobs
  - Download em lote (ZIP)
  - Deletar em lote
  
- [ ] **Exportar Logs**:
  - Download de logs de job
  - Exportar lista de jobs (CSV)

---

#### 6.2.3 Voice Cloning Enhancements
- [ ] **Preview de Áudio**:
  - Player inline na lista de vozes
  - Waveform visualization (WaveSurfer.js)
  
- [ ] **Tags & Categorias**:
  - Adicionar tags customizadas
  - Filtrar por tags
  - Categorias: Masculino, Feminino, Infantil, etc.
  
- [ ] **Compartilhamento**:
  - Gerar link público para voz
  - QR code
  - Exportar perfil de voz (JSON)

---

#### 6.2.4 RVC Models Management
- [ ] **Validação de Modelo**:
  - Teste automático após upload
  - Preview com sample text
  - Detectar problemas (corrupted file, wrong format)
  
- [ ] **Model Marketplace** (futuro):
  - Galeria de modelos públicos
  - Download de modelos community
  - Rating & reviews

---

#### 6.2.5 Quality Profiles UI/UX
- [ ] **Visual Editor**:
  - Sliders para parâmetros
  - Preview em tempo real
  - A/B comparison
  
- [ ] **Presets Templates**:
  - Templates prontos: Podcast, Audiobook, Voice Message
  - Import/Export JSON
  
- [ ] **Profile Analytics**:
  - Quantos jobs usaram cada perfil
  - Average quality score
  - Popular profiles

---

### 6.3 WebUI Backend Endpoints (Novos)

Criar em `app/main.py`:

```python
# Training Dataset Management
@app.post("/training/dataset/download")
@app.post("/training/dataset/segment")
@app.post("/training/dataset/transcribe")
@app.post("/training/dataset/build")
@app.get("/training/dataset/stats")
@app.get("/training/dataset/samples")

# Training Control
@app.post("/training/start")
@app.post("/training/pause")
@app.post("/training/resume")
@app.post("/training/stop")
@app.get("/training/status")
@app.get("/training/logs")
@app.get("/training/checkpoints")

# Training Inference
@app.post("/training/inference/load")
@app.post("/training/inference/synthesize")
@app.post("/training/inference/compare")

# Dashboard Analytics
@app.get("/analytics/jobs-per-day")
@app.get("/analytics/engines-usage")
@app.get("/analytics/voices-by-language")
@app.get("/analytics/rvc-usage")

# Voice Cloning Enhancements
@app.post("/voices/{voice_id}/tags")
@app.get("/voices/{voice_id}/share")
@app.get("/voices/{voice_id}/export")

# RVC Models Validation
@app.post("/rvc/models/{model_id}/validate")
@app.get("/rvc/models/{model_id}/preview")
```

Total: ~20 novos endpoints

---

### 6.4 WebUI JavaScript Refactoring

- [ ] **Modularizar `app.js`**:
  - Separar em módulos: `dashboard.js`, `jobs.js`, `voices.js`, `training.js`, `rvc.js`
  - Usar ES6 modules
  
- [ ] **Adicionar Libraries**:
  - Chart.js (gráficos)
  - WaveSurfer.js (waveform)
  - Socket.IO (real-time updates)
  - QRCode.js (compartilhamento)
  
- [ ] **State Management**:
  - Implementar simple store (Redux-like)
  - Cache de dados
  - Offline support (ServiceWorker)

---

### Sprint 6 - Deliverables

- [ ] Página "Training" completa (3 tabs)
- [ ] 20+ novos endpoints implementados
- [ ] Dashboard com gráficos (Chart.js)
- [ ] WebSocket para real-time updates
- [ ] Jobs & Voices com filtros avançados
- [ ] RVC model validation
- [ ] JavaScript modularizado
- [ ] Documentação atualizada

---

## 🚀 Sprint 7: Advanced Features & Optimizations (NOVO)

**Objetivo**: Features avançadas e otimizações de performance  
**Duração estimada**: 10-12 horas  
**Prioridade**: P2 (MÉDIA - nice to have)

### 7.1 Batch Processing
- [ ] Endpoint `/jobs/batch`:
  - Aceita array de textos
  - Cria múltiplos jobs
  - Retorna ZIP com todos os áudios
  
- [ ] WebUI: Bulk TTS Generator:
  - Upload CSV (texto, idioma, voz)
  - Preview de batch
  - Download ZIP

---

### 7.2 Advanced Voice Cloning
- [ ] **Multi-speaker Dataset**:
  - Suporte a múltiplos speakers em um dataset
  - Auto-detect speaker diarization
  
- [ ] **Voice Morphing**:
  - Misturar 2+ vozes (interpolação)
  - Ajustar características (pitch, speed, tone)
  
- [ ] **Voice Style Transfer**:
  - Aplicar estilo de uma voz em outra
  - Preservar conteúdo, mudar prosódia

---

### 7.3 Performance Optimizations
- [ ] **Model Caching**:
  - Cache de modelos em memória (LRU)
  - Lazy loading de checkpoints
  
- [ ] **Parallel Processing**:
  - Celery workers paralelos
  - GPU batch inference
  
- [ ] **Audio Streaming**:
  - Streaming de áudio gerado (chunks)
  - Reduzir latência inicial

---

### 7.4 Monitoring & Observability
- [ ] **Prometheus Metrics**:
  - Endpoint `/metrics`
  - Métricas: request count, latency, GPU usage
  
- [ ] **Grafana Dashboard**:
  - Setup de Grafana + Prometheus
  - Dashboards pré-configurados
  
- [ ] **Logging Centralizado**:
  - Integração com Loki ou ELK
  - Structured logging (JSON)

---

### 7.5 Security Enhancements
- [ ] **API Authentication**:
  - JWT tokens
  - API keys
  - Rate limiting (Redis-based)
  
- [ ] **Input Validation**:
  - Sanitização de inputs
  - File upload limits
  - Malware scanning (ClamAV)
  
- [ ] **HTTPS & Certificates**:
  - Let's Encrypt automation
  - Reverse proxy (Nginx)

---

### Sprint 7 - Deliverables

- [ ] Batch processing implementado
- [ ] Voice morphing funcional
- [ ] Model caching otimizado
- [ ] Prometheus + Grafana configurados
- [ ] JWT authentication
- [ ] Rate limiting
- [ ] Documentação de segurança

---

## 📊 Cronograma Geral

| Sprint | Duração | Prioridade | Dependências |
|--------|---------|------------|--------------|
| **Sprint 4** | 6-8h | P1 | Sprint 3 ✅ |
| **Sprint 5** | 4-5h | P2 | Sprint 4 |
| **Sprint 6** | 8-10h | P1 | Sprint 3 ✅ |
| **Sprint 7** | 10-12h | P2 | Sprint 6 |

**Total estimado**: 28-35 horas

**Ordem sugerida**:
1. Sprint 4 (testes - crítico para qualidade)
2. Sprint 6 (WebUI - alto impacto UX)
3. Sprint 5 (docs - necessário para produção)
4. Sprint 7 (features avançadas - nice to have)

---

## 🎯 Métricas de Sucesso

### Sprint 4
- [ ] Coverage > 75%
- [ ] 25+ testes passando
- [ ] Zero warnings de linting
- [ ] mypy sem erros críticos

### Sprint 5
- [ ] Docs completas (50+ páginas)
- [ ] CI passing em todos os PRs
- [ ] README com badges
- [ ] Novos devs onboarding < 30min

### Sprint 6
- [ ] Página Training funcional
- [ ] 20+ endpoints implementados
- [ ] Real-time updates funcionando
- [ ] UX score > 8/10 (user feedback)

### Sprint 7
- [ ] Batch processing latency < 10s/job
- [ ] Voice morphing quality > 85%
- [ ] API response time < 200ms (p95)
- [ ] Security audit passed

---

## 📝 Próximos Passos

**IMEDIATO** (Agora):
1. ✅ Validar testes existentes em `train/test/`
2. ⏳ Implementar testes faltantes (Sprint 4.2)
3. ⏳ Configurar pre-commit hooks (Sprint 4.5)

**CURTO PRAZO** (Próximas 2 semanas):
1. Completar Sprint 4 (testes + linting)
2. Iniciar Sprint 6 (WebUI training page)
3. Implementar endpoints de training

**MÉDIO PRAZO** (Próximo mês):
1. Completar Sprint 5 (docs + CI)
2. Finalizar Sprint 6 (WebUI completa)
3. Iniciar Sprint 7 (features avançadas)

---

**Última atualização**: 2025-12-06  
**Mantido por**: Tech Lead (Claude Sonnet 4.5)  
**Próxima revisão**: Após conclusão de Sprint 4
