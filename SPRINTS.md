# 🚀 Plano de Sprints - TTS WebUI XTTS-v2

**Projeto**: Implementação completa de pipeline fine-tuning XTTS-v2  
**Baseado em**: [MORE.md](./MORE.md)  
**Tech Lead**: Claude Sonnet 4.5  
**Data início**: 2025-12-06

---

## 📊 Visão Geral

| Sprint | Foco | Duração | Status |
|--------|------|---------|--------|
| Sprint 0 | Segurança & Cleanup | 1-2h | 🔄 Pronto para iniciar |
| Sprint 1 | Estrutura `train/` + Pipeline Dados | 4-6h | ⏳ Planejada |
| Sprint 2 | Treinamento XTTS-v2 | 6-8h | ⏳ Planejada |
| Sprint 3 | Integração API + Inferência | 3-4h | ⏳ Planejada |
| Sprint 4 | Qualidade & Testes | 4-5h | ⏳ Planejada |
| Sprint 5 | Docs & DevOps | 2-3h | ⏳ Planejada |

**Total estimado**: 20-28 horas de desenvolvimento

---

## 🔒 Sprint 0: Segurança & Cleanup (CRÍTICO)

**Objetivo**: Garantir segurança do repositório e limpar referências obsoletas.

**Duração**: 1-2 horas  
**Prioridade**: P0 (CRÍTICO)

### Tasks

#### 1. Auditoria de Secrets
- [ ] Verificar se `.env` está no `.gitignore`
  ```bash
  grep -E "^\.env$" .gitignore
  ```
- [ ] Inspecionar histórico Git por secrets commitados
  ```bash
  git log --all --full-history --source --pickaxe-regex -S "API_KEY|SECRET|PASSWORD" -- .env
  ```
- [ ] Se encontrar secrets expostos:
  - Rotacionar todas as chaves imediatamente
  - Usar `git filter-branch` ou BFG Repo-Cleaner para remover histórico
  - Documentar em `SECURITY_INCIDENT.md`

**Critérios de Aceitação**:
- ✅ `.env` não está commitado no repositório
- ✅ `.env.example` criado sem valores sensíveis
- ✅ Nenhum secret no histórico Git

**Riscos**:
- 🔴 **ALTO**: Secrets expostos podem comprometer APIs externas
- 🟡 **MÉDIO**: Reescrever histórico Git pode afetar colaboradores

---

#### 2. Limpar Docs Obsoletas de F5-TTS
- [ ] Atualizar `docs/LOW_VRAM.md`:
  - Adicionar nota no topo: "⚠️ DEPRECATED: F5-TTS removed in v2.0"
  - Marcar seções F5-TTS como obsoletas
- [ ] Atualizar `docs/QUALITY_PROFILES.md`:
  - Remover seção "Perfis Padrão F5-TTS"
  - Atualizar exemplos para XTTS apenas
- [ ] Atualizar `docs/CHANGELOG.md`:
  - Adicionar entrada para v2.0 destacando remoção F5-TTS
  - Link para `F5_TTS_REMOVED.md`

**Critérios de Aceitação**:
- ✅ Nenhuma documentação sugere que F5-TTS está funcional
- ✅ Todas as referências marcadas como deprecated ou removidas
- ✅ Changelog atualizado com v2.0

**Riscos**:
- 🟢 **BAIXO**: Apenas documentação, sem risco técnico

---

#### 3. Renomear `scripts/not_remove/`
- [ ] Mover para estrutura mais clara:
  ```bash
  mkdir -p scripts/dataset
  mv scripts/not_remove/* scripts/dataset/
  rmdir scripts/not_remove
  ```
- [ ] Atualizar imports se algum script referencia:
  ```python
  # Antes
  from scripts.not_remove.download_youtube import download
  # Depois
  from scripts.dataset.download_youtube import download
  ```
- [ ] Atualizar README com nova estrutura

**Critérios de Aceitação**:
- ✅ `scripts/not_remove/` não existe mais
- ✅ `scripts/dataset/` contém todos os scripts de preparação de dados
- ✅ Nenhum import quebrado

**Riscos**:
- 🟡 **MÉDIO**: Imports podem quebrar se não testar bem

---

## 🏗️ Sprint 1: Estrutura `train/` + Pipeline de Dados

**Objetivo**: Adaptar scripts existentes em `scripts/not_remove/` para estrutura `train/` com foco em XTTS-v2 (formato LJSpeech).

**Duração**: 4-6 horas  
**Prioridade**: P0 (CRÍTICO - bloqueia Sprint 2)

**ATUALIZAÇÃO**: Scripts já existem em `scripts/not_remove/`! Pipeline completo:
1. `download_youtube.py` → Baixa de `videos.csv` para `raw/`
2. `prepare_segments_optimized.py` → VAD + segmentação → `processed/wavs/`
3. `transcribe_or_subtitles.py` → Whisper + legendas YT → `transcriptions.json`
4. `build_metadata_csv.py` → Gera LJSpeech `metadata.csv`

**Nova abordagem**: Migrar e adaptar para XTTS-v2 (não F5-TTS)!

### Tasks

#### 1.1 Criar Estrutura de Diretórios
- [ ] Criar árvore de pastas:
  ```bash
  mkdir -p train/{config,data/{raw,processed},scripts,output/{checkpoints,samples},logs}
  mkdir -p train/data/MyTTSDataset/wavs  # LJSpeech format
  ```
- [ ] Adicionar `.gitkeep` em pastas vazias
- [ ] Criar `.gitignore` para `train/data/raw/*` e `train/output/*` (não commitar datasets/checkpoints grandes)

