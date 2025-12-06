# Plano de Sprints – F5-TTS Project

**Projeto:** Fine-tuning F5-TTS PT-BR - Transformação em Código Profissional  
**Tech Lead:** Engenharia de Software & ML  
**Data Início:** 06 de Dezembro de 2025  
**Versão:** 1.0  
**Total de Sprints:** 8 sprints principais + 1 backlog futuro

---

## Visão Geral

Este plano de sprints foi desenvolvido com base no relatório técnico completo (`MORE.md`) e tem como objetivo transformar o projeto de fine-tuning F5-TTS de um estado "funcionando mas bagunçado" para um código de **nível profissional** com:

- ✅ Configuração unificada e clara
- ✅ Separação de responsabilidades (SOLID)
- ✅ Pipeline de dados modular e testável
- ✅ Reprodutibilidade garantida
- ✅ Experiência de desenvolvedor de alta qualidade
- ✅ Testes automatizados
- ✅ Documentação completa

### Estratégia de Execução

- **Sprints 1-2:** CRÍTICO - Corrigir problemas que causam bugs em produção
- **Sprints 3-4:** ALTA - Refatoração estrutural para manutenibilidade
- **Sprints 5-6:** MÉDIA - Melhorias de DX e produtividade
- **Sprints 7-8:** BAIXA-MÉDIA - Profissionalização e MLOps
- **Backlog Futuro:** Ideias de longo prazo

---

## Sprint 1: Unificação de Configuração e Paths

**Objetivo:** Eliminar fragmentação de configuração e garantir consistência de paths críticos.

**Duração Estimada:** 2-3 dias

**Prioridade:** 🔴 CRÍTICA

### Premissas / Dependências
- Nenhuma (primeiro sprint)
- Requer revisão de todos os arquivos de config existentes

### Entregáveis Principais
1. Configuração unificada em `train/config.yaml`
2. Módulo Python `train/config/loader.py` para carregar e validar config
3. Vocabulário consolidado em um único lugar com validação de hash
4. Documentação de hierarquia de configuração

### Lista de Tarefas

#### S1-T1: Criar Configuração Unificada
- **Categoria:** Config
- **Prioridade:** ALTA
- **Descrição:**
  - Criar `train/config/base_config.yaml` com TODAS as configs (paths, hiperparâmetros, dataset, audio, etc.)
  - Migrar valores de `train/.env`, `train_config.yaml`, `dataset_config.yaml`
  - Definir defaults sensatos
  - Documentar cada seção com comentários
- **Arquivos Afetados:**
  - NOVO: `train/config/base_config.yaml`
  - Referência: `train/.env`, `train/config/train_config.yaml`, `train/config/dataset_config.yaml`
- **Impacto Esperado:** Fonte única de verdade para toda configuração

#### S1-T2: Implementar Config Loader com Validação
- **Categoria:** Código
- **Prioridade:** ALTA
- **Descrição:**
  - Criar `train/config/loader.py`
  - Usar Pydantic para validação de tipos e valores
  - Implementar hierarquia: defaults → base_config.yaml → .env overrides → CLI args
  - Validar paths (existência, permissões)
  - Retornar objeto imutável (frozen dataclass ou Pydantic BaseModel)
- **Arquivos Afetados:**
  - NOVO: `train/config/loader.py`
  - NOVO: `train/config/schemas.py` (Pydantic models)
  - Modificar: `train/utils/env_loader.py` (deprecar ou integrar)
- **Impacto Esperado:** Config validada e type-safe

#### S1-T3: Consolidar Vocabulário com Hash
- **Categoria:** Data Pipeline
- **Prioridade:** ALTA
- **Descrição:**
  - Escolher `train/config/vocab.txt` como source of truth
  - Adicionar comentário no topo com SHA256 hash: `# VOCAB_HASH: sha256:abc123...`
  - Deletar cópias em `train/data/vocab.txt` e `train/data/f5_dataset/vocab.txt`
  - Criar função `train/utils/vocab.py::validate_vocab(path)` que verifica hash
  - Atualizar scripts para copiar/linkar de `train/config/vocab.txt`
- **Arquivos Afetados:**
  - Modificar: `train/config/vocab.txt` (adicionar hash)
  - DELETAR: `train/data/vocab.txt`, `train/data/f5_dataset/vocab.txt`
  - NOVO: `train/utils/vocab.py`
  - Modificar: scripts que usam vocab
- **Impacto Esperado:** Garantia de vocab consistente entre treino e inferência

#### S1-T4: Refatorar run_training.py para Usar Config Unificado
- **Categoria:** Código
- **Prioridade:** ALTA
- **Descrição:**
  - Modificar `train/run_training.py` para importar `train.config.loader`
  - Remover dependência de `env_loader.py`
  - Usar config validado em vez de dict
  - Logar config completa no início do treino (para auditoria)
- **Arquivos Afetados:**
  - Modificar: `train/run_training.py`
- **Impacto Esperado:** Treino usa config unificado

#### S1-T5: Refatorar Scripts de Inferência para Usar Config Unificado
- **Categoria:** Código
- **Prioridade:** MÉDIA
- **Descrição:**
  - Modificar `train/scripts/AgentF5TTSChunk.py`
  - Remover paths hardcoded (linha 180-182)
  - Importar config de `train.config.loader`
- **Arquivos Afetados:**
  - Modificar: `train/scripts/AgentF5TTSChunk.py`
  - Modificar: `train/test.py`
- **Impacto Esperado:** Inferência consistente com treino

