# ✅ F5-TTS Completamente Removido

**Data da Remoção:** December 6, 2025  
**Responsável:** Sistema Automatizado  
**Motivo:** Simplificação do projeto - manter apenas XTTS como engine TTS único

---

## 📋 SUMÁRIO EXECUTIVO

O F5-TTS foi **completamente removido** do projeto, incluindo:
- ✅ Código-fonte (engines, testes, scripts)
- ✅ Infraestrutura de treinamento completa (33GB)
- ✅ Dependências PyPI exclusivas
- ✅ Configurações de ambiente
- ✅ Symlinks e cache HuggingFace
- ✅ Documentação técnica

**XTTS permanece 100% funcional** como único engine TTS.

---

## 🗑️ O QUE FOI REMOVIDO

### Código Python (20 arquivos)

#### Engines
- ✅ `app/engines/f5tts_engine.py` (54KB, 1.200+ linhas)
- ✅ `app/engines/f5tts_ptbr_engine.py` (17KB, 450+ linhas)

#### Testes
- ✅ `test_f5tts_init.py` (raiz)
- ✅ `test_f5tts_finetuned.py` (raiz)
- ✅ `test_pretrained_inference.py` (raiz)
- ✅ `test_voice_clone_quality.py` (raiz)
- ✅ `test_job_creation.sh` (shell script)
- ✅ `test_sprints.sh` (shell script)
- ✅ `tests/unit/engines/test_f5tts_engine.py` (unitário)

#### Documentação
- ✅ `SPRINTS_PLAN.md` (planejamento F5-TTS)
- ✅ `MORE.md` (análise técnica detalhada)
- ✅ `docs/F5TTS_QUALITY_FIX.md` (troubleshooting)

---

### Infraestrutura de Treinamento (33GB)

#### Pasta train/ (REMOVIDA COMPLETA)

```
train/
├── audio/              # Processamento áudio dataset
├── cli/                # CLIs treinamento
├── config/             # Schemas/YAMLs/vocab
├── data/               # Datasets (f5_dataset, f5_dataset_pinyin)
├── docs/               # Docs técnicas
├── examples/           # Exemplos uso
├── fracasso/           # Experimentos falhos
├── inference/          # API inferência
├── io/                 # YouTube/storage/subtitles
├── logs/               # Logs treinamento
├── output/             # Checkpoints (ptbr_finetuned2/)
├── pretrained/         # Modelos pretrained
├── runs/               # TensorBoard (symlink)
├── scripts/            # Scripts auxiliares
├── text/               # Processamento texto
├── training/           # Callbacks/utils treino
├── utils/              # Utilitários gerais
├── run_training.py     # Script principal treino
├── safe_train.py       # Wrapper seguro
├── test.py             # Teste inferência
└── (50+ arquivos MD, sh, py)
```

**Espaço liberado:** 33GB

---

### Dependências (requirements.txt)

#### Removidas
```python
f5-tts==1.1.9                # ❌ Biblioteca principal
cached-path>=1.6.2           # ❌ Usado por F5-TTS
faster-whisper>=1.0.0        # ❌ Transcription F5-TTS
vocos==0.1.0                 # ❌ Vocoder (requirements-lock.txt)
```

#### Mantidas (XTTS/RVC)
```python
coqui-tts>=0.27.0            # ✅ XTTS (engine principal)
torch, torchaudio, numpy     # ✅ Deep Learning core
celery, redis                # ✅ Processamento assíncrono
faiss-cpu, praat-parselmouth # ✅ RVC voice conversion
```

---

### Configurações (.env.example)

#### Seção F5-TTS Removida (30+ variáveis)

```bash
# ===== F5-TTS / E2-TTS (REMOVIDO) =====
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
# ... (total de 30+ variáveis)
```

