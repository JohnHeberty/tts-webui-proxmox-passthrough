# SPRINTS – RVC Removal & XTTS-v2 Consolidation

**Data início**: 2025-12-07  
**Baseado em**: [MORE.md](./MORE.md) - Análise completa do projeto  
**Objetivo**: Remover 100% do RVC e consolidar para XTTS-v2 puro com arquitetura SOLID

---

## 📊 Visão Geral

| Sprint | Foco | Duração | Prioridade | Status |
|--------|------|---------|------------|--------|
| Sprint RVC-0 | RVC Cleanup Completo | 3-4h | P0 CRÍTICO | 🔄 Em andamento |
| Sprint ARCH-1 | Arquitetura SOLID + Eager Load | 4-5h | P0 CRÍTICO | ⏳ Pendente |
| Sprint CONFIG-2 | Configuração Centralizada | 2-3h | P1 HIGH | ⏳ Pendente |
| Sprint TRAIN-3 | Pipeline Treinamento | 3-4h | P1 HIGH | ⏳ Pendente |
| Sprint QUALITY-4 | Perfis de Qualidade | 2-3h | P2 MEDIUM | ⏳ Pendente |
| Sprint RESIL-5 | Resiliência & Observabilidade | 3-4h | P1 HIGH | ⏳ Pendente |
| Sprint FINAL-6 | WebUI, Docs & Polish | 2-3h | P2 MEDIUM | ⏳ Pendente |

**Total estimado**: 19-26 horas

---

## 🔥 Sprint RVC-0: RVC Cleanup Completo

**Objetivo**: Remover 100% dos vestígios RVC do projeto (código, configs, deps, testes, docs)

**Duração**: 3-4 horas  
**Prioridade**: P0 (CRÍTICO - bloqueia tudo)  
**Status**: 🔄 Em andamento

### Inventário RVC (de MORE.md)

**Python (990+ linhas):**
- `app/rvc_client.py` (327 linhas)
- `app/rvc_model_manager.py` (330 linhas)
- `app/rvc_dependencies.py`
- `app/models.py`: RvcModel, RvcParameters
- `app/exceptions.py`: 6 classes Rvc*
- `app/metrics.py`: métricas RVC (linhas 92-157)
- `app/engines/xtts_engine.py`: integração (linhas 147-621 = 474 linhas)

**API Endpoints:**
- `/rvc-models` (GET, POST, DELETE)
- `/rvc-models/{id}` (GET, DELETE)
- Parâmetros em `/jobs`: enable_rvc, rvc_model_id, etc.

**Config:**
- `app/config.py`: seção RVC (linhas 135-151)
- `.env`: vars RVC_DEVICE, RVC_MODELS_DIR

**Scripts:**
- `scripts/validate-deps.sh` (RVC checks)
- `scripts/validate-sprint4.sh` (XTTS+RVC integration)
- `scripts/validate-gpu.sh` (RVC VRAM checks)

**Testes (7 arquivos):**
- `tests/test_rvc_*.py`
- `tests/test_xtts_rvc_integration.py`

**Dependencies (requirements.txt):**
- tts-with-rvc
- fairseq
- praat-parselmouth
- pyworld
- torchcrepe
- (+ ~10 dependências transitivas)

---

### Tasks (ordem segura de remoção)

#### ✅ Task 0.1: Backup & Preparação (15min)
- [x] Git commit checkpoint: "pre-rvc-cleanup"
- [ ] Backup `/models/rvc` → `/archive/rvc_models_backup_20251207`
- [ ] Listar todos imports RVC:
  ```bash
  grep -r "from.*rvc" app/ --include="*.py" | tee /tmp/rvc_imports.txt
  grep -r "import.*rvc" app/ --include="*.py" | tee -a /tmp/rvc_imports.txt
  ```

**Critérios**: 
- ✅ Checkpoint commitado
- ✅ Backup de modelos RVC
- ✅ Lista de imports gerada

---

#### Task 0.2: Remover Dependencies PRIMEIRO (30min)

**Ordem crítica**: Remover deps ANTES do código para evitar build quebrado.

- [ ] Editar `requirements.txt`:
  ```bash
  # Remover estas linhas:
  tts-with-rvc
  fairseq
  praat-parselmouth
  pyworld
  torchcrepe
  ```
- [ ] Rebuild Docker:
  ```bash
  docker compose down
  docker compose build --no-cache
  ```
- [ ] Verificar build OK (sem erros de instalação)

**Critérios**:
- ✅ Dependencies RVC removidas
- ✅ Build Docker OK
- ✅ requirements.txt limpo

**Riscos**:
- 🟡 Se código RVC ainda existir, vai dar erro de import → OK, vamos remover em seguida

---

#### Task 0.3: Deletar Módulos RVC Core (30min)

- [ ] Deletar arquivos:
  ```bash
  rm app/rvc_client.py
  rm app/rvc_model_manager.py
  rm app/rvc_dependencies.py
  git add -u  # stage deletions
  ```

- [ ] Editar `app/models.py` - Remover classes RVC:
  ```python
  # REMOVER:
  class RvcModel(BaseModel):
      ...
  
  class RvcParameters(BaseModel):
      ...
  ```

- [ ] Editar `app/exceptions.py` - Remover exceções RVC:
  ```python
  # REMOVER todas as classes:
  class RvcException(BaseException): ...
  class RvcConversionException(RvcException): ...
  class RvcModelNotFoundException(RvcException): ...
  class RvcInvalidParametersException(RvcException): ...
  class RvcDeviceException(RvcException): ...
  class RvcDependencyException(RvcException): ...
  ```

- [ ] Editar `app/metrics.py` - Remover métricas RVC (linhas 92-157):
  ```python
  # REMOVER:
  rvc_conversion_total = Counter(...)
  rvc_conversion_duration_seconds = Histogram(...)
  rvc_model_load_total = Counter(...)
  # ... etc
  ```

**Critérios**:
- ✅ 3 arquivos deletados
- ✅ Nenhuma classe/métrica RVC em models.py, exceptions.py, metrics.py
- ✅ Commits: "refactor: Remove RVC core modules"

---

#### Task 0.4: Limpar xtts_engine.py (1h)

**Arquivo crítico**: `app/engines/xtts_engine.py` tem 474 linhas de RVC (linhas 147-621).