#### S1-T6: Documentar Hierarquia de Configuração
- **Categoria:** Docs
- **Prioridade:** BAIXA
- **Descrição:**
  - Criar `train/docs/CONFIGURATION.md`
  - Explicar hierarquia: defaults → base_config.yaml → .env → CLI
  - Exemplos de uso
  - Como adicionar nova config
  - Como fazer override em deploy
- **Arquivos Afetados:**
  - NOVO: `train/docs/CONFIGURATION.md`
- **Impacto Esperado:** DX melhorado, onboarding mais rápido

---

## Sprint 2: Checkpoint Path e Vocoder Consistency

**Objetivo:** Garantir que fine-tuning seja usado em produção e que vocoder seja consistente.

**Duração Estimada:** 2 dias

**Prioridade:** 🔴 CRÍTICA

### Premissas / Dependências
- Sprint 1 concluído (config unificado disponível)

### Entregáveis Principais
1. Função utilitária para resolver checkpoint path
2. API de inferência (`f5tts_engine.py`) respeitando checkpoint customizado
3. Validação de checkpoint antes de carregar
4. Documentação de formato de checkpoint

### Lista de Tarefas

#### S2-T1: Criar Função Utilitária para Resolver Checkpoint Path
- **Categoria:** Código
- **Prioridade:** ALTA
- **Descrição:**
  - Criar `train/utils/checkpoint.py::resolve_checkpoint_path(config)`
  - Lógica de prioridade:
    1. `config.custom_checkpoint_path` (se arquivo existir)
    2. `train/output/{exp_name}/model_best.pt` (se existir)
    3. `train/output/{exp_name}/model_last.pt` (se existir)
    4. Download de HuggingFace (fallback)
  - Validar tamanho mínimo (> 1GB para detectar corrompidos)
  - Logar decisão claramente
- **Arquivos Afetados:**
  - NOVO: `train/utils/checkpoint.py`
- **Impacto Esperado:** Checkpoint resolution consistente

#### S2-T2: Adicionar Validação de Checkpoint
- **Categoria:** Código
- **Prioridade:** ALTA
- **Descrição:**
  - Em `train/utils/checkpoint.py`, adicionar `validate_checkpoint(path)`
  - Verificar: pode carregar com torch.load, tamanho > 1GB, tem keys esperadas
  - Se corrompido, renomear para `.corrupted` e tentar próximo
  - Retornar info: `CheckpointInfo(path, size, num_keys, metadata)`
- **Arquivos Afetados:**
  - Modificar: `train/utils/checkpoint.py`
- **Impacto Esperado:** Previne uso de checkpoints corrompidos

#### S2-T3: Refatorar f5tts_engine.py para Respeitar Custom Checkpoint
- **Categoria:** Código
- **Prioridade:** ALTA
- **Descrição:**
  - Modificar `app/engines/f5tts_engine.py::__init__()`
  - Importar `train.utils.checkpoint.resolve_checkpoint_path`
  - Usar checkpoint customizado se `F5TTS_CUSTOM_CHECKPOINT` estiver no .env
  - Remover lógica de patch inline (mover para script separado se necessário)
  - Logar qual checkpoint foi carregado
- **Arquivos Afetados:**
  - Modificar: `app/engines/f5tts_engine.py` (linhas 100-250)
- **Impacto Esperado:** Fine-tuning usado em produção

#### S2-T4: Adicionar Metadata ao Checkpoint
- **Categoria:** Código
- **Prioridade:** MÉDIA
- **Descrição:**
  - Modificar `train/run_training.py` para salvar `model_last.metadata.json` junto com checkpoint
  - Metadata: timestamp, git_commit, config completa, vocab_hash, dataset info, metrics finais
  - Validar ao carregar: se metadata existir, logar informações
- **Arquivos Afetados:**
  - Modificar: `train/run_training.py` (após salvar checkpoint)
  - NOVO: `train/utils/checkpoint.py::save_checkpoint_metadata()`
- **Impacto Esperado:** Rastreabilidade de checkpoints

#### S2-T5: Documentar Formato de Checkpoint
- **Categoria:** Docs
- **Prioridade:** BAIXA
- **Descrição:**
  - Criar `train/docs/CHECKPOINT_FORMAT.md`
  - Explicar estrutura esperada de checkpoint (keys, prefixes, metadata)
  - Como patch é aplicado (se necessário)
  - Como validar checkpoint manualmente
- **Arquivos Afetados:**
  - NOVO: `train/docs/CHECKPOINT_FORMAT.md`
- **Impacto Esperado:** Debugging facilitado

---

## Sprint 3: Refatoração de Pipeline de Dados - Módulos

**Objetivo:** Separar pipeline de dados monolítico em módulos reutilizáveis e testáveis.

**Duração Estimada:** 4-5 dias

**Prioridade:** ⚠️ ALTA

### Premissas / Dependências
- Sprint 1 concluído (config unificado)
- Scripts atuais funcionando (não quebrar funcionalidade)

### Entregáveis Principais
1. Módulos organizados: `train/audio/`, `train/text/`, `train/io/`
2. Funções puras sem efeitos colaterais (sem I/O direto)
3. Scripts principais virando "orquestradores" finos
4. Testes unitários para cada módulo

### Lista de Tarefas

