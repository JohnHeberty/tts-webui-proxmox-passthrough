# 🎯 PONTOS DE ENTRADA CRÍTICOS - Guia de Implementação

**Data**: 2024-12-07  
**Para**: Time de Desenvolvimento  
**Ref**: MORE.md + SPRINTS.md

---

## 🚨 BLOQUEADORES CRÍTICOS (Resolver AGORA)

### 1. WebUI não mostra checkpoints (ARCH-02)

**Arquivo**: `app/training_api.py`  
**Linha**: ~499  
**Função**: `_scan_checkpoint_dir()`

```python
# PROBLEMA ATUAL (linha 499):
for ckpt_file in checkpoint_dir.glob("*.pth"):  # ❌ ERRADO

# SOLUÇÃO:
for ckpt_file in checkpoint_dir.glob("*.pt"):   # ✅ CORRETO
```

**Por quê**: Script de treino salva `checkpoint_epoch_1.pt`, mas API busca `*.pth`

**Testar**:
```bash
cd /home/tts-webui-proxmox-passthrough
python3 -m train.scripts.train_xtts  # Treinar 1 epoch
# Abrir WebUI → Training → Checkpoints
# Deve mostrar: checkpoint_epoch_1.pt
```

---

### 2. Samples de áudio não aparecem na WebUI (UI-02)

**Arquivos a criar/editar**:

#### 2.1. Backend - Novo endpoint
**Arquivo**: `app/training_api.py`  
**Adicionar após linha 520** (após função `_scan_checkpoint_dir`):

```python
@router.get("/samples")
async def list_training_samples(model_name: Optional[str] = None):
    """
    List training samples (epoch_N_output.wav files)
    """
    import re
    try:
        samples = []
        samples_root = Path("train/output/samples")
        
        if not samples_root.exists():
            return []
        
        # Scan for epoch_*_output.wav
        for wav_file in sorted(samples_root.glob("epoch_*_output.wav")):
            # Extract epoch number from filename
            epoch_match = re.search(r"epoch_(\d+)", wav_file.stem)
            epoch = int(epoch_match.group(1)) if epoch_match else 0
            
            stat = wav_file.stat()
            
            samples.append({
                "epoch": epoch,
                "filename": wav_file.name,
                "path": f"/static/samples/{wav_file.name}",
                "size_mb": round(stat.st_size / 1024 / 1024, 2),
                "date": datetime.fromtimestamp(stat.st_mtime).strftime("%Y-%m-%d %H:%M")
            })
        
        # Sort by epoch (newest first)
        samples.sort(key=lambda x: x["epoch"], reverse=True)
        
        return samples
        
    except Exception as e:
        logger.error(f"❌ Error listing samples: {e}")
        raise HTTPException(status_code=500, detail=str(e))
```

#### 2.2. API - Mount samples folder
**Arquivo**: `app/main.py`  
**Linha**: ~82 (após mount de /webui)

```python
# Mount WebUI static files
webui_path = Path(__file__).parent / "webui"
if webui_path.exists():
    app.mount("/webui", StaticFiles(directory=str(webui_path)), name="webui")
    logger.info(f"✅ WebUI mounted at /webui from {webui_path}")
else:
    logger.warning(f"⚠️ WebUI directory not found: {webui_path}")

# ADICIONAR AQUI:
# Mount training samples for playback
samples_path = Path("train/output/samples")
if samples_path.exists():
    app.mount("/static/samples", StaticFiles(directory=str(samples_path)), name="samples")
    logger.info(f"✅ Samples mounted at /static/samples")
```

#### 2.3. Frontend - Carregar e exibir samples
**Arquivo**: `app/webui/assets/js/app.js`  
**Procurar função**: `loadCheckpoints()` (linha ~2748)  
**Adicionar nova função após ela**:

```javascript
/**
 * Load training samples
 */
async loadTrainingSamples() {
    try {
        const response = await this.api('/training/samples');
        const samples = await response.json();
        
        const container = document.getElementById('training-samples-list');
        
        if (!samples || samples.length === 0) {
            container.innerHTML = '<p class="p-3 text-muted mb-0">Nenhuma amostra disponível</p>';
            return;
        }
        
        container.innerHTML = samples.map(s => `
            <div class="list-group-item">
                <div class="d-flex justify-content-between align-items-center mb-2">
                    <strong>Epoch ${s.epoch}</strong>
                    <small class="text-muted">${s.date}</small>
                </div>
                <audio controls class="w-100" src="${s.path}">
                    Your browser does not support audio playback.
                </audio>
            </div>
        `).join('');
        
    } catch (error) {
        console.error('❌ Error loading samples:', error);
    }
}
```

**Chamar a função**:
Procurar `loadTrainingDashboard()` ou similar e adicionar:
```javascript
async loadTrainingDashboard() {
    this.loadCheckpoints();
    this.loadTrainingSamples();  // ADICIONAR ESTA LINHA
}
```

#### 2.4. Frontend - Adicionar container na UI
**Arquivo**: `app/webui/index.html`  
**Procurar seção**: `id="section-training"` (linha ~1200-1300)  
**Adicionar novo card**:

```html
<!-- Dentro da seção training, após o card de checkpoints -->
<div class="col-md-6 mb-3">
    <div class="card">
        <div class="card-header bg-success text-white">
            <i class="bi bi-music-note-beamed"></i> Training Samples
        </div>
        <div class="card-body p-0">
            <div id="training-samples-list" class="list-group list-group-flush" style="max-height: 400px; overflow-y: auto;">
                <div class="text-center p-3">
                    <div class="spinner-border text-success" role="status"></div>
                </div>
            </div>
        </div>
    </div>
</div>
```

---

## ⚠️ PROBLEMAS DE MÉDIO IMPACTO

### 3. Configurações duplicadas (ARCH-03)

**Problema**: Mesma variável definida em múltiplos lugares

**Arquivos afetados**:
1. `.env.example` (linhas 97, 102, 107)
2. `train/.env.example`
3. `train/env_config.py` (linhas 126-127)
4. `train/train_settings.py` (linhas 41, 44, 57)

**Solução (Sprint 3)**:
Criar `config/settings.py` central. Ver SPRINTS.md → Sprint 3 para implementação completa.

**Quick fix temporário**:
Documentar claramente em `.env.example` qual arquivo prevalece:
```bash
# === TREINAMENTO XTTS ===
# NOTA: Train também lê train/.env (sobrescreve se existir)
MAX_TRAIN_SAMPLES=  # Vazio = dataset completo
NUM_EPOCHS=1000
```

---

### 4. Python global sujo (ENV-01)

**Problema**: 183 pacotes instalados globalmente, sem venv

**Solução (Sprint 2)**:

```bash
cd /home/tts-webui-proxmox-passthrough

# 1. Criar venv
python3.11 -m venv venv

# 2. Ativar
source venv/bin/activate

# 3. Instalar deps
pip install --upgrade pip
pip install -r requirements.txt -c constraints.txt

# 4. Testar
python run.py
# Verificar que API inicia sem erros
```

**Arquivos a atualizar depois**:
- `Dockerfile` (multi-stage build com venv)
- `scripts/*.sh` (ativar venv antes de executar)
- Docs (adicionar instruções de setup)

---

### 5. Referências a F5-TTS e RVC na WebUI (LEG-01)

#### 5.1. Remover aba "Modelos RVC"
**Arquivo**: `app/webui/index.html`  
**Linha**: ~56

```html
<!-- REMOVER ESTA SEÇÃO COMPLETA: -->
<li class="nav-item">
    <a class="nav-link" href="#" onclick="app.navigate('rvc-models')">
        <i class="bi bi-cpu"></i> Modelos RVC
    </a>
</li>
```

#### 5.2. Limpar funções RVC do JavaScript
**Arquivo**: `app/webui/assets/js/app.js`  
**Buscar e remover**:
```javascript
// REMOVER funções:
loadRVCModels()
uploadRVCModel()
deleteRVCModel()
// E qualquer referência a 'rvc' ou 'RVC'
```

**Comando para encontrar**:
```bash
grep -n "rvc\|RVC" app/webui/assets/js/app.js
# Remover linhas encontradas
```

---

## 📚 DOCUMENTAÇÃO A LIMPAR

### 6. Docs com referências F5-TTS/RVC

**Estratégia**: Adicionar banner de aviso no topo

**Arquivos**:
1. `docs/LOW_VRAM.md`
2. `docs/API_PARAMETERS.md`
3. `docs/ARCHITECTURE.md`
4. `docs/README.md`

**Banner a adicionar** (linha 1 de cada arquivo):
```markdown
> ⚠️ **AVISO - v2.0**: F5-TTS e RVC foram removidos. Este projeto usa **exclusivamente XTTS-v2**.
> 
> Algumas seções abaixo são históricas e estão marcadas como deprecated.

---
```

**Seções específicas a marcar**:

Em `docs/API_PARAMETERS.md` (linhas 15, 43, 44):
```markdown
| `tts_engine` | string | `"xtts"` | ~~Engine TTS: `"xtts"` ou `"f5tts"`~~ **DEPRECATED: apenas XTTS em v2.0** |
```

---

## 🐳 DOCKER

### 7. Dockerfile - Remover criação de pastas F5/RVC

**Arquivo**: `Dockerfile`  
**Linha**: ~84

```dockerfile
# ANTES:
RUN mkdir -p /app/uploads /app/processed /app/temp \
    /app/voice_profiles /app/models /app/models/f5tts /app/models/whisper /app/models/rvc \
    /app/logs

# DEPOIS:
RUN mkdir -p /app/uploads /app/processed /app/temp \
    /app/voice_profiles /app/models /app/models/whisper \
    /app/logs
```

---

## 🔗 SYMLINKS

### 8. Remover symlink /runs

**Problema**: `/runs` é symlink para `/train/runs`, polui namespace raiz

**Solução**:
```bash
cd /home/tts-webui-proxmox-passthrough
rm runs  # É symlink, seguro remover

# Verificar se há referências no código
grep -r '"/runs"' . --exclude-dir=node_modules
# Se houver, trocar por "train/runs"
```

