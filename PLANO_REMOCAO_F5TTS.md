# 🗑️ PLANO COMPLETO DE REMOÇÃO F5-TTS

**Data:** $(date +%Y-%m-%d)  
**Status:** APROVADO - PRONTO PARA EXECUÇÃO  
**Objetivo:** Remover completamente integração F5-TTS, mantendo apenas XTTS funcional

---

## 📋 SUMÁRIO EXECUTIVO

Este documento consolida **TUDO** que será removido/modificado para eliminar F5-TTS do projeto.

### Escopo da Remoção

- ✅ **50+ arquivos Python** (engines, testes, scripts)
- ✅ **Pasta train/ inteira** (~5GB com datasets/checkpoints)
- ✅ **5-6 dependências PyPI** exclusivas F5-TTS
- ✅ **30+ variáveis de ambiente**
- ✅ **Symlinks internos e externos**
- ✅ **Documentação técnica** (10+ arquivos MD)

### Impacto

- **NENHUM impacto no XTTS** (engine principal permanece intacto)
- **API backwards-compatible** (endpoints permanecem, apenas rejeitam `engine=f5tts`)
- **Redução de ~5-10GB** em disco (models + checkpoints + datasets)
- **Simplificação de dependências** (remove Vocos, F5-TTS, Whisper, etc.)

---

## 🎯 FASE 1: MAPEAMENTO COMPLETO (✅ CONCLUÍDO)

### Arquivos Identificados

#### 1.1 Engines Python (REMOÇÃO TOTAL)

```bash
app/engines/f5tts_engine.py              # Engine principal F5-TTS
app/engines/f5tts_ptbr_engine.py         # Versão otimizada PT-BR
```

#### 1.2 Testes (REMOÇÃO TOTAL)

```bash
test_f5tts_init.py                       # Teste raiz: inicialização
test_f5tts_finetuned.py                  # Teste raiz: modelo finetuned
test_pretrained_inference.py             # Teste raiz: inferência pretrained
test_voice_clone_quality.py              # Teste raiz: qualidade clonagem
tests/unit/engines/test_f5tts_engine.py  # Testes unitários engine
tests/train/                             # Testes de treinamento (pasta inteira)
```

#### 1.3 Documentação (REMOÇÃO TOTAL)

```bash
SPRINTS_PLAN.md                          # Planejamento sprints F5-TTS
MORE.md                                  # Análise técnica detalhada
docs/F5TTS_QUALITY_FIX.md                # Troubleshooting qualidade
FIX_CHECKPOINTS_*.md                     # Troubleshooting checkpoints
IMPLEMENTATION_COMPLETE.md               # Doc de implementação (verificar se específico F5)
```

#### 1.4 Scripts de Teste (REMOÇÃO TOTAL)

```bash
test_job_creation.sh                     # Testa criação job com f5tts
test_sprints.sh                          # Testa implementação sprints
```

#### 1.5 Pasta train/ (REMOÇÃO TOTAL - ~5GB)

```
train/
├── audio/              # Processamento áudio dataset
├── cli/                # CLIs treinamento
├── config/             # Schemas/YAMLs/vocab
├── data/               # Datasets (f5_dataset, f5_dataset_pinyin)
│   └── f5_dataset_pinyin → SYMLINK (será removido)
├── docs/               # Docs técnicas
├── examples/           # Exemplos uso
├── fracasso/           # Experimentos falhos
├── inference/          # API inferência
├── io/                 # YouTube/storage/subtitles
├── logs/               # Logs treinamento
├── output/             # Checkpoints (ptbr_finetuned2/)
├── pretrained/         # Modelos pretrained
├── runs/               # TensorBoard (pode ser symlink)
├── scripts/            # Scripts auxiliares
├── text/               # Processamento texto
├── training/           # Callbacks/utils treino
├── utils/              # Utilitários gerais
├── run_training.py     # Script principal treino
├── safe_train.py       # Wrapper seguro
├── test.py             # Teste inferência
└── (50+ arquivos MD, sh, py)
```

**⚠️ ATENÇÃO:** `train/data/f5_dataset_pinyin` é um **SYMLINK** (destino desconhecido, investigar manualmente)

#### 1.6 Symlinks (REMOÇÃO MANUAL + SCRIPT)