- [ ] Remover método `_load_rvc_client()` (linhas ~178-195)
- [ ] Remover método `_apply_rvc()` (linhas ~576-621)
- [ ] Remover parâmetros RVC de `synthesize()`:
  ```python
  # ANTES:
  async def synthesize(
      self, text, speaker_wav, language,
      enable_rvc=False, rvc_model_id=None, ...
  ):
  
  # DEPOIS:
  async def synthesize(
      self, text, speaker_wav, language
  ):
  ```
- [ ] Remover imports:
  ```python
  # REMOVER:
  from app.rvc_client import RvcClient
  from app.rvc_model_manager import rvc_model_manager
  ```
- [ ] Remover lógica condicional RVC:
  ```python
  # REMOVER blocos:
  if enable_rvc and rvc_model_id:
      audio = await self._apply_rvc(audio, rvc_model_id, ...)
  ```

- [ ] Validar sintaxe:
  ```bash
  python3 -m py_compile app/engines/xtts_engine.py
  ```

**Critérios**:
- ✅ 474 linhas removidas
- ✅ Nenhum import RVC
- ✅ Sem erros de sintaxe
- ✅ Commit: "refactor: Remove RVC integration from xtts_engine"

---

#### Task 0.5: Limpar API Endpoints (main.py) (45min)

`app/main.py` tem 1771 linhas - muitas são rotas RVC.

- [ ] Remover rotas RVC:
  ```python
  # REMOVER completamente:
  @app.get("/rvc-models")
  async def list_rvc_models(): ...
  
  @app.post("/rvc-models")
  async def create_rvc_model(): ...
  
  @app.delete("/rvc-models/{id}")
  async def delete_rvc_model(): ...
  
  @app.get("/rvc-models/{id}")
  async def get_rvc_model(): ...
  ```

- [ ] Remover parâmetros RVC de `/jobs`:
  ```python
  # ANTES:
  class JobRequest(BaseModel):
      text: str
      enable_rvc: bool = False
      rvc_model_id: Optional[str] = None
      ...
  
  # DEPOIS:
  class JobRequest(BaseModel):
      text: str
      # sem RVC
  ```

- [ ] Remover imports:
  ```python
  # REMOVER:
  from app.rvc_model_manager import rvc_model_manager
  ```

- [ ] Testar startup:
  ```bash
  docker compose up -d
  curl http://localhost:8005/health
  ```

**Critérios**:
- ✅ Nenhuma rota `/rvc-*`
- ✅ JobRequest sem campos RVC
- ✅ Serviço inicia sem erros
- ✅ Commit: "refactor: Remove RVC API endpoints"

---

#### Task 0.6: Limpar Configuração (20min)

- [ ] Editar `app/config.py` - Remover seção RVC (linhas 135-151):
  ```python
  # REMOVER:
  class RvcConfig:
      device: str = "cuda"
      models_dir: Path = Path("/app/models/rvc")
      ...
  ```

- [ ] Editar `.env.example`:
  ```bash
  # REMOVER:
  RVC_DEVICE=cuda
  RVC_MODELS_DIR=/app/models/rvc
  RVC_ENABLE=false
  ```

- [ ] Editar `docker-compose.yml`:
  ```yaml
  # REMOVER mapeamento:
  volumes:
    - ./models/rvc:/app/models/rvc  # ← DELETE THIS
  ```

**Critérios**:
- ✅ Sem seção RVC em config.py
- ✅ Sem vars RVC em .env.example
- ✅ Sem volume RVC em docker-compose
- ✅ Commit: "config: Remove RVC configuration"

---

#### Task 0.7: Deletar Scripts & Testes (30min)

- [ ] Deletar testes RVC:
  ```bash
  rm tests/test_rvc_client.py
  rm tests/test_rvc_client_coverage.py
  rm tests/test_rvc_dependencies.py
  rm tests/test_rvc_edge_cases.py
  rm tests/test_rvc_model_manager.py
  rm tests/test_api_rvc_endpoints.py
  rm tests/test_e2e_rvc_pipeline.py
  rm tests/test_xtts_rvc_integration.py
  ```

- [ ] Limpar `scripts/validate-deps.sh`:
  ```bash
  # Remover checks de:
  # - tts-with-rvc
  # - fairseq
  # - praat-parselmouth
  ```

- [ ] Limpar `scripts/validate-gpu.sh`:
  ```bash
  # Remover warning:
  # "RVC + XTTS requires ≥12GB VRAM"
  ```

- [ ] Deletar `scripts/validate-sprint4.sh` (era específico de RVC+XTTS):
  ```bash
  rm scripts/validate-sprint4.sh
  ```

- [ ] Rodar testes restantes:
  ```bash
  pytest tests/ -v --tb=short
  ```

**Critérios**:
- ✅ 8 arquivos de teste deletados
- ✅ Scripts de validação limpos
- ✅ Testes restantes passam
- ✅ Commit: "test: Remove RVC tests and validation scripts"

---

#### Task 0.8: Limpar Dados & Docker (15min)

- [ ] Mover modelos RVC:
  ```bash
  mkdir -p archive/rvc_backup_20251207
  mv models/rvc/* archive/rvc_backup_20251207/ 2>/dev/null || true
  rmdir models/rvc
  ```

- [ ] Editar `Dockerfile` - Remover comentários RVC:
  ```dockerfile
  # REMOVER linhas tipo:
  # Install RVC dependencies
  # RVC models will be downloaded at runtime
  ```

- [ ] Editar `docker-compose-gpu.yml` - Remover refs RVC

- [ ] Rebuild final:
  ```bash
  docker compose down
  docker compose build --no-cache
  docker compose up -d
  ```

**Critérios**:
- ✅ `/models/rvc` não existe
- ✅ Backup em `/archive`
- ✅ Dockerfile sem comentários RVC
- ✅ Serviço saudável

---

#### Task 0.9: Validação Final & Testes (30min)

- [ ] Grep por RVC remanescente:
  ```bash
  grep -ri "rvc\|voice.*conversion\|retrieval.*voice" \
    --include="*.py" --include="*.yml" --include="*.yaml" \
    app/ tests/ scripts/ docs/
  ```
  **Esperado**: 0 matches ou só em CHANGELOG/docs deprecated