#### S3-T1: Criar Módulo train/audio/ com VAD e Segmentação
- **Categoria:** Código - Arquitetura
- **Prioridade:** ALTA
- **Descrição:**
  - Criar estrutura:
    ```
    train/audio/
      __init__.py
      vad.py           # Voice Activity Detection
      segmentation.py  # Audio segmentation
      normalization.py # Loudness normalization
      effects.py       # Fade, filters
      io.py            # Load/save audio
    ```
  - Extrair código de `prepare_segments_optimized.py`:
    - `vad.py::detect_voice_regions(audio, params)` (linhas 90-150)
    - `segmentation.py::segment_audio(audio, voice_regions, params)` (linhas 200-300)
    - `normalization.py::normalize_loudness(audio, target_lufs)` (linhas 350-400)
    - `effects.py::apply_fade(audio, fade_ms)`
  - Funções puras: recebem np.ndarray, retornam np.ndarray ou List
- **Arquivos Afetados:**
  - NOVO: `train/audio/__init__.py`, `vad.py`, `segmentation.py`, `normalization.py`, `effects.py`, `io.py`
  - Referência: `train/scripts/prepare_segments_optimized.py`
- **Impacto Esperado:** Código modular e testável

#### S3-T2: Criar Módulo train/text/ com Normalização e QA
- **Categoria:** Código - Arquitetura
- **Prioridade:** ALTA
- **Descrição:**
  - Criar estrutura:
    ```
    train/text/
      __init__.py
      normalizer.py  # Já existe! Apenas mover
      qa.py          # Quality assurance
      vocab.py       # Moved from utils
    ```
  - Mover `train/utils/text_normalizer.py` → `train/text/normalizer.py`
  - Extrair de `transcribe_or_subtitles.py`:
    - `qa.py::check_text_quality(text, vocab)` (verifica OOV, etc.)
  - Mover `train/utils/vocab.py` (criado em S1-T3) → `train/text/vocab.py`
- **Arquivos Afetados:**
  - MOVER: `train/utils/text_normalizer.py` → `train/text/normalizer.py`
  - NOVO: `train/text/qa.py`
  - MOVER: `train/utils/vocab.py` → `train/text/vocab.py`
- **Impacto Esperado:** Texto processing organizado

#### S3-T3: Criar Módulo train/io/ para YouTube e Legendas
- **Categoria:** Código - Arquitetura
- **Prioridade:** MÉDIA
- **Descrição:**
  - Criar estrutura:
    ```
    train/io/
      __init__.py
      youtube.py      # Download YouTube
      subtitles.py    # Extract subtitles
      storage.py      # File operations
    ```
  - Extrair de `download_youtube.py` e `transcribe_or_subtitles.py`:
    - `youtube.py::download_audio(url, output_path, config)`
    - `subtitles.py::download_subtitles(url, output_path, config)`
- **Arquivos Afetados:**
  - NOVO: `train/io/__init__.py`, `youtube.py`, `subtitles.py`, `storage.py`
  - Referência: `train/scripts/download_youtube.py`, `train/scripts/transcribe_or_subtitles.py`
- **Impacto Esperado:** I/O separado de lógica

#### S3-T4: Refatorar prepare_segments_optimized.py em Orquestrador
- **Categoria:** Código - Refatoração
- **Prioridade:** ALTA
- **Descrição:**
  - Reduzir `prepare_segments_optimized.py` de 570 linhas para ~100 linhas
  - Importar de `train.audio` e `train.io`
  - Função main vira:
    ```python
    def main():
        config = load_config()
        for audio_path in get_audio_files():
            audio = audio_io.load(audio_path)
            voice_regions = vad.detect_voice_regions(audio, config.vad)
            segments = segmentation.segment_audio(audio, voice_regions, config.segment)
            normalized = [normalization.normalize(s, config.audio) for s in segments]
            audio_io.save_all(normalized, output_dir)
    ```
- **Arquivos Afetados:**
  - Modificar: `train/scripts/prepare_segments_optimized.py`
- **Impacto Esperado:** Script limpo, fácil de entender

#### S3-T5: Refatorar transcribe_or_subtitles.py em Orquestrador
- **Categoria:** Código - Refatoração
- **Prioridade:** MÉDIA
- **Descrição:**
  - Reduzir de 756 linhas para ~150 linhas
  - Importar de `train.text` e `train.io`
  - Separar lógica de Whisper em `train/audio/transcription.py`
- **Arquivos Afetados:**
  - Modificar: `train/scripts/transcribe_or_subtitles.py`
  - NOVO: `train/audio/transcription.py`
- **Impacto Esperado:** Código modular

#### S3-T6: Adicionar Testes Unitários para Módulos
- **Categoria:** Testes
- **Prioridade:** MÉDIA
- **Descrição:**
  - Criar `tests/train/audio/` com testes para cada módulo
  - Fixtures: áudio sintético (1s de silence, 1s de noise, 1s de speech simulado)
  - Testes:
    - `test_vad.py::test_detect_voice_in_silence()` → deve retornar []
    - `test_segmentation.py::test_segment_audio()` → deve retornar N segmentos
    - `test_normalization.py::test_normalize_loudness()` → verificar LUFS alvo
  - Coverage > 80%
- **Arquivos Afetados:**
  - NOVO: `tests/train/audio/test_vad.py`, `test_segmentation.py`, etc.
  - NOVO: `tests/fixtures/audio_samples.py` (synthetic audio generator)
- **Impacto Esperado:** Confiança em refatorar

---

## Sprint 4: Reprodutibilidade e MLOps Básico

**Objetivo:** Garantir experimentos reproduzíveis e adicionar versionamento de dependências.

**Duração Estimada:** 3 dias

