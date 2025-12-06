# Relatório Técnico – Auditoria F5-TTS Project

**Data:** 06 de Dezembro de 2025  
**Versão:** 1.0  
**Autor:** Tech Lead - Análise de Código e Arquitetura  
**Objetivo:** Auditoria completa do projeto de fine-tuning F5-TTS PT-BR para transformação em código de nível profissional

---

## 1. Sumário Executivo

### 🔴 5-10 Principais Problemas / Riscos

1. **Config & Paths Fragmentados (CRÍTICO)**
   - Paths de dataset, checkpoints, vocoder e vocab espalhados em 5+ lugares diferentes (.env raiz, train/.env, YAML, código Python)
   - Risco de modelo mudo/grunhidos por vocabulário inconsistente entre treino e inferência

2. **Inconsistência Treino vs Inferência (ALTA)**
   - Scripts de treino (run_training.py) usam API do F5-TTS de forma diferente da inferência (AgentF5TTS, f5tts_engine.py)
   - `vocab_file`, `use_ema`, `device`, `vocoder` configurados de formas conflitantes
   - Já existe histórico de bugs de checkpoint (ERROR.md, CHECKPOINT_FIX.md)

3. **Duplicação de Configuração (MÉDIA-ALTA)**
   - train/.env, train/config/train_config.yaml e train/config/dataset_config.yaml têm overlaps
   - Valores hardcoded em scripts Python sobrescrevem configs YAML
   - Impossível saber qual config é "source of truth"

4. **Vocabulário Duplicado e Sem Versionamento (ALTA)**
   - 3 cópias de vocab.txt em lugares diferentes (train/config/, train/data/, train/data/f5_dataset/)
   - Nenhuma garantia de que são idênticos
   - Sem versionamento ou hash para validar consistência

5. **Pipeline de Dados Sem Separação de Responsabilidades (MÉDIA)**
   - Scripts gigantes que fazem tudo (download, corte, VAD, transcrição, normalização)
   - prepare_segments_optimized.py tem 570 linhas misturando lógica de infra e domínio
   - Difícil testar, debugar e manter

6. **Falta de Reprodutibilidade Completa (MÉDIA)**
   - Seed definido apenas no .env (SEED=666), mas não propagado consistentemente
   - Nenhum script de setup documentado para reproduzir ambiente exato
   - Versões de dependências não pinadas (requirements.txt usa >=, não ==)

7. **Checkpoints sem Validação Automática (MÉDIA)**
   - run_training.py tem validação manual, mas não é executada antes de carregar checkpoint
   - Histórico de checkpoints corrompidos (CHECKPOINT_FIX.md)
   - Sem verificação de hash/tamanho esperado

8. **Logging e Debugging Insuficientes (BAIXA-MÉDIA)**
   - Logs espalhados em vários arquivos sem rotação
   - Falta de structured logging (JSON) para facilitar parsing
   - Sem níveis de log configuráveis por módulo

9. **Testes Ausentes para Pipeline de Treino (MÉDIA)**
   - Testes existem apenas para app/ (API REST), não para train/
   - Nenhum teste de fumaça para pipeline de dados, load de checkpoint, inferência pós-treino
   - Impossível validar mudanças sem rodar pipeline completo

10. **DX (Developer Experience) Ruim (BAIXA)**
    - README genérico na raiz, documentação de treino só em train/README.md
    - Scripts sem docstrings completas
    - Nomes de arquivos confusos (_deprecated/, scripts de experimento misturados com "oficiais")

### ✅ 5-10 Principais Oportunidades

1. **Unificação de Configuração**
   - Centralizar toda config em um único lugar (ex: train/config.yaml com overrides via .env)
   - Criar classes de configuração Python (Pydantic) para validação e type safety

2. **Separação Clara de Responsabilidades**
   - Camada de domínio (TTS, Dataset, Models) separada de infra (paths, logging, CLI)
   - Utilitários genéricos (normalização, VAD, etc.) em módulos reutilizáveis

3. **Pipeline de Dados Modular**
   - Quebrar scripts gigantes em funções/classes pequenas e testáveis
   - Pipeline em etapas: Download → Segment → Transcribe → Normalize → Validate → Build Dataset
   - Cada etapa com interface clara (input/output)

4. **Experiência de Treino Melhorada**
   - Callbacks personalizados (early stopping, checkpoint, metrics)
   - Métricas além de loss (ex: MCD, MOS estimado, duração média)
   - CLI mais amigável com argumentos validados (typer ou click)

5. **Experiência de Inferência Simplificada**
   - API unificada para inferência (mesma interface para AgentF5TTS e f5tts_engine.py)
   - CLI de teste rápido (python -m train.infer --checkpoint X --text "..." --output Y)
   - Service layer para encapsular lógica de load/cache de modelo

6. **Documentação e Exemplos**
   - README por pasta (train/, train/scripts/, train/utils/)
   - Scripts de exemplo (examples/) com casos de uso reais
   - Tutorial passo-a-passo para iniciantes

7. **Testes Automatizados**
   - Testes de fumaça para cada script (pytest)
   - Fixtures para datasets pequenos de teste
   - Testes de integração para pipeline completo (smoke test end-to-end)

8. **MLOps e Reproducibilidade**
   - Versionamento de datasets (DVC ou similar)
   - Registro de experimentos (MLflow ou Weights & Biases)
   - Scripts de setup automático (make setup, docker-compose para treino)

9. **Qualidade de Código**
   - Linting (ruff ou flake8) e formatação (black)
   - Type hints em todas as funções
   - Pre-commit hooks

10. **Monitoramento e Debugging**
    - Structured logging (loguru com JSON)
    - Health checks para validar setup antes de treinar
    - Script de benchmark para comparar checkpoints

---

## 2. Erros e Problemas por Categoria

### 2.1 Config & Paths

#### **P1: Paths de Dataset Fragmentados**