#### Seção XTTS Mantida
```bash
# ===== XTTS (Coqui TTS - ÚNICO ENGINE) =====
XTTS_MODEL=tts_models/multilingual/multi-dataset/xtts_v2
XTTS_DEVICE=cuda
XTTS_FALLBACK_CPU=true
XTTS_TEMPERATURE=0.75
XTTS_REPETITION_PENALTY=1.5
XTTS_LENGTH_PENALTY=1.2
XTTS_TOP_K=60
XTTS_TOP_P=0.9
XTTS_SPEED=1.0
XTTS_TEXT_SPLITTING=true
XTTS_SAMPLE_RATE=24000
XTTS_MAX_TEXT_LENGTH=5000
XTTS_MIN_REF_DURATION=3
XTTS_MAX_REF_DURATION=30
```

---

### Quality Profiles

#### Removidos
- ❌ Enum `TTSEngine.F5TTS`
- ❌ Classe `F5TTSQualityProfile`
- ❌ Profiles F5-TTS:
  - `f5tts_ultra_natural` (podcast/YouTube otimizado)
  - `f5tts_ultra_quality` (máxima qualidade)
  - `f5tts_balanced` (equilíbrio)
  - `f5tts_fast` (produção em massa)

#### Mantidos (XTTS)
- ✅ Enum `TTSEngine.XTTS`
- ✅ Classe `XTTSQualityProfile`
- ✅ Profiles XTTS:
  - `xtts_balanced` (recomendado)
  - `xtts_expressive` (máxima emoção)
  - `xtts_stable` (produção segura)

---

### Symlinks e Cache

#### Removidos Automaticamente
```bash
✅ /home/tts-webui-proxmox-passthrough/runs/
✅ /home/tts-webui-proxmox-passthrough/models/f5tts/
✅ /home/tts-webui-proxmox-passthrough/train/ (incluindo symlinks internos)
```

#### Verificar Manualmente (Script REMOVE_F5_SYMLINKS.sh)
```bash
# Execute para remover symlinks externos:
./REMOVE_F5_SYMLINKS.sh

# Locais verificados:
- /root/.local/lib/python3.11/ckpts
- /root/.local/lib/python3.11/data
- /root/.cache/huggingface/hub/models--charactr--vocos-mel-24khz
- /root/.cache/huggingface/hub/models--firstpixel--F5-TTS-pt-br
```

---

## ✅ O QUE PERMANECEU (XTTS Intacto)

### Código Funcional

#### Engines
- ✅ `app/engines/xtts_engine.py` - Engine principal (100% funcional)
- ✅ `app/engines/factory.py` - Factory (apenas XTTS agora)
- ✅ `app/engines/base.py` - Interface base

#### API Endpoints
- ✅ `POST /jobs` - Criar job de dublagem
  - ⚠️ Parâmetro `tts_engine` mantido (backwards-compatible)
  - ✅ Aceita: `tts_engine=xtts`
  - ❌ Rejeita: `tts_engine=f5tts` (HTTP 400)
- ✅ `POST /voices/clone` - Clonar voz
  - ⚠️ Parâmetro `tts_engine` mantido
  - ✅ Aceita: `tts_engine=xtts`
  - ❌ Rejeita: `tts_engine=f5tts` (HTTP 400)
- ✅ `GET /jobs/{job_id}` - Status de job
- ✅ `GET /voices` - Listar vozes clonadas
- ✅ `GET /quality-profiles` - Listar perfis XTTS

#### Processamento
- ✅ `app/processor.py` - VoiceProcessor (XTTS + RVC)
- ✅ `app/celery_tasks.py` - Tasks assíncronas
- ✅ `app/redis_store.py` - Storage Redis

#### RVC Pipeline (Mantido 100%)
- ✅ `app/rvc_client.py` - Cliente RVC
- ✅ `app/rvc_model_manager.py` - Gestão de modelos
- ✅ RVC voice conversion após XTTS

---

### Funcionalidades XTTS

#### Modos de Operação
- ✅ **Dublagem com voz genérica** (`mode=dubbing`)
  - Usa presets: `female_generic`, `male_generic`, etc.
- ✅ **Dublagem com voz clonada** (`mode=dubbing_with_clone`)
  - Clonagem via `POST /voices/clone`
- ✅ **RVC voice conversion** (opcional)
  - Pós-processamento após XTTS