**Prioridade:** ⚠️ ALTA

### Premissas / Dependências
- Sprint 1 concluído (config unificado)

### Entregáveis Principais
1. Dependências pinadas (`requirements-lock.txt`)
2. Seed aplicado globalmente
3. Registro básico de experimentos (sem MLflow ainda)
4. Scripts de setup automatizado

### Lista de Tarefas

#### S4-T1: Pinar Dependências com Versões Exatas
- **Categoria:** MLOps
- **Prioridade:** ALTA
- **Descrição:**
  - Gerar `requirements-lock.txt` com `pip freeze`
  - Separar:
    - `requirements-lock.txt` (ambiente base + API)
    - `train/requirements-train-lock.txt` (treino)
  - Atualizar CI/CD para usar `-lock.txt`
  - Documentar processo de atualização de deps
- **Arquivos Afetados:**
  - NOVO: `requirements-lock.txt`
  - NOVO: `train/requirements-train-lock.txt`
  - Modificar: `.github/workflows/*.yml` (se existir CI)
- **Impacto Esperado:** Reprodutibilidade garantida

#### S4-T2: Implementar Seed Global para Reprodutibilidade
- **Categoria:** Código - MLOps
- **Prioridade:** ALTA
- **Descrição:**
  - Criar `train/utils/reproducibility.py::set_seed(seed, deterministic=True)`
  - Implementar:
    ```python
    import torch, numpy as np, random
    def set_seed(seed, deterministic=True):
        torch.manual_seed(seed)
        torch.cuda.manual_seed_all(seed)
        np.random.seed(seed)
        random.seed(seed)
        if deterministic:
            torch.backends.cudnn.deterministic = True
            torch.backends.cudnn.benchmark = False
    ```
  - Chamar no início de `run_training.py`, `test.py`, scripts de inferência
  - Logar warning se deterministic=True (pode ser 10% mais lento)
- **Arquivos Afetados:**
  - NOVO: `train/utils/reproducibility.py`
  - Modificar: `train/run_training.py`, `train/test.py`
- **Impacto Esperado:** Experimentos reproduzíveis

#### S4-T3: Criar experiment.json com Metadata de Treino
- **Categoria:** MLOps
- **Prioridade:** MÉDIA
- **Descrição:**
  - Modificar `run_training.py` para salvar `train/output/{exp_name}/experiment.json`
  - Conteúdo:
    ```json
    {
      "timestamp": "2025-12-06T10:00:00Z",
      "git_commit": "abc123",
      "config": {...},  // config completa
      "vocab_hash": "sha256:...",
      "dataset": {
        "path": "...",
        "num_samples": 5000,
        "total_duration_hours": 10.5
      },
      "dependencies": {
        "torch": "2.1.0",
        "f5-tts": "1.1.9"
      },
      "hardware": {
        "gpu": "Tesla V100",
        "cuda": "11.8"
      }
    }
    ```
  - Útil para reproduzir experimento depois
- **Arquivos Afetados:**
  - Modificar: `train/run_training.py`
  - NOVO: `train/utils/experiment.py::save_experiment_metadata()`
- **Impacto Esperado:** Rastreabilidade de experimentos

#### S4-T4: Criar Script de Setup Automatizado
- **Categoria:** DevOps
- **Prioridade:** MÉDIA
- **Descrição:**
  - Criar `Makefile` na raiz:
    ```makefile
    setup:
        python3.11 -m venv .venv
        .venv/bin/pip install -r requirements-lock.txt
        .venv/bin/pip install -r train/requirements-train-lock.txt
        mkdir -p train/{data,output,runs,logs}
        @echo "✅ Setup completo! Ative o venv: source .venv/bin/activate"
    
    validate:
        .venv/bin/python -m train.scripts.validate_setup
    
    test:
        .venv/bin/pytest tests/
    ```
  - Atualizar README com instruções: `make setup`
- **Arquivos Afetados:**
  - NOVO: `Makefile`
  - Modificar: `README.md`
- **Impacto Esperado:** Onboarding em 1 comando

#### S4-T5: Criar Health Check Script
- **Categoria:** DevOps
- **Prioridade:** BAIXA
- **Descrição:**
  - Criar `train/scripts/health_check.py`
  - Validações:
    - CUDA disponível e GPU detectada
    - Dataset path existe e tem samples
    - Vocab.txt hash válido
    - Disk space > 10GB
    - RAM > 8GB (warning se < 16GB)
  - Output colorido (emoji)
- **Arquivos Afetados:**
  - NOVO: `train/scripts/health_check.py`
- **Impacto Esperado:** Validação antes de treinar

---

## Sprint 5: Experiência de Treino Melhorada

**Objetivo:** Adicionar callbacks, métricas avançadas e CLI amigável.

**Duração Estimada:** 3-4 dias

**Prioridade:** 📊 MÉDIA

### Premissas / Dependências
- Sprint 2 concluído (checkpoint utils)
- Sprint 3 concluído (módulos organizados)

### Entregáveis Principais
1. Callbacks customizados (best model, audio samples)
2. Métricas além de loss (MCD, duração)
3. CLI com argumentos validados (typer)
4. Logs estruturados (JSON)

### Lista de Tarefas

#### S5-T1: Implementar Callback para Salvar Best Model
- **Categoria:** Código - Treino
- **Prioridade:** ALTA
- **Descrição:**
  - Criar `train/training/callbacks.py::BestModelCallback`
  - Rastrear melhor val_loss (ou metric escolhida)
  - Salvar `model_best.pt` quando métrica melhora
  - Integrar em `run_training.py` (se F5-TTS CLI suportar callbacks)
  - Alternativa: monitorar logs e copiar checkpoint manualmente
