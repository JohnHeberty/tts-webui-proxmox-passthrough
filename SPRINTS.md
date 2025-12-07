# SPRINT PLAN – XTTS-v2 Migration & Cleanup

**Projeto**: Audio Voice Service  
**Objetivo**: Migração 100% XTTS-v2 + limpeza de legado F5-TTS/RVC  
**Metodologia**: Sprints incrementais (1-2 semanas cada)  
**Data**: 2024-12-07

---

## 📊 Visão Geral

| Sprint | Tema | Duração | Prioridade | Status |
|--------|------|---------|------------|--------|
| Sprint 0 | Quick Wins & Blockers | 2 dias | 🔴 CRITICAL | 📋 Planejada |
| Sprint 1 | Limpeza F5-TTS/RVC | 1 semana | 🔴 HIGH | 📋 Planejada |
| Sprint 2 | Ambiente Python Limpo | 1 semana | 🔴 HIGH | 📋 Planejada |
| Sprint 3 | Centralização de Configs | 1 semana | 🟡 MEDIUM | 📋 Planejada |
| Sprint 4 | Pipeline de Dataset na WebUI | 2 semanas | 🟡 MEDIUM | 📋 Planejada |
| Sprint 5 | Integração Checkpoints + Samples | 1 semana | 🟡 MEDIUM | 📋 Planejada |
| Sprint 6 | Otimização de Qualidade XTTS | 2 semanas | 🟢 LOW | 📋 Planejada |
| Sprint 7 | Hardening & Observabilidade | 1 semana | 🟢 LOW | 📋 Planejada |

**Total estimado**: ~10 semanas (2.5 meses)

---

## Sprint 0 – Quick Wins & Blockers 🚀

**Duração**: 2 dias  
**Objetivo**: Resolver problemas críticos que bloqueiam uso imediato  
**Owner**: Tech Lead + 1 Dev

### Escopo

Corrigir bugs que impedem WebUI de funcionar corretamente.

### Tarefas

#### ✅ Task 0.1: Fix extensão de checkpoint (.pt vs .pth)
**Prioridade**: 🔴 BLOCKER  
**Tempo estimado**: 30 minutos  
**Arquivos**:
- `app/training_api.py` (linha ~499)

**Mudança**:
```python
# Função _scan_checkpoint_dir
# ANTES:
for ckpt_file in checkpoint_dir.glob("*.pth"):

# DEPOIS:
for ckpt_file in checkpoint_dir.glob("*.pt"):
```

**Teste**:
1. Rodar treino: `python3 -m train.scripts.train_xtts`
2. Abrir WebUI → Training → Checkpoints
3. Verificar que checkpoints aparecem na lista

---

#### ✅ Task 0.2: Criar endpoint para listar samples de áudio
**Prioridade**: 🔴 HIGH  
**Tempo estimado**: 2 horas  
**Arquivos**:
- `app/training_api.py` (novo endpoint)
- `app/webui/assets/js/app.js` (fetch)
- `app/webui/index.html` (UI)

**Implementação**:
```python
# Em app/training_api.py
@router.get("/samples")
async def list_samples(model_name: Optional[str] = None):
    """List training samples (epoch_N_output.wav)"""
    try:
        samples = []
        samples_root = Path("train/output/samples")
        
        if samples_root.exists():
            for wav_file in sorted(samples_root.glob("epoch_*_output.wav")):
                epoch_match = re.search(r"epoch_(\d+)", wav_file.stem)
                epoch = int(epoch_match.group(1)) if epoch_match else 0
                
                samples.append({
                    "epoch": epoch,
                    "path": f"/static/samples/{wav_file.name}",
                    "filename": wav_file.name,
                    "size_mb": round(wav_file.stat().st_size / 1024 / 1024, 2)
                })
        
        samples.sort(key=lambda x: x["epoch"], reverse=True)
        return samples
    except Exception as e:
        raise HTTPException(500, str(e))
```

**WebUI (app.js)**:
```javascript
async loadTrainingSamples() {
    const response = await this.api('/training/samples');
    const samples = await response.json();
    
    const container = document.getElementById('training-samples');
    container.innerHTML = samples.map(s => `
        <div class="sample-item">
            <span>Epoch ${s.epoch}</span>
            <audio controls src="${s.path}"></audio>
        </div>
    `).join('');
}
```