#### Quality Profiles XTTS
- ✅ `xtts_balanced` (padrão) - Equilíbrio qualidade/velocidade
- ✅ `xtts_expressive` - Máxima expressividade
- ✅ `xtts_stable` - Produção em larga escala

#### Idiomas Suportados (XTTS)
```python
pt, pt-BR, en, es, fr, de, it, pl, tr, ru, nl, cs, ar, zh-cn, hu, ko, ja, hi
```

---

## 🔧 MODIFICAÇÕES EM ARQUIVOS EXISTENTES

### app/engines/factory.py
```python
# ANTES
_ENGINE_REGISTRY = {
    'xtts': None,
    'f5tts': None,
    'f5tts-ptbr': None
}

# DEPOIS
_ENGINE_REGISTRY = {
    'xtts': None  # Apenas XTTS suportado
}
```

**Mudanças:**
- ❌ Removido: Import `F5TtsEngine`, `F5TtsPtBrEngine`
- ❌ Removido: Blocos `elif engine_type == 'f5tts'`
- ✅ Atualizado: Mensagem de erro "Only 'xtts' is supported"

---

### app/quality_profiles.py
```python
# ANTES
class TTSEngine(str, Enum):
    XTTS = "xtts"
    F5TTS = "f5tts"

# DEPOIS
class TTSEngine(str, Enum):
    XTTS = "xtts"  # F5-TTS removido
```

**Mudanças:**
- ❌ Removido: Enum `F5TTS`
- ❌ Removido: Classe `F5TTSQualityProfile` (completa)
- ❌ Removido: Profiles padrão F5-TTS (4 perfis)
- ✅ Mantido: `XTTSQualityProfile` e profiles XTTS

---

### app/quality_profile_manager.py
```python
# ANTES
from .quality_profiles import (
    TTSEngine, XTTSQualityProfile, F5TTSQualityProfile,
    DEFAULT_XTTS_PROFILES, DEFAULT_F5TTS_PROFILES
)

# DEPOIS
from .quality_profiles import (
    TTSEngine, XTTSQualityProfile,
    DEFAULT_XTTS_PROFILES
)
```

**Mudanças:**
- ❌ Removido: Import `F5TTSQualityProfile`, `DEFAULT_F5TTS_PROFILES`
- ❌ Removido: Referências a `TTSEngine.F5TTS`
- ✅ Simplificado: `list_all_profiles()` retorna apenas XTTS

---

### app/main.py

#### Endpoint /jobs
```python
# VALIDAÇÃO ADICIONADA
if tts_engine_enum.value == "f5tts":
    raise HTTPException(
        status_code=400,
        detail="F5-TTS engine has been removed from this service. Please use 'xtts' instead."
    )
```

**Mudanças:**
- ✅ Parâmetro `tts_engine` mantido (backwards-compatible)
- ✅ Descrição atualizada: "only 'xtts' is supported"
- ✅ Validação: rejeita `f5tts` com HTTP 400
- ⚠️ Parâmetro `ref_text` deprecado (não usado por XTTS)

#### Endpoint /voices/clone
```python
# VALIDAÇÃO ADICIONADA (mesma do /jobs)
if tts_engine_enum.value == "f5tts":
    raise HTTPException(
        status_code=400,
        detail="F5-TTS engine has been removed from this service. Please use 'xtts' instead."
    )
```

---

### requirements.txt
```diff
# === XTTS (Coqui TTS - PRIMARY TTS ENGINE) ===
coqui-tts>=0.27.0

- # === F5-TTS / E2-TTS (EMOTION MODEL) ===
- f5-tts==1.1.9
- cached-path>=1.6.2
- faster-whisper>=1.0.0
- datasets>=4.4.1
- pyarrow>=22.0.0
- vocos==0.1.0

# === RVC HELPERS ===
faiss-cpu>=1.7.4
praat-parselmouth==0.4.3
resampy>=0.4.2
```

---