- **Arquivos Afetados:**
  - NOVO: `train/training/callbacks.py`
  - Modificar: `train/run_training.py`
- **Impacto Esperado:** Checkpoint best disponível

#### S5-T2: Adicionar Callback para Gerar Audio Samples
- **Categoria:** Código - Treino
- **Prioridade:** MÉDIA
- **Descrição:**
  - Em `train/training/callbacks.py::AudioSampleCallback`
  - A cada N epochs, gerar sample de áudio com texto fixo
  - Salvar em `train/output/{exp_name}/samples/sample_epoch_{n}.wav`
  - Logar no TensorBoard (se possível)
- **Arquivos Afetados:**
  - Modificar: `train/training/callbacks.py`
- **Impacto Esperado:** Validação auditiva durante treino

#### S5-T3: Adicionar Métricas Avançadas (MCD)
- **Categoria:** Código - Treino
- **Prioridade:** BAIXA
- **Descrição:**
  - Calcular MCD (Mel Cepstral Distortion) entre samples gerados e referência
  - Usar biblioteca `pymcd` ou implementar manualmente
  - Logar no TensorBoard como scalar
  - Opcional: MOS estimado (usar modelo pré-treinado)
- **Arquivos Afetados:**
  - Modificar: `train/run_training.py` ou callbacks
  - NOVO: `train/training/metrics.py`
- **Impacto Esperado:** Visibilidade de qualidade

#### S5-T4: Criar CLI Amigável com Typer
- **Categoria:** Código - DX
- **Prioridade:** MÉDIA
- **Descrição:**
  - Refatorar `train/run_training.py` para usar `typer`
  - Argumentos:
    ```bash
    python -m train.run_training \
      --config train/config/base_config.yaml \
      --learning-rate 0.0002 \
      --epochs 100 \
      --batch-size 8 \
      --exp-name my_experiment
    ```
  - Validar argumentos (typer faz isso automaticamente)
  - Help text detalhado
- **Arquivos Afetados:**
  - Modificar: `train/run_training.py`
  - NOVO: `train/requirements-train-lock.txt` (adicionar typer)
- **Impacto Esperado:** CLI amigável

#### S5-T5: Implementar Structured Logging com Loguru
- **Categoria:** Código - Infra
- **Prioridade:** BAIXA
- **Descrição:**
  - Substituir `logging` por `loguru`
  - Configurar para logar em JSON:
    ```python
    logger.add("train/logs/train.json", format="{time} {level} {message}", serialize=True)
    ```
  - Adicionar contexto estruturado:
    ```python
    logger.info("Epoch completed", epoch=10, loss=0.123, lr=0.0001)
    ```
  - Facilita parsing com `jq` ou ferramentas de log
- **Arquivos Afetados:**
  - Modificar: todos os scripts em `train/`
  - NOVO: `train/utils/logging.py::setup_logger()`
- **Impacto Esperado:** Logs estruturados, fácil análise

---

## Sprint 6: Experiência de Inferência e API Unificada

**Objetivo:** Criar interface consistente para inferência e CLI de teste rápido.

**Duração Estimada:** 3 dias

**Prioridade:** 📊 MÉDIA

### Premissas / Dependências
- Sprint 1 concluído (config unificado)
- Sprint 2 concluído (checkpoint resolution)

### Entregáveis Principais
1. API unificada `F5TTSInference` usada por API REST e scripts
2. CLI de teste rápido `train.infer`
3. Service layer com cache de modelo
4. Documentação de uso

### Lista de Tarefas

#### S6-T1: Criar API Unificada F5TTSInference
- **Categoria:** Código - Arquitetura
- **Prioridade:** ALTA
- **Descrição:**
  - Criar `train/inference/api.py::F5TTSInference`
  - Interface:
    ```python
    class F5TTSInference:
        def __init__(self, checkpoint_path, vocab_file, device, config):
            ...
        
        def generate(
            self,
            text: str,
            ref_audio: Path,
            ref_text: str = "",
            nfe_step: int = 32
        ) -> np.ndarray:
            ...
    ```
  - Implementação deve encapsular `F5TTS` da lib
  - Usado por: API REST, scripts, CLI
- **Arquivos Afetados:**
  - NOVO: `train/inference/__init__.py`, `api.py`
- **Impacto Esperado:** Interface consistente

#### S6-T2: Refatorar f5tts_engine.py para Usar API Unificada
- **Categoria:** Código - Refatoração
- **Prioridade:** ALTA
- **Descrição:**
  - Modificar `app/engines/f5tts_engine.py`
  - Remover lógica duplicada
  - Importar `train.inference.F5TTSInference`
  - Delegar geração de áudio para API unificada
- **Arquivos Afetados:**
  - Modificar: `app/engines/f5tts_engine.py`
- **Impacto Esperado:** Menos duplicação

#### S6-T3: Refatorar AgentF5TTSChunk.py para Usar API Unificada
- **Categoria:** Código - Refatoração
- **Prioridade:** MÉDIA
- **Descrição:**
  - Modificar `train/scripts/AgentF5TTSChunk.py`
  - Importar `train.inference.F5TTSInference`
  - Simplificar lógica (remover wrapper redundante)
- **Arquivos Afetados:**
  - Modificar: `train/scripts/AgentF5TTSChunk.py`