- [ ] Smoke tests:
  ```bash
  # Criar job TTS
  curl -X POST http://localhost:8005/jobs \
    -H "Content-Type: application/json" \
    -d '{"text": "Test without RVC", "voice": "default"}'
  
  # Healthcheck
  curl http://localhost:8005/health
  
  # Quality profiles (sem f5tts, sem rvc)
  curl http://localhost:8005/quality-profiles
  ```

- [ ] Verificar logs:
  ```bash
  docker compose logs api | grep -i "error\|exception" | grep -i rvc
  # Esperado: nenhum erro relacionado a RVC
  ```

- [ ] Rodar suite completa:
  ```bash
  pytest tests/ -v --cov=app --cov-report=term-missing
  ```

**Critérios de Aceitação Sprint RVC-0**:
- ✅ 0 referências a RVC no código ativo
- ✅ 0 testes RVC
- ✅ 0 dependências RVC em requirements.txt
- ✅ API funciona sem parâmetros RVC
- ✅ Serviço inicia em <10s (sem RVC lazy-load)
- ✅ Testes passam (≥80% coverage)

**Commit final**:
```bash
git add -A
git commit -m "feat: Complete RVC removal from project

- Removed 990+ lines of RVC code
- Deleted 8 test files
- Cleaned 15+ dependencies
- Removed API endpoints /rvc-models
- Cleaned configuration (config.py, .env)
- Archived RVC models to /archive

BREAKING CHANGE: RVC voice conversion no longer available.
Use XTTS-v2 native voice cloning instead.

Ref: MORE.md Section 1.1"
```

---

## 🏗️ Sprint ARCH-1: Arquitetura SOLID + Eager Load

**Objetivo**: Refatorar XTTS para seguir SOLID + eager load models

**Duração**: 4-5 horas  
**Prioridade**: P0 (CRÍTICO)  
**Depende de**: Sprint RVC-0

### Tasks

#### Task 1.1: Criar XTTSService (2h)

**Novo arquivo**: `app/services/xtts_service.py`

```python
"""
XTTS-v2 Service - Single Responsibility Principle
Responsável APENAS por síntese TTS, sem HTTP, sem RVC.
"""
from pathlib import Path
from typing import Optional, Dict
import torch
import numpy as np
from TTS.tts.configs.xtts_config import XttsConfig
from TTS.tts.models.xtts import Xtts

from app.logging_config import get_logger
from app.exceptions import XTTSException

logger = get_logger(__name__)


class XTTSService:
    """
    Service layer para XTTS-v2.
    
    Principles:
    - SRP: Só TTS synthesis, nada mais
    - Eager load: Modelos carregados no startup
    - Stateless: Sem cache interno de embeddings (use Redis)
    """
    
    def __init__(self, model_path: Path, device: str = "cuda"):
        self.model_path = model_path
        self.device = device
        self.model: Optional[Xtts] = None
        self.config: Optional[XttsConfig] = None
        self._initialized = False
    
    def initialize(self) -> None:
        """
        Eager load do modelo no startup.
        Chamado via @app.on_event("startup")
        """
        if self._initialized:
            logger.warning("XTTS already initialized, skipping")
            return
        
        logger.info(f"Loading XTTS-v2 from {self.model_path}")
        
        try:
            self.config = XttsConfig()
            self.config.load_json(self.model_path / "config.json")
            
            self.model = Xtts.init_from_config(self.config)
            self.model.load_checkpoint(
                self.config, 
                checkpoint_dir=str(self.model_path),
                use_deepspeed=False
            )
            self.model.to(self.device)
            self.model.eval()
            
            self._initialized = True
            logger.info("✅ XTTS-v2 loaded successfully")
            
        except Exception as e:
            logger.error(f"Failed to load XTTS: {e}")
            raise XTTSException(f"Model initialization failed: {e}")
    
    async def synthesize(
        self,
        text: str,
        speaker_wav: Path,
        language: str = "pt",
        quality_profile: str = "balanced"
    ) -> np.ndarray:
        """
        Sintetiza áudio usando XTTS-v2.
        
        Args:
            text: Texto para sintetizar
            speaker_wav: Path do áudio de referência
            language: Código da linguagem (pt, en, es, etc.)
            quality_profile: fast | balanced | high_quality
        
        Returns:
            numpy array com áudio (sample_rate = 24000)
        """
        if not self._initialized:
            raise XTTSException("Service not initialized. Call initialize() first")
        
        # Quality profiles (implementado no Task 1.4)
        params = self._get_profile_params(quality_profile)
        
        try:
            logger.info(f"Synthesizing: {len(text)} chars, lang={language}, profile={quality_profile}")
            
            # XTTS synthesis
            outputs = self.model.synthesize(
                text=text,
                config=self.config,
                speaker_wav=str(speaker_wav),
                language=language,
                temperature=params["temperature"],
                speed=params["speed"],
                top_p=params["top_p"]
            )
            
            audio = outputs["wav"]
            
            # Denoise se high_quality
            if params.get("denoise", False):
                audio = self._apply_denoise(audio)
            
            logger.info(f"✅ Synthesis complete: {len(audio)/24000:.2f}s audio")
            return audio
            
        except Exception as e:
            logger.error(f"Synthesis failed: {e}")
            raise XTTSException(f"Synthesis error: {e}")
    
    def _get_profile_params(self, profile: str) -> Dict:
        """Retorna parâmetros do perfil de qualidade"""
        profiles = {
            "fast": {
                "temperature": 0.7,
                "speed": 1.2,
                "top_p": 0.85,
                "denoise": False
            },
            "balanced": {
                "temperature": 0.75,
                "speed": 1.0,
                "top_p": 0.9,
                "denoise": False
            },
            "high_quality": {
                "temperature": 0.6,
                "speed": 0.95,
                "top_p": 0.95,
                "denoise": True
            }
        }
        return profiles.get(profile, profiles["balanced"])
    
    def _apply_denoise(self, audio: np.ndarray) -> np.ndarray:
        """Aplica denoise (placeholder)"""
        # TODO: Implementar com noisereduce ou similar
        return audio
    
    @property
    def is_ready(self) -> bool:
        """Healthcheck"""
        return self._initialized and self.model is not None
```