**Localização:**
- `.env` (raiz): `F5TTS_CUSTOM_CHECKPOINT=/app/train/output/ptbr_finetuned2/model_last.pt`
- `train/.env`: `DATASET_PATH=train/data/f5_dataset`, `OUTPUT_DIR=train/output/ptbr_finetuned2`
- `train/config/train_config.yaml`: `dataset_path: "./train/data/f5_dataset"`, `output_dir: "train/output/ptbr_finetuned2"`
- `train/config/dataset_config.yaml`: (não define paths base, apenas subpaths relativos)
- Código Python hardcoded em scripts

**Descrição:**
Existem pelo menos 4 fontes de verdade para paths críticos:
1. .env na raiz (usado pela API de inferência)
2. train/.env (usado pelo run_training.py via env_loader.py)
3. train_config.yaml (parcialmente usado, mas sobrescrito por .env)
4. Hardcoded em scripts (ex: AgentF5TTSChunk.py linha 182: `/home/tts-webui-proxmox-passthrough/train/config/vocab.txt`)

**Impacto:**
- **CRÍTICO**: Se paths divergirem, modelo pode treinar em um dataset mas inferir esperando outro
- Difícil manter sincronizado quando mudar estrutura de pastas
- Onboarding de novos devs é confuso

**Severidade:** ALTA

**Solução:**
1. Criar `train/config/paths.yaml` (ou seção `paths:` em config unificado)
2. Todos os scripts devem importar de um único módulo `train.config.paths`
3. Usar variáveis de ambiente apenas para overrides em deploy (não como config principal)
4. Validar paths no startup (se não existir, criar ou falhar com erro claro)

---

#### **P2: Vocabulário Duplicado sem Garantia de Consistência**

**Localização:**
- `train/config/vocab.txt` (2546 linhas)
- `train/data/vocab.txt` (não verificado se idêntico)
- `train/data/f5_dataset/vocab.txt` (idem)

**Descrição:**
Existem 3 cópias do vocab.txt em lugares diferentes. Nenhum script verifica se são idênticos.

F5-TTS espera que treino e inferência usem o MESMO vocab.txt. Se forem diferentes:
- Modelo pode gerar tokens fora do vocabulário → grunhidos, ruídos
- Embeddings de texto ficam misalinhados

**Impacto:**
- **ALTO**: Risco de modelo mudo ou com qualidade ruim
- Debugging difícil (bug silencioso, só aparece em produção)

**Severidade:** ALTA

**Solução:**
1. Manter vocab.txt em UM ÚNICO LUGAR: `train/config/vocab.txt` (source of truth)
2. Scripts que precisam de vocab devem:
   - Copiar de `train/config/vocab.txt` para o destino
   - OU criar symlink
   - OU passar path como argumento
3. Adicionar hash/checksum no início do arquivo (comentário): `# SHA256: abc123...`
4. Script de validação: `python -m train.scripts.validate_vocab` que verifica hash

---

#### **P3: Checkpoint Path Inconsistente entre Treino e Inferência**

**Localização:**
- Treino: `run_training.py` busca checkpoints em ordem: `train/output/`, `ckpts/`, `models/f5tts/`
- Inferência API: `f5tts_engine.py` linha 221: baixa de HuggingFace e aplica patch
- Inferência Script: `AgentF5TTSChunk.py` linha 180: usa path hardcoded `/app/train/output/ptbr_finetuned2/model_last.pt`
- .env raiz: `F5TTS_CUSTOM_CHECKPOINT=/app/train/output/ptbr_finetuned2/model_last.pt`

**Descrição:**
Cada contexto (treino, inferência API, script de teste) tem lógica diferente para localizar checkpoint.

Problema específico:
- `f5tts_engine.py` sempre baixa modelo do HuggingFace e aplica patch (linhas 239-300)
- Não respeita `F5TTS_CUSTOM_CHECKPOINT` do .env para usar checkpoint local fine-tunado
- Usuário treina modelo, mas API continua usando modelo base PT-BR

**Impacto:**
- **MÉDIO-ALTO**: Fine-tuning não é usado em produção (API ignora)
- Tempo desperdiçado treinando se não for usado
- Confusão: "por que meu modelo não melhorou?"

**Severidade:** ALTA

**Solução:**
1. Criar função utilitária: `train.utils.checkpoint.resolve_checkpoint_path(priority_list, fallback)`
2. Usar SEMPRE a mesma lógica em treino, inferência API e scripts
3. Prioridade recomendada:
   - 1º: Env var `F5TTS_CUSTOM_CHECKPOINT` (se existir arquivo)
   - 2º: train/output/{exp_name}/model_last.pt
   - 3º: Download do HuggingFace
4. Logar claramente qual checkpoint foi carregado

---

#### **P4: Config YAML vs .env vs Hardcoded: Quem Manda?**

**Localização:**
- `train/config/train_config.yaml`: define `learning_rate: 1.0e-4`, `batch_size_per_gpu: 4`, etc.
- `train/.env`: define `LEARNING_RATE=0.0001`, `BATCH_SIZE=2`, etc.
- `train/utils/env_loader.py`: faz merge com `.env` tendo prioridade sobre YAML
- Scripts Python: alguns sobrescrevem com valores hardcoded

**Descrição:**
Hierarquia de precedência não é clara:
- `train_config.yaml` parece ser config "oficial" (mais completo)
- Mas `env_loader.py` carrega `.env` que sobrescreve YAML
- E ainda tem hardcoded em alguns scripts

Exemplo:
```python
# train_config.yaml
batch_size_per_gpu: 4

# train/.env
BATCH_SIZE=2

# env_loader.py retorna
'batch_size': 2  # ← .env vence
```

**Impacto:**
- **MÉDIO**: Confusão sobre qual config está realmente ativa
- Dificulta reproduzir experimentos
- Erros silenciosos (mudou YAML mas não teve efeito)

**Severidade:** MÉDIA