- **Impacto Esperado:** Código limpo

#### S6-T4: Criar CLI de Teste Rápido
- **Categoria:** Código - DX
- **Prioridade:** MÉDIA
- **Descrição:**
  - Criar `train/cli/infer.py`
  - Uso:
    ```bash
    python -m train.cli.infer \
      --checkpoint train/output/model_last.pt \
      --text "Olá, mundo!" \
      --ref-audio ref.wav \
      --output output.wav \
      --nfe-step 32
    ```
  - Usar typer para CLI
  - Logar tempo de geração, RTF
- **Arquivos Afetados:**
  - NOVO: `train/cli/__init__.py`, `infer.py`
- **Impacto Esperado:** Teste rápido pós-treino

#### S6-T5: Implementar Service Layer com Cache
- **Categoria:** Código - Otimização
- **Prioridade:** BAIXA
- **Descrição:**
  - Criar `train/inference/service.py::F5TTSService` (Singleton)
  - Cachear modelo carregado em memória
  - Lazy load: só carrega quando necessário
  - Unload após timeout (opcional)
- **Arquivos Afetados:**
  - NOVO: `train/inference/service.py`
- **Impacto Esperado:** Inferência mais rápida

#### S6-T6: Documentar API de Inferência
- **Categoria:** Docs
- **Prioridade:** BAIXA
- **Descrição:**
  - Criar `train/docs/INFERENCE_API.md`
  - Exemplos de uso
  - Parâmetros disponíveis
  - Troubleshooting
- **Arquivos Afetados:**
  - NOVO: `train/docs/INFERENCE_API.md`
- **Impacto Esperado:** DX melhorado

---

## Sprint 7: Qualidade de Código e Testes

**Objetivo:** Adicionar linting, formatação, type checking e testes automatizados.

**Duração Estimada:** 4 dias

**Prioridade:** 📝 BAIXA-MÉDIA

### Premissas / Dependências
- Sprint 3 concluído (módulos organizados, facilitando testes)

### Entregáveis Principais
1. Linting e formatação configurados (ruff, black)
2. Type checking com mypy
3. Pre-commit hooks
4. Testes unitários com >70% coverage
5. Teste de integração end-to-end

### Lista de Tarefas

#### S7-T1: Configurar Linting com Ruff
- **Categoria:** Qualidade de Código
- **Prioridade:** MÉDIA
- **Descrição:**
  - Criar `pyproject.toml` com config do ruff
  - Regras: E (pycodestyle), F (pyflakes), I (isort), N (naming)
  - Rodar `ruff check train/` e corrigir warnings críticos
  - Adicionar ao Makefile: `make lint`
- **Arquivos Afetados:**
  - NOVO: `pyproject.toml`
  - Modificar: `Makefile`
- **Impacto Esperado:** Código consistente

#### S7-T2: Configurar Formatação com Black
- **Categoria:** Qualidade de Código
- **Prioridade:** MÉDIA
- **Descrição:**
  - Configurar black no `pyproject.toml`
  - Line length: 100
  - Rodar `black train/`
  - Adicionar ao Makefile: `make format`
- **Arquivos Afetados:**
  - Modificar: `pyproject.toml`
  - Modificar: `Makefile`
- **Impacto Esperado:** Formatação automática

#### S7-T3: Adicionar Type Hints e Mypy
- **Categoria:** Qualidade de Código
- **Prioridade:** MÉDIA
- **Descrição:**
  - Adicionar type hints em funções públicas de módulos críticos (train/audio/, train/text/)
  - Configurar mypy no `pyproject.toml`
  - Rodar `mypy train/ --strict` (ou --ignore-missing-imports para começar)
  - Corrigir erros críticos
  - Adicionar ao Makefile: `make typecheck`
- **Arquivos Afetados:**
  - Modificar: `pyproject.toml`, `Makefile`
  - Modificar: funções em `train/audio/`, `train/text/`, etc.
- **Impacto Esperado:** Type safety

#### S7-T4: Configurar Pre-commit Hooks
- **Categoria:** DevOps
- **Prioridade:** BAIXA
- **Descrição:**
  - Criar `.pre-commit-config.yaml`
  - Hooks: black, ruff, mypy (opcional)
  - Instalar: `pre-commit install`
  - Testar: `pre-commit run --all-files`
- **Arquivos Afetados:**
  - NOVO: `.pre-commit-config.yaml`
- **Impacto Esperado:** Qualidade garantida antes de commit

#### S7-T5: Adicionar Testes Unitários (continuação de S3-T6)
- **Categoria:** Testes
- **Prioridade:** ALTA
- **Descrição:**
  - Expandir testes de S3-T6
  - Coverage > 70% em módulos críticos (audio, text, config)
  - Usar pytest com fixtures
  - Adicionar ao Makefile: `make test`, `make coverage`
- **Arquivos Afetados:**
  - Expandir: `tests/train/`
  - NOVO: `tests/train/text/`, `tests/train/config/`, etc.
- **Impacto Esperado:** Confiança em mudanças

#### S7-T6: Criar Teste de Integração End-to-End
- **Categoria:** Testes
- **Prioridade:** MÉDIA
- **Descrição:**
  - Criar `tests/train/test_e2e_pipeline.py`
  - Fluxo completo com dataset pequeno (5 samples):
    1. Download fake audio (synthetic ou fixture)
    2. Segment
    3. Transcribe (mock Whisper)
    4. Normalize
    5. Build dataset
    6. Train (1 epoch, batch_size=1)
    7. Infer
  - Validar: checkpoint gerado, sample de áudio criado
  - Tempo: ~2min