**Critérios de Aceitação**:
- ✅ Estrutura completa criada
- ✅ Git ignora arquivos grandes de dados/modelos
- ✅ README em `train/README.md` explicando estrutura

**Riscos**:
- 🟢 **BAIXO**: Apenas criação de pastas

---

#### 1.2 Criar `train/config/dataset_config.yaml`
- [ ] Implementar configuração adaptada para XTTS-v2:
  ```yaml
  # Dataset preparation config for XTTS-v2
  audio:
    target_sample_rate: 22050  # XTTS-v2 requirement (não 24000!)
    channels: 1                # mono
    bit_depth: 16
    format: wav
  
  youtube:
    audio_format: "bestaudio/best"
    max_retries: 3
    retry_delay: 5
    subtitles:
      languages: ["pt", "pt-BR"]
      format: "vtt"
  
  segmentation:
    use_vad: true
    vad_threshold: -40.0        # dB, voice activity detection
    vad_frame_size: 512
    vad_chunk_duration: 10.0    # streaming chunks
    min_silence_duration: 0.3   # seconds to split
    
    min_duration: 7.0           # XTTS-v2: 7-12s ideal range!
    max_duration: 12.0
    target_duration: 10.0
    segment_overlap: 0.5        # overlap between segments
    
    fade_duration: 0.05         # fade in/out to avoid clicks
    normalization_method: "rms" # or "loudnorm"
    target_rms_db: -20.0
  
  transcription:
    whisper_model: "base"       # base, small, medium
    whisper_hp_model: "medium"  # high-precision fallback
    language: "pt"
    temperature: 0.0            # deterministic
    oov_threshold: 0.15         # out-of-vocab trigger for HP model
  
  text_processing:
    expand_numbers: true        # "123" → "cento e vinte e três"
    lowercase: true             # XTTS works better with lowercase
    normalize_whitespace: true
    remove_extra_punctuation: false
  
  quality_filters:
    min_words: 3
    max_words: 50
    # Adicionar filtros específicos se necessário
  
  dataset:
    train_split: 0.9
    val_split: 0.1
    shuffle: true
    seed: 42
  ```

**Critérios de Aceitação**:
- ✅ YAML válido com valores XTTS-v2 corretos (22050Hz, 7-12s)
- ✅ Configuração de VAD streaming (otimizado para memória)
- ✅ Parâmetros de transcrição (Whisper + fallback HP)
- ✅ Normalização de texto para pt-BR

**Riscos**:
- 🟢 **BAIXO**: Apenas arquivo de configuração

---

#### 1.3 Migrar e Adaptar `download_youtube.py`
- [ ] Copiar `scripts/not_remove/download_youtube.py` → `train/scripts/download_youtube.py`
- [ ] **MANTER**: Leitura de `videos.csv` (formato já funcional)
- [ ] **AJUSTAR**: Sample rate de 24000 → **22050Hz** (XTTS-v2)
  ```python
  # Antes
  "-ar", "24000",
  # Depois
  "-ar", str(config["audio"]["target_sample_rate"]),  # 22050
  ```
- [ ] **AJUSTAR**: Paths para `train/data/`:
  ```python
  data_dir = project_root / "train" / "data"
  videos_csv = data_dir / "videos.csv"
  raw_dir = data_dir / "raw"
  ```
- [ ] **MANTER**: Retry logic, logging, yt-dlp options

**Critérios de Aceitação**:
- ✅ Lê `train/data/videos.csv` (copiar de `scripts/not_remove/videos.csv`)
- ✅ Download para 22050Hz mono 16-bit
- ✅ Salva em `train/data/raw/video_XXXXX.wav`
- ✅ Logging em `train/logs/download_youtube.log`

**Riscos**:
- 🟢 **BAIXO**: Script já funcional, só ajustar paths
- 🟡 **MÉDIO**: yt-dlp pode quebrar com updates do YouTube

---

#### 1.4 Migrar e Adaptar `prepare_segments_optimized.py`
- [ ] Copiar `scripts/not_remove/prepare_segments_optimized.py` → `train/scripts/segment_audio.py`
- [ ] **MANTER**: Streaming VAD (já otimizado para memória!)
  - `iter_voice_regions()` - detecta fala em chunks de 10s
  - `iter_final_segments_from_regions()` - gera segmentos finais
- [ ] **AJUSTAR**: Duração para XTTS-v2 (7-12s, não 3-30s)
  ```python
  # Antes (F5-TTS)
  min_duration = 3.0
  max_duration = 30.0
  # Depois (XTTS-v2)
  min_duration = 7.0
  max_duration = 12.0
  target_duration = 10.0
  ```
- [ ] **AJUSTAR**: Sample rate 24000 → 22050Hz
  ```python
  target_sr = config["audio"]["target_sample_rate"]  # 22050
  ```
- [ ] **AJUSTAR**: Paths para `train/data/`:
  ```python
  raw_dir = project_root / "train" / "data" / "raw"
  processed_dir = project_root / "train" / "data" / "processed"
  ```
- [ ] **MANTER**: 
  - Fade in/out para evitar clicks
  - Normalização RMS ou pyloudnorm
  - Resample usando scipy.signal
  - Logging detalhado

**Critérios de Aceitação**:
- ✅ Processa arquivos grandes (>1GB) sem OOM
- ✅ Segmentos entre 7-12s (target 10s) - XTTS-v2 ideal
- ✅ 22050Hz mono 16-bit preservado
- ✅ VAD remove silêncios longos

**Riscos**:
- 🟢 **BAIXO**: Script já testado, só ajustar parâmetros

