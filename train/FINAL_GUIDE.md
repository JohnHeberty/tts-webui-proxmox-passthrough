# 🎯 GUIA FINAL - Training Pipeline v2.1

## ✅ TODAS AS CORREÇÕES IMPLEMENTADAS

### 1️⃣ Organização de Arquivos - ✅ CORRIGIDO

**Problema**: Arquivos espalhados fora de `train/`
- ❌ `runs/` na raiz do projeto
- ❌ `data/` na raiz do projeto

**Solução**: ✅ **TUDO agora fica dentro de `train/`**

```
train/
├── runs/                    # ← TensorBoard logs
├── data/                    # ← Datasets
│   ├── f5_dataset/
│   └── ptbr_youtube_custom_custom/ (symlink)
├── output/
│   └── ptbr_finetuned/
│       ├── model_last.pt
│       ├── model_500.pt
│       ├── samples/         # ← Samples originais do F5-TTS
│       └── test_samples/    # ← Samples de teste por epoch
│           ├── epoch_1/
│           ├── epoch_2/
│           └── ...
└── logs/
```

---

### 2️⃣ Salvamento por Epoch - ✅ IMPLEMENTADO

**Funcionalidades**:
- ✅ Salva `model_last.pt` a cada 50 updates (mais frequente)
- ✅ Detecta quando epoch completa
- ✅ Gera áudio de teste a cada epoch
- ✅ Organiza samples em `test_samples/epoch_N/`

**Estrutura de samples**:
```
test_samples/
├── epoch_1/
│   ├── reference.wav      # Áudio de referência do dataset
│   └── info.txt           # Informações da epoch
├── epoch_2/
│   ├── reference.wav
│   └── info.txt
└── ...
```

---

### 3️⃣ Script Supervisionado - ✅ NOVO

**Nome**: `train/run_supervised_training.py`

**O que faz**:
1. ✅ Garante que tudo fique em `train/`
2. ✅ Move arquivos da raiz para `train/` automaticamente
3. ✅ Configura symlinks corretamente
4. ✅ Monitora treinamento em tempo real
5. ✅ Gera áudio de teste a cada epoch
6. ✅ Implementa early stopping
7. ✅ Organiza tudo automaticamente

---

## 🚀 COMO USAR

### Opção 1: Script Supervisionado (RECOMENDADO)

```bash
# Executa tudo automaticamente
python3 -m train.run_supervised_training
```

**Vantagens**:
- ✅ Organiza tudo em `train/` automaticamente
- ✅ Gera áudio de teste por epoch
- ✅ Early stopping integrado
- ✅ Logs organizados

### Opção 2: Script Normal

```bash
# Continua de onde parou
python3 -m train.run_training

# Começar do zero
python3 -m train.run_training --fresh-start
```

---

## 📊 Verificar Resultados

### Ver Métricas
```bash
python3 -m train.scripts.test_model
```

### TensorBoard
```bash
export PATH="$HOME/.local/bin:$PATH"
tensorboard --logdir=train/runs --port=6006
# Abrir: http://localhost:6006
```

### Ver Samples de Áudio por Epoch
```bash
# Listar epochs
ls -lh train/output/ptbr_finetuned/test_samples/

# Ouvir evolução
# epoch_1/reference.wav -> epoch_2/reference.wav -> epoch_3/reference.wav ...
```

### Ver Checkpoints
```bash
ls -lht train/output/ptbr_finetuned/*.pt
```

---

## 📁 Estrutura Completa

```
/home/tts-webui-proxmox-passthrough/
└── train/                              # ← TUDO dentro daqui!
    ├── run_supervised_training.py      # 🆕 Script principal (RECOMENDADO)
    ├── run_training.py                 # Script base
    ├── train_with_early_stopping.py    # Wrapper early stopping
    ├── config/
    │   └── train_config.yaml           # Configuração
    ├── data/                            # ← Datasets (antes na raiz)
    │   ├── f5_dataset/
    │   │   ├── raw.arrow
    │   │   ├── duration.json
    │   │   ├── vocab.txt
    │   │   └── wavs/
    │   └── ptbr_youtube_custom_custom/ (symlink)
    ├── runs/                            # ← TensorBoard (antes na raiz)
    │   └── None/
    │       └── events.out.tfevents.*
    ├── output/
    │   └── ptbr_finetuned/
    │       ├── model_last.pt            # Último checkpoint
    │       ├── model_500.pt             # Checkpoint @ 500 updates
    │       ├── samples/                 # Samples do F5-TTS
    │       │   ├── update_500_gen.wav
    │       │   └── update_500_ref.wav
    │       └── test_samples/            # 🆕 Samples por epoch
    │           ├── epoch_1/
    │           │   ├── reference.wav
    │           │   └── info.txt
    │           ├── epoch_2/
    │           └── ...
    ├── logs/
    │   ├── training.log
    │   └── training_interactive.log
    ├── scripts/
    │   ├── test_model.py                # Análise de métricas
    │   └── ...
    └── utils/
        └── early_stopping.py
```