**Checklist**:
- [ ] Arquivo criado em `app/services/xtts_service.py`
- [ ] Imports funcionando
- [ ] Testes unitários:
  ```python
  # tests/test_xtts_service.py
  def test_service_initialization():
      service = XTTSService(model_path, device="cpu")
      service.initialize()
      assert service.is_ready
  ```

---

#### Task 1.2: Implementar Eager Load no Startup (1h)

Editar `app/main.py`:

```python
from app.services.xtts_service import XTTSService
from app.config import settings

# Global service instance
xtts_service = XTTSService(
    model_path=settings.xtts_model_path,
    device=settings.device
)

@app.on_event("startup")
async def startup_event():
    """
    Eager load de modelos no startup.
    FastAPI vai esperar este evento completar antes de aceitar requests.
    """
    logger.info("🚀 Starting TTS WebUI...")
    
    # Load XTTS-v2 (5-10s)
    xtts_service.initialize()
    
    # Warm-up: primeira síntese (pre-aloca CUDA)
    try:
        dummy_audio = await xtts_service.synthesize(
            text="Warm up test",
            speaker_wav=Path("/app/voice_profiles/default.wav"),
            language="pt"
        )
        logger.info(f"✅ Warm-up complete: {len(dummy_audio)} samples")
    except Exception as e:
        logger.warning(f"Warm-up failed (non-critical): {e}")
    
    logger.info("✅ All models loaded. Ready to serve!")


@app.get("/health")
async def health_check():
    """Healthcheck detalhado"""
    return {
        "status": "healthy" if xtts_service.is_ready else "unhealthy",
        "components": {
            "xtts": {
                "loaded": xtts_service.is_ready,
                "device": xtts_service.device,
                "model_path": str(xtts_service.model_path)
            },
            "gpu": {
                "available": torch.cuda.is_available(),
                "device_name": torch.cuda.get_device_name(0) if torch.cuda.is_available() else None,
                "vram_allocated_gb": torch.cuda.memory_allocated(0) / 1e9 if torch.cuda.is_available() else 0
            }
        },
        "uptime_seconds": time.time() - app.state.start_time
    }

# Store start time
@app.on_event("startup")
async def store_start_time():
    app.state.start_time = time.time()
```

**Critérios**:
- ✅ Serviço inicia em 5-15s (eager load)
- ✅ Primeira request TTS retorna em <2s (sem lazy-load)
- ✅ `/health` mostra modelos carregados
- ✅ Logs mostram "All models loaded"

---

#### Task 1.3: Dependency Injection (1h)

Criar `app/dependencies.py`:

```python
"""
FastAPI Dependencies - Dependency Injection Pattern
"""
from fastapi import Depends, HTTPException
from app.services.xtts_service import XTTSService
from app.main import xtts_service  # global instance


async def get_xtts_service() -> XTTSService:
    """
    Dependency para injetar XTTSService nos endpoints.
    Garante que o serviço está inicializado.
    """
    if not xtts_service.is_ready:
        raise HTTPException(
            status_code=503,
            detail="XTTS service not ready. Server may be starting up."
        )
    return xtts_service
```

Atualizar endpoints em `main.py`:

```python
from app.dependencies import get_xtts_service

@app.post("/synthesize")
async def synthesize_endpoint(
    request: SynthesizeRequest,
    xtts: XTTSService = Depends(get_xtts_service)
):
    """
    Síntese TTS com dependency injection.
    """
    try:
        audio = await xtts.synthesize(
            text=request.text,
            speaker_wav=Path(request.speaker_wav),
            language=request.language,
            quality_profile=request.quality_profile
        )
        
        # Save to temp file
        output_path = f"/app/temp/synth_{uuid.uuid4()}.wav"
        sf.write(output_path, audio, 24000)
        
        return FileResponse(output_path, media_type="audio/wav")
        
    except XTTSException as e:
        raise HTTPException(status_code=500, detail=str(e))
```

**Critérios**:
- ✅ Endpoints usam `Depends(get_xtts_service)`
- ✅ 503 retornado se serviço não pronto
- ✅ Código mais testável (mock de dependencies)

---

#### Task 1.4: Perfis de Qualidade (1h)

Já implementado parcialmente no `XTTSService._get_profile_params()`.

Adicionar validação:

```python
# app/validators.py
from enum import Enum

class QualityProfile(str, Enum):
    FAST = "fast"
    BALANCED = "balanced"
    HIGH_QUALITY = "high_quality"

# Em main.py
from app.validators import QualityProfile

class SynthesizeRequest(BaseModel):
    text: str
    speaker_wav: str
    language: str = "pt"
    quality_profile: QualityProfile = QualityProfile.BALANCED
```

Expor via `/quality-profiles`:

```python
@app.get("/quality-profiles")
async def list_quality_profiles():
    """Lista perfis de qualidade XTTS"""
    return {
        "xtts_profiles": [
            {
                "id": "fast",
                "name": "Rápido",
                "description": "Menor latência, qualidade adequada",
                "parameters": {"temperature": 0.7, "speed": 1.2}
            },
            {
                "id": "balanced",
                "name": "Balanceado",
                "description": "Equilíbrio entre velocidade e qualidade",
                "parameters": {"temperature": 0.75, "speed": 1.0}
            },
            {
                "id": "high_quality",
                "name": "Alta Qualidade",
                "description": "Máxima qualidade, com denoise",
                "parameters": {"temperature": 0.6, "speed": 0.95, "denoise": true}
            }
        ],
        "f5tts_profiles": [],  # mantém por compatibilidade
        "total_count": 3
    }
```

**Critérios Sprint ARCH-1**:
- ✅ XTTSService criado (SRP)
- ✅ Eager load funcional (<15s startup)
- ✅ Dependency injection implementada
- ✅ 3 perfis de qualidade funcionais
- ✅ Testes passam
- ✅ Commit: "refactor: Implement SOLID architecture for XTTS"

---

## 🔧 Sprint CONFIG-2: Configuração Centralizada

**Objetivo**: Config única com Pydantic Settings + validação

**Duração**: 2-3 horas  
**Prioridade**: P1 (HIGH)

### Tasks

#### Task 2.1: Pydantic Settings (1.5h)

Criar `app/settings.py`:

```python
"""
Configuração centralizada usando Pydantic Settings.
Substitui app/config.py e .env dispersos.
"""
from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field, validator


class Settings(BaseSettings):
    """
    Configuração global do projeto.
    Carrega de .env automaticamente.
    """
    
    # Paths (validados no __init__)
    base_dir: Path = Field(default=Path("/app"))
    xtts_model_path: Path = Field(default=Path("/app/models/xtts"))
    voice_profiles_dir: Path = Field(default=Path("/app/voice_profiles"))
    temp_dir: Path = Field(default=Path("/app/temp"))
    
    # XTTS Settings
    xtts_device: str = Field(default="cuda", env="DEVICE")
    xtts_sample_rate: int = 24000
    xtts_default_language: str = "pt"
    
    # Redis
    redis_host: str = Field(default="redis", env="REDIS_HOST")
    redis_port: int = Field(default=6379, env="REDIS_PORT")
    redis_db: int = 0
    
    # Celery
    celery_broker_url: str = Field(default="redis://redis:6379/0")
    celery_result_backend: str = Field(default="redis://redis:6379/0")
    
    # API
    api_host: str = "0.0.0.0"
    api_port: int = 8005
    debug: bool = Field(default=False, env="DEBUG")
    
    # Training (consolidado)
    train_epochs: int = 20
    train_batch_size: int = 2
    train_sample_rate: int = 24000  # alinhado com XTTS
    train_max_audio_length: int = 12  # segundos
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False
    )
    
    @validator("xtts_model_path", "voice_profiles_dir", "temp_dir")
    def validate_paths_exist(cls, v: Path) -> Path:
        """Valida que paths críticos existem"""
        if not v.exists():
            raise ValueError(f"Path does not exist: {v}")
        return v
    
    @validator("xtts_device")
    def validate_device(cls, v: str) -> str:
        """Valida device CUDA"""
        if v == "cuda" and not torch.cuda.is_available():
            raise ValueError("CUDA not available, use device='cpu'")
        return v


# Singleton
settings = Settings()
```

Migrar código:

```python
# ANTES (app/config.py):
XTTS_MODEL_PATH = os.getenv("XTTS_MODEL_PATH", "/app/models/xtts")

# DEPOIS (qualquer arquivo):
from app.settings import settings
model_path = settings.xtts_model_path
```

**Critérios**:
- ✅ Settings carrega de .env
- ✅ Validação de paths funciona
- ✅ Substituir todos imports de `app/config.py`
- ✅ Deletar `app/config.py` obsoleto

---

#### Task 2.2: Consolidar Train Configs (1h)

Mesclar YAMLs em `train/config/`:

```bash
# Antes:
train/config/audio_config.yaml
train/config/model_config.yaml
train/config/training_config.yaml

# Depois:
train/config/xtts_train.yaml  # único arquivo
```

Conteúdo de `xtts_train.yaml`:

```yaml
# XTTS-v2 Training Configuration
# Alinhado com app/settings.py

audio:
  sample_rate: 24000  # FIXO - alinhado com inference
  max_length_seconds: 12
  normalization: "lufs"  # -20 LUFS target
  target_lufs: -20.0

model:
  architecture: "xtts-v2"
  checkpoint: "/app/models/xtts/base_model"

training:
  epochs: 20
  batch_size: 2
  gradient_accumulation_steps: 4
  learning_rate: 1.0e-5
  warmup_steps: 100
  
  # GPU optimization
  use_mixed_precision: true
  gradient_checkpointing: true

validation:
  val_split: 0.1
  val_check_interval: 500
  
logging:
  tensorboard_dir: "/app/train/logs/tensorboard"
  checkpoint_dir: "/app/train/output/checkpoints"
```

Usar em scripts:

```python
# train/scripts/train_pipeline.py
import yaml
from app.settings import settings

with open("train/config/xtts_train.yaml") as f:
    train_config = yaml.safe_load(f)

# Validar alinhamento
assert train_config["audio"]["sample_rate"] == settings.xtts_sample_rate
```

**Critérios Sprint CONFIG-2**:
- ✅ Pydantic Settings funcional
- ✅ .env centralizado
- ✅ Train config único (YAML)
- ✅ Sample rate alinhado (24kHz)
- ✅ Commit: "config: Centralize configuration with Pydantic Settings"

---

## 🎓 Sprint TRAIN-3: Pipeline Treinamento

**Objetivo**: Pipeline limpo e alinhado com guia XTTS

**Duração**: 3-4 horas  
**Prioridade**: P1 (HIGH)

### Tasks

#### Task 3.1: Consolidar Scripts (30min)

```bash
# Remover duplicados
rm train/scripts/pipeline_v2.py
rm train/scripts/pipeline_backup.py

# Manter apenas:
train/scripts/train_pipeline.py  # ÚNICO script de treino
```

---

#### Task 3.2: Implementar Normalização -20 LUFS (1.5h)

Adicionar em `train/scripts/audio_preprocessing.py`:

```python
import ffmpeg
import soundfile as sf
import numpy as np

def normalize_lufs(input_path: Path, target_lufs: float = -20.0) -> np.ndarray:
    """
    Normaliza áudio para target LUFS usando ffmpeg loudnorm.
    
    Args:
        input_path: Path do áudio original
        target_lufs: Target em LUFS (default -20.0)
    
    Returns:
        numpy array normalizado
    """
    try:
        # Pass 1: Measure loudness
        probe = ffmpeg.probe(
            str(input_path),
            f="lavfi",
            i=f"amovie={input_path},ebur128=metadata=1"
        )
        
        # Pass 2: Apply loudnorm
        output, _ = (
            ffmpeg
            .input(str(input_path))
            .filter("loudnorm", I=target_lufs, TP=-1.5, LRA=11)
            .output("pipe:", format="wav")
            .run(capture_stdout=True, capture_stderr=True)
        )
        
        # Load normalized audio
        audio, sr = sf.read(io.BytesIO(output))
        return audio, sr
        
    except Exception as e:
        logger.error(f"LUFS normalization failed: {e}")
        # Fallback: peak normalization
        audio, sr = sf.read(input_path)
        return audio / np.max(np.abs(audio)) * 0.95, sr
```

Integrar em pipeline:

```python
# train/scripts/train_pipeline.py
from audio_preprocessing import normalize_lufs

def preprocess_audio(audio_path: Path) -> Path:
    """Preprocessa áudio: resample + normalize + trim"""
    
    # 1. Normalize LUFS
    audio, sr = normalize_lufs(audio_path, target_lufs=-20.0)
    
    # 2. Resample para 24kHz
    if sr != 24000:
        audio = librosa.resample(audio, orig_sr=sr, target_sr=24000)
    
    # 3. Trim silence
    audio, _ = librosa.effects.trim(audio, top_db=30)
    
    # 4. Reject se muito curto/longo
    duration = len(audio) / 24000
    if duration < 1.0 or duration > 12.0:
        raise ValueError(f"Audio duration {duration:.1f}s out of range [1, 12]")
    
    # 5. Save
    output_path = Path(f"/app/train/data/processed/{audio_path.stem}.wav")
    sf.write(output_path, audio, 24000)
    
    return output_path
```

---

#### Task 3.3: Validação de Dataset (1h)

Adicionar checks de qualidade:

```python
def validate_dataset(dataset_dir: Path) -> Dict:
    """
    Valida dataset antes do treino.
    
    Checks:
    - Sample rate consistente (24kHz)
    - Duração válida (1-12s)
    - Sem clipping (peak < 0.99)
    - Transcrições existem
    - SNR aceitável (> 20dB)
    """
    stats = {
        "total_files": 0,
        "valid_files": 0,
        "errors": []
    }
    
    for audio_file in dataset_dir.glob("*.wav"):
        stats["total_files"] += 1
        
        try:
            audio, sr = sf.read(audio_file)
            
            # Check 1: Sample rate
            if sr != 24000:
                stats["errors"].append(f"{audio_file.name}: Wrong SR {sr}")
                continue
            
            # Check 2: Duration
            duration = len(audio) / sr
            if duration < 1.0 or duration > 12.0:
                stats["errors"].append(f"{audio_file.name}: Duration {duration:.1f}s")
                continue
            
            # Check 3: Clipping
            if np.max(np.abs(audio)) > 0.99:
                stats["errors"].append(f"{audio_file.name}: Clipped audio")
                continue
            
            # Check 4: Transcription exists
            txt_file = audio_file.with_suffix(".txt")
            if not txt_file.exists():
                stats["errors"].append(f"{audio_file.name}: Missing transcription")
                continue
            
            stats["valid_files"] += 1
            
        except Exception as e:
            stats["errors"].append(f"{audio_file.name}: {e}")
    
    return stats
```

---

#### Task 3.4: Hyperparâmetros Guia XTTS (30min)

Atualizar `train/config/xtts_train.yaml`:

```yaml
# Baseado em: https://docs.coqui.ai/en/latest/tutorial_for_nervous_beginners.html

training:
  # Epochs: 10-40 (sweet spot = 20)
  epochs: 20
  
  # Batch size: 2 para RTX 3090 24GB
  batch_size: 2
  gradient_accumulation_steps: 4  # effective batch = 8
  
  # Learning rate: 1e-5 (XTTS recomendado)
  learning_rate: 1.0e-5
  scheduler: "linear_with_warmup"
  warmup_steps: 100
  
  # Regularization
  weight_decay: 0.01
  gradient_clip_norm: 1.0
  
  # Mixed precision (RTX 3090)
  use_mixed_precision: true
  gradient_checkpointing: true
```

**Critérios Sprint TRAIN-3**:
- ✅ Pipeline único consolidado
- ✅ Normalização -20 LUFS funcional
- ✅ Validação de dataset implementada
- ✅ Hyperparâmetros alinhados com guia
- ✅ Sample rate fixo 24kHz
- ✅ Commit: "train: Consolidate pipeline with XTTS best practices"

---

## 🎤 Sprint QUALITY-4: Perfis de Qualidade

**Objetivo**: Implementar perfis de qualidade na API

**Duração**: 2-3 horas  
**Prioridade**: P2 (MEDIUM)

### Tasks

Já 80% implementado no Sprint ARCH-1 Task 1.4.

#### Task 4.1: Adicionar Denoise (1h)

Instalar `noisereduce`:

```bash
pip install noisereduce
```

Implementar em `XTTSService`:

```python
import noisereduce as nr

def _apply_denoise(self, audio: np.ndarray) -> np.ndarray:
    """
    Aplica denoise usando spectral gating.
    Só usado em quality_profile='high_quality'.
    """
    try:
        # Stationary noise reduction
        denoised = nr.reduce_noise(
            y=audio,
            sr=24000,
            stationary=True,
            prop_decrease=1.0
        )
        logger.debug("Denoise applied")
        return denoised
    except Exception as e:
        logger.warning(f"Denoise failed: {e}, returning original")
        return audio
```

---

#### Task 4.2: WebUI - Seletor de Perfil (1h)

Atualizar `app/webui/templates/index.html`:

```html
<div class="form-group">
  <label for="quality_profile">Perfil de Qualidade:</label>
  <select id="quality_profile" name="quality_profile" class="form-control">
    <option value="fast">⚡ Rápido (menor latência)</option>
    <option value="balanced" selected>⚖️ Balanceado</option>
    <option value="high_quality">🎯 Alta Qualidade (+ denoise)</option>
  </select>
  <small class="form-text text-muted">
    Rápido: ~2s/req | Balanceado: ~3s/req | Alta: ~5s/req
  </small>
</div>
```

JavaScript:

```javascript
// Enviar quality_profile na request
const formData = {
  text: $("#text").val(),
  voice: $("#voice").val(),
  quality_profile: $("#quality_profile").val()
};

fetch("/jobs", {
  method: "POST",
  headers: {"Content-Type": "application/json"},
  body: JSON.stringify(formData)
});
```

**Critérios Sprint QUALITY-4**:
- ✅ Denoise funcional (high_quality)
- ✅ WebUI com seletor de perfil
- ✅ API aceita quality_profile param
- ✅ Commit: "feat: Add quality profiles with denoise support"

---

## 🛡️ Sprint RESIL-5: Resiliência & Observabilidade

**Objetivo**: Tornar API production-ready

**Duração**: 3-4 horas  
**Prioridade**: P1 (HIGH)

### Tasks

#### Task 5.1: Middleware de Error Handling (1h)

Criar `app/middleware/error_handler.py`:

```python
"""
Global exception handler middleware.
Garante respostas consistentes e logging estruturado.
"""
from fastapi import Request, Response
from fastapi.responses import JSONResponse
from app.logging_config import get_logger
import traceback
import time

logger = get_logger(__name__)


async def error_handler_middleware(request: Request, call_next):
    """
    Middleware global para:
    - Adicionar request_id
    - Capturar exceptions
    - Logging estruturado
    - Response time
    """
    request_id = str(uuid.uuid4())
    request.state.request_id = request_id
    
    start_time = time.time()
    
    try:
        response = await call_next(request)
        duration_ms = (time.time() - start_time) * 1000
        
        logger.info(
            "Request completed",
            extra={
                "request_id": request_id,
                "method": request.method,
                "path": request.url.path,
                "status_code": response.status_code,
                "duration_ms": round(duration_ms, 2)
            }
        )
        
        return response
        
    except Exception as exc:
        duration_ms = (time.time() - start_time) * 1000
        
        logger.error(
            f"Request failed: {type(exc).__name__}",
            extra={
                "request_id": request_id,
                "method": request.method,
                "path": request.url.path,
                "error": str(exc),
                "traceback": traceback.format_exc(),
                "duration_ms": round(duration_ms, 2)
            }
        )
        
        return JSONResponse(
            status_code=500,
            content={
                "error": type(exc).__name__,
                "detail": str(exc),
                "request_id": request_id
            }
        )


# Register em main.py
app.middleware("http")(error_handler_middleware)
```

---

#### Task 5.2: Structured Logging (1h)

Atualizar `app/logging_config.py`:

```python
import logging
import json
from datetime import datetime

class JSONFormatter(logging.Formatter):
    """Formatter para logs em JSON estruturado"""
    
    def format(self, record: logging.LogRecord) -> str:
        log_obj = {
            "timestamp": datetime.utcnow().isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }
        
        # Adicionar extras (request_id, duration_ms, etc.)
        if hasattr(record, "request_id"):
            log_obj["request_id"] = record.request_id
        if hasattr(record, "duration_ms"):
            log_obj["duration_ms"] = record.duration_ms
        if hasattr(record, "status_code"):
            log_obj["status_code"] = record.status_code
        
        return json.dumps(log_obj)


def setup_logging():
    """Configura logging estruturado"""
    handler = logging.StreamHandler()
    handler.setFormatter(JSONFormatter())
    
    root_logger = logging.getLogger()
    root_logger.handlers = [handler]
    root_logger.setLevel(logging.INFO)
```

---

#### Task 5.3: Limpar Métricas Prometheus (30min)

Editar `app/metrics.py`:

```python
"""
Prometheus metrics - XTTS only (RVC removido)
"""
from prometheus_client import Counter, Histogram, Gauge

# XTTS metrics
xtts_synthesis_total = Counter(
    "xtts_synthesis_total",
    "Total XTTS synthesis requests",
    ["status", "quality_profile", "language"]
)

xtts_synthesis_duration_seconds = Histogram(
    "xtts_synthesis_duration_seconds",
    "XTTS synthesis duration",
    ["quality_profile"]
)

xtts_gpu_memory_bytes = Gauge(
    "xtts_gpu_memory_bytes",
    "GPU memory allocated for XTTS"
)

# Job metrics
job_queue_size = Gauge(
    "job_queue_size",
    "Current job queue size"
)

# ❌ REMOVER: Todas métricas RVC
# rvc_conversion_total = ...  # DELETE
# rvc_model_load_total = ...  # DELETE
```

Endpoint de métricas:

```python
from prometheus_client import generate_latest, CONTENT_TYPE_LATEST

@app.get("/metrics")
async def metrics():
    """Prometheus metrics endpoint"""
    return Response(
        content=generate_latest(),
        media_type=CONTENT_TYPE_LATEST
    )
```

---

#### Task 5.4: Circuit Breaker para CUDA OOM (1h)

Criar `app/resilience/circuit_breaker.py`:

```python
"""
Circuit Breaker para CUDA OOM.
Auto-retry com CPU fallback.
"""
import torch
from functools import wraps
from app.logging_config import get_logger

logger = get_logger(__name__)


class CUDACircuitBreaker:
    """
    Detecta CUDA OOM e faz fallback para CPU.
    """
    def __init__(self, max_failures: int = 3):
        self.max_failures = max_failures
        self.failures = 0
        self.state = "closed"  # closed | open | half_open
    
    def __call__(self, func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            if self.state == "open":
                # Circuit open: force CPU
                logger.warning("Circuit OPEN: forcing CPU device")
                kwargs["device"] = "cpu"
            
            try:
                result = await func(*args, **kwargs)
                
                # Success: reset failures
                if self.failures > 0:
                    logger.info("Circuit recovered, resetting failures")
                    self.failures = 0
                    self.state = "closed"
                
                return result
                
            except RuntimeError as e:
                if "out of memory" in str(e).lower():
                    self.failures += 1
                    logger.error(f"CUDA OOM detected ({self.failures}/{self.max_failures})")
                    
                    if self.failures >= self.max_failures:
                        self.state = "open"
                        logger.critical("Circuit OPEN: too many CUDA OOMs, switching to CPU")
                    
                    # Retry com CPU
                    torch.cuda.empty_cache()
                    kwargs["device"] = "cpu"
                    return await func(*args, **kwargs)
                else:
                    raise
        
        return wrapper


# Usage
cuda_breaker = CUDACircuitBreaker()

@cuda_breaker
async def synthesize_with_breaker(...):
    return await xtts_service.synthesize(...)
```

**Critérios Sprint RESIL-5**:
- ✅ Middleware de error handling global
- ✅ Logs estruturados (JSON)
- ✅ Métricas Prometheus limpas (sem RVC)
- ✅ Circuit breaker CUDA funcional
- ✅ Commit: "feat: Add resiliency and structured observability"

---

## 🎨 Sprint FINAL-6: WebUI, Docs & Polish

**Objetivo**: Limpar WebUI e atualizar docs

**Duração**: 2-3 horas  
**Prioridade**: P2 (MEDIUM)

### Tasks

#### Task 6.1: Limpar WebUI (1h)

Buscar refs RVC:

```bash
grep -ri "rvc\|voice.*conversion" app/webui/ --include="*.html" --include="*.js"
```