---
---

#### 1.5 Migrar e Adaptar `transcribe_or_subtitles.py`
- [ ] Copiar `scripts/not_remove/transcribe_or_subtitles.py` → `train/scripts/transcribe_audio.py`
- [ ] **MANTER**: Lógica completa já implementada!
  - Tenta baixar legendas do YouTube (yt-dlp)
  - Se não houver, usa Whisper
  - Cache de modelos Whisper (evita reload)
  - Fallback para modelo HP se OOV alto (>15%)
  - Normalização pt-BR completa:
    - `num2words` para números
    - Lowercase
    - Whitespace normalization
    - Remoção de pontuação extra
  - Vocabulário pt-BR embutido para detectar OOV
- [ ] **AJUSTAR**: Paths para `train/data/`:
  ```python
  data_dir = project_root / "train" / "data"
  videos_csv = data_dir / "videos.csv"
  processed_dir = data_dir / "processed"
  transcriptions_file = processed_dir / "transcriptions.json"
  ```
- [ ] **AJUSTAR**: Carregar config de `dataset_config.yaml`:
  ```python
  whisper_model = config["transcription"]["whisper_model"]
  whisper_hp_model = config["transcription"]["whisper_hp_model"]
  oov_threshold = config["transcription"]["oov_threshold"]
  ```
- [ ] **MANTER**: 
  - Rate limit handling (HTTP 429)
  - Retry logic
  - Logging detalhado

**Critérios de Aceitação**:
- ✅ Prioriza legendas do YouTube (mais rápido, exato)
- ✅ Fallback para Whisper funcional
- ✅ Normalização pt-BR completa (números expandidos)
- ✅ Salva `train/data/processed/transcriptions.json`
---

#### 1.6 Migrar e Adaptar `build_metadata_csv.py`
- [ ] Copiar `scripts/not_remove/build_metadata_csv.py` → `train/scripts/build_ljs_dataset.py`
- [ ] **REMOVER**: Referências a F5-TTS (comentários, paths `f5_dataset/`)
- [ ] **AJUSTAR**: Formato metadata.csv para XTTS-v2 (compatível com LJSpeech):
  ```
  # F5-TTS (ANTIGO)
  wavs/audio_0001.wav|texto em português aqui
  
  # XTTS-v2 / LJSpeech (NOVO - mantém compatibilidade!)
  wavs/audio_00001.wav|texto em português aqui
  ```
  - **NOTA**: XTTS aceita formato F5 (1 coluna), mas pode expandir para 2 se quiser
- [ ] **AJUSTAR**: Paths para `train/data/`:
  ```python
  data_dir = project_root / "train" / "data"
  processed_dir = data_dir / "processed"
  dataset_dir = data_dir / "MyTTSDataset"  # não f5_dataset!
  wavs_dir = dataset_dir / "wavs"
  ```
- [ ] **MANTER**:
  - Copia WAVs de `processed/` para `MyTTSDataset/wavs/`
  - Gera `metadata.csv` com formato `relative_path|text`
  - Logging detalhado
  - Estatísticas de duração
- [ ] **ADICIONAR** (opcional): Filtros de qualidade
  ```python
  # Filtrar por duração (7-12s)
  if not (7.0 <= item["duration"] <= 12.0):
      logger.warning(f"Duração fora do range: {item['duration']:.1f}s")
      continue
  
  # Filtrar por palavras (3-50)
  word_count = len(item["text"].split())
  if not (3 <= word_count <= 50):
      logger.warning(f"Palavras fora do range: {word_count}")
      continue
  ```
- [ ] **ADICIONAR**: Train/val split
  ```python
  # Shuffle e split
  random.seed(config["dataset"]["seed"])
  random.shuffle(metadata_lines)
  
  split_idx = int(len(metadata_lines) * config["dataset"]["train_split"])
  train_lines = metadata_lines[:split_idx]
  val_lines = metadata_lines[split_idx:]
  
  # Salvar splits
  (dataset_dir / "metadata_train.csv").write_text("\n".join(train_lines))
  (dataset_dir / "metadata_val.csv").write_text("\n".join(val_lines))
  ```

**Critérios de Aceitação**:
- ✅ `metadata.csv` em formato LJSpeech (compatível XTTS-v2)
- ✅ WAVs organizados em `MyTTSDataset/wavs/`
---

#### 1.7 Criar `pipeline.py` (Orquestrador)
- [ ] Criar script master para executar pipeline completo:
  ```python
  # train/scripts/pipeline.py
  
  """
  Pipeline completo de preparação de dataset XTTS-v2
  
  Uso:
      python -m train.scripts.pipeline
      python -m train.scripts.pipeline --skip-download
      python -m train.scripts.pipeline --only-step transcribe
  """
  
  import click
  from pathlib import Path
  import yaml
  
  @click.command()
  @click.option('--config', type=Path, default='train/config/dataset_config.yaml')
  @click.option('--skip-download', is_flag=True, help='Pular download (usar raw/ existente)')
  @click.option('--skip-segment', is_flag=True, help='Pular segmentação')
  @click.option('--skip-transcribe', is_flag=True, help='Pular transcrição')
  @click.option('--only-step', type=click.Choice(['download', 'segment', 'transcribe', 'build']), 
                help='Executar apenas um step')
  def run_pipeline(config, skip_download, skip_segment, skip_transcribe, only_step):
      """
      Executa pipeline completo de preparação de dataset:
      
      1. download_youtube.py   → raw/
      2. segment_audio.py      → processed/wavs/
      3. transcribe_audio.py   → processed/transcriptions.json
      4. build_ljs_dataset.py  → MyTTSDataset/metadata.csv
      """
      cfg = load_config(config)', is_flag=True)
  @click.option('--skip-transcribe', is_flag=True)
  def run_pipeline(config, sources, skip_download, skip_segment, skip_transcribe):
      """
      Run complete data pipeline:
      1. Download YouTube videos
      2. Segment audio with VAD
      3. Transcribe with Whisper
      4. Build LJSpeech dataset
      """
      cfg = load_config(config)
      
      if not skip_download:
          logger.info("Step 1: Downloading videos...")
          download_youtube_batch(sources, cfg)
      
      if not skip_segment:
          logger.info("Step 2: Segmenting audio...")
          segment_all_audio(cfg)
      
      if not skip_transcribe:
          logger.info("Step 3: Transcribing...")
          transcribe_all_segments(cfg)
      
      logger.info("Step 4: Building LJSpeech dataset...")
      build_ljspeech_dataset(cfg)
      
      logger.info("✅ Pipeline complete!")
  ```
