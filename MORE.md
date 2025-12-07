# MORE – Map Of Refactors & Errors

**Data**: 2024-12-07  
**Autor**: Tech Lead / Arquiteto Sênior  
**Objetivo**: Diagnóstico completo do projeto para migração 100% XTTS-v2 e limpeza de legado F5-TTS/RVC

---

## Sumário Executivo

O projeto está **funcional mas poluído** com:
- ✅ **XTTS-v2** já é o único engine TTS em produção (bom!)
- ❌ **Referências mortas** a F5-TTS e RVC em docs, WebUI e código comentado
- ❌ **183 pacotes Python instalados globalmente** (sistema sujo, sem venv)
- ❌ **Configurações duplicadas** em múltiplos arquivos (.env, train/.env, YAMLs)
- ❌ **WebUI busca checkpoints em path errado** (procura `*.pth`, mas treino gera `*.pt`)
- ❌ **Lazy loading removido da API, mas não na documentação**
- ❌ **Symlink `/runs → /train/runs`** (desnecessário, poluição de namespace)
- ⚠️ **Qualidade de timbre XTTS** pode melhorar (dataset, hiperparâmetros, técnica de fine-tuning)

---

## 1. Erros / Problemas Encontrados

### 1.1. Arquitetura & Organização

#### 🔴 ARCH-01: Pasta `/train` isolada mas não integrada corretamente
**Local**: Estrutura geral do projeto  
**Problema**: 
- `/train` é um mini-projeto separado (bom design!)
- Mas há **symlink `/runs → /train/runs`** que polui namespace raiz
- Docker monta pastas diretamente em vez de usar paths compartilhados centralizados

**Impacto**: 
- Confusão sobre onde ficam os checkpoints
- Dificuldade de rastrear logs e saídas
- Quebra de separação de responsabilidades

**Sugestão**:
- Remover symlink `/runs`
- Centralizar paths em config única
- Docker deve montar `/train` inteiro, não subpastas

**Arquivos afetados**:
- `/runs` (symlink a remover)
- `docker-compose.yml` (revisar volumes)
- Docs que referenciam `/runs`

---

#### 🔴 ARCH-02: WebUI busca checkpoints com extensão errada
**Local**: `app/webui/assets/js/app.js:2748`, `app/training_api.py:465`  
**Problema**:
- API `/training/checkpoints` procura `*.pth` (linha 499 do `training_api.py`)
- Mas script de treino **salva `*.pt`** (verificado em `train/output/checkpoints/`)
- Resultado: WebUI lista "Nenhum checkpoint disponível" mesmo com checkpoints existentes

**Impacto**: 
- **CRÍTICO** - WebUI não mostra checkpoints treinados
- Usuário não consegue testar modelos finetuned
- Perda de funcionalidade core

**Sugestão**:
```python
# Em app/training_api.py:499
# ANTES:
for ckpt_file in checkpoint_dir.glob("*.pth"):

# DEPOIS:
for ckpt_file in checkpoint_dir.glob("*.pt"):
```

**Arquivos afetados**:
- `app/training_api.py` (função `_scan_checkpoint_dir`)

---

#### 🟡 ARCH-03: Configurações duplicadas entre `/app` e `/train`
**Local**: `.env.example`, `train/.env.example`, `train/env_config.py`, `app/settings.py`  
**Problema**:
- Mesmas variáveis definidas em 4 lugares diferentes:
  - `MAX_TRAIN_SAMPLES`: `.env.example:97`, `train/train_settings.py:41`
  - `NUM_EPOCHS`: `.env.example:102`, `train/train_settings.py:44`
  - `LOG_EVERY_N_STEPS`: `.env.example:107`, `train/train_settings.py:57`
  - Paths (`DATA_DIR`, `OUTPUT_DIR`, `MODELS_DIR`): múltiplas definições
- Risco de valores conflitantes