**Dentro do Repositório:**
```bash
/home/tts-webui-proxmox-passthrough/runs → (destino desconhecido - investigar)
/home/tts-webui-proxmox-passthrough/train/data/f5_dataset_pinyin → (destino desconhecido)
```

**HuggingFace Cache (models/f5tts/):**
```bash
models/f5tts/models--charactr--vocos-mel-24khz/snapshots/.../pytorch_model.bin
models/f5tts/models--charactr--vocos-mel-24khz/snapshots/.../config.yaml
models/f5tts/models--firstpixel--F5-TTS-pt-br/snapshots/.../model_200000.pt
models/f5tts/models--firstpixel--F5-TTS-pt-br/snapshots/.../model_last.pt
models/f5tts/models--firstpixel--F5-TTS-pt-br/snapshots/.../AgentF5TTSChunk.py
```

**Possíveis Symlinks Externos (MENCIONAR EM MORE.md):**
```bash
/root/.local/lib/python3.11/ckpts/        # Mencionado em MORE.md
/root/.local/lib/python3.11/data/         # Mencionado em MORE.md
```

---

## 🔧 FASE 2: MODIFICAÇÕES EM ARQUIVOS EXISTENTES

### 2.1 Dependências (requirements.txt)

**REMOVER:**
```python
f5-tts==1.1.9                # ❌ Biblioteca principal
cached-path>=1.6.2           # ❌ Usado por F5-TTS
faster-whisper>=1.0.0        # ❌ Transcription F5-TTS
vocos==0.1.0                 # ❌ Vocoder (requirements-lock.txt)
```

**AVALIAR (podem ser usados por outros componentes):**
```python
datasets>=4.4.1              # ⚠️ Verificar se XTTS ou RVC usam
pyarrow>=22.0.0              # ⚠️ Verificar se usado por datasets XTTS
```

**MANTER (usados por XTTS/RVC):**
```python
torch, torchaudio, numpy, soundfile
coqui-tts                    # ✅ XTTS
faiss-cpu, praat-parselmouth, resampy  # ✅ RVC
```

### 2.2 Configuração (.env.example)

**REMOVER LINHAS 69-104:**
```bash
# ===== F5-TTS / E2-TTS (Flow Matching Diffusion - EMOTION MODEL) =====
F5TTS_ENABLED=true
F5TTS_MODEL=firstpixel/F5-TTS-pt-br
F5TTS_DEVICE=cuda
F5TTS_FALLBACK_CPU=true
F5TTS_WHISPER_MODEL=base
F5TTS_WHISPER_DEVICE=cpu
F5TTS_NFE_STEP_FAST=24
F5TTS_NFE_STEP_BALANCED=40
F5TTS_NFE_STEP_ULTRA=64
F5TTS_CFG_STRENGTH=2.0
F5TTS_SWAY_SAMPLING_COEF=-1.0
F5TTS_SPEED=1.0
F5TTS_DENOISE_STRENGTH=0.85
F5TTS_DEESSING_FREQ=7000
F5TTS_HIGHPASS_FREQ=50
F5TTS_LOWPASS_FREQ=12000
F5TTS_SAMPLE_RATE=24000
F5TTS_MIN_REF_DURATION=3
F5TTS_MAX_REF_DURATION=30
F5TTS_MAX_TEXT_LENGTH=10000
F5TTS_WHISPER_AUTO_TRANSCRIBE=true
F5TTS_CUSTOM_CHECKPOINT=  # Path to custom checkpoint (opcional)
# ... (~30+ variáveis no total)
```

### 2.3 Engine Factory (app/engines/factory.py)

**REMOVER:**
- Import: `from .f5tts_engine import F5TtsEngine`
- Import: `from .f5tts_ptbr_engine import F5TtsPtBrEngine`
- Entrada no `_ENGINE_REGISTRY`: `'f5tts': None` e `'f5tts-ptbr': None`
- Blocos `elif engine_type == 'f5tts':` e `elif engine_type == 'f5tts-ptbr':` (linhas ~86-120)

**Alteração:**
```python
# ANTES
_ENGINE_REGISTRY: Dict[str, Optional[Type[TTSEngine]]] = {
    'xtts': None,
    'f5tts': None,
    'f5tts-ptbr': None
}

# DEPOIS
_ENGINE_REGISTRY: Dict[str, Optional[Type[TTSEngine]]] = {
    'xtts': None
}
```