Remover:
- Formulários RVC
- Checkboxes "Enable RVC"
- Selectors de modelo RVC

Atualizar labels:
- "TTS Engine: XTTS-v2 only"
- Remover opções F5-TTS

---

#### Task 6.2: Atualizar README (1h)

```markdown
# TTS WebUI - XTTS-v2

**Voice cloning e síntese TTS usando XTTS-v2.**

## Features

- ✅ XTTS-v2 voice cloning (Coqui TTS)
- ✅ 3 perfis de qualidade (fast/balanced/high_quality)
- ✅ Eager load (primeira request em <2s)
- ✅ GPU acceleration (CUDA 11.8)
- ✅ Async job queue (Celery + Redis)
- ✅ Prometheus metrics
- ❌ ~~RVC support~~ (removed in v2.0)
- ❌ ~~F5-TTS support~~ (removed in v2.0)

## Quick Start

```bash
docker compose up -d
curl http://localhost:8005/health
```

## API Endpoints

- `POST /synthesize` - Síntese TTS
  - Parâmetros: `text`, `voice`, `quality_profile`
- `GET /quality-profiles` - Listar perfis
- `GET /health` - Healthcheck detalhado
- `GET /metrics` - Prometheus metrics

## Quality Profiles

| Profile | Latency | Quality | Use Case |
|---------|---------|---------|----------|
| fast | ~2s | Good | Chatbots, real-time |
| balanced | ~3s | Better | Default |
| high_quality | ~5s | Best | Production audio |

## Training

Ver [SPRINTS.md](./SPRINTS.md) Sprint TRAIN-3.

## Changelog

Ver [CHANGELOG.md](./docs/CHANGELOG.md).

## Migration from v1.x

RVC removed in v2.0. Use XTTS-v2 native voice cloning.
```

---

#### Task 6.3: Atualizar CHANGELOG (30min)

```markdown
# Changelog

## [2.0.0] - 2025-12-07

### 🔥 Breaking Changes
- **REMOVED**: RVC voice conversion completely
- **REMOVED**: F5-TTS engine
- **CHANGED**: API endpoints - removed `/rvc-models`
- **CHANGED**: Job parameters - removed RVC fields

### ✨ Features
- **NEW**: XTTS-v2 eager load (5-15s startup, <2s first request)
- **NEW**: Quality profiles (fast/balanced/high_quality)
- **NEW**: Structured logging (JSON + request_id)
- **NEW**: Circuit breaker for CUDA OOM
- **NEW**: Healthcheck detalhado (`/health`)

### 🏗️ Architecture
- **REFACTOR**: SOLID principles (XTTSService layer)
- **REFACTOR**: Dependency injection
- **REFACTOR**: Centralized Pydantic Settings
- **REFACTOR**: Consolidated training pipeline

### 🐛 Fixes
- Fixed quality profiles 500 error (f5tts_profiles)
- Fixed download permission denied (/app/temp)
- Fixed lazy-load delays (now eager-loaded)

### 📚 Documentation
- Updated README (removed RVC)
- Added MORE.md (comprehensive analysis)
- Added SPRINTS_RVC_REMOVAL.md

### 🗑️ Removed
- 990+ lines of RVC code
- 8 RVC test files
- 15+ RVC dependencies
- RVC API endpoints
- RVC configuration

---

## [1.x] - Previous versions

See git history.
```

**Critérios Sprint FINAL-6**:
- ✅ WebUI sem refs RVC
- ✅ README atualizado
- ✅ CHANGELOG completo
- ✅ Commit: "docs: Update docs for v2.0 (RVC removal)"

---

## 🎯 Definition of Done (Global)

### Código
- [ ] 0 referências a RVC no código Python
- [ ] 0 referências a F5-TTS (exceto docs deprecated)
- [ ] Testes passam (≥80% coverage)
- [ ] Linter OK (flake8, black)
- [ ] Type hints completos (mypy --strict)

### API
- [ ] Serviço inicia em <15s (eager load)
- [ ] Primeira request TTS em <2s
- [ ] 3 perfis de qualidade funcionais
- [ ] `/health` detalhado
- [ ] Prometheus metrics limpas

### Arquitetura
- [ ] SRP: XTTSService isolado
- [ ] Dependency injection implementada
- [ ] Config centralizada (Pydantic Settings)
- [ ] Error handling consistente
- [ ] Logging estruturado (JSON)

### Training
- [ ] Pipeline único consolidado
- [ ] Sample rate fixo (24kHz)
- [ ] Normalização -20 LUFS
- [ ] Hyperparâmetros alinhados com guia

### Docs
- [ ] README sem RVC
- [ ] CHANGELOG v2.0 completo
- [ ] API docs atualizados
- [ ] Migration guide (v1 → v2)

### DevOps
- [ ] Docker build OK
- [ ] docker-compose up OK
- [ ] Smoke tests passam
- [ ] Rollback plan documentado

---

## 📈 Métricas de Sucesso

| Métrica | Antes (v1.x) | Meta v2.0 | Atual |
|---------|--------------|-----------|-------|
| Startup time | ~30s (lazy) | <15s | - |
| First request latency | ~10s | <2s | - |
| Code LOC | 15000+ | <12000 | - |
| Dependencies | 80+ | <50 | - |
| Test coverage | 45% | ≥80% | - |
| RVC references | 150+ | 0 | - |

---

## 🚀 Deployment Plan

1. **Pre-deploy**:
   - [ ] Backup produção atual
   - [ ] Notificar usuários (RVC descontinuado)
   - [ ] Preparar rollback

2. **Deploy**:
   ```bash
   git checkout main
   git pull origin main
   docker compose down
   docker compose build --no-cache
   docker compose up -d
   ```

3. **Validation**:
   - [ ] Healthcheck OK: `curl /health`
   - [ ] Smoke test: criar job TTS
   - [ ] Logs sem erros: `docker compose logs -f | grep ERROR`

4. **Rollback** (se necessário):
   ```bash
   git checkout v1.9.0  # última versão estável
   docker compose down
   docker compose up -d --build
   ```

---

## 📞 Contato

Dúvidas sobre sprints: ver [MORE.md](./MORE.md)

**Status atual**: Sprint RVC-0 em andamento (Task 0.1 completa)