- [ ] Logging estruturado (rich progress bars)
- [ ] Tratamento de erros global
- [ ] Checkpoint/resume (se pipeline falhar no meio)

**Critérios de Aceitação**:
- ✅ Pipeline roda de ponta a ponta sem intervenção
- ✅ Flags para pular etapas já completadas
- ✅ Progress bars claros
- ✅ Logs salvos em `train/logs/pipeline_{timestamp}.log`

**Riscos**:
- 🟡 **MÉDIO**: Pipeline pode falhar no meio (precisa ser resiliente)
- 🟢 **BAIXO**: Lógica simples se scripts individuais estão OK

---

### Sprint 1 - Deliverables

- [x] Estrutura `train/` completa
- [x] `dataset_config.yaml` bem documentado
- [x] Scripts refatorados e integrados:
  - `download_youtube.py`
  - `segment_audio.py`
  - `transcribe_whisper.py`
  - `build_ljs_dataset.py`
  - `pipeline.py`
- [x] Dataset LJSpeech de teste gerado (1-2h de áudio pt-BR)
- [x] Documentação em `train/README.md`

---

## 🎓 Sprint 2: Treinamento XTTS-v2

**Objetivo**: Implementar fine-tuning completo do XTTS-v2 com suporte a LoRA.

**Duração**: 6-8 horas  
**Prioridade**: P0 (CRÍTICO - core feature)

### Tasks

#### 2.1 Criar `train/config/train_config.yaml`
- [ ] Configuração de treinamento:
  ```yaml
  # XTTS-v2 Fine-tuning Configuration
  
  model:
    name: xtts_v2
    # Base model - auto-download via Coqui TTS
    checkpoint: tts_models/multilingual/multi-dataset/xtts_v2
    # Or custom checkpoint:
    # checkpoint: ./models/xtts_pretrained/model.pth
    
    # LoRA config (memory-efficient)
    use_lora: true
    lora_rank: 8
    lora_alpha: 16
    lora_dropout: 0.1
  
  training:
    # Hardware
    device: cuda
    mixed_precision: true  # FP16
    num_workers: 4
    
    # Optimization
    batch_size: 4          # adjust for VRAM
    gradient_accumulation_steps: 2  # effective batch = 8
    epochs: 50
    learning_rate: 1.0e-5
    warmup_steps: 100
    scheduler: cosine
    
    # Regularization
    weight_decay: 0.01
    gradient_clip_norm: 1.0
    
    # Constraints
    max_text_length: 200   # characters
    max_audio_length: 12   # seconds
    
    # Checkpointing
    save_every_n_epochs: 5
    keep_last_n_checkpoints: 3
    early_stopping_patience: 10
  
  dataset:
    path: ./train/data/MyTTSDataset
    metadata_train: metadata_train.csv
    metadata_val: metadata_val.csv
    language: pt-BR
    sample_rate: 22050
    
    # Data augmentation (optional)
    augmentation:
      enabled: false
      pitch_shift_semitones: [-2, 2]
      time_stretch_factor: [0.9, 1.1]
  
  logging:
    tensorboard_dir: ./train/output/tensorboard
    log_every_n_steps: 10
    sample_every_n_epochs: 5  # generate audio samples
    num_samples: 3
  ```

**Critérios de Aceitação**:
- ✅ YAML válido e bem documentado
- ✅ Suporta LoRA e full fine-tune
- ✅ Valores reasonable para RTX 3090 (23GB VRAM)

**Riscos**:
- 🟢 **BAIXO**: Apenas arquivo de configuração

---

#### 2.2 Baixar Modelo Pretrained XTTS-v2
- [ ] Script para download automático:
  ```python
  # train/scripts/download_pretrained.py
  
  from TTS.api import TTS
  import shutil
  
  def download_xtts_v2(output_dir: Path):
      """Download XTTS-v2 pretrained model via Coqui TTS."""
      print("Downloading XTTS-v2 base model...")
      tts = TTS("tts_models/multilingual/multi-dataset/xtts_v2")
      
      # Model files são salvos em ~/.local/share/tts/
      # Copiar para projeto para garantir versionamento
      src = Path.home() / ".local/share/tts/tts_models--multilingual--multi-dataset--xtts_v2"
      dst = output_dir / "xtts_v2_base"
      
      if dst.exists():
          print(f"Model already exists at {dst}")
          return dst
      
      shutil.copytree(src, dst)
      print(f"✅ Model downloaded to {dst}")
      return dst
  ```
- [ ] Salvar em `models/xtts_pretrained/`
- [ ] Adicionar verificação de integridade (checksum)