**Solução:**
1. Definir hierarquia clara e documentada:
   - Nível 1 (padrão): `train/config/defaults.yaml`
   - Nível 2 (override): `train/config/train_config.yaml` (usuário edita)
   - Nível 3 (override de deploy): `train/.env` (apenas para CI/CD)
   - Nível 4 (override temporário): argumentos CLI `--learning-rate 0.0002`
2. Implementar com OmegaConf ou Hydra (bibliotecas especializadas em config)
3. Validar config no startup e logar valores finais

---

### 2.2 Treino vs Inferência

#### **P5: Uso de `vocab_file` Diferente entre Treino e Inferência**

**Localização:**
- Treino: `run_training.py` chama `finetune_cli` que usa vocab padrão do F5-TTS (ou não especifica)
- Inferência API: `f5tts_engine.py` linha 150: `load_model(vocab_file='', ...)` (usa padrão da lib)
- Inferência Script: `AgentF5TTSChunk.py` linha 182: `vocab_file="/home/.../train/config/vocab.txt"`
- train_config.yaml linha 18: `vocab_file: "/home/.../train/config/vocab.txt"` (mas não usado no código)

**Descrição:**
Scripts de inferência passam `vocab_file` explicitamente, mas treino não.

F5-TTS tem vocab padrão em `f5_tts/configs/vocab.txt` (multilingual). Se treino usa vocab padrão mas inferência usa customizado (ou vice-versa), embeddings ficam incompatíveis.

**Impacto:**
- **ALTO**: Modelo pode gerar áudio corrompido (grunhidos, cortes)
- Bug difícil de diagnosticar (só aparece em certas palavras)

**Severidade:** ALTA

**Solução:**
1. Sempre especificar `vocab_file` tanto no treino quanto na inferência
2. Usar o mesmo arquivo: `train/config/vocab.txt` (source of truth)
3. Adicionar validação: se checkpoint foi treinado com vocab X, inferência deve usar vocab X
   - Salvar hash do vocab nos metadados do checkpoint
   - Validar na carga

---

#### **P6: `use_ema` Inconsistente**

**Localização:**
- Treino: `train_config.yaml` linha 74: `use_ema: true`
- Inferência API: `f5tts_engine.py` linha 150: `use_ema=True`
- Inferência Script: `AgentF5TTSChunk.py` linha 28: `use_ema=True`
- Mas: checkpoint baixado de HuggingFace tem bug de prefix (ema. vs ema_model.)

**Descrição:**
Todos usam `use_ema=True`, que está correto.

Porém, há histórico de bug no checkpoint PT-BR (ERROR.md): chaves com prefix `ema.` em vez de `ema_model.`, causando falha no load.

Solução foi implementada (IMPLEMENTATION_COMPLETE.md), mas código ainda tem lógica de patch em `f5tts_engine.py` (linhas 239-300). Isso adiciona complexidade e pode quebrar se formato de checkpoint mudar.

**Impacto:**
- **MÉDIO**: Código funciona, mas é frágil
- Patch hardcoded dificulta manutenção
- Se F5-TTS mudar formato, patch pode falhar silenciosamente

**Severidade:** MÉDIA

**Solução:**
1. Usar checkpoints no formato correto desde o início
2. Se patch for necessário, mover para script separado: `python -m train.scripts.patch_checkpoint input.pt output.pt`
3. Não fazer patch em runtime (lento, arriscado)
4. Documentar formato esperado de checkpoint em `train/docs/CHECKPOINT_FORMAT.md`

---

#### **P7: Device Selection Duplicada**

**Localização:**
- `f5tts_engine.py` linha 117: `self.device = self._select_device(device, fallback_to_cpu)`
- `AgentF5TTSChunk.py` linha 14: `device=None` (auto-detect na F5TTS API)
- `run_training.py`: usa `env_loader.py` que retorna `device` do .env

**Descrição:**
Cada módulo tem lógica própria de seleção de device:
- API Engine: método `_select_device()` com fallback
- Script: passa `None` e deixa F5TTS decidir
- Treino: lê do .env

Não há garantia de que todos usam mesma lógica. Por exemplo:
- Se GPU não estiver disponível, API pode falhar mas script pode funcionar em CPU
- Logs diferentes dificultam debug

**Impacto:**
- **BAIXO-MÉDIO**: Funciona, mas inconsistente
- Dificulta debug (comportamento diferente entre contextos)

**Severidade:** BAIXA

**Solução:**
1. Criar função utilitária: `train.utils.device.select_device(preferred, fallback_to_cpu)`
2. Usar em todos os contextos (treino, inferência, scripts)
3. Logar decisão: "Using device: cuda:0 (preferred) / cpu (fallback)"

---

### 2.3 Data Pipeline / Pré-processamento

#### **P8: Scripts Gigantes Violam SRP (Single Responsibility Principle)**

**Localização:**
- `prepare_segments_optimized.py`: 570 linhas, faz: VAD, segmentação, normalização, resample, fade
- `transcribe_or_subtitles.py`: 756 linhas, faz: download legendas, Whisper ASR, normalização, QA
- `prepare_f5_dataset.py`: 210 linhas, faz: leitura metadata, filtragem, conversão Arrow

**Descrição:**
Scripts tentam fazer tudo em um arquivo monolítico:
- Lógica de domínio (VAD, normalização) misturada com infra (paths, logging, CLI)
- Funções enormes (ex: `iter_voice_regions` tem 100+ linhas)
- Difícil extrair para reutilizar em outros contextos

**Impacto:**
- **MÉDIO**: Manutenção difícil, bugs escondem-se em funções longas
- Testes impossíveis (como testar VAD sem rodar script inteiro?)
- Duplicação (normalização está em 2 scripts diferentes)

**Severidade:** MÉDIA

**Solução:**
1. Refatorar em módulos:
   ```
   train/audio/
     vad.py           # Voice Activity Detection
     segmentation.py  # Audio segmentation
     normalization.py # Audio normalization
     effects.py       # Fade, filters
   train/text/
     normalizer.py    # Text normalization (já existe!)
     qa.py            # Quality assurance
   train/io/
     youtube.py       # YouTube download
     subtitles.py     # Subtitle extraction
   ```