### 2.4 Quality Profiles (app/quality_profiles.py)

**REMOVER:**
- Enum `TTSEngine.F5TTS` (linha 14)
- Classe `F5TTSQualityProfile` (linhas ~80-180)
- Profiles padrão F5-TTS:
  - `F5TTS_FAST` (linha ~320)
  - `F5TTS_BALANCED` (linha ~346)
  - `F5TTS_ULTRA_QUALITY` (linha ~372)
  - `F5TTS_EXPERIMENTAL_ULTRA` (linha ~398)

**Alteração:**
```python
# ANTES
class TTSEngine(str, Enum):
    XTTS = "xtts"
    F5TTS = "f5tts"

# DEPOIS
class TTSEngine(str, Enum):
    XTTS = "xtts"
```

### 2.5 Quality Profile Manager (app/quality_profile_manager.py)

**REMOVER:**
- Referências a `TTSEngine.F5TTS` (linhas 66, 218)
- Método `list_profiles()` deve retornar apenas XTTS profiles
- Seed de profiles padrão F5-TTS (método `_seed_default_profiles()`)

### 2.6 Form Parsers (app/utils/form_parsers.py)

**REMOVER:**
- Comentário linha 107: `# tts_engine é TTSEngine.F5TTS`
- Qualquer lógica específica para validação F5TTS

### 2.7 Config (app/config.py)

**VERIFICAR e REMOVER:**
- Seção `tts_engines['f5tts']` (config específica F5-TTS)
- Feature flags relacionados a F5TTS

### 2.8 API Endpoints (app/main.py)

**MODIFICAR (linhas 229-350 e 713-800):**
- Endpoint `/jobs`: Manter parâmetro `tts_engine` mas **rejeitar** `engine=f5tts`
- Endpoint `/voices/clone`: Manter parâmetro `tts_engine` mas **rejeitar** `engine=f5tts`
- Adicionar validação:
  ```python
  if tts_engine_enum.value == "f5tts":
      raise HTTPException(
          status_code=400,
          detail="F5-TTS engine has been removed. Please use 'xtts' instead."
      )
  ```

**Alteração no Form description:**
```python
# ANTES
tts_engine: str = Form('xtts', description="TTS engine: 'xtts' (default/stable) or 'f5tts' (experimental/high-quality)")

# DEPOIS
tts_engine: str = Form('xtts', description="TTS engine: only 'xtts' is supported")
```

### 2.9 Documentação (docs/)

**REMOVER SEÇÕES F5-TTS em:**
- `docs/ARCHITECTURE.md` - Seção "F5-TTS as PT-BR specialized engine"
- `docs/FORM_ENUM_PATTERN.md` - Enum value `f5tts`
- `docs/API_PARAMETERS.md` - Parâmetros F5-TTS (se houver)

**ATUALIZAR:**
- `README.md` - Remover menções a F5-TTS, atualizar features
- `docs/getting-started.md` - Remover seções de setup F5-TTS

---

## 🚀 FASE 3: EXECUÇÃO (ORDEM CRONOLÓGICA)

### ETAPA 1: Backup (CRÍTICO)

```bash
# Criar backup completo antes de qualquer alteração
cd /home/tts-webui-proxmox-passthrough
tar -czf backup_pre_f5tts_removal_$(date +%Y%m%d).tar.gz \
    train/ \
    app/engines/f5tts*.py \
    requirements.txt \
    .env.example \
    test_f5tts*.py \
    SPRINTS_PLAN.md \
    MORE.md
```

### ETAPA 2: Remover Arquivos Isolados

```bash
# Engines
rm -f app/engines/f5tts_engine.py
rm -f app/engines/f5tts_ptbr_engine.py

# Testes raiz
rm -f test_f5tts_init.py
rm -f test_f5tts_finetuned.py
rm -f test_pretrained_inference.py
rm -f test_voice_clone_quality.py
rm -f test_job_creation.sh
rm -f test_sprints.sh

# Testes unitários
rm -f tests/unit/engines/test_f5tts_engine.py

# Documentação
rm -f SPRINTS_PLAN.md
rm -f MORE.md
rm -f docs/F5TTS_QUALITY_FIX.md
rm -f FIX_CHECKPOINTS_*.md
```