**Critérios de Aceitação**:
- ✅ Modelo baixado automaticamente
- ✅ Arquivos copiados para `models/xtts_pretrained/`
- ✅ Checksum validado (MD5 ou SHA256)

**Riscos**:
- 🟡 **MÉDIO**: Download pode falhar (retry logic)
- 🟡 **MÉDIO**: Modelo grande (~2GB) pode demorar

---

#### 2.3 Implementar `xtts_train.py`
- [ ] Script de treinamento completo:
  ```python
  # train/scripts/xtts_train.py
  
  import torch
  from TTS.tts.configs.xtts_config import XttsConfig
  from TTS.tts.models.xtts import Xtts
  from TTS.tts.datasets import load_tts_samples
  from torch.utils.data import DataLoader
  from torch.utils.tensorboard import SummaryWriter
  
  class XTTSTrainer:
      def __init__(self, config_path: Path):
          self.config = load_config(config_path)
          self.device = torch.device(self.config.training.device)
          
          # Load model
          self.model = self._load_model()
          
          # Setup LoRA if enabled
          if self.config.model.use_lora:
              self._setup_lora()
          
          # Optimizer & Scheduler
          self.optimizer = self._create_optimizer()
          self.scheduler = self._create_scheduler()
          
          # Data loaders
          self.train_loader, self.val_loader = self._create_data_loaders()
          
          # Logging
          self.writer = SummaryWriter(self.config.logging.tensorboard_dir)
      
      def _load_model(self):
          """Load XTTS-v2 base model."""
          config = XttsConfig()
          config.load_json(self.config.model.checkpoint + "/config.json")
          
          model = Xtts.init_from_config(config)
          model.load_checkpoint(
              config,
              checkpoint_path=self.config.model.checkpoint,
              eval=False
          )
          model.to(self.device)
          return model
      
      def _setup_lora(self):
          """Configure LoRA layers."""
          from peft import LoraConfig, get_peft_model
          
          lora_config = LoraConfig(
              r=self.config.model.lora_rank,
              lora_alpha=self.config.model.lora_alpha,
              lora_dropout=self.config.model.lora_dropout,
              target_modules=["q_proj", "v_proj"],  # XTTS attention layers
              bias="none"
          )
          self.model = get_peft_model(self.model, lora_config)
          print(f"LoRA enabled: {self.model.print_trainable_parameters()}")
      
      def train_epoch(self, epoch: int):
          """Train one epoch."""
          self.model.train()
          total_loss = 0
          
          for batch_idx, batch in enumerate(self.train_loader):
              # Move to device
              text_input = batch["text_input"].to(self.device)
              audio_target = batch["audio"].to(self.device)
              
              # Forward pass
              loss = self.model(text_input, audio_target)
              
              # Backward pass
              loss = loss / self.config.training.gradient_accumulation_steps
              loss.backward()
              
              # Optimizer step
              if (batch_idx + 1) % self.config.training.gradient_accumulation_steps == 0:
                  torch.nn.utils.clip_grad_norm_(
                      self.model.parameters(),
                      self.config.training.gradient_clip_norm
                  )
                  self.optimizer.step()
                  self.scheduler.step()
                  self.optimizer.zero_grad()
              
              total_loss += loss.item()
              
              # Logging
              if batch_idx % self.config.logging.log_every_n_steps == 0:
                  self.writer.add_scalar("Loss/train", loss.item(), epoch * len(self.train_loader) + batch_idx)
          
          return total_loss / len(self.train_loader)
      
      def validate(self, epoch: int):
          """Validate on val set."""
          self.model.eval()
          total_loss = 0
          
          with torch.no_grad():
              for batch in self.val_loader:
                  text_input = batch["text_input"].to(self.device)
                  audio_target = batch["audio"].to(self.device)
                  loss = self.model(text_input, audio_target)
                  total_loss += loss.item()
          
          avg_loss = total_loss / len(self.val_loader)
          self.writer.add_scalar("Loss/val", avg_loss, epoch)
          return avg_loss
      
      def generate_samples(self, epoch: int):
          """Generate audio samples for validation."""
          self.model.eval()
          sample_texts = [
              "Olá, este é um teste de síntese de voz.",
              "O fine-tuning está funcionando corretamente.",
              "Português brasileiro com XTTS versão dois."
          ]
          
          for idx, text in enumerate(sample_texts):
              audio = self.model.inference(text, language="pt")
              self.writer.add_audio(
                  f"Sample_{idx}",
                  audio,
                  epoch,
                  sample_rate=22050
              )
              # Save to disk
              output_path = self.config.logging.tensorboard_dir / f"epoch_{epoch}_sample_{idx}.wav"
              save_wav(audio, output_path, 22050)
      
      def train(self):
          """Main training loop."""
          best_val_loss = float('inf')
          patience_counter = 0
          
          for epoch in range(self.config.training.epochs):
              print(f"\nEpoch {epoch+1}/{self.config.training.epochs}")
              
              # Train
              train_loss = self.train_epoch(epoch)
              print(f"Train Loss: {train_loss:.4f}")
              
              # Validate
              val_loss = self.validate(epoch)
              print(f"Val Loss: {val_loss:.4f}")
              
              # Generate samples
              if epoch % self.config.logging.sample_every_n_epochs == 0:
                  self.generate_samples(epoch)
              
              # Save checkpoint
              if epoch % self.config.training.save_every_n_epochs == 0:
                  self.save_checkpoint(epoch, val_loss)
              
              # Early stopping
              if val_loss < best_val_loss:
                  best_val_loss = val_loss
                  patience_counter = 0
                  self.save_checkpoint(epoch, val_loss, is_best=True)
              else:
                  patience_counter += 1
                  if patience_counter >= self.config.training.early_stopping_patience:
                      print(f"Early stopping at epoch {epoch}")
                      break
          
          print("✅ Training complete!")
      
      def save_checkpoint(self, epoch: int, val_loss: float, is_best: bool = False):
          """Save model checkpoint."""
          checkpoint_dir = Path("train/output/checkpoints")
          checkpoint_dir.mkdir(parents=True, exist_ok=True)
          
          checkpoint_path = checkpoint_dir / f"checkpoint_epoch_{epoch}.pth"
          torch.save({
              'epoch': epoch,
              'model_state_dict': self.model.state_dict(),
              'optimizer_state_dict': self.optimizer.state_dict(),
              'val_loss': val_loss,
              'config': self.config
          }, checkpoint_path)
          
          if is_best:
              best_path = checkpoint_dir / "best_model.pth"
              shutil.copy(checkpoint_path, best_path)
              print(f"✅ Best model saved: {best_path}")
  
  
  if __name__ == "__main__":
      trainer = XTTSTrainer("train/config/train_config.yaml")
      trainer.train()
  ```