**Teste**:
1. Treinar 2 epochs
2. Abrir WebUI → Training
3. Verificar que aparece player de áudio para cada época

---

#### ✅ Task 0.3: Mount samples folder como static
**Prioridade**: 🔴 HIGH  
**Tempo estimado**: 15 minutos  
**Arquivos**:
- `app/main.py`

**Mudança**:
```python
# Em app/main.py, após mount de /webui
app.mount("/static/samples", StaticFiles(directory="train/output/samples"), name="samples")
```

---

### Critérios de Aceitação

- [x] WebUI lista checkpoints gerados pelo treino
- [x] WebUI mostra samples de áudio de cada época
- [x] Áudio toca direto no browser

### Dependências

Nenhuma

---

## Sprint 1 – Limpeza F5-TTS/RVC 🧹

**Duração**: 1 semana  
**Objetivo**: Remover 100% de referências a F5-TTS e RVC  
**Owner**: 2 Devs

### Escopo

Limpar código, docs, WebUI e configs de todo legado F5-TTS e RVC.

### Tarefas

#### 📝 Task 1.1: Auditoria completa de referências
**Tempo**: 2 horas  
**Ação**:
```bash
# Buscar todas as refs
grep -r "f5-tts\|f5tts\|F5TTS\|F5-TTS" . --exclude-dir=node_modules > refs_f5.txt
grep -r "rvc\|RVC" . --exclude-dir=node_modules > refs_rvc.txt

# Revisar e classificar:
# - DELETE: código/docs a remover
# - ARCHIVE: docs históricos (mover para docs/archive/)
# - MARK: manter mas marcar como "removed in v2.0"
```

---

#### 📄 Task 1.2: Limpar documentação
**Tempo**: 3 horas  
**Arquivos**:
- `docs/LOW_VRAM.md`
- `docs/API_PARAMETERS.md`
- `docs/ARCHITECTURE.md`
- `docs/README.md`
- `docs/V2_RELEASE_NOTES.md`

**Ações**:
1. Adicionar banner no topo de cada doc:
   ```markdown
   > ⚠️ **ATENÇÃO**: F5-TTS e RVC foram removidos em v2.0. Este projeto usa exclusivamente XTTS-v2.
   ```

2. Seções específicas:
   - `docs/LOW_VRAM.md`: Remover linhas 22, 30, 32, 91, 187+
   - `docs/API_PARAMETERS.md`: Remover linhas 15, 43, 44
   - `docs/ARCHITECTURE.md`: Remover seções RVC (linhas 29-31, 47, 49, 55-56)
   - `docs/README.md`: Remover seção "RVC Voice Conversion" (linhas 148-151)

3. Criar `docs/archive/F5_RVC_LEGACY.md` com histórico

---

#### 🎨 Task 1.3: Limpar WebUI
**Tempo**: 2 horas  
**Arquivos**:
- `app/webui/index.html`
- `app/webui/assets/js/app.js`

**Mudanças**:
1. `index.html` linha 56: **Remover aba "Modelos RVC"**
2. `app.js`: Remover funções:
   - `loadRVCModels()`
   - `uploadRVCModel()`
   - Qualquer outra ref a RVC

3. Verificar CSS/assets relacionados

---

#### 🐳 Task 1.4: Limpar Dockerfile
**Tempo**: 30 minutos  
**Arquivo**: `Dockerfile`

**Mudança**:
```dockerfile
# Linha 84 - REMOVER /app/models/rvc
# ANTES:
RUN mkdir -p /app/uploads /app/processed /app/temp \
    /app/voice_profiles /app/models /app/models/f5tts /app/models/whisper /app/models/rvc \
    /app/logs

# DEPOIS:
RUN mkdir -p /app/uploads /app/processed /app/temp \
    /app/voice_profiles /app/models /app/models/whisper /app/logs
```

---

#### 🔧 Task 1.5: Remover symlinks F5-TTS em Python global
**Tempo**: 30 minutos  
**Ação**:
```bash
chmod +x REMOVE_F5_SYMLINKS.sh
./REMOVE_F5_SYMLINKS.sh
# Seguir prompts interativos, confirmar remoções
```