### ETAPA 3: Remover Pasta train/

```bash
# ATENÇÃO: ~5GB, contém symlinks
# Usar -rf com CUIDADO
rm -rf /home/tts-webui-proxmox-passthrough/train/
```

### ETAPA 4: Remover Symlinks Internos

```bash
# Verificar se são symlinks antes de remover
if [ -L /home/tts-webui-proxmox-passthrough/runs ]; then
    rm /home/tts-webui-proxmox-passthrough/runs
fi

# train/data/f5_dataset_pinyin já será removido com train/
```

### ETAPA 5: Remover HuggingFace Cache

```bash
rm -rf /home/tts-webui-proxmox-passthrough/models/f5tts/
```

### ETAPA 6: Modificar Arquivos Python (usar script ou manual)

Ver detalhes em **FASE 2** acima. Principais arquivos:
- `requirements.txt`
- `.env.example`
- `app/engines/factory.py`
- `app/quality_profiles.py`
- `app/quality_profile_manager.py`
- `app/main.py`
- `app/config.py`

### ETAPA 7: Modificar Documentação

- Atualizar `README.md`
- Atualizar `docs/ARCHITECTURE.md`
- Atualizar `docs/getting-started.md`

---

## 🔍 FASE 4: VERIFICAÇÃO PÓS-REMOÇÃO

### 4.1 Checklist de Validação

```bash
# Verificar se nenhum import F5TTS restou
grep -r "f5tts" --include="*.py" app/
grep -r "F5TTS" --include="*.py" app/

# Verificar se pasta train/ foi removida
ls -la train/  # deve retornar "No such file or directory"

# Verificar se dependencies foram removidas
grep "f5-tts" requirements.txt  # deve retornar vazio
grep "vocos" requirements*.txt  # deve retornar vazio

# Verificar se .env.example foi limpo
grep "F5TTS" .env.example  # deve retornar vazio

# Verificar se API rejeita f5tts
curl -X POST http://localhost:8000/jobs \
  -F "text=teste" \
  -F "source_language=pt-BR" \
  -F "mode=dubbing" \
  -F "tts_engine=f5tts"
# Esperado: HTTP 400 "F5-TTS engine has been removed"
```

### 4.2 Testes de Regressão XTTS

```bash
# Testar que XTTS ainda funciona
curl -X POST http://localhost:8000/jobs \
  -F "text=Olá mundo" \
  -F "source_language=pt-BR" \
  -F "mode=dubbing" \
  -F "tts_engine=xtts"
# Esperado: HTTP 200 com job_id

# Rodar testes XTTS
pytest tests/unit/engines/test_xtts_engine.py -v
```

---

## 📜 FASE 5: SCRIPT DE LIMPEZA DE SYMLINKS EXTERNOS

Criar arquivo `REMOVE_F5_SYMLINKS.sh` (executar MANUALMENTE após revisão):

```bash
#!/bin/bash
# Script para remover symlinks F5-TTS FORA do repositório
# EXECUTE COM CUIDADO - Revisar destinos antes de confirmar

set -euo pipefail

echo "🔍 Procurando symlinks F5-TTS em /root/.local/lib/python3.11/..."

# Possíveis locais mencionados em MORE.md
POSSIBLE_SYMLINKS=(
    "/root/.local/lib/python3.11/ckpts"
    "/root/.local/lib/python3.11/data"
    "/root/.cache/huggingface/hub/models--charactr--vocos-mel-24khz"
    "/root/.cache/huggingface/hub/models--firstpixel--F5-TTS-pt-br"
)

for symlink in "${POSSIBLE_SYMLINKS[@]}"; do
    if [ -L "$symlink" ]; then
        echo "📌 SYMLINK ENCONTRADO: $symlink"
        ls -la "$symlink"
        read -p "Remover este symlink? (y/N): " confirm
        if [[ "$confirm" == "y" || "$confirm" == "Y" ]]; then
            rm -v "$symlink"
            echo "✅ Removido: $symlink"
        else
            echo "⏭️ Pulado: $symlink"
        fi
    elif [ -d "$symlink" ]; then
        echo "📁 DIRETÓRIO ENCONTRADO (não é symlink): $symlink"
        echo "   Tamanho: $(du -sh "$symlink" 2>/dev/null || echo 'N/A')"
        read -p "Remover este diretório? (y/N): " confirm
        if [[ "$confirm" == "y" || "$confirm" == "Y" ]]; then
            rm -rfv "$symlink"
            echo "✅ Removido: $symlink"
        else
            echo "⏭️ Pulado: $symlink"
        fi
    else
        echo "❌ NÃO ENCONTRADO: $symlink"
    fi
done

echo ""
echo "🎯 Procurar manualmente por outros symlinks F5-TTS:"
echo "   find /root -type l -name '*f5*' 2>/dev/null"
echo "   find /root -type l -name '*vocos*' 2>/dev/null"
```