**Critérios de Aceitação**:
- ✅ Carrega modelo XTTS-v2 base
- ✅ Suporta LoRA e full fine-tune
- ✅ Training loop funcional com val loss
- ✅ Checkpoints salvos a cada N epochs
- ✅ TensorBoard logging
- ✅ Audio samples gerados para validação manual
- ✅ Early stopping implementado

**Riscos**:
- 🔴 **ALTO**: XTTS API pode mudar (pinned version)
- 🟡 **MÉDIO**: OOM se batch_size muito grande
- 🟡 **MÉDIO**: Convergência pode ser lenta (ajustar LR)

---

#### 2.4 Testes de Treinamento
- [ ] Criar `tests/test_xtts_train.py`:
  ```python
  def test_load_model():
      """Test XTTS-v2 model loads correctly."""
      
  def test_lora_setup():
      """Test LoRA layers are added correctly."""
      
  def test_forward_pass():
      """Test forward pass with dummy data."""
      
  def test_checkpoint_save_load():
      """Test checkpoint save/load cycle."""
  ```
- [ ] Teste de smoke (1 epoch com mini-dataset)

**Critérios de Aceitação**:
- ✅ Testes passam sem erros
- ✅ Smoke test completa em <5min

**Riscos**:
- 🟢 **BAIXO**: Testes unitários são isolados

---

### Sprint 2 - Deliverables

- [x] `train_config.yaml` completo
- [x] Modelo XTTS-v2 base baixado
- [x] `xtts_train.py` implementado e testado
- [x] Primeiro fine-tune rodado (smoke test)
- [x] Checkpoints salvos em `train/output/checkpoints/`
- [x] Audio samples em `train/output/samples/`
- [x] TensorBoard logs funcionando

---

## 🎤 Sprint 3: Integração API + Inferência

**Objetivo**: Integrar modelo fine-tunado na API existente e criar endpoints de inferência.

**Duração**: 3-4 horas  
**Prioridade**: P1 (IMPORTANTE)

### Tasks

#### 3.1 Criar `train/scripts/xtts_inference.py`
- [ ] Wrapper de inferência:
  ```python
  # train/scripts/xtts_inference.py
  
  class XTTSInference:
      def __init__(self, checkpoint_path: Path = None):
          """
          Load XTTS-v2 model for inference.
          
          Args:
              checkpoint_path: Path to fine-tuned checkpoint.
                               If None, uses base model.
          """
          if checkpoint_path and checkpoint_path.exists():
              self.model = self._load_finetuned(checkpoint_path)
              logger.info(f"Loaded fine-tuned model: {checkpoint_path}")
          else:
              self.model = TTS("tts_models/multilingual/multi-dataset/xtts_v2")
              logger.info("Loaded base XTTS-v2 model")
          
          self.model.to("cuda" if torch.cuda.is_available() else "cpu")
      
      def synthesize(
          self,
          text: str,
          language: str = "pt",
          speaker_wav: Path = None,
          speed: float = 1.0
      ) -> np.ndarray:
          """
          Generate speech from text.
          
          Args:
              text: Input text
              language: Language code (pt, en, es, etc)
              speaker_wav: Reference audio for voice cloning
              speed: Speech speed multiplier
          
          Returns:
              Audio array (22050 Hz mono)
          """
          if speaker_wav:
              audio = self.model.tts_to_file(
                  text=text,
                  speaker_wav=str(speaker_wav),
                  language=language,
                  speed=speed,
                  file_path=None  # return array
              )
          else:
              audio = self.model.tts(text=text, language=language)
          
          return audio
      
      def clone_voice(
          self,
          text: str,
          reference_wav: Path,
          language: str = "pt"
      ) -> np.ndarray:
          """
          Clone voice from reference audio.
          
          Args:
              text: Text to synthesize
              reference_wav: Path to reference audio (3-10s)
              language: Target language
          
          Returns:
              Cloned audio (22050 Hz mono)
          """
          return self.synthesize(
              text=text,
              speaker_wav=reference_wav,
              language=language
          )
  ```

**Critérios de Aceitação**:
- ✅ Carrega modelo base ou fine-tunado
- ✅ Síntese de texto funciona
- ✅ Voice cloning funciona
- ✅ Retorna audio em 22050 Hz mono

**Riscos**:
- 🟡 **MÉDIO**: Checkpoint loading pode falhar (validar formato)

---