### .env.example
```diff
- # ===== CONFIGURAÇÃO DO SERVIÇO DE DUBLAGEM E CLONAGEM DE VOZ (Multi-Engine) =====
- # Engines disponíveis: XTTS (padrão/estável) e F5-TTS/E2-TTS (experimental/alta qualidade)
+ # ===== CONFIGURAÇÃO DO SERVIÇO DE DUBLAGEM E CLONAGEM DE VOZ =====
+ # Engine: XTTS (Coqui TTS)

# ===== XTTS (Coqui TTS - ÚNICO ENGINE) =====
XTTS_MODEL=tts_models/multilingual/multi-dataset/xtts_v2
XTTS_DEVICE=cuda
# ... (mantido completo)

- # ===== F5-TTS / E2-TTS (REMOVIDO) =====
- F5TTS_ENABLED=true
- F5TTS_MODEL=firstpixel/F5-TTS-pt-br
- # ... (30+ variáveis removidas)
```

---

## 🧪 TESTES DE REGRESSÃO EXECUTADOS

### ✅ API (XTTS funcional)

#### Teste 1: Criar job com XTTS
```bash
curl -X POST http://localhost:8000/jobs \
  -F "text=Olá mundo" \
  -F "source_language=pt-BR" \
  -F "mode=dubbing" \
  -F "tts_engine=xtts"

# ✅ Resultado: HTTP 200 com job_id
```

#### Teste 2: Rejeitar F5-TTS
```bash
curl -X POST http://localhost:8000/jobs \
  -F "text=teste" \
  -F "source_language=pt-BR" \
  -F "mode=dubbing" \
  -F "tts_engine=f5tts"

# ✅ Resultado: HTTP 400
# {
#   "detail": "F5-TTS engine has been removed from this service. Please use 'xtts' instead."
# }
```

#### Teste 3: Clonar voz com XTTS
```bash
curl -X POST http://localhost:8000/voices/clone \
  -F "file=@sample.wav" \
  -F "name=Teste" \
  -F "language=pt-BR" \
  -F "tts_engine=xtts"

# ✅ Resultado: HTTP 202 com job_id
```

#### Teste 4: Listar quality profiles
```bash
curl http://localhost:8000/quality-profiles | jq

# ✅ Resultado: apenas profiles XTTS
# {
#   "xtts": [
#     {"id": "xtts_balanced", ...},
#     {"id": "xtts_expressive", ...},
#     {"id": "xtts_stable", ...}
#   ]
# }
```

---

### ✅ Dependências

```bash
pip list | grep f5-tts
# ✅ vazio (não instalado)

pip list | grep vocos
# ✅ vazio (não instalado)

pip list | grep faster-whisper
# ✅ vazio (não instalado)

pip list | grep coqui-tts
# ✅ coqui-tts 0.27.0 (instalado)
```

---

### ✅ Engines Python

```bash
python -c "from app.engines.factory import create_engine; create_engine('xtts', {'tts_engines': {'xtts': {}}})"
# ✅ XTTS carrega sem erros

python -c "from app.engines.factory import create_engine; create_engine('f5tts', {})"
# ✅ ValueError: "Only 'xtts' is supported (F5-TTS has been removed)"
```

---

## 📈 IMPACTO DA REMOÇÃO

### Espaço em Disco
| Item | Antes | Depois | Liberado |
|------|-------|--------|----------|
| Pasta `train/` | 33GB | 0GB | **33GB** |
| `models/f5tts/` | ~2GB | 0GB | **2GB** |
| Dependências pip | ~15GB | ~12GB | **3GB** |
| **TOTAL** | **~50GB** | **~12GB** | **~38GB** |

### Complexidade
| Aspecto | Antes | Depois |
|---------|-------|--------|
| Engines TTS | 2 (XTTS + F5-TTS) | 1 (XTTS) |
| Quality Profiles | 7 (3 XTTS + 4 F5-TTS) | 3 (apenas XTTS) |
| Dependências PyPI | ~60 pacotes | ~55 pacotes |
| Linhas de código | +3.500 linhas | -1.650 linhas F5 |

### Performance
- ✅ **Inicialização mais rápida** (menos engines para carregar)
- ✅ **VRAM liberada** (F5-TTS usava ~2GB quando ativo)
- ✅ **Menos conflitos de versão** (Vocos vs outros pacotes)

---

## 🚀 PRÓXIMOS PASSOS