- **Arquivos Afetados:**
  - NOVO: `tests/train/test_e2e_pipeline.py`
  - NOVO: `tests/fixtures/mini_dataset/` (5 samples)
- **Impacto Esperado:** Smoke test completo

---

## Sprint 8: Documentação Completa e MLOps Avançado

**Objetivo:** Profissionalizar projeto com docs completas, MLflow e Docker para treino.

**Duração Estimada:** 3-4 dias

**Prioridade:** 📝 BAIXA-MÉDIA

### Premissas / Dependências
- Todas as sprints anteriores concluídas (código estável)

### Entregáveis Principais
1. Documentação completa (README, tutoriais, API docs)
2. MLflow integrado (opcional)
3. Docker para treino (opcional)
4. Scripts de exemplo

### Lista de Tarefas

#### S8-T1: Reorganizar e Completar READMEs
- **Categoria:** Docs
- **Prioridade:** ALTA
- **Descrição:**
  - Atualizar `README.md` raiz com seção "Training" linkando para `train/README.md`
  - Criar README por pasta:
    - `train/scripts/README.md`: lista scripts e uso
    - `train/audio/README.md`: descreve módulos de áudio
    - `train/text/README.md`: descreve processamento de texto
  - Criar `train/docs/INDEX.md` listando todos os docs
- **Arquivos Afetados:**
  - Modificar: `README.md`
  - NOVO: `train/scripts/README.md`, `train/audio/README.md`, etc.
  - NOVO: `train/docs/INDEX.md`
- **Impacto Esperado:** Navegação fácil

#### S8-T2: Criar Tutorial Passo-a-Passo
- **Categoria:** Docs
- **Prioridade:** ALTA
- **Descrição:**
  - Criar `train/docs/TUTORIAL.md`
  - Seções:
    1. Setup do ambiente (make setup)
    2. Preparar dataset (passo-a-passo)
    3. Configurar treino (editar config.yaml)
    4. Iniciar treino (python -m train.run_training)
    5. Monitorar (TensorBoard)
    6. Testar checkpoint (python -m train.cli.infer)
    7. Deploy (copiar checkpoint para API)
  - Screenshots (ou ASCII art) se possível
- **Arquivos Afetados:**
  - NOVO: `train/docs/TUTORIAL.md`
- **Impacto Esperado:** Onboarding guiado

#### S8-T3: Criar Scripts de Exemplo
- **Categoria:** Docs + Código
- **Prioridade:** MÉDIA
- **Descrição:**
  - Criar `train/examples/`
  - Scripts:
    - `01_quick_train.py`: treino mínimo (1 epoch)
    - `02_inference_simple.py`: inferência básica
    - `03_custom_dataset.py`: como criar dataset do zero
    - `04_resume_training.py`: continuar de checkpoint
  - Cada script com comentários explicativos
- **Arquivos Afetados:**
  - NOVO: `train/examples/*.py`
- **Impacto Esperado:** Exemplos práticos

#### S8-T4: Integrar MLflow (Opcional)
- **Categoria:** MLOps
- **Prioridade:** BAIXA
- **Descrição:**
  - Instalar MLflow: `pip install mlflow`
  - Modificar `run_training.py` para logar experimentos:
    ```python
    import mlflow
    with mlflow.start_run():
        mlflow.log_params(config)
        mlflow.log_metrics({"loss": loss})
        mlflow.log_artifact("model_last.pt")
    ```
  - Rodar UI: `mlflow ui --port 5000`
  - Documentar em `train/docs/MLFLOW.md`
- **Arquivos Afetados:**
  - Modificar: `train/run_training.py`
  - NOVO: `train/docs/MLFLOW.md`
- **Impacto Esperado:** Tracking de experimentos

#### S8-T5: Criar Dockerfile para Treino (Opcional)
- **Categoria:** DevOps
- **Prioridade:** BAIXA
- **Descrição:**
  - Criar `docker/train/Dockerfile`
  - Base: `pytorch/pytorch:2.1.0-cuda11.8-cudnn8`
  - Instalar requirements-lock.txt
  - Copiar código
  - Entrypoint: `python -m train.run_training`
  - Build: `docker build -t f5tts-train docker/train/`
  - Run: `docker run --gpus all -v $(pwd)/train:/app/train f5tts-train`
- **Arquivos Afetados:**
  - NOVO: `docker/train/Dockerfile`
  - NOVO: `docker/train/.dockerignore`
- **Impacto Esperado:** Ambiente reproduzível

#### S8-T6: Criar Script de Benchmark (Opcional)
- **Categoria:** MLOps
- **Prioridade:** BAIXA
- **Descrição:**
  - Criar `train/scripts/benchmark.py`
  - Comparar checkpoints:
    ```bash
    python -m train.scripts.benchmark \
      --checkpoints model_epoch10.pt model_epoch50.pt \
      --test-texts test_samples.txt
    ```
  - Métricas: MCD, RTF, MOS estimado
  - Output: tabela Markdown
- **Arquivos Afetados:**
  - NOVO: `train/scripts/benchmark.py`
- **Impacto Esperado:** Comparação objetiva

---

## Backlog Futuro / Ideias Extras

### Melhorias de Longo Prazo (não incluídas nas 8 sprints)

#### BL-1: Avaliação Automática de MOS
- **Descrição:** Usar modelo pré-treinado (ex: MOSNet) para estimar MOS de samples gerados
- **Benefício:** Métrica de qualidade objetiva
- **Esforço:** 2-3 dias