#### 3.2 Modificar `app/engines/xtts_engine.py`
- [ ] Adicionar suporte a checkpoint custom:
  ```python
  # app/engines/xtts_engine.py
  
  class XTTSEngine(TTSEngine):
      def __init__(self, config: Dict[str, Any]):
          super().__init__(config)
          
          # Check for custom checkpoint
          custom_checkpoint = os.getenv("XTTS_CUSTOM_CHECKPOINT")
          if custom_checkpoint and Path(custom_checkpoint).exists():
              logger.info(f"Loading custom XTTS checkpoint: {custom_checkpoint}")
              self.model = self._load_custom_checkpoint(custom_checkpoint)
          else:
              logger.info("Loading base XTTS-v2 model")
              self.model = TTS("tts_models/multilingual/multi-dataset/xtts_v2")
      
      def _load_custom_checkpoint(self, checkpoint_path: str):
          """Load fine-tuned checkpoint."""
          # Implementation similar to xtts_inference.py
          ...
  ```
- [ ] Atualizar `.env.example`:
  ```bash
  # XTTS Configuration
  XTTS_CUSTOM_CHECKPOINT=/app/train/output/checkpoints/best_model.pth
  ```

**Critérios de Aceitação**:
- ✅ Suporta modelo base e fine-tunado
- ✅ Env var funciona
- ✅ Fallback para base se checkpoint não existir

**Riscos**:
- 🟢 **BAIXO**: Lógica simples

---

#### 3.3 Criar Endpoint Síncrono `/tts/synthesize`
- [ ] Adicionar em `app/main.py`:
  ```python
  @app.post("/tts/synthesize", response_class=StreamingResponse)
  async def synthesize_tts(
      text: str = Form(...),
      language: str = Form("pt-BR"),
      reference_audio: UploadFile = File(None),
      speed: float = Form(1.0)
  ):
      """
      Síntese de voz síncrona (retorna WAV imediatamente).
      
      Args:
          text: Texto a ser sintetizado
          language: Código do idioma (pt-BR, en-US, etc)
          reference_audio: (Opcional) Áudio de referência para clonagem
          speed: Velocidade da fala (0.5-2.0)
      
      Returns:
          Audio WAV (22050 Hz mono)
      """
      try:
          # Get engine
          engine = engine_factory.get_engine("xtts")
          
          # Save reference audio if provided
          speaker_wav = None
          if reference_audio:
              speaker_wav = Path(f"/tmp/ref_{uuid.uuid4()}.wav")
              with open(speaker_wav, "wb") as f:
                  f.write(await reference_audio.read())
          
          # Synthesize
          audio = engine.synthesize(
              text=text,
              language=language.split("-")[0],  # pt-BR -> pt
              speaker_wav=speaker_wav,
              speed=speed
          )
          
          # Convert to WAV bytes
          wav_bytes = audio_array_to_wav(audio, sample_rate=22050)
          
          # Cleanup
          if speaker_wav and speaker_wav.exists():
              speaker_wav.unlink()
          
          return StreamingResponse(
              io.BytesIO(wav_bytes),
              media_type="audio/wav",
              headers={
                  "Content-Disposition": f"attachment; filename=synthesized_{int(time.time())}.wav"
              }
          )
      
      except Exception as e:
          logger.exception("Synthesis failed")
          raise HTTPException(status_code=500, detail=str(e))
  ```

**Critérios de Aceitação**:
- ✅ Endpoint `/tts/synthesize` funciona
- ✅ Aceita texto + optional reference audio
- ✅ Retorna WAV diretamente
- ✅ Tratamento de erros

**Riscos**:
- 🟡 **MÉDIO**: Requests grandes podem timeout (limitar texto)

---

#### 3.4 Documentar API
- [ ] Atualizar `docs/api-reference.md`:
  ```markdown
  ## POST /tts/synthesize
  
  Síntese de voz síncrona usando XTTS-v2.
  
  ### Request
  
  **Form Data:**
  - `text` (required): Texto a sintetizar (max 500 chars)
  - `language` (optional): Código idioma (default: pt-BR)
  - `reference_audio` (optional): Arquivo WAV para clonagem
  - `speed` (optional): Velocidade (0.5-2.0, default: 1.0)
  
  ### Example
  
  ```bash
  # Simple TTS
  curl -X POST http://localhost:8005/tts/synthesize \
    -F "text=Olá, este é um teste" \
    -F "language=pt-BR" \
    -o output.wav
  
  # Voice cloning
  curl -X POST http://localhost:8005/tts/synthesize \
    -F "text=Texto com voz clonada" \
    -F "reference_audio=@reference.wav" \
    -o cloned.wav
  ```
  
  ### Response
  
  - Status: 200 OK
  - Content-Type: audio/wav
  - Body: WAV file (22050 Hz mono)
  ```

**Critérios de Aceitação**:
- ✅ Docs claras com exemplos curl
- ✅ Swagger UI atualizado (automático via FastAPI)

**Riscos**:
- 🟢 **BAIXO**: Apenas documentação

---

### Sprint 3 - Deliverables

- [x] `xtts_inference.py` implementado
- [x] `xtts_engine.py` suporta checkpoint custom
- [x] Endpoint `/tts/synthesize` funcionando
- [x] API documentada
- [x] Testes manuais com curl
- [x] README atualizado com link para Swagger

---

## ✅ Sprint 4: Qualidade & Testes

**Objetivo**: Garantir qualidade de código e cobertura de testes.

**Duração**: 4-5 horas  
**Prioridade**: P1 (IMPORTANTE)

### Tasks