2. Scripts principais viram "orquestradores" finos que chamam funções

---

#### **P9: VAD Simples Demais para Casos Complexos**

**Localização:**
- `prepare_segments_optimized.py` linha 90-150: implementação de VAD baseada em RMS energy

**Descrição:**
VAD implementado é baseado apenas em energia RMS (dB). Problemas:
- Falha com música de fundo (pega tudo como voz)
- Falha com ruído de fundo constante (ar condicionado, ventilador)
- Threshold fixo (-40dB) pode não funcionar para todos os áudios

F5-TTS precisa de segmentos limpos. VAD ruim pode incluir silêncios ou cortar palavras.

**Impacto:**
- **MÉDIO-ALTO**: Dataset com segmentos ruins → modelo ruim
- Usuário precisa validar manualmente (trabalhoso)

**Severidade:** MÉDIA

**Solução:**
1. Adicionar opção de VAD avançado (Silero VAD, WebRTC VAD)
2. Fazer VAD configurável no dataset_config.yaml:
   ```yaml
   segmentation:
     vad_method: "energy"  # energy, silero, webrtc
     vad_threshold: -40
   ```
3. Para casos críticos, permitir VAD manual (Audacity, script com visualização)

---

#### **P10: Normalização de Áudio Pode Ser Agressiva Demais**

**Localização:**
- `dataset_config.yaml` linha 25: `target_lufs: -23.0`
- `prepare_segments_optimized.py`: usa pyloudnorm com esse valor

**Descrição:**
LUFS -23 é padrão broadcast, mas pode ser muito alto para treino TTS.

Se áudio original é -30 LUFS, normalizar para -23 aumenta volume +7dB. Isso pode:
- Amplificar ruído de fundo
- Causar clipping (se headroom for insuficiente)
- Mudar características naturais da voz

**Impacto:**
- **BAIXO-MÉDIO**: Pode degradar qualidade do dataset
- Difícil diagnosticar (modelo parece OK mas tem artefatos sutis)

**Severidade:** BAIXA

**Solução:**
1. Testar diferentes valores de LUFS (-23, -24, -26)
2. Fazer análise de distribuição de loudness no dataset original
3. Considerar normalização adaptativa (só normalizar se fora de range aceitável)
4. Documentar escolha em `train/docs/AUDIO_PROCESSING.md`

---

#### **P11: Falta de Validação de Qualidade Pós-Processamento**

**Localização:**
- `prepare_segments_optimized.py`: processa segmentos mas não valida qualidade
- `validate_and_reprocess.py`: existe mas não é executado automaticamente

**Descrição:**
Scripts de processamento não validam automaticamente se output está bom:
- Duração dos segmentos (muito curtos/longos?)
- SNR (signal-to-noise ratio)
- Clipping
- Sample rate correto

Validation script existe (`validate_and_reprocess.py`) mas deve ser rodado manualmente.

**Impacto:**
- **MÉDIO**: Segmentos ruins entram no dataset
- Descoberto tarde (após treinar)

**Severidade:** MÉDIA

**Solução:**
1. Integrar validação no final do pipeline de processamento
2. Gerar relatório: `train/data/processed/validation_report.json`
3. Incluir métricas:
   - Número de segmentos
   - Duração min/max/média
   - SNR estimado
   - Taxa de clipping
4. Rejeitar automaticamente segmentos abaixo de threshold

---

### 2.4 Qualidade de Código & Arquitetura

#### **P12: Falta de Type Hints e Docstrings**

**Localização:**
- Maioria das funções em `train/scripts/` não tem type hints
- Docstrings incompletas ou ausentes

**Descrição:**
Exemplo de `prepare_segments_optimized.py`:
```python
def detect_voice_in_chunk(audio_chunk: np.ndarray, sr: int, seg_config: dict):  # ← tem types
    """..."""  # ← tem docstring
    ...

def process_audio_file(input_path, output_dir, config):  # ← sem types
    # sem docstring
    ...
```

Inconsistente. Dificulta entender o que cada função faz/espera.

**Impacto:**
- **BAIXO-MÉDIO**: DX ruim, erros de tipo não detectados
- Onboarding lento

**Severidade:** BAIXA

**Solução:**
1. Adicionar type hints em todas as funções públicas
2. Usar mypy para validação estática
3. Docstrings no formato Google ou NumPy
4. Pre-commit hook para garantir

---

#### **P13: Mistura de Lógica de Negócio e Infra**

**Localização:**
- Scripts em `train/scripts/` misturam CLI parsing, logging, paths e lógica de domínio

**Descrição:**
Exemplo de padrão ruim:
```python
def main():
    # CLI parsing
    # Setup logging
    # Load config
    # Create directories
    # Business logic
    # Save results
    # Print summary
```

Tudo em uma função. Dificulta:
- Testar apenas a lógica de negócio
- Reutilizar em outros contextos (API, notebook)
- Mockar dependências (filesystem, logging)

**Impacto:**
- **MÉDIO**: Código não testável, não reutilizável
- Duplicação inevitável

**Severidade:** MÉDIA

**Solução:**
1. Aplicar Arquitetura em Camadas:
   ```
   CLI layer → Service layer → Domain layer
   ```
2. CLI apenas faz parsing e chama service
3. Service orquestra domínio e infra
4. Domínio é puro (sem I/O, sem logging)
5. Exemplo:
   ```python
   # Domain
   def segment_audio(audio: np.ndarray, params: SegmentParams) -> List[Segment]:
       ...
   
   # Service
   class AudioProcessingService:
       def process_file(self, input_path: Path, output_dir: Path) -> ProcessResult:
           audio = self.audio_loader.load(input_path)
           segments = segment_audio(audio, self.params)
           self.audio_saver.save_all(segments, output_dir)
           return ProcessResult(...)
   
   # CLI
   def main():
       service = AudioProcessingService(config)
       result = service.process_file(Path(args.input), Path(args.output))
       print(result)
   ```