**Impacto**: 
- Manutenção difícil
- Bugs silenciosos (mudar em um lugar, esquecer outro)
- Violação do princípio DRY (Don't Repeat Yourself)

**Sugestão**:
- **Opção 1** (preferida): Train lê `.env` raiz do projeto + sobrescreve com `train/.env` se existir
- **Opção 2**: Train tem seu próprio `.env` completamente independente
- Documentar claramente qual prevalece

**Arquivos afetados**:
- `.env.example`
- `train/.env.example`
- `train/env_config.py`
- `train/train_settings.py`

---

### 1.2. Legado F5-TTS e RVC

#### 🟡 LEG-01: Referências documentais a F5-TTS e RVC
**Local**: `docs/`, `app/webui/index.html`  
**Problema**:
- Documentos mencionam F5-TTS e RVC como opções disponíveis
- WebUI tem aba "Modelos RVC" (linha 56 de `index.html`)
- Docs fazem referências a engines removidos

**Arquivos com referências F5-TTS**:
- `docs/LOW_VRAM.md` (linhas 4, 22, 30, 32, 91, 187+)
- `docs/V2_RELEASE_NOTES.md` (linhas 32, 76, 139)
- `docs/API_PARAMETERS.md` (linhas 15, 43, 44)
- `docs/ARCHITECTURE.md` (linha 6, 84)
- `docs/README.md` (linhas 30, 38, 148-151)

**Arquivos com referências RVC**:
- `app/webui/index.html` (linha 56 - aba "Modelos RVC")
- `docs/README.md` (linhas 148-151)
- `docs/ARCHITECTURE.md` (linhas 29-31, 47, 49, 55-56, 84, 102, 106)
- `Dockerfile` (linha 84 - cria pasta `/app/models/rvc`)

**Impacto**: 
- Confusão para novos desenvolvedores
- Documentação desatualizada = perda de confiança
- UI oferece funcionalidade inexistente

**Sugestão**:
- **Docs**: Marcar como "removido em v2.0" ou apagar seções inteiras
- **WebUI**: Remover aba "Modelos RVC" completamente
- **Dockerfile**: Remover criação de pasta `/app/models/rvc`

---

#### 🟢 LEG-02: Código F5-TTS/RVC já foi removido (OK!)
**Local**: `app/engines/`, código Python  
**Status**: ✅ **JÁ RESOLVIDO**  
**Evidência**:
- Não há `f5tts_engine.py` ou `rvc_client.py` em `app/`
- Apenas XTTS engine presente: `app/engines/xtts_engine.py`
- Nenhum import de F5 ou RVC no código ativo

**Ação**: Manter vigilância em code reviews futuros

---

### 1.3. Ambiente Python & Dependências

#### 🔴 ENV-01: Python global sujo (183 pacotes sem venv)
**Local**: Sistema global `/usr/bin/python3.11`  
**Problema**:
- **183 pacotes instalados globalmente** (via `pip list`)
- Nenhum venv no projeto
- Dificulta reprodutibilidade e versionamento de deps
- Riscos de conflitos entre projetos

**Impacto**: 
- **ALTO** - Ambiente não reproduzível
- Dificulta deploy limpo
- Impossível garantir versões exatas de dependências

**Sugestão**:
1. Criar venv limpo:
   ```bash
   cd /home/tts-webui-proxmox-passthrough
   python3.11 -m venv venv
   source venv/bin/activate
   pip install --upgrade pip
   pip install -r requirements.txt -c constraints.txt
   ```

2. Atualizar scripts para usar venv:
   ```bash
   # Em train/scripts/*.py
   #!/home/tts-webui-proxmox-passthrough/venv/bin/python
   ```

3. Docker: criar stage com venv isolado
   ```dockerfile
   # Multi-stage build
   FROM base AS builder
   RUN python3.11 -m venv /opt/venv
   ENV PATH="/opt/venv/bin:$PATH"
   RUN pip install -r requirements.txt
   
   FROM base AS runtime
   COPY --from=builder /opt/venv /opt/venv
   ENV PATH="/opt/venv/bin:$PATH"
   ```

**Arquivos afetados**:
- `Dockerfile`
- Scripts shell em `scripts/`
- CI/CD pipelines se houver

---

#### 🟡 ENV-02: Symlinks F5-TTS em Python global
**Local**: `/root/.local/lib/python3.11/...`  
**Problema**:
- Script `REMOVE_F5_SYMLINKS.sh` indica que havia/há symlinks de F5-TTS em instalação global
- Pode causar imports não intencionais

**Impacto**: 
- Baixo (se F5 não é importado)
- Médio (se houver imports residuais)

**Sugestão**:
- Executar `REMOVE_F5_SYMLINKS.sh` (já existe!)
- Migrar para venv (resolve definitivamente)

**Arquivos**:
- `REMOVE_F5_SYMLINKS.sh` (já existe, executar)

---

### 1.4. API & Resiliência

#### 🟢 API-01: Eager loading já implementado (OK!)
**Local**: `app/main.py:203`, `app/services/xtts_service.py:90`  
**Status**: ✅ **JÁ RESOLVIDO**  
**Evidência**:
- `@app.on_event("startup")` carrega XTTS no startup
- `XTTSService.initialize()` faz eager load do modelo
- Primeira request não tem atraso

**Observação**: 
- Docs ainda mencionam "lazy load" em alguns lugares (atualizar)

---

#### 🟡 API-02: Falta lifespan context manager (FastAPI moderno)
**Local**: `app/main.py`  
**Problema**:
- Usa `@app.on_event("startup")` (deprecated desde FastAPI 0.100+)
- Recomendação: migrar para `lifespan` context manager

**Impacto**: 
- Baixo (funciona, mas não é best practice)

**Sugestão**:
```python
from contextlib import asynccontextmanager

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    logger.info("🚀 Starting Audio Voice Service...")
    xtts_service = XTTSService(...)
    xtts_service.initialize()
    set_xtts_service(xtts_service)
    
    yield  # Aplicação roda aqui
    
    # Shutdown
    logger.info("Shutting down...")

app = FastAPI(lifespan=lifespan)
```

**Arquivos**:
- `app/main.py`

---

### 1.5. WebUI & UX

#### 🔴 UI-01: Checkpoints não aparecem (extensão errada)
**Ver ARCH-02** (mesmo problema, impacto na UI)

---

#### 🟡 UI-02: Amostras de áudio não listadas na WebUI
**Local**: `app/webui/` (verificar se há endpoint para listar samples)  
**Problema**:
- Script de treino gera samples em `train/output/samples/epoch_N_output.wav`
- WebUI não tem endpoint/lógica para listar e tocar esses samples

**Impacto**: 
- Usuário não consegue avaliar qualidade do treino em tempo real
- Perde funcionalidade valiosa de A/B test

**Sugestão**:
- Criar endpoint `GET /training/samples?model_name=X`
- WebUI: adicionar player de áudio para cada época
- Mostrar ao lado dos checkpoints na lista

**Arquivos afetados**:
- `app/training_api.py` (novo endpoint)
- `app/webui/assets/js/app.js` (fetch + render)
- `app/webui/index.html` (UI para samples)

---

#### 🟡 UI-03: Link TensorBoard não configurável
**Local**: `app/webui/index.html` (se houver)  
**Problema**:
- TensorBoard roda em porta 6006 (hardcoded em treino)
- WebUI precisa exibir link correto (baseado em HOST do deployment)

**Sugestão**:
- Endpoint `/training/tensorboard-url` retorna URL configurada via env
- WebUI renderiza link dinamicamente

**Arquivos**:
- `train/train_settings.py` (adicionar `tensorboard_url`)
- `app/training_api.py` (endpoint de configuração)
- WebUI (exibir link)

---

### 1.6. Treinamento / XTTS-v2

#### 🟡 TRAIN-01: Pipeline de preparação de dataset está OK, mas não integrado na WebUI
**Local**: `train/scripts/`  
**Problema**:
- Scripts existem e funcionam:
  - `download_youtube.py`
  - `segment_audio.py`
  - `transcribe_audio_parallel.py`
  - `build_ljs_dataset.py`
- **Mas não há botões na WebUI para executá-los**
- Usuário precisa usar linha de comando (não user-friendly)

**Impacto**: 
- Baixo (usuário avançado consegue usar)
- Alto (usuário final não usa)

**Sugestão**:
- Adicionar seção "Dataset Preparation" na WebUI
- Botões para cada etapa do pipeline
- Usar endpoints de `app/training_api.py` (já existem!)

**Arquivos**:
- `app/webui/index.html` (adicionar seção)
- `app/webui/assets/js/app.js` (integrar com API)

---

#### 🟡 TRAIN-02: Configuração de XTTS fine-tuning não otimizada
**Local**: `train/train_settings.py`, `train/scripts/train_xtts.py`  
**Problema**:
- Hiperparâmetros podem não estar otimizados para PT-BR
- Learning rate: `1e-5` (pode ser agressivo ou conservador demais)
- Batch size: 2 (muito pequeno, treino lento)
- Não usa LoRA (comentado como "TODO: fix target modules")

**Impacto**: 
- Qualidade de timbre pode ser subótima
- Treino pode não convergir bem

**Sugestão**:
- **Fase 1**: Testar LoRA (economiza VRAM, permite batch maior)
- **Fase 2**: Grid search de hiperparâmetros (LR, batch, epochs)
- **Fase 3**: Técnicas avançadas (data augmentation, ensemble)

**Arquivos**:
- `train/train_settings.py`
- `train/scripts/train_xtts.py`
- Criar `docs/HYPERPARAMETER_TUNING.md`

---

#### 🟡 TRAIN-03: Qualidade de timbre não ótima
**Local**: Saídas de inferência  
**Problema**:
- Pode ser causado por:
  1. **Dataset pequeno/ruidoso**: Poucos exemplos de boa qualidade
  2. **Segmentação ruim**: Chunks com múltiplos speakers ou silêncio
  3. **Transcrição imprecisa**: Whisper pode errar, texto não alinha com áudio
  4. **Hiperparâmetros**: LR, temperature, epochs não otimizados
  5. **Fine-tuning insuficiente**: Poucas épocas, underfitting

**Sugestão**:
1. **Dataset**: 
   - Filtrar segmentos por qualidade (SNR, duração, único speaker)
   - Usar VAD mais agressivo
   - Revisar transcrições (correção manual de erros críticos)

2. **Treino**:
   - Aumentar epochs (testar 500-1000)
   - Ajustar LR (testar 5e-6 a 1e-4 com scheduler)
   - Usar LoRA (permite batch maior sem OOM)

3. **Inferência**:
   - Testar diferentes temperaturas (0.5 - 0.9)
   - Ajustar `repetition_penalty` e `speed`

**Arquivos**:
- `train/scripts/segment_audio.py` (melhorar VAD)
- `train/scripts/transcribe_audio_parallel.py` (revisar Whisper)
- `train/train_settings.py` (hiperparâmetros)

---

## 2. Melhorias Sugeridas

### 2.1. Arquitetura & Organização

#### ✨ IMPROVE-ARCH-01: Centralizar configurações
- **O quê**: Criar `config/central_config.py` que lê `.env` e distribui para `/app` e `/train`
- **Por quê**: Elimina duplicação, fonte única de verdade
- **Como**:
  ```python
  # config/central_config.py
  from pydantic_settings import BaseSettings
  
  class GlobalConfig(BaseSettings):
      # Paths
      data_root: Path = Path("data")
      train_root: Path = Path("train")
      models_dir: Path = Path("models")
      
      # Training
      max_train_samples: Optional[int] = None
      num_epochs: int = 1000
      
      class Config:
          env_file = ".env"
  ```

---

#### ✨ IMPROVE-ARCH-02: Remover symlinks desnecessários
- **O quê**: Deletar `/runs` (symlink para `/train/runs`)
- **Por quê**: Polui namespace raiz, confunde paths
- **Como**: 
  ```bash
  rm /home/tts-webui-proxmox-passthrough/runs
  # Atualizar refs em docs/código para usar `train/runs`
  ```

---

#### ✨ IMPROVE-ARCH-03: Docker volumes centralizados
- **O quê**: Montar `/train` inteiro em vez de subpastas
- **Como**:
  ```yaml
  volumes:
    - ./train:/app/train
    # Remove mounts individuais de train/output, train/data, etc.
  ```

---

### 2.2. Legado F5-TTS e RVC

#### ✨ IMPROVE-LEG-01: Limpeza de docs
- **O quê**: Remover/marcar seções F5-TTS e RVC
- **Como**:
  - Adicionar banner: `> ⚠️ F5-TTS removed in v2.0 - XTTS-only`
  - Ou deletar seções inteiras e criar `docs/archive/`

---

#### ✨ IMPROVE-LEG-02: Limpeza de WebUI
- **O quê**: Remover aba "Modelos RVC"
- **Como**: Editar `app/webui/index.html`, remover linha 56 + código JS relacionado

---

### 2.3. Ambiente Python

#### ✨ IMPROVE-ENV-01: Criar venv limpo
- **O quê**: Migrar de Python global para venv isolado
- **Como**: Ver sugestão em ENV-01

---

#### ✨ IMPROVE-ENV-02: Executar REMOVE_F5_SYMLINKS.sh
- **O quê**: Limpar symlinks F5-TTS em sistema global
- **Como**: 
  ```bash
  chmod +x REMOVE_F5_SYMLINKS.sh
  ./REMOVE_F5_SYMLINKS.sh
  ```

---

### 2.4. API & Resiliência

#### ✨ IMPROVE-API-01: Migrar para lifespan
- Ver sugestão em API-02

---

### 2.5. WebUI & UX

#### ✨ IMPROVE-UI-01: Adicionar listagem de samples
- Ver sugestão em UI-02

#### ✨ IMPROVE-UI-02: TensorBoard URL configurável
- Ver sugestão em UI-03

#### ✨ IMPROVE-UI-03: Integrar pipeline de dataset na WebUI
- Ver sugestão em TRAIN-01

---

### 2.6. Treinamento / XTTS-v2

#### ✨ IMPROVE-TRAIN-01: Implementar LoRA no fine-tuning
- **O quê**: Ativar LoRA para reduzir VRAM e acelerar treino
- **Como**: 
  - Descobrir target modules corretos do XTTS-v2
  - Descomentar código LoRA em `train/scripts/train_xtts.py`
  - Testar com `lora_rank=8`, `lora_alpha=16`

---

#### ✨ IMPROVE-TRAIN-02: Grid search de hiperparâmetros
- **O quê**: Script automático para testar combinações de LR, batch, temperature
- **Como**: Criar `train/scripts/hyperparameter_search.py`

---

#### ✨ IMPROVE-TRAIN-03: Melhorar qualidade de dataset
- **O quê**: Filtros de qualidade, limpeza de transcrições
- **Como**: 
  - Adicionar SNR filter em `segment_audio.py`
  - Revisar output do Whisper (correção automática de números, nomes próprios)

---

## 3. Priorização (MoSCoW)

### Must Have (Sprint 1-2)
- 🔴 **ARCH-02**: Fix extensão checkpoint (`.pt` vs `.pth`) - **BLOCKER**
- 🔴 **ENV-01**: Criar venv limpo
- 🟡 **LEG-01**: Limpar docs e WebUI de refs a F5/RVC

### Should Have (Sprint 3-4)
- 🟡 **ARCH-03**: Centralizar configs
- 🟡 **UI-02**: Listar samples de áudio
- 🟡 **TRAIN-01**: Integrar pipeline na WebUI

### Could Have (Sprint 5-6)
- 🟡 **API-02**: Migrar para lifespan
- 🟡 **TRAIN-02**: Otimizar hiperparâmetros
- 🟡 **TRAIN-03**: Melhorar qualidade dataset

### Won't Have (Backlog)
- Migração completa para outro framework de TTS
- Support multi-GPU distribuído

---

## 4. Métricas de Sucesso

- ✅ Zero referências a F5-TTS/RVC em código ativo
- ✅ WebUI mostra checkpoints corretamente
- ✅ Projeto roda 100% em venv isolado
- ✅ Qualidade de timbre >= baseline (avaliação A/B test)
- ✅ Tempo de treino < 2h para 100 epochs (com LoRA)
- ✅ Docs 100% atualizados para XTTS-only

---

## 5. Riscos

| Risco | Probabilidade | Impacto | Mitigação |
|-------|---------------|---------|-----------|
| Venv quebrar imports existentes | Média | Alto | Testar em staging primeiro, rollback fácil |
| LoRA não funcionar com XTTS | Alta | Médio | Manter full fine-tuning como fallback |
| Performance degradar com refactor | Baixa | Médio | Benchmarks antes/depois |
| Dataset pequeno limitar qualidade | Alta | Alto | Coletar mais dados, técnicas de augmentation |

---

## 6. Próximos Passos

1. ✅ Ler este relatório (você está aqui!)
2. 📋 Revisar e priorizar com time
3. 🚀 Executar Sprint 1 (ver SPRINTS.md)
4. 🔄 Iterar e ajustar com base em resultados

---

**Autor**: Claude (Tech Lead AI)  
**Revisão**: Time de desenvolvimento  
**Última atualização**: 2024-12-07