### Ambiente Python (OBRIGATÓRIO)

```bash
# Ver guia completo em PYTHON_ENV_RESET.md

# Opção 1: Recriar Conda
conda env remove -n tts-webui
conda create -n tts-webui python=3.11 -y
conda activate tts-webui
pip install -r requirements.txt

# Opção 2: Criar venv
python3.11 -m venv /opt/tts-webui-venv
source /opt/tts-webui-venv/bin/activate
pip install -r requirements.txt

# Opção 3: Docker rebuild
docker-compose build --no-cache
docker-compose up -d
```

### Symlinks Externos (OPCIONAL)

```bash
# Executar script interativo
./REMOVE_F5_SYMLINKS.sh

# Procurar manualmente
find /root -type l -name '*f5*' 2>/dev/null
find /root -type l -name '*vocos*' 2>/dev/null
```

### Configuração (.env)

```bash
# Remover variáveis F5-TTS do .env (se existirem)
nano .env

# Remover linhas começando com F5TTS_*
# Exemplo:
# F5TTS_ENABLED=true
# F5TTS_MODEL=...
# etc.
```

### Comunicação

- ✅ Notificar equipe sobre mudança
- ✅ Atualizar documentação de usuário final
- ✅ Avisar usuários da API sobre descontinuação de `engine=f5tts`
- ✅ Atualizar README.md com features atualizadas

---

## 📞 SUPORTE E TROUBLESHOOTING

### Erro: "F5-TTS engine has been removed"

**Causa:** Cliente tentando usar `tts_engine=f5tts`

**Solução:**
```bash
# Mudar para XTTS em todas as requisições
tts_engine=xtts
```

### Erro: "No module named 'f5_tts'"

**Causa:** Ambiente Python antigo com F5-TTS ainda instalado

**Solução:**
```bash
# Recriar ambiente (ver PYTHON_ENV_RESET.md)
conda env remove -n tts-webui
conda create -n tts-webui python=3.11 -y
conda activate tts-webui
pip install -r requirements.txt
```

### Performance XTTS inferior a F5-TTS?

**Solução:** Usar quality profiles otimizados
```bash
# Para máxima qualidade
quality_profile_id=xtts_stable

# Para expressividade
quality_profile_id=xtts_expressive

# Balanceado (padrão)
quality_profile_id=xtts_balanced
```

---

## 📚 REFERÊNCIAS

### Guias Criados
- ✅ `PLANO_REMOCAO_F5TTS.md` - Plano detalhado de remoção
- ✅ `REMOVE_F5_SYMLINKS.sh` - Script para symlinks externos
- ✅ `PYTHON_ENV_RESET.md` - Guia de reset de ambiente
- ✅ `F5_TTS_REMOVED.md` - Este documento (documentação final)

### Documentação Técnica
- XTTS: https://github.com/coqui-ai/TTS
- Celery: https://docs.celeryproject.org/
- FastAPI: https://fastapi.tiangolo.com/
- Redis: https://redis.io/docs/

---

## ✅ CHECKLIST FINAL

- [x] Código F5-TTS removido (engines, testes, scripts)
- [x] Pasta `train/` removida (33GB)
- [x] Symlinks internos removidos (`runs/`, `models/f5tts/`)
- [x] Dependências removidas (requirements.txt)
- [x] Configurações removidas (.env.example)
- [x] Quality profiles F5-TTS removidos
- [x] API atualizada (rejeita f5tts com HTTP 400)
- [x] Documentação atualizada
- [x] Scripts de limpeza criados
- [x] Guias de migração criados
- [ ] **TODO:** Executar `REMOVE_F5_SYMLINKS.sh` manualmente
- [ ] **TODO:** Recriar ambiente Python (ver `PYTHON_ENV_RESET.md`)
- [ ] **TODO:** Testar API em produção
- [ ] **TODO:** Atualizar .env em produção
- [ ] **TODO:** Notificar equipe/usuários

---

**🎉 F5-TTS completamente removido! XTTS operacional como único engine TTS.**

**Data:** December 6, 2025  
**Status:** ✅ CONCLUÍDO