---

#### 🗑️ Task 1.6: Remover symlink /runs
**Tempo**: 15 minutos  
**Ação**:
```bash
cd /home/tts-webui-proxmox-passthrough
rm runs  # É symlink para train/runs
```

**Atualizar refs**:
- Buscar `"/runs"` ou `"runs/"` no código
- Trocar por `"train/runs"`

---

### Critérios de Aceitação

- [x] Zero menções a F5-TTS/RVC em código Python ativo
- [x] Docs marcados como "removed" ou arquivados
- [x] WebUI sem aba RVC
- [x] Dockerfile não cria pastas F5/RVC
- [x] Symlinks removidos

### Dependências

Nenhuma

---

## Sprint 2 – Ambiente Python Limpo 🐍

**Duração**: 1 semana  
**Objetivo**: Migrar de Python global para venv isolado  
**Owner**: DevOps + 1 Dev

### Escopo

Criar ambiente reproduzível, limpo e versionado.

### Tarefas

#### 🔨 Task 2.1: Criar venv no projeto
**Tempo**: 1 hora  
**Ação**:
```bash
cd /home/tts-webui-proxmox-passthrough

# Criar venv
python3.11 -m venv venv

# Ativar
source venv/bin/activate

# Upgrade pip
pip install --upgrade pip

# Instalar dependências
pip install -r requirements.txt -c constraints.txt

# Salvar freeze exato
pip freeze > requirements-lock.txt
```

---

#### 🐳 Task 2.2: Adaptar Dockerfile para usar venv
**Tempo**: 2 horas  
**Arquivo**: `Dockerfile`

**Nova estratégia (multi-stage)**:
```dockerfile
# Stage 1: Build venv
FROM nvidia/cuda:11.8.0-cudnn8-runtime-ubuntu22.04 AS builder

RUN apt-get update && apt-get install -y python3.11 python3.11-venv
WORKDIR /app

COPY requirements.txt constraints.txt ./
RUN python3.11 -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"
RUN pip install --upgrade pip && \
    pip install -r requirements.txt -c constraints.txt

# Stage 2: Runtime
FROM nvidia/cuda:11.8.0-cudnn8-runtime-ubuntu22.04

RUN apt-get update && apt-get install -y python3.11 ffmpeg libsndfile1
COPY --from=builder /opt/venv /opt/venv

ENV PATH="/opt/venv/bin:$PATH"
WORKDIR /app

COPY . .
CMD ["python", "run.py"]
```

**Benefícios**:
- Imagem final menor (sem build tools)
- Venv isolado e reproduzível
- Cache de layers otimizado

---

#### 📜 Task 2.3: Atualizar scripts para usar venv
**Tempo**: 1 hora  
**Arquivos**: `scripts/*.sh`, shebang em Python scripts

**Exemplo**:
```bash
# scripts/validate-gpu.sh
#!/bin/bash
source /home/tts-webui-proxmox-passthrough/venv/bin/activate
python -c "import torch; print(torch.cuda.is_available())"
```