---

## 🐍 FASE 6: GUIA DE RESET DO AMBIENTE PYTHON

Criar arquivo `PYTHON_ENV_RESET.md`:

```markdown
# 🐍 Guia de Reset do Ambiente Python (Pós-Remoção F5-TTS)

## Objetivo

Recriar ambiente Python limpo, sem dependências órfãs do F5-TTS.

## Opção 1: Manter Conda (Recomendado para GPU)

\`\`\`bash
# 1. Desativar ambiente atual
conda deactivate

# 2. Remover ambiente antigo
conda env remove -n tts-webui

# 3. Criar ambiente limpo
conda create -n tts-webui python=3.11 -y

# 4. Ativar novo ambiente
conda activate tts-webui

# 5. Reinstalar dependências
pip install -r requirements.txt

# 6. Verificar CUDA (se GPU disponível)
python -c "import torch; print(f'CUDA: {torch.cuda.is_available()}')"
\`\`\`

## Opção 2: Migrar para venv (Mais leve)

\`\`\`bash
# 1. Criar venv
python3.11 -m venv /opt/tts-webui-venv

# 2. Ativar
source /opt/tts-webui-venv/bin/activate

# 3. Atualizar pip
pip install --upgrade pip setuptools wheel

# 4. Instalar dependências
pip install -r requirements.txt

# 5. Verificar instalação
pip list | grep -E "coqui-tts|torch|celery|redis"
\`\`\`

## Opção 3: Docker (Isolamento Completo)

\`\`\`bash
# Rebuild imagem Docker (já remove F5-TTS via requirements.txt limpo)
docker-compose build --no-cache

# Rodar container
docker-compose up -d
\`\`\`

## Verificação Pós-Setup

\`\`\`bash
# Verificar que F5-TTS não está instalado
pip list | grep f5-tts  # deve retornar vazio
pip list | grep vocos   # deve retornar vazio

# Verificar que XTTS funciona
python -c "from TTS.api import TTS; tts = TTS('tts_models/multilingual/multi-dataset/xtts_v2'); print('XTTS OK')"
\`\`\`

## Troubleshooting

**Erro: "No module named 'f5_tts'"**
- Solução: Ambiente antigo ainda ativo. Recriar venv/conda.

**Erro: CUDA not available**
- Verificar drivers NVIDIA: `nvidia-smi`
- Reinstalar PyTorch com CUDA: `pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118`

**Erro: Celery não conecta ao Redis**
- Verificar Redis: `redis-cli ping` (esperado: PONG)
- Verificar .env: `REDIS_HOST=localhost` e `REDIS_PORT=6379`
\`\`\`

---

## 📊 FASE 7: DOCUMENTAÇÃO FINAL

Criar arquivo `F5_TTS_REMOVED.md`:

```markdown
# ✅ F5-TTS Completamente Removido

**Data da Remoção:** $(date +%Y-%m-%d)  
**Responsável:** [Seu Nome]  
**Motivo:** Simplificação do projeto - manter apenas XTTS como engine TTS

---

## 🗑️ O Que Foi Removido

### Código Python (18 arquivos)
- ✅ `app/engines/f5tts_engine.py` (432 linhas)
- ✅ `app/engines/f5tts_ptbr_engine.py` (315 linhas)
- ✅ `test_f5tts_init.py`
- ✅ `test_f5tts_finetuned.py`
- ✅ `test_pretrained_inference.py`
- ✅ `test_voice_clone_quality.py`
- ✅ `tests/unit/engines/test_f5tts_engine.py`
- ✅ `tests/train/` (pasta inteira)