---

#### **P14: Acoplamento Excessivo a Paths Absolutos**

**Localização:**
- `AgentF5TTSChunk.py` linha 180: `/home/tts-webui-proxmox-passthrough/...`
- `train_config.yaml` linha 18: `/home/tts-webui-proxmox-passthrough/...`

**Descrição:**
Paths absolutos hardcoded no código. Problemas:
- Não funciona em outro ambiente (Docker, outro usuário, CI/CD)
- Dificulta colaboração (cada dev precisa editar)

**Impacto:**
- **BAIXO-MÉDIO**: Código não portável
- Onboarding frustrante

**Severidade:** BAIXA

**Solução:**
1. Usar paths relativos a PROJECT_ROOT
2. Definir PROJECT_ROOT dinamicamente:
   ```python
   PROJECT_ROOT = Path(__file__).parent.parent.parent.resolve()
   ```
3. Configs em YAML devem usar paths relativos
4. Se path absoluto for necessário, usar env var

---

### 2.5 MLOps / Reprodutibilidade

#### **P15: Dependências Não Pinadas**

**Localização:**
- `requirements-f5tts.txt`: `f5-tts>=1.1.9` (usa >=, não ==)
- `train/requirements_train.txt`: `torch>=2.0.0`, `accelerate>=0.25.0`, etc.

**Descrição:**
Versões não pinadas causam problemas:
- Hoje funciona com torch 2.1, amanhã sai torch 2.5 com breaking change
- Impossível reproduzir ambiente exato
- CI/CD pode falhar aleatoriamente

**Impacto:**
- **MÉDIO**: Reprodutibilidade quebrada
- Bug "funciona na minha máquina"

**Severidade:** MÉDIA

**Solução:**
1. Gerar `requirements-lock.txt` com versões exatas:
   ```bash
   pip freeze > requirements-lock.txt
   ```
2. OU usar poetry/pipenv com lock file
3. Atualizar dependências de forma controlada (não automática)

---

#### **P16: Seed Não Propagado Consistentemente**

**Localização:**
- `train/.env`: `SEED=666`
- `env_loader.py` linha 105: retorna `'seed': 666`
- Mas: não há código que define `torch.manual_seed()`, `np.random.seed()`, `random.seed()`

**Descrição:**
Seed é lido do .env mas não aplicado globalmente.

Para reprodutibilidade, é preciso:
```python
torch.manual_seed(seed)
torch.cuda.manual_seed_all(seed)
np.random.seed(seed)
random.seed(seed)
torch.backends.cudnn.deterministic = True
```

Sem isso, cada run terá resultados diferentes.

**Impacto:**
- **MÉDIO**: Experimentos não reproduzíveis
- Dificulta comparação de checkpoints

**Severidade:** MÉDIA

**Solução:**
1. Criar `train/utils/reproducibility.py`:
   ```python
   def set_seed(seed: int, deterministic: bool = True):
       torch.manual_seed(seed)
       ...
   ```
2. Chamar no início de `run_training.py` e scripts de inferência
3. Documentar que determinism pode afetar performance (~10% mais lento)

---

#### **P17: Falta de Registro de Experimentos**

**Localização:**
- TensorBoard é usado (`train/runs/`), mas logs não são estruturados
- Nenhum registro de hiperparâmetros, versão do código, dataset usado

**Descrição:**
Para reproduzir experimento, é preciso saber:
- Hiperparâmetros exatos
- Versão do código (commit hash)
- Dataset usado (path, número de amostras, duração)
- Modelo base (checkpoint inicial)

Atualmente, essas informações estão espalhadas (logs, .env, YAML) e não são versionadas juntas.

**Impacto:**
- **MÉDIO**: Impossível reproduzir experimento depois
- "Por que esse checkpoint era bom?"

**Severidade:** MÉDIA

**Solução:**
1. Adicionar MLflow ou Weights & Biases
2. Logar no início do treino:
   ```python
   mlflow.log_params({
       'learning_rate': config['learning_rate'],
       'batch_size': config['batch_size'],
       'dataset_path': config['dataset_path'],
       'git_commit': subprocess.check_output(['git', 'rev-parse', 'HEAD']).decode().strip(),
       'seed': config['seed'],
   })
   ```
3. OU criar arquivo `train/output/{exp_name}/experiment.json` com essas infos

---

#### **P18: Checkpoints sem Metadata Completo**

**Localização:**
- `run_training.py` salva checkpoints via `finetune_cli`
- Formato é controlado pela lib F5-TTS

**Descrição:**
Checkpoints devem ter metadata:
- Versão do código
- Config completa
- Métricas finais (loss, epoch)
- Vocab usado (hash)
- Dataset usado

Sem isso, é difícil saber "com o que esse checkpoint foi treinado?".

**Impacto:**
- **BAIXO-MÉDIO**: Debugging difícil
- Checkpoints "órfãos" (sem saber origem)

**Severidade:** BAIXA

**Solução:**
1. Após salvar checkpoint, adicionar arquivo `model_last.metadata.json`:
   ```json
   {
     "timestamp": "2025-12-06T10:00:00Z",
     "git_commit": "abc123",
     "config": {...},
     "vocab_hash": "sha256:...",
     "dataset": {
       "path": "train/data/f5_dataset",
       "num_samples": 5000,
       "total_duration_hours": 10.5
     },
     "metrics": {
       "final_loss": 0.123,
       "final_epoch": 50
     }
   }
   ```
2. Validar ao carregar checkpoint

---

### 2.6 DX (Developer Experience) & Organização do Projeto

#### **P19: README Genérico, Documentação Fragmentada**

**Localização:**
- `README.md` (raiz): foca na API REST, não menciona treino
- `train/README.md`: completo mas separado
- `train/docs/`: alguns docs, mas não indexados