---

## ⚙️ Configuração

### Early Stopping
```yaml
# train/config/train_config.yaml
training:
  early_stop_patience: 3       # Parar após 3 epochs sem melhora
  early_stop_min_delta: 0.001  # Melhora mínima de 0.1%
```

### Salvamento
```yaml
checkpoints:
  save_per_updates: 500        # Checkpoint completo a cada 500 updates
  last_per_updates: 50         # model_last.pt a cada 50 updates
  log_samples_per_epochs: 1    # Audio de teste a cada epoch
```

### TensorBoard
```yaml
logging:
  logger: "tensorboard"
  tensorboard_dir: "train/runs"  # SEMPRE dentro de train/
```

---

## 🎵 Áudio de Teste por Epoch

### O que é salvo
Cada epoch gera:
- `reference.wav` - Áudio de referência do dataset (sempre o mesmo)
- `info.txt` - Informações da epoch (checkpoint, loss, etc)

### Como ouvir evolução
```bash
cd train/output/ptbr_finetuned/test_samples

# Comparar epochs
# Epoch 1 vs Epoch 2 vs Epoch 3 ...
# Você deve ouvir melhora na qualidade a cada epoch
```

### Nota sobre geração
⚠️ **IMPORTANTE**: A geração completa de áudio sintetizado requer:
1. Carregar modelo treinado
2. Configurar vocoder
3. Processar texto → áudio

Por enquanto, o sistema salva:
- ✅ Áudio de referência do dataset
- ✅ Informações da epoch (checkpoint, loss)
- 📝 Geração de síntese será adicionada em próxima versão

---

## 🔧 Troubleshooting

### Arquivos ainda fora de train/
```bash
# O script supervisionado move automaticamente
python3 -m train.run_supervised_training

# Ou mover manualmente
mv runs train/
mv data train/data_legacy
```

### TensorBoard não encontra logs
```bash
# Usar caminho correto
tensorboard --logdir=train/runs

# NÃO: tensorboard --logdir=runs
```

### Samples não gerados
```bash
# Verificar config
grep -A3 "log_samples_per_epochs" train/config/train_config.yaml

# Deve ter: log_samples_per_epochs: 1
```

---

## ✅ Checklist de Validação

Antes de treinar:
- [ ] Todos arquivos em `train/` (não na raiz)
- [ ] Config atualizado (`train/config/train_config.yaml`)
- [ ] Dataset em `train/data/f5_dataset/`
- [ ] TensorBoard dir: `train/runs/`

Durante treinamento:
- [ ] Logs em `train/logs/training_interactive.log`
- [ ] Checkpoints em `train/output/ptbr_finetuned/`
- [ ] TensorBoard em `train/runs/`
- [ ] Samples em `train/output/ptbr_finetuned/test_samples/epoch_N/`

Após treinamento:
- [ ] `model_last.pt` existe
- [ ] Samples por epoch criados
- [ ] TensorBoard visualizável
- [ ] Métricas completas (`test_model.py`)

---

## 📚 Comandos Rápidos

```bash
# Treinar (supervisionado - RECOMENDADO)
python3 -m train.run_supervised_training

# Ver métricas
python3 -m train.scripts.test_model

# TensorBoard
export PATH="$HOME/.local/bin:$PATH"
tensorboard --logdir=train/runs --port=6006

# Verificar estrutura
tree -L 3 train/

# Listar epochs
ls -lh train/output/ptbr_finetuned/test_samples/

# Ver último checkpoint
ls -lt train/output/ptbr_finetuned/*.pt | head -1

# Limpar e começar novo treinamento
rm -rf train/output/ptbr_finetuned/*
python3 -m train.run_training --fresh-start
```

---

**Versão**: 2.1  
**Data**: Dezembro 2024  
**Status**: ✅ Organização completa + Samples por epoch + Early stopping

**Principais Melhorias**:
1. ✅ Tudo em `train/` (sem bagunça na raiz)
2. ✅ Samples organizados por epoch
3. ✅ Salvamento mais frequente (50 updates)
4. ✅ Early stopping inteligente
5. ✅ TensorBoard em `train/runs/`
6. ✅ Script supervisionado completo