### Infraestrutura de Treinamento
- ✅ `train/` (pasta completa - ~5GB)
  - Datasets (f5_dataset, f5_dataset_pinyin)
  - Checkpoints (ptbr_finetuned2/)
  - Scripts de treinamento (50+ arquivos)
  - Configs YAML, vocabs, logging

### Dependências (requirements.txt)
- ✅ `f5-tts==1.1.9`
- ✅ `cached-path>=1.6.2`
- ✅ `faster-whisper>=1.0.0`
- ✅ `vocos==0.1.0`

### Configurações (.env.example)
- ✅ Seção F5-TTS completa (30+ variáveis)
  - F5TTS_ENABLED, F5TTS_MODEL, F5TTS_DEVICE
  - Quality profiles (NFE_STEP_*, CFG_STRENGTH, etc.)
  - DSP settings (DENOISE, DEESSING, filters)
  - Whisper transcription config

### Quality Profiles
- ✅ Enum `TTSEngine.F5TTS`
- ✅ Classe `F5TTSQualityProfile`
- ✅ Profiles padrão: F5TTS_FAST, F5TTS_BALANCED, F5TTS_ULTRA_QUALITY

### Symlinks
- ✅ `/runs` (interno)
- ✅ `train/data/f5_dataset_pinyin` (interno)
- ✅ `models/f5tts/` (HuggingFace cache)
- ⚠️ Externos em `/root/.local/lib/python3.11/` (verificar manualmente)

### Documentação
- ✅ `SPRINTS_PLAN.md`
- ✅ `MORE.md`
- ✅ `docs/F5TTS_QUALITY_FIX.md`
- ✅ `FIX_CHECKPOINTS_*.md`

---

## ✅ O Que Permaneceu (XTTS Intacto)

### Código Funcional
- ✅ `app/engines/xtts_engine.py` - Engine principal (funcional)
- ✅ `app/engines/factory.py` - Factory (apenas XTTS)
- ✅ `app/main.py` - API endpoints (rejeitam f5tts)
- ✅ `app/processor.py` - VoiceProcessor (XTTS + RVC)

### Dependências Mantidas
- ✅ `coqui-tts` (XTTS)
- ✅ `torch`, `torchaudio` (GPU)
- ✅ `celery`, `redis` (processamento assíncrono)
- ✅ `faiss-cpu`, `praat-parselmouth` (RVC)

### Funcionalidades XTTS
- ✅ Dublagem com voz genérica (`mode=dubbing`)
- ✅ Dublagem com voz clonada (`mode=dubbing_with_clone`)
- ✅ Clonagem de voz (`POST /voices/clone`)
- ✅ RVC voice conversion (Sprint 7)
- ✅ Quality profiles XTTS (fast, balanced, ultra)

---

## 🔧 Modificações em Arquivos Existentes

### app/engines/factory.py
- ❌ Removido: Import `F5TtsEngine`, `F5TtsPtBrEngine`
- ❌ Removido: Entradas `'f5tts'` e `'f5tts-ptbr'` do registry
- ✅ Mantido: Apenas `'xtts'`

### app/quality_profiles.py
- ❌ Removido: Enum `TTSEngine.F5TTS`
- ❌ Removido: Classe `F5TTSQualityProfile`
- ❌ Removido: Profiles F5TTS_FAST, F5TTS_BALANCED, F5TTS_ULTRA_QUALITY
- ✅ Mantido: `TTSEngine.XTTS` e `XTTSQualityProfile`

### app/main.py
- ✅ Parâmetro `tts_engine` mantido (backwards-compatible)
- ✅ Validação adicionada: rejeita `engine=f5tts` com HTTP 400
- ✅ Descrição atualizada: "only 'xtts' is supported"

### requirements.txt
- ❌ Removido: f5-tts, vocos, faster-whisper, cached-path
- ✅ Mantido: coqui-tts, torch, celery, redis, fastapi

### .env.example
- ❌ Removido: Seção F5-TTS inteira (linhas 69-104)
- ✅ Mantido: Seções XTTS, RVC, Celery, Redis