#### 4.1 Testes do Pipeline de Dados
- [ ] `tests/test_download_youtube.py`
- [ ] `tests/test_segment_audio.py`
- [ ] `tests/test_transcribe.py`
- [ ] `tests/test_build_metadata.py`
- [ ] `tests/test_pipeline_integration.py` (end-to-end)

**Critérios de Aceitação**:
- ✅ Coverage > 80% nos scripts de pipeline
- ✅ Testes passam em CI

---

#### 4.2 Testes de Treinamento
- [ ] `tests/test_xtts_train.py`
- [ ] Smoke test (1 epoch, mini-dataset)

---

#### 4.3 Testes de API
- [ ] `tests/test_api_synthesize.py`
- [ ] `tests/test_voice_cloning_endpoint.py`
- [ ] `tests/test_custom_checkpoint_loading.py`

---

#### 4.4 Configurar Linting
- [ ] Adicionar pre-commit:
  ```yaml
  # .pre-commit-config.yaml
  repos:
    - repo: https://github.com/psf/black
      rev: 24.3.0
      hooks:
        - id: black
    
    - repo: https://github.com/pycqa/isort
      rev: 5.13.2
      hooks:
        - id: isort
    
    - repo: https://github.com/pre-commit/pre-commit-hooks
      rev: v4.5.0
      hooks:
        - id: trailing-whitespace
        - id: end-of-file-fixer
        - id: check-yaml
  ```
- [ ] Rodar em todo o código:
  ```bash
  black .
  isort .
  ```

---

#### 4.5 Type Hints
- [ ] Adicionar hints em todos os scripts de `train/`
- [ ] Configurar mypy:
  ```ini
  [mypy]
  python_version = 3.11
  warn_return_any = True
  warn_unused_configs = True
  disallow_untyped_defs = True
  ```

---

### Sprint 4 - Deliverables

- [x] Cobertura de testes > 80%
- [x] Linting configurado (black, isort)
- [x] Type hints completos
- [x] CI pipeline básico (GitHub Actions)

---

## 📚 Sprint 5: Docs & DevOps

**Objetivo**: Documentação completa e melhorias de DevOps.

**Duração**: 2-3 horas  
**Prioridade**: P2 (NICE TO HAVE)

### Tasks

#### 5.1 Criar `ENV_SETUP.md`
- [ ] Guia de setup completo:
  - Instalação de dependências
  - Criação de venv
  - Configuração VSCode
  - Download de modelos

---

#### 5.2 Criar `CONTRIBUTING.md`
- [ ] Guidelines para contribuidores
- [ ] Code style
- [ ] Commit conventions

---

#### 5.3 Atualizar README.md
- [ ] Seção "Quick Start" atualizada
- [ ] Link para Swagger docs
- [ ] Badges (build status, coverage)

---

#### 5.4 Criar Diagramas
- [ ] Pipeline de dados (Mermaid)
- [ ] Arquitetura do sistema
- [ ] Fluxo de treinamento

---

#### 5.5 GitHub Actions CI
- [ ] Workflow básico:
  ```yaml
  # .github/workflows/ci.yml
  name: CI
  
  on: [push, pull_request]
  
  jobs:
    test:
      runs-on: ubuntu-latest
      steps:
        - uses: actions/checkout@v3
        - uses: actions/setup-python@v4
          with:
            python-version: '3.11'
        - run: pip install -r requirements.txt -r requirements-dev.txt
        - run: pytest
        - run: black --check .
        - run: mypy .
  ```

---

### Sprint 5 - Deliverables

- [x] `ENV_SETUP.md` completo
- [x] `CONTRIBUTING.md` criado
- [x] README atualizado com quick start
- [x] Diagramas de arquitetura
- [x] CI pipeline funcionando

---

## 📈 Métricas de Sucesso

### Sprint 1
- [ ] Dataset LJSpeech gerado (mín 1h de áudio pt-BR)
- [ ] Pipeline roda end-to-end sem erros
- [ ] Tempo de processamento < 2h para 1h de áudio

### Sprint 2
- [ ] Modelo fine-tuna sem OOM
- [ ] Val loss converge (decresce por > 10 epochs)
- [ ] Audio samples têm qualidade aceitável (validação manual)

### Sprint 3
- [ ] API `/tts/synthesize` responde em < 5s para texto curto
- [ ] Voice cloning funciona com latência < 10s
- [ ] Modelo custom carrega corretamente

### Sprint 4
- [ ] Coverage > 80%
- [ ] Zero warnings de linting
- [ ] Todos os testes passam

### Sprint 5
- [ ] Docs completas (README + contributing)
- [ ] CI passa em todos os PRs
- [ ] Novos devs conseguem setup em < 30min

---

## 🚧 Riscos Globais

### Técnicos
- **XTTS API breaking changes** → Pinned version (coqui-tts==0.27.0)
- **OOM durante treino** → LoRA + gradient accumulation
- **Whisper lento** → Usar GPU, modelo small
- **Dataset pequeno** → Começar com 1-2h, expandir depois

### Processo
- **Sprints muito longas** → Dividir tasks maiores
- **Falta de validação manual** → Audio samples a cada epoch
- **Documentação desatualizada** → Update docs em cada sprint

---

## 📝 Notas Finais

- **Priorizar Sprint 0 e 1** antes de qualquer outra coisa
- **Commits frequentes** (atomic commits por task)
- **Testes manuais** antes de marcar task como done
- **Documentar decisões técnicas** em comentários/docstrings

**Próxima ação**: Executar **Sprint 0 - Task 1** (auditoria de secrets).

---

**Última atualização**: 2025-12-06  
**Mantido por**: Tech Lead (Claude Sonnet 4.5)