**Python scripts** (train/scripts/*.py):
```python
#!/home/tts-webui-proxmox-passthrough/venv/bin/python
# Ou usar /usr/bin/env python se venv ativo
```

---

#### 📋 Task 2.4: Documentar setup de venv
**Tempo**: 1 hora  
**Arquivo**: `docs/DEVELOPMENT_SETUP.md`

**Conteúdo**:
```markdown
# Development Setup

## Prerequisites
- Python 3.11
- CUDA 11.8+ (for GPU support)
- 16GB RAM, 8GB VRAM recommended

## Setup Virtual Environment

1. Create venv:
   ```bash
   python3.11 -m venv venv
   source venv/bin/activate
   ```

2. Install dependencies:
   ```bash
   pip install --upgrade pip
   pip install -r requirements.txt -c constraints.txt
   ```

3. Verify installation:
   ```bash
   python -c "import torch; print(torch.cuda.is_available())"
   ```

## Running the Service

### Development (local)
```bash
source venv/bin/activate
python run.py
```

### Production (Docker)
```bash
docker-compose up --build
```
```

---

#### 🧪 Task 2.5: Testar tudo com venv
**Tempo**: 2 horas  
**Checklist**:
- [ ] API inicia sem erros
- [ ] Inference funciona (TTS básico)
- [ ] Treino funciona (1 epoch teste)
- [ ] WebUI acessa API corretamente
- [ ] Celery worker conecta e processa jobs

---

#### 🗑️ Task 2.6: (Opcional) Limpar Python global
**Tempo**: 30 minutos  
**Ação**: 
```bash
# CUIDADO: Só fazer se não houver outros projetos!
pip freeze > /tmp/global-packages.txt
pip uninstall -y -r /tmp/global-packages.txt

# Ou simplesmente não usar mais (venv ativo sempre)
```

---

### Critérios de Aceitação

- [x] Venv criado e funcional
- [x] Dockerfile usa venv isolado
- [x] Scripts usam venv
- [x] Docs atualizados
- [x] Tudo funciona igual (ou melhor) que antes

### Dependências

Nenhuma (pode rodar em paralelo com Sprint 1)

---

## Sprint 3 – Centralização de Configs ⚙️

**Duração**: 1 semana  
**Objetivo**: DRY - fonte única de verdade para configs  
**Owner**: 1 Dev Senior

### Escopo

Eliminar duplicação de configurações entre `/app`, `/train` e `.env`.

### Tarefas

#### 📐 Task 3.1: Análise de configs duplicadas
**Tempo**: 2 horas  
**Ação**:
1. Listar todas as variáveis de ambiente usadas:
   - `grep -r "os.getenv\|os.environ" app/ train/`
   - `grep -r "Field(.*env=" app/ train/`

2. Criar planilha:
   | Variável | .env | train/.env | app/settings.py | train/env_config.py | Conflito? |
   |----------|------|------------|-----------------|---------------------|-----------|
   | MAX_TRAIN_SAMPLES | ✅ | ✅ | ❌ | ✅ | Sim |

---

#### 🏗️ Task 3.2: Criar config central
**Tempo**: 4 horas  
**Novo arquivo**: `config/settings.py`

**Estrutura**:
```python
from pathlib import Path
from typing import Optional
from pydantic_settings import BaseSettings, SettingsConfigDict

class GlobalSettings(BaseSettings):
    """Configurações compartilhadas entre /app e /train"""
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )
    
    # === Paths ===
    project_root: Path = Path(__file__).parent.parent
    data_dir: Path = Path("data")
    models_dir: Path = Path("models")
    train_dir: Path = Path("train")
    
    @property
    def train_output_dir(self) -> Path:
        return self.train_dir / "output"
    
    @property
    def train_checkpoints_dir(self) -> Path:
        return self.train_output_dir / "checkpoints"
    
    # === Training ===
    max_train_samples: Optional[int] = None
    num_epochs: int = 1000
    log_every_n_steps: int = 10
    
    # === XTTS ===
    xtts_model_name: str = "tts_models/multilingual/multi-dataset/xtts_v2"
    xtts_device: str = "cuda"
    
    # === Whisper ===
    whisper_model: str = "base"
    whisper_num_workers: int = 4

_settings = None

def get_settings() -> GlobalSettings:
    global _settings
    if _settings is None:
        _settings = GlobalSettings()
    return _settings
```

---

#### 🔄 Task 3.3: Migrar app/settings.py para usar central
**Tempo**: 2 horas  
**Arquivo**: `app/settings.py`

**Antes**:
```python
class Settings(BaseSettings):
    xtts_model_name: str = "tts_models/..."
    # ... muitas variáveis
```

**Depois**:
```python
from config.settings import get_settings as get_global_settings

class AppSettings(BaseSettings):
    """Settings específicos da API"""
    # Herda de global
    _global = get_global_settings()
    
    # Sobrescreve apenas o que é específico da API
    port: int = 8005
    debug: bool = False
```

---

#### 🔄 Task 3.4: Migrar train/env_config.py para usar central
**Tempo**: 2 horas  
**Arquivo**: `train/env_config.py`

**Mudança**:
```python
from config.settings import get_settings

settings = get_settings()

# Expor como antes para compatibilidade
TRAIN_ROOT = settings.train_dir
OUTPUT_DIR = settings.train_output_dir
MAX_TRAIN_SAMPLES = settings.max_train_samples
```

---

#### 📄 Task 3.5: Atualizar .env.example
**Tempo**: 1 hora  
**Ação**:
- Remover duplicatas
- Organizar por seções claras
- Adicionar comentários explicativos

---

#### 🧪 Task 3.6: Testar configs centralizadas
**Tempo**: 2 horas  
**Teste**:
1. Mudar `MAX_TRAIN_SAMPLES` em `.env`
2. Rodar treino: verificar que usa valor correto
3. API: verificar que também usa (se aplicável)

---

### Critérios de Aceitação

- [x] Uma única fonte de verdade: `config/settings.py`
- [x] Zero duplicação de variáveis
- [x] `.env` limpo e organizado
- [x] App e Train usam mesma config

### Dependências

Sprint 2 (venv) recomendado antes

---

## Sprint 4 – Pipeline de Dataset na WebUI 🎨

**Duração**: 2 semanas  
**Objetivo**: Tornar preparação de dataset user-friendly  
**Owner**: 1 Frontend + 1 Backend Dev

### Escopo

Adicionar seção na WebUI para executar pipeline de dataset:
1. Download YouTube
2. Segmentação
3. Transcrição
4. Build dataset LJS

### Tarefas

#### 🎨 Task 4.1: Design UI de pipeline
**Tempo**: 4 horas  
**Deliverable**: Mockup ou wireframe

**Seções**:
1. **Step 1: Download**
   - Textarea para URLs (uma por linha)
   - Botão "Download"
   - Progress bar

2. **Step 2: Segment**
   - Slider min/max duration
   - Slider VAD threshold
   - Botão "Segment"

3. **Step 3: Transcribe**
   - Select Whisper model (base/small/medium)
   - Checkbox "parallel mode"
   - Botão "Transcribe"

4. **Step 4: Build Dataset**
   - Input dataset name
   - Botão "Build"

5. **Status**
   - Real-time logs
   - Files count
   - Total duration

---

#### 🔧 Task 4.2: Backend - WebSocket para logs
**Tempo**: 6 horas  
**Arquivo**: `app/training_api.py`

**Implementação**:
```python
from fastapi import WebSocket
import asyncio

@router.websocket("/ws/pipeline")
async def pipeline_logs_ws(websocket: WebSocket):
    await websocket.accept()
    
    # Stream logs from subprocess
    process = training_state["process"]
    while process and process.poll() is None:
        line = process.stdout.readline()
        if line:
            await websocket.send_json({"log": line})
        await asyncio.sleep(0.1)
    
    await websocket.close()
```

---

#### 🎨 Task 4.3: Frontend - UI implementation
**Tempo**: 8 horas  
**Arquivos**:
- `app/webui/index.html` (nova seção)
- `app/webui/assets/js/app.js` (lógica)
- `app/webui/assets/css/styles.css` (estilo)

**Exemplo (HTML)**:
```html
<section id="section-dataset-pipeline">
    <h1>Dataset Pipeline</h1>
    
    <div class="card">
        <h3>Step 1: Download YouTube</h3>
        <textarea id="youtube-urls" rows="5"></textarea>
        <button onclick="app.downloadYouTube()">Download</button>
    </div>
    
    <div class="card">
        <h3>Step 2: Segment Audio</h3>
        <input type="range" id="min-duration" min="3" max="15" value="7">
        <button onclick="app.segmentAudio()">Segment</button>
    </div>
    
    <!-- ... Steps 3-4 -->
    
    <div class="card">
        <h3>Logs</h3>
        <pre id="pipeline-logs"></pre>
    </div>
</section>
```

**JS (WebSocket)**:
```javascript
connectPipelineWebSocket() {
    const ws = new WebSocket(`ws://${window.location.host}/training/ws/pipeline`);
    
    ws.onmessage = (event) => {
        const data = JSON.parse(event.data);
        const logsEl = document.getElementById('pipeline-logs');
        logsEl.textContent += data.log + '\n';
        logsEl.scrollTop = logsEl.scrollHeight;
    };
}
```

---

#### 🧪 Task 4.4: Testes E2E
**Tempo**: 4 horas  
**Casos**:
1. Download 1 vídeo curto (5min)
2. Segmentar → verificar arquivos gerados
3. Transcrever → verificar metadata.csv
4. Build dataset → verificar estrutura LJS

---

### Critérios de Aceitação

- [x] WebUI tem seção "Dataset Pipeline"
- [x] Usuário executa pipeline sem CLI
- [x] Logs em tempo real via WebSocket
- [x] Dataset final pronto para treino

### Dependências

Sprint 0 (samples fix) e Sprint 3 (configs)

---

## Sprint 5 – Integração Checkpoints + Samples 📊

**Duração**: 1 semana  
**Objetivo**: WebUI mostra checkpoints E samples side-by-side  
**Owner**: 1 Frontend Dev

### Escopo

Melhorar UX da aba Training com:
- Lista de checkpoints
- Samples de cada época
- A/B test: base vs finetuned

### Tarefas

#### 🎨 Task 5.1: Redesign seção Training
**Tempo**: 3 horas  
**Mockup**: Layout em 3 colunas
- Col 1: Checkpoints list
- Col 2: Samples (áudio players)
- Col 3: Inference test

---

#### 🔧 Task 5.2: Endpoint /training/checkpoint-details
**Tempo**: 2 horas  
**Arquivo**: `app/training_api.py`

**Endpoint**:
```python
@router.get("/checkpoint/{checkpoint_id}/details")
async def get_checkpoint_details(checkpoint_id: str):
    """Get checkpoint with related samples"""
    ckpt_path = Path(checkpoint_id)
    epoch = extract_epoch(ckpt_path.stem)
    
    # Find related samples
    samples_dir = Path("train/output/samples")
    samples = list(samples_dir.glob(f"epoch_{epoch}_*.wav"))
    
    return {
        "checkpoint": {
            "path": str(ckpt_path),
            "epoch": epoch,
            "size_mb": ckpt_path.stat().st_size / 1024 / 1024
        },
        "samples": [
            {
                "type": "output" if "output" in s.name else "reference",
                "path": f"/static/samples/{s.name}"
            }
            for s in samples
        ]
    }
```

---

#### 🎨 Task 5.3: Frontend - Checkpoint card com samples
**Tempo**: 4 horas  
**Componente**:
```javascript
async renderCheckpointCard(checkpoint) {
    const details = await this.api(`/training/checkpoint/${checkpoint.path}/details`);
    
    return `
        <div class="checkpoint-card">
            <h4>Epoch ${details.checkpoint.epoch}</h4>
            <p>${details.checkpoint.size_mb} MB</p>
            
            <div class="samples">
                ${details.samples.map(s => `
                    <div>
                        <label>${s.type}</label>
                        <audio controls src="${s.path}"></audio>
                    </div>
                `).join('')}
            </div>
            
            <button onclick="app.loadCheckpoint('${checkpoint.path}')">
                Load for Inference
            </button>
        </div>
    `;
}
```

---

#### 🧪 Task 5.4: A/B Test UI
**Tempo**: 3 horas  
**Feature**: Comparar base model vs finetuned

**UI**:
```html
<div id="ab-test">
    <h3>A/B Comparison</h3>
    <input id="ab-text" placeholder="Texto para testar...">
    <button onclick="app.runABTest()">Generate Both</button>
    
    <div class="ab-results">
        <div>
            <h4>Base Model</h4>
            <audio id="ab-base" controls></audio>
        </div>
        <div>
            <h4>Finetuned (Epoch ${epoch})</h4>
            <audio id="ab-finetuned" controls></audio>
        </div>
    </div>
</div>
```

---

### Critérios de Aceitação

- [x] Checkpoints listados com samples lado-a-lado
- [x] Áudio toca direto no browser
- [x] A/B test funciona
- [x] UX intuitiva e rápida

### Dependências

Sprint 0 (samples endpoint)

---

## Sprint 6 – Otimização de Qualidade XTTS 🎯

**Duração**: 2 semanas  
**Objetivo**: Melhorar timbre e naturalidade do áudio gerado  
**Owner**: ML Engineer + 1 Dev

### Escopo

Técnicas para melhorar qualidade:
1. Implementar LoRA
2. Grid search de hiperparâmetros
3. Melhorar qualidade de dataset
4. Data augmentation

### Tarefas

#### 🔬 Task 6.1: Pesquisa - Target modules para LoRA no XTTS
**Tempo**: 4 horas  
**Ação**:
1. Ler código XTTS-v2 (Coqui TTS)
2. Identificar layers treináveis (attention, feedforward)
3. Testar com `peft` library

**Resultado esperado**:
```python
# Em train/scripts/train_xtts.py
from peft import LoraConfig, get_peft_model

lora_config = LoraConfig(
    r=8,
    lora_alpha=16,
    target_modules=["q_proj", "v_proj", "out_proj"],  # DESCOBRIR
    lora_dropout=0.1,
    bias="none"
)

model = get_peft_model(base_model, lora_config)
```

---

#### 🔧 Task 6.2: Implementar LoRA no treino
**Tempo**: 6 horas  
**Arquivo**: `train/scripts/train_xtts.py`

**Mudanças**:
1. Descomentar código LoRA
2. Ajustar target_modules baseado em Task 6.1
3. Testar treino com batch_size maior (4 → 8)

---

#### 🧪 Task 6.3: Grid search de hiperparâmetros
**Tempo**: 8 horas (+ tempo de treino)  
**Novo arquivo**: `train/scripts/hyperparameter_search.py`

**Parâmetros a testar**:
```python
param_grid = {
    "learning_rate": [5e-6, 1e-5, 5e-5],
    "batch_size": [4, 8],
    "lora_rank": [4, 8, 16],
    "num_epochs": [100, 500]
}
```

**Métrica**: Loss no validation set + avaliação humana (MOS)

---

#### 🎧 Task 6.4: Filtro de qualidade de dataset
**Tempo**: 6 horas  
**Arquivo**: `train/scripts/segment_audio.py`

**Adicionar**:
1. **SNR filter**: Descartar segmentos com ruído alto
   ```python
   import noisereduce as nr
   
   def calculate_snr(audio, sr):
       # Signal-to-Noise Ratio
       signal_power = np.mean(audio ** 2)
       noise = nr.reduce_noise(y=audio, sr=sr)
       noise_power = np.mean((audio - noise) ** 2)
       return 10 * np.log10(signal_power / noise_power)
   ```

2. **Speaker diarization**: Descartar segmentos com múltiplos speakers
   (usar pyannote.audio se viável)

3. **Silence ratio**: Descartar se >30% silêncio

---

#### 📊 Task 6.5: Avaliação sistemática
**Tempo**: 4 horas  
**Criar**: `train/scripts/evaluate_quality.py`

**Métricas**:
1. **MOS automatizado** (usando modelo pré-treinado)
2. **Similarity score** (comparar voz gerada vs referência)
3. **Intelligibility** (WER com Whisper)

---

### Critérios de Aceitação

- [x] LoRA funcionando, treino 2x mais rápido
- [x] Grid search encontra melhores hiperparâmetros
- [x] Dataset filtrado (>80% segmentos de alta qualidade)
- [x] Qualidade de timbre >= baseline (avaliação subjetiva)

### Dependências

Sprint 2 (venv), Sprint 3 (configs)

---

## Sprint 7 – Hardening & Observabilidade 🛡️

**Duração**: 1 semana  
**Objetivo**: Produção-ready (monitoramento, erros, docs)  
**Owner**: DevOps + Tech Lead

### Escopo

Preparar para produção com:
- Monitoramento (Prometheus/Grafana)
- Logs estruturados
- Error tracking
- Docs finalizados

### Tarefas

#### 📊 Task 7.1: Prometheus metrics
**Tempo**: 4 horas  
**Arquivo**: `app/metrics.py` (já existe?)

**Adicionar**:
```python
from prometheus_client import Counter, Histogram, Gauge

# Metrics
tts_requests_total = Counter("tts_requests_total", "Total TTS requests")
tts_duration_seconds = Histogram("tts_duration_seconds", "TTS latency")
training_loss = Gauge("training_loss", "Current training loss")
```

**Expor**: `GET /metrics` (Prometheus format)

---

#### 📝 Task 7.2: Structured logging
**Tempo**: 3 horas  
**Arquivo**: `app/logging_config.py`

**Migrar para JSON logs**:
```python
import structlog

logger = structlog.get_logger()

# Usage
logger.info("tts_request", user_id=123, text_length=500, duration_ms=1200)
```

---

#### 🐛 Task 7.3: Error tracking (Sentry/Rollbar)
**Tempo**: 2 horas  
**Ação**:
```python
import sentry_sdk

sentry_sdk.init(
    dsn="https://...",
    environment=settings.environment
)
```

---

#### 📚 Task 7.4: Finalizar documentação
**Tempo**: 6 horas  
**Docs a atualizar**:
- [ ] README.md (badges, quick start)
- [ ] docs/API_REFERENCE.md (OpenAPI completo)
- [ ] docs/DEPLOYMENT.md (Docker, K8s, scaling)
- [ ] docs/TRAINING_GUIDE.md (passo-a-passo)
- [ ] docs/TROUBLESHOOTING.md (FAQ)

---

#### 🧪 Task 7.5: Testes de carga
**Tempo**: 4 horas  
**Tool**: Locust ou k6

**Cenários**:
1. 10 req/s de TTS básico
2. 5 req/s de voice cloning
3. 1 treino concorrente

**Métricas**:
- Latência p50, p95, p99
- Throughput
- Error rate

---

### Critérios de Aceitação

- [x] Metrics expostos para Prometheus
- [x] Logs estruturados em JSON
- [x] Errors rastreados (Sentry)
- [x] Docs 100% atualizados
- [x] Load tests passam (p95 < 5s)

### Dependências

Todas as sprints anteriores

---

## 🎯 Roadmap Visual

```
Semana 1-2:  Sprint 0 ████ (CRITICAL)
             Sprint 1 ████████ (Limpeza F5/RVC)
             
Semana 3-4:  Sprint 2 ████████ (Python venv)
             Sprint 3 ████████ (Configs)
             
Semana 5-6:  Sprint 4 ████████████████ (Dataset UI)

Semana 7:    Sprint 5 ████████ (Checkpoints+Samples)

Semana 8-9:  Sprint 6 ████████████████ (Qualidade XTTS)

Semana 10:   Sprint 7 ████████ (Hardening)
```

---

## 📋 Checklists de Validação

### Antes de Cada Sprint
- [ ] Ler objetivos e escopo
- [ ] Verificar dependências atendidas
- [ ] Estimar tempo realista (adicionar buffer 20%)
- [ ] Alocar pessoas certas

### Durante Sprint
- [ ] Daily standup (15min)
- [ ] Atualizar board (Jira/Trello)
- [ ] Code reviews em 24h
- [ ] Testes automatizados passam

### Fim de Sprint
- [ ] Demo para stakeholders
- [ ] Retrospectiva (What went well / To improve)
- [ ] Deploy em staging
- [ ] Atualizar documentação

---

## 🚀 Como Executar Este Plano

### 1. Preparação (Dia 1)
```bash
# Clone e setup
cd /home/tts-webui-proxmox-passthrough
git checkout -b sprint-0-quick-wins

# Ler MORE.md e SPRINTS.md
cat MORE.md
cat SPRINTS.md
```

### 2. Executar Sprint 0 (Dias 1-2)
```bash
# Task 0.1: Fix checkpoint extension
vim app/training_api.py
# Mudar *.pth → *.pt

# Task 0.2 & 0.3: Samples endpoint
vim app/training_api.py  # Adicionar endpoint
vim app/main.py          # Mount static
vim app/webui/assets/js/app.js  # Frontend

# Testar
python run.py
# Abrir WebUI → Training → Verificar checkpoints e samples
```

### 3. Commit & PR
```bash
git add .
git commit -m "Sprint 0: Fix checkpoints (.pt) + samples endpoint"
git push origin sprint-0-quick-wins
# Criar PR no GitHub/GitLab
```

### 4. Repetir para cada Sprint

---

## 📞 Contato & Suporte

**Tech Lead**: [Seu nome]  
**Slack**: #tts-webui-dev  
**Docs**: `/docs`  
**Issues**: GitHub Issues

---

**Última atualização**: 2024-12-07  
**Versão**: 1.0