**Descrição:**
Novo dev clona repo e não sabe:
- Onde começar?
- Como treinar modelo?
- Onde está documentação de cada módulo?

**Impacto:**
- **BAIXO-MÉDIO**: Onboarding lento
- Perguntas repetidas

**Severidade:** BAIXA

**Solução:**
1. README.md raiz deve ter seção "Training" com link para train/README.md
2. Criar `train/docs/INDEX.md` listando todos os docs
3. README por pasta:
   - `train/scripts/README.md`: descreve cada script
   - `train/utils/README.md`: descreve utilitários
4. Adicionar diagrama de arquitetura (draw.io ou mermaid)

---

#### **P20: Nome de Arquivos Confuso**

**Localização:**
- `prepare_segments_optimized.py`: por que "optimized"? Otimizado em relação a quê?
- `_deprecated/`: scripts antigos misturados no repo
- `AgentF5TTSChunk.py`: nome não intuitivo (o que é "Agent"? O que é "Chunk"?)

**Descrição:**
Nomes não seguem convenção clara:
- Alguns com underscore (`prepare_segments_optimized.py`)
- Outros camelCase (`AgentF5TTSChunk.py`)
- Alguns com sufixos (`_optimized`, `_or_subtitles`)

**Impacto:**
- **BAIXO**: Confusão, mas funciona
- DX ruim

**Severidade:** BAIXA

**Solução:**
1. Convenção de nomes:
   - Scripts: `snake_case.py`
   - Classes: `CamelCase`
   - Funções: `snake_case`
2. Renomear:
   - `prepare_segments_optimized.py` → `prepare_segments.py` (se é o único, não precisa sufixo)
   - `AgentF5TTSChunk.py` → `f5tts_inference.py` ou `f5tts_cli.py`
3. Mover `_deprecated/` para fora do repo (ou deletar se não precisa)

---

#### **P21: Falta de Scripts de Setup Automatizado**

**Localização:**
- Não há `make setup` ou `scripts/setup.sh`
- README diz "pip install ...", mas não valida

**Descrição:**
Novo dev precisa:
1. Instalar Python 3.11
2. Criar venv
3. Instalar deps (requirements.txt + requirements-f5tts.txt + train/requirements_train.txt)
4. Baixar modelos
5. Criar diretórios

Sem script automatizado, cada dev faz de forma diferente → erros.

**Impacto:**
- **BAIXO-MÉDIO**: Onboarding lento
- Ambiente inconsistente

**Severidade:** BAIXA

**Solução:**
1. Criar `Makefile`:
   ```makefile
   setup:
       python3.11 -m venv .venv
       .venv/bin/pip install -r requirements.txt -r requirements-f5tts.txt -r train/requirements_train.txt
       .venv/bin/python -m train.scripts.download_models
       mkdir -p train/{data,output,runs,logs}
   
   validate:
       .venv/bin/python -m train.scripts.validate_setup
   ```
2. README: "Run `make setup` to get started"

---

## 3. Oportunidades de Melhoria

### 3.1 Experiência de Treino

#### **O1: Callbacks Personalizados para Treino**

**Descrição:**
F5-TTS usa callbacks (early stopping já existe). Adicionar:
- Callback para salvar best model (baseado em val loss, não apenas last)
- Callback para gerar samples de áudio a cada N epochs (já existe parcialmente)
- Callback para enviar notificação (email/Slack) quando treino terminar

**Benefício:**
- Menos babysitting
- Validação automática de qualidade

**Implementação:**
```python
class AudioSampleCallback:
    def on_epoch_end(self, epoch, model):
        if epoch % 5 == 0:
            generate_sample(model, text="Teste", output=f"sample_epoch{epoch}.wav")

class BestModelCallback:
    def on_validation_end(self, val_loss, model):
        if val_loss < self.best_loss:
            save_checkpoint(model, "model_best.pt")
            self.best_loss = val_loss
```

---

#### **O2: Métricas Além de Loss**

**Descrição:**
Atualmente, apenas loss é logado. Adicionar:
- MCD (Mel Cepstral Distortion): mede distorção em relação a ref
- Duração média dos samples gerados
- Taxa de NaN/Inf em gradientes

**Benefício:**
- Melhor visibilidade de qualidade
- Detectar overfitting cedo

**Implementação:**
- Usar bibliotecas: `pymcd`, `librosa`
- Logar no TensorBoard como scalar

---

#### **O3: CLI de Treino Mais Amigável**

**Descrição:**
Atualmente: `python -m train.run_training` (sem argumentos).

Config vem de .env e YAML. Usuário não consegue fazer quick test com params diferentes.

**Benefício:**
- Experimentação rápida
- Validação de argumentos

**Implementação:**
Usar `typer` ou `click`:
```python
@app.command()
def train(
    config: Path = typer.Option("train/config/train_config.yaml"),
    learning_rate: float = typer.Option(None),
    epochs: int = typer.Option(None),
):
    cfg = load_config(config)
    if learning_rate:
        cfg['learning_rate'] = learning_rate
    ...
```

---

### 3.2 Experiência de Inferência

#### **O4: API Unificada para Inferência**

**Descrição:**
Atualmente:
- API REST usa `f5tts_engine.py` (classe `F5TtsEngine`)
- Scripts usam `AgentF5TTS` (wrapper de `F5TTS` da lib)
- Código duplicado

**Benefício:**
- Mesma interface em todos os contextos
- Menos duplicação

**Implementação:**
```python
class F5TTSInference:
    def __init__(self, checkpoint_path, vocab_file, device):
        ...
    
    def generate(self, text: str, ref_audio: Path, ref_text: str = "") -> np.ndarray:
        ...

# Usado por API Engine
# Usado por CLI
# Usado por notebooks
```

---

#### **O5: CLI de Teste Rápido**

**Descrição:**
Para testar checkpoint rapidamente:
```bash
python -m train.infer \
    --checkpoint train/output/model_last.pt \
    --text "Olá, mundo!" \
    --ref-audio ref.wav \
    --output output.wav
```