---

## 🧪 Testes de Regressão Executados

### API (XTTS funcional)
\`\`\`bash
✅ POST /jobs (xtts, dubbing) - HTTP 200
✅ POST /jobs (xtts, dubbing_with_clone) - HTTP 200
✅ POST /voices/clone (xtts) - HTTP 202
❌ POST /jobs (f5tts, *) - HTTP 400 "F5-TTS engine removed"
\`\`\`

### Engines
\`\`\`bash
✅ XTTS inicializa corretamente (GPU/CPU fallback)
✅ XTTS gera áudio com qualidade esperada
✅ RVC pipeline funciona com XTTS
\`\`\`

### Dependências
\`\`\`bash
❌ pip list | grep f5-tts  # vazio (correto)
❌ pip list | grep vocos   # vazio (correto)
✅ pip list | grep coqui-tts  # instalado (correto)
\`\`\`

---

## 📈 Impacto da Remoção

### Espaço em Disco
- **Removido:** ~5-10 GB (train/ + models/f5tts/)
- **Economizado:** Backups menores, builds Docker mais rápidos

### Complexidade
- **Antes:** 2 engines (XTTS + F5-TTS), 2 sets de quality profiles
- **Depois:** 1 engine (XTTS), arquitetura simplificada

### Dependências
- **Antes:** 60+ pacotes PyPI
- **Depois:** 55- pacotes PyPI (menos conflitos de versão)

---

## 🚀 Próximos Passos

1. ✅ Remover variáveis F5-TTS do `.env` em produção
2. ✅ Atualizar documentação de usuário final (remover menções a F5-TTS)
3. ✅ Notificar equipe sobre mudança de API (f5tts não mais suportado)
4. ⏭️ Monitorar logs para garantir que ninguém está tentando usar f5tts

---

## 📞 Suporte

**Erro ao tentar usar F5-TTS:**
- Mensagem: "F5-TTS engine has been removed. Please use 'xtts' instead."
- Solução: Mudar `tts_engine=xtts` nas requisições

**Performance XTTS pior que F5-TTS:**
- Solução: Usar quality profiles XTTS (`xtts_ultra_quality` para máxima qualidade)
- Referência: `GET /quality-profiles` para listar perfis disponíveis
\`\`\`

---

## 🎯 RESUMO DE AÇÕES

### Remover
1. ✅ Arquivos Python: `app/engines/f5tts*.py`, `test_f5tts*.py`, `tests/train/`
2. ✅ Pasta: `train/` (inteira)
3. ✅ Symlinks: `runs/`, `models/f5tts/`, `train/data/f5_dataset_pinyin`
4. ✅ Dependências: `f5-tts`, `vocos`, `faster-whisper`, `cached-path`
5. ✅ Configs: Seção F5-TTS do `.env.example` (30+ vars)
6. ✅ Documentação: `SPRINTS_PLAN.md`, `MORE.md`, `docs/F5TTS_*.md`

### Modificar
1. ✅ `app/engines/factory.py` - Remove F5TTS do registry
2. ✅ `app/quality_profiles.py` - Remove enum F5TTS e profiles
3. ✅ `app/main.py` - Adiciona validação para rejeitar f5tts
4. ✅ `requirements.txt` - Remove dependências F5-TTS
5. ✅ `.env.example` - Remove seção F5-TTS
6. ✅ `README.md`, `docs/ARCHITECTURE.md` - Atualiza features

### Criar
1. ✅ `REMOVE_F5_SYMLINKS.sh` - Script para symlinks externos
2. ✅ `PYTHON_ENV_RESET.md` - Guia de reset de ambiente
3. ✅ `F5_TTS_REMOVED.md` - Documentação final

---

## ⚠️ AVISOS IMPORTANTES

1. **BACKUP OBRIGATÓRIO** antes de executar (ver ETAPA 1)
2. **Symlinks externos** devem ser inspecionados manualmente antes de remover
3. **Ambiente Python** deve ser recriado após remoção (ver `PYTHON_ENV_RESET.md`)
4. **API backwards-compatible** mas rejeita `f5tts` - avisar usuários
5. **Testes de regressão XTTS** obrigatórios pós-remoção (ver FASE 4.2)

---

**FIM DO PLANO**