#### BL-2: UI Mínima para Visualização de Treino
- **Descrição:** Dashboard web (Streamlit ou Gradio) para visualizar métricas, samples, config
- **Benefício:** UX melhor que TensorBoard
- **Esforço:** 3-4 dias

#### BL-3: Suporte Multi-línguas no Pipeline
- **Descrição:** Adaptar scripts de normalização e transcrição para outras línguas (EN, ES)
- **Benefício:** Reuso do pipeline
- **Esforço:** 2-3 dias

#### BL-4: Dataset Augmentation
- **Descrição:** Adicionar pitch shift, time stretch, noise injection para aumentar dataset
- **Benefício:** Modelo mais robusto
- **Esforço:** 2 dias

#### BL-5: Distributed Training (Multi-GPU)
- **Descrição:** Usar `accelerate` ou `torch.distributed` para treino multi-GPU
- **Benefício:** Treino mais rápido
- **Esforço:** 3-4 dias

#### BL-6: Continuous Integration (CI/CD)
- **Descrição:** GitHub Actions para rodar testes, linting, build Docker em cada push
- **Benefício:** Qualidade garantida
- **Esforço:** 1-2 dias

#### BL-7: Versionamento de Datasets com DVC
- **Descrição:** Usar DVC para versionar datasets e checkpoints
- **Benefício:** Reprodutibilidade total
- **Esforço:** 2 dias

#### BL-8: Notebook Interativo (Jupyter)
- **Descrição:** Criar notebook `train/notebooks/training_demo.ipynb` com exemplos interativos
- **Benefício:** Exploração fácil
- **Esforço:** 1 dia

#### BL-9: Otimização de Hiperparâmetros (Optuna)
- **Descrição:** Usar Optuna para buscar hiperparâmetros ótimos (learning rate, batch size, etc.)
- **Benefício:** Melhor modelo
- **Esforço:** 3-4 dias

#### BL-10: API REST para Treino Remoto
- **Descrição:** Endpoint `/api/train` para iniciar treino remotamente, monitorar via WebSocket
- **Benefício:** Treino como serviço
- **Esforço:** 4-5 dias

---

## Resumo de Estimativas

| Sprint | Foco                                | Duração | Prioridade |
|--------|-------------------------------------|---------|------------|
| 1      | Unificação de Configuração          | 2-3d    | 🔴 CRÍTICA |
| 2      | Checkpoint Path Consistency         | 2d      | 🔴 CRÍTICA |
| 3      | Refatoração Pipeline de Dados       | 4-5d    | ⚠️ ALTA    |
| 4      | Reprodutibilidade e MLOps Básico    | 3d      | ⚠️ ALTA    |
| 5      | Experiência de Treino               | 3-4d    | 📊 MÉDIA   |
| 6      | Experiência de Inferência           | 3d      | 📊 MÉDIA   |
| 7      | Qualidade de Código e Testes        | 4d      | 📝 BAIXA-M |
| 8      | Documentação e MLOps Avançado       | 3-4d    | 📝 BAIXA-M |
| **TOTAL** | **8 Sprints**                    | **24-30 dias** | - |

**Observação:** Estimativas são para 1 desenvolvedor full-time. Com 2+ devs trabalhando em paralelo (sprints independentes), tempo total pode reduzir para ~15-20 dias.

---

## Critérios de Aceitação por Sprint

### Sprint 1
- [ ] `train/config/base_config.yaml` criado e completo
- [ ] `train/config/loader.py` com validação Pydantic funcionando
- [ ] Vocabulário consolidado em 1 lugar com hash
- [ ] `run_training.py` usando config unificado
- [ ] CI verde (se existir)

### Sprint 2
- [ ] `train/utils/checkpoint.py::resolve_checkpoint_path()` funcionando
- [ ] `f5tts_engine.py` respeitando `F5TTS_CUSTOM_CHECKPOINT`
- [ ] Checkpoints validados antes de carregar
- [ ] `experiment.json` gerado após treino

### Sprint 3 ✅ COMPLETO
- [x] Módulos `train/audio/`, `train/text/`, `train/io/` criados
- [x] Scripts reduzidos para <150 linhas (orquestradores)
- [x] Testes unitários com >70% coverage em módulos críticos

### Sprint 4 ✅ COMPLETO
- [x] `requirements-lock.txt` gerado
- [x] Seed aplicado globalmente em treino e inferência
- [x] `make setup` funcionando
- [x] Health check script validando setup

### Sprint 5 ✅ COMPLETO
- [x] Callbacks de best model e audio samples funcionando
- [x] CLI com typer aceita argumentos
- [x] Logs estruturados em JSON

### Sprint 6 ✅ COMPLETO
- [x] `F5TTSInference` API unificada funcionando
- [x] API REST e scripts usando mesma implementação
- [x] CLI `train.cli.infer` funcionando

### Sprint 7 ✅ COMPLETO
- [x] Linting (ruff) e formatação (black) configurados
- [x] Mypy passando (ou com --ignore-missing-imports)
- [x] Pre-commit hooks instalados
- [x] Teste e2e passando

### Sprint 8 ✅ COMPLETO
- [x] READMEs atualizados
- [x] Tutorial completo em `train/docs/TUTORIAL.md`
- [x] Scripts de exemplo funcionando
- [x] (Opcional) MLflow integrado - NÃO IMPLEMENTADO (opcional)

---

**Fim do Plano de Sprints**