**Benefício:**
- Validação rápida após treino
- Não precisa subir API

**Implementação:**
- Script `train/infer.py` (CLI)
- Usa API unificada (O4)

---

#### **O6: Service Layer para Cache de Modelo**

**Descrição:**
Atualmente, modelo é carregado toda vez.

Service layer pode:
- Cachear modelo em memória
- Lazy load (só carrega quando necessário)
- Unload após timeout

**Benefício:**
- Inferência mais rápida (não recarrega modelo)
- Economia de VRAM (unload quando não usado)

**Implementação:**
```python
class F5TTSService:
    _instance = None
    _model = None
    
    @classmethod
    def get_instance(cls):
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance
    
    def generate(self, ...):
        if self._model is None:
            self._model = load_model(...)
        return self._model.infer(...)
```

---

### 3.3 Organização do Código

#### **O7: Módulos Especializados**

**Descrição:**
Criar estrutura clara:
```
train/
  audio/          # Audio processing (VAD, segment, normalize)
  text/           # Text processing (normalize, QA)
  data/           # Dataset loading, Arrow format
  models/         # Model wrappers, checkpoint utils
  training/       # Training loop, callbacks
  inference/      # Inference API
  io/             # YouTube, files, storage
  utils/          # Generic utils (device, seed, logging)
  cli/            # CLI commands
```

**Benefício:**
- Código organizado
- Fácil encontrar o que precisa

---

#### **O8: Camada de Abstração para F5-TTS**

**Descrição:**
F5-TTS é lib externa. Criar abstração:
```python
class F5TTSWrapper:
    def train(self, dataset, config) -> Checkpoint:
        ...
    
    def infer(self, checkpoint, text, ref_audio) -> Audio:
        ...
```

**Benefício:**
- Se F5-TTS mudar API, só atualiza wrapper
- Facilita testes (mock do wrapper)

---

### 3.4 Documentação e Exemplos

#### **O9: README por Pasta**

**Descrição:**
Cada pasta importante deve ter README:
- `train/scripts/README.md`: lista scripts e uso
- `train/utils/README.md`: descreve utilitários
- `train/audio/README.md`: explica processamento de áudio

**Benefício:**
- Documentação local (perto do código)
- Fácil navegar

---

#### **O10: Scripts de Exemplo**

**Descrição:**
Criar pasta `train/examples/`:
- `example_01_quick_train.py`: treino mínimo
- `example_02_inference.py`: inferência simples
- `example_03_custom_dataset.py`: como criar dataset

**Benefício:**
- Onboarding rápido
- Mostra uso correto da API

---

#### **O11: Tutorial Passo-a-Passo**

**Descrição:**
Criar `train/docs/TUTORIAL.md`:
1. Setup do ambiente
2. Preparar dataset
3. Treinar modelo
4. Testar inferência
5. Deploy

**Benefício:**
- Guia completo para iniciantes
- Reduz perguntas

---

### 3.5 Testes Automatizados

#### **O12: Testes de Fumaça para Cada Script**

**Descrição:**
Criar `tests/train/` com testes:
- `test_prepare_segments.py`: testa segmentação com áudio fake
- `test_transcribe.py`: testa transcrição (mock Whisper)
- `test_build_metadata.py`: testa construção de metadata

**Benefício:**
- Detecta bugs cedo
- Confiança em refatorar

**Implementação:**
```python
def test_segment_audio():
    audio = np.random.randn(24000)  # 1 segundo
    segments = segment_audio(audio, params)
    assert len(segments) > 0
    assert all(len(s) > 0 for s in segments)
```

---

#### **O13: Fixtures para Datasets de Teste**

**Descrição:**
Criar mini dataset:
```
tests/fixtures/
  audio/
    sample_01.wav  # 5s
    sample_02.wav  # 10s
  metadata.csv
```

**Benefício:**
- Testes rápidos (não precisa dataset real)
- Reproduzível

---

#### **O14: Teste de Integração End-to-End**

**Descrição:**
Teste que executa pipeline completo:
1. Download fake audio
2. Segment
3. Transcribe
4. Build dataset
5. Train (1 epoch)
6. Infer

**Benefício:**
- Garante pipeline funciona
- Smoke test antes de deploy

---

### 3.6 MLOps e Reproducibilidade

#### **O15: Versionamento de Datasets (DVC)**

**Descrição:**
Usar DVC para versionar datasets:
```bash
dvc add train/data/f5_dataset
git add train/data/f5_dataset.dvc
```

**Benefício:**
- Dataset versionado junto com código
- Reproduzir experimentos antigos

---

#### **O16: Registro de Experimentos (MLflow)**

**Descrição:**
Integrar MLflow:
```python
with mlflow.start_run():
    mlflow.log_params(config)
    mlflow.log_metrics({"loss": loss})
    mlflow.log_artifact("model_last.pt")
```

**Benefício:**
- Comparar experimentos facilmente
- UI web para visualizar

---

#### **O17: Docker para Treino**

**Descrição:**
Criar `docker/train/Dockerfile`:
```dockerfile
FROM pytorch/pytorch:2.1.0-cuda11.8-cudnn8
COPY requirements.txt .
RUN pip install -r requirements.txt
...
```

**Benefício:**
- Ambiente reproduzível
- Fácil deploy em cloud

---

### 3.7 Qualidade de Código

#### **O18: Linting e Formatação**

**Descrição:**
Adicionar:
- `ruff` (linter rápido)
- `black` (formatter)
- `isort` (organiza imports)

**Benefício:**
- Código consistente
- Menos code review sobre estilo

**Implementação:**
```bash
pip install ruff black isort
ruff check train/
black train/
isort train/
```

---

#### **O19: Type Checking com mypy**

**Descrição:**
Adicionar mypy:
```bash
mypy train/ --strict
```

**Benefício:**
- Detecta erros de tipo
- Documentação viva (types)