---

## 🎓 TREINAMENTO

### 9. Melhorar qualidade de timbre (TRAIN-03)

**Arquivos principais**:

#### 9.1. Ajustar hiperparâmetros
**Arquivo**: `train/train_settings.py`  
**Linhas**: 44-56

```python
# EXPERIMENTAR:
num_epochs: int = Field(default=500, description="Number of epochs")  # Aumentar de 1000
learning_rate: float = Field(default=5.0e-6, description="Learning rate")  # Mais conservador
batch_size: int = Field(default=4, description="Training batch size")  # Ou 8 com LoRA
```

#### 9.2. Implementar LoRA
**Arquivo**: `train/scripts/train_xtts.py`  
**Linha**: ~25 (descomentar import)

```python
# Descomentar:
from peft import LoraConfig, get_peft_model

# Procurar função load_pretrained_model() e adicionar LoRA
```

**NOTA**: Requer pesquisa dos target_modules corretos do XTTS. Ver Sprint 6.

#### 9.3. Filtrar dataset por qualidade
**Arquivo**: `train/scripts/segment_audio.py`  
**Adicionar após VAD**:

```python
def calculate_snr(audio_data, sample_rate):
    """Calculate Signal-to-Noise Ratio"""
    try:
        import noisereduce as nr
        signal_power = np.mean(audio_data ** 2)
        noise_estimate = nr.reduce_noise(y=audio_data, sr=sample_rate)
        noise_power = np.mean((audio_data - noise_estimate) ** 2)
        
        if noise_power == 0:
            return float('inf')
        
        snr_db = 10 * np.log10(signal_power / noise_power)
        return snr_db
    except:
        return 0  # Fallback

# No loop de segmentação, adicionar:
snr = calculate_snr(chunk_data, sample_rate)
if snr < 10:  # Descartar chunks muito ruidosos
    logger.debug(f"Discarding chunk (SNR={snr:.1f}dB < 10dB)")
    continue
```

---

## 🧪 TESTES ESSENCIAIS

### Checklist de testes após cada mudança:

```bash
# 1. API inicia sem erros
python run.py
# Abrir http://localhost:8005 → deve retornar JSON

# 2. WebUI carrega
# Abrir http://localhost:8005/webui/index.html

# 3. Checkpoints aparecem
# WebUI → Training → Checkpoints
# Deve listar arquivos *.pt em train/output/checkpoints/

# 4. Samples aparecem
# WebUI → Training → Samples
# Deve mostrar players de áudio

# 5. Treino funciona
MAX_TRAIN_SAMPLES=100 NUM_EPOCHS=1 python3 -m train.scripts.train_xtts
# Deve completar 1 epoch sem erro

# 6. Inferência funciona
# WebUI → Criar Job → Dublar texto
# Deve gerar áudio
```

---

## 📞 DÚVIDAS FREQUENTES

### P: Por que checkpoints não aparecem?
**R**: Extensão errada. API busca `*.pth`, mas treino gera `*.pt`. Ver Fix #1.

### P: Como ativar venv?
**R**: `source venv/bin/activate` (criar antes se não existe - ver #4)

### P: Posso apagar Python global?
**R**: NÃO recomendado. Só usar venv e ignorar global. Ver Sprint 2.

### P: LoRA funciona com XTTS?
**R**: Sim, mas requer descobrir target_modules corretos. Ver Sprint 6, Task 6.1.

### P: Como melhorar qualidade de voz?
**R**: 
1. Mais dados de qualidade
2. Filtrar dataset (SNR, VAD)
3. Ajustar hiperparâmetros (LR, epochs)
4. Usar LoRA (permite batch maior)

---

## 🚀 ORDEM DE IMPLEMENTAÇÃO SUGERIDA

### Dia 1 (CRÍTICO):
1. ✅ Fix #1: Checkpoint extension (`.pth` → `.pt`)
2. ✅ Fix #2: Samples endpoint + mount + UI

### Semana 1:
3. ⚠️ Fix #5: Remover refs RVC na WebUI
4. ⚠️ Fix #7: Limpar Dockerfile
5. ⚠️ Fix #8: Remover symlink /runs

### Semana 2:
6. 🐍 Fix #4: Criar venv limpo
7. ⚙️ Fix #3: Centralizar configs (opcional, mas recomendado)

### Semana 3+:
8. 📚 Fix #6: Limpar docs (adicionar banners)
9. 🎓 Fix #9: Otimizar qualidade (LoRA, hiperparâmetros)

---

## 📊 MÉTRICAS DE SUCESSO

Após todas as mudanças:

- [ ] WebUI mostra checkpoints ✅
- [ ] WebUI mostra samples de áudio ✅
- [ ] Zero referências a F5-TTS/RVC no código ativo ✅
- [ ] Projeto roda em venv isolado ✅
- [ ] Docs atualizados ✅
- [ ] Qualidade de timbre >= baseline ✅

---

**Dúvidas?** Consulte MORE.md (diagnóstico) e SPRINTS.md (planejamento detalhado)

**Bom trabalho! 🚀**