---

#### **O20: Pre-commit Hooks**

**Descrição:**
Criar `.pre-commit-config.yaml`:
```yaml
repos:
  - repo: https://github.com/psf/black
    hooks:
      - id: black
  - repo: https://github.com/astral-sh/ruff-pre-commit
    hooks:
      - id: ruff
```

**Benefício:**
- Qualidade garantida antes de commit
- Menos erros no CI

---

### 3.8 Monitoramento e Debugging

#### **O21: Structured Logging com Loguru**

**Descrição:**
Substituir logging padrão por loguru:
```python
from loguru import logger

logger.add("train/logs/train.json", format="{time} {level} {message}", serialize=True)
logger.info("Training started", config=config)
```

**Benefício:**
- Logs estruturados (JSON)
- Fácil parsing/análise

---

#### **O22: Health Check Script**

**Descrição:**
Script que valida setup antes de treinar:
```python
python -m train.scripts.health_check

✅ CUDA disponível: Tesla V100
✅ Dataset encontrado: 5000 samples
✅ Vocab consistente: SHA256 match
✅ Disk space: 50GB disponível
⚠️  RAM: 8GB (recomendado: 16GB)
```

**Benefício:**
- Detecta problemas antes de treinar
- Evita falhas no meio do treino

---

#### **O23: Script de Benchmark**

**Descrição:**
Comparar checkpoints:
```python
python -m train.scripts.benchmark \
    --checkpoints model_epoch10.pt model_epoch50.pt \
    --test-set test_samples.txt

# Output:
| Checkpoint      | MCD  | RTF  | MOS (est) |
|-----------------|------|------|-----------|
| model_epoch10   | 5.2  | 1.5  | 3.8       |
| model_epoch50   | 4.1  | 1.4  | 4.2       |
```

**Benefício:**
- Comparação objetiva
- Decidir qual checkpoint usar

---

## 4. Recomendações Prioritárias

### 🔴 Prioridade CRÍTICA (Sprint 1-2)

1. **[P1] Unificar Configuração de Paths**
   - Resolver duplicação de paths em .env, YAML e código
   - Criar módulo `train.config.paths` (source of truth)
   - **Impacto:** Elimina risco de modelo usar dataset/vocab errado

2. **[P2] Garantir Consistência de Vocabulário**
   - Consolidar vocab.txt em um único lugar com hash
   - Validar que treino e inferência usam mesmo vocab
   - **Impacto:** Previne modelo mudo/grunhidos

3. **[P5] Validar vocab_file em Treino e Inferência**
   - Sempre especificar vocab_file explicitamente
   - Adicionar validação de hash no checkpoint
   - **Impacto:** Qualidade de áudio garantida

### ⚠️ Prioridade ALTA (Sprint 3-4)

4. **[P3] Corrigir Checkpoint Path para Fine-tuning**
   - f5tts_engine.py deve respeitar `F5TTS_CUSTOM_CHECKPOINT`
   - Criar função utilitária para resolver checkpoint path
   - **Impacto:** Fine-tuning usado em produção

5. **[P8] Refatorar Scripts Gigantes**
   - Quebrar em módulos menores (audio/, text/, io/)
   - Separar lógica de negócio de infra
   - **Impacto:** Código testável e manutenível

6. **[P15] Pinar Dependências**
   - Gerar requirements-lock.txt com versões exatas
   - **Impacto:** Reprodutibilidade garantida

### 📊 Prioridade MÉDIA (Sprint 5-6)

7. **[P4] Definir Hierarquia de Config Clara**
   - Documentar precedência: defaults → YAML → .env → CLI
   - Implementar com OmegaConf ou Hydra
   - **Impacto:** Menos confusão

8. **[P16] Aplicar Seed Globalmente**
   - Criar utils/reproducibility.py
   - Chamar no início de treino e inferência
   - **Impacto:** Experimentos reproduzíveis

9. **[O12-O14] Adicionar Testes Automatizados**
   - Testes de fumaça para cada script
   - Fixtures para datasets de teste
   - Teste end-to-end
   - **Impacto:** Confiança em refatorar

10. **[O1-O3] Melhorar Experiência de Treino**
    - Callbacks personalizados
    - Métricas além de loss
    - CLI mais amigável
    - **Impacto:** Produtividade

### 📝 Prioridade BAIXA (Backlog)

11. **[P19-P21] Melhorar DX**
    - README organizado
    - Scripts de setup
    - Convenção de nomes
    - **Impacto:** Onboarding

12. **[O15-O17] MLOps Avançado**
    - DVC para datasets
    - MLflow para experimentos
    - Docker para treino
    - **Impacto:** Profissionalização

13. **[O18-O20] Qualidade de Código**
    - Linting, formatação, type checking
    - Pre-commit hooks
    - **Impacto:** Consistência

---

## 5. Referências Utilizadas

### F5-TTS Oficial

- **PyPI:** https://pypi.org/project/f5-tts/
- **HuggingFace:** https://huggingface.co/firstpixel/F5-TTS-pt-br
- **GitHub:** https://github.com/SWivid/F5-TTS

### Boas Práticas

- **Clean Architecture:** Robert C. Martin
- **SOLID Principles:** Design patterns para OOP
- **MLOps Best Practices:** ML Code Smells (Google, 2020)
- **Python Type Hints:** PEP 484, mypy documentation
- **Config Management:** OmegaConf, Hydra docs

### Ferramentas Recomendadas

- **Linting:** ruff (https://github.com/astral-sh/ruff)
- **Formatting:** black (https://github.com/psf/black)
- **Type Checking:** mypy (https://mypy.readthedocs.io/)
- **Config:** OmegaConf (https://omegaconf.readthedocs.io/)
- **Logging:** loguru (https://loguru.readthedocs.io/)
- **Experiments:** MLflow (https://mlflow.org/)
- **Dataset Versioning:** DVC (https://dvc.org/)

---

**Fim do Relatório MORE.md**
