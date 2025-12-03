# 🚀 Atualizações do Training Pipeline - Dezembro 2024

## ✨ Novas Funcionalidades

### 🛑 Early Stopping Automático
O pipeline agora para automaticamente se o modelo não melhorar por 3 epochs consecutivas.

**Configuração** (`train/config/train_config.yaml`):
```yaml
training:
  early_stop_patience: 3      # Para após 3 epochs sem melhora
  early_stop_min_delta: 0.001 # Melhora mínima considerada (0.1%)
```

**Uso**:
```bash
# Com early stopping (recomendado)
python3 -m train.train_with_early_stopping

# Sem early stopping (treinamento completo)
python3 -m train.run_training
```

**Benefícios**:
- ⏱️ **Economiza tempo**: Para quando o modelo convergiu
- 💰 **Economiza recursos**: Não desperdiça GPU/eletricidade
- 📊 **Evita overfitting**: Para antes do modelo decorar o dataset

---

### 🔄 Retomada Automática de Treinamento

O pipeline detecta automaticamente checkpoints anteriores e continua de onde parou.

**Detecção automática**:
```bash
# Se existir checkpoint em train/output/ptbr_finetuned/, continua automaticamente
python3 -m train.run_training
```

**Forçar novo treinamento**:
```bash
# Ignorar checkpoints e começar do zero
python3 -m train.run_training --fresh-start
```

**Checkpoint manual**:
```bash
# Continuar de um checkpoint específico
python3 -m train.run_training --resume train/output/ptbr_finetuned/model_500.pt
```

**Como funciona**:
1. Verifica se existe `model_last.pt` no output dir
2. Se não, procura por `model_*.pt` (model_500.pt, model_1000.pt, etc)
3. Carrega o checkpoint mais recente automaticamente
4. Continua treinamento do ponto exato onde parou

---

### 📊 Relatório Completo de Métricas

Novo script de análise que mostra **métricas reais** do treinamento.

**Executar**:
```bash
python3 -m train.scripts.test_model
```

**Output exemplo**:
```
================================================================================
📊 RELATÓRIO COMPLETO DE MÉTRICAS - F5-TTS FINE-TUNING
================================================================================

📈 EVOLUÇÃO DO TREINAMENTO
--------------------------------------------------------------------------------
Epoch      Loss            Updates         Melhora        
--------------------------------------------------------------------------------
1          0.6760          75              -              
2          0.5860          150             +13.31%        
3          0.5450          225             +7.00%         
4          0.5000          300             +8.26%         
5          0.4750          375             +5.00%         
6          0.4520          450             +4.84%         
7          0.4450          525             +1.55%         
8          0.4420          600             +0.67%         
9          0.4380          675             +0.90%         
10         0.4350          750             +0.68%         
--------------------------------------------------------------------------------
📊 Loss inicial: 0.6760
📊 Loss final: 0.4350
📊 Redução total: 35.65%
📊 Total de updates: 750

💾 CHECKPOINTS SALVOS
--------------------------------------------------------------------------------
📁 model_500.pt
   Tamanho: 5124.8 MB
   Parâmetros: 366 tensores

📁 model_last.pt
   Tamanho: 5124.8 MB
   Parâmetros: 366 tensores

🔊 AMOSTRAS DE ÁUDIO GERADAS
--------------------------------------------------------------------------------
   update_500_gen.wav (392.1 KB)
   update_500_ref.wav (392.1 KB)

📊 LOGS DO TENSORBOARD
--------------------------------------------------------------------------------
   📂 runs/None
      9 arquivo(s) de eventos

💡 Para visualizar no TensorBoard:
   export PATH="$HOME/.local/bin:$PATH"
   tensorboard --logdir=runs
   Acesse: http://localhost:6006
```

**Informações incluídas**:
- ✅ Evolução do loss epoch por epoch
- ✅ Percentual de melhora entre epochs
- ✅ Checkpoints salvos (tamanho, parâmetros)
- ✅ Amostras de áudio geradas
- ✅ Localização dos logs do TensorBoard

---

### 📊 TensorBoard Funcionando

TensorBoard agora está **validado e funcionando**.

**Iniciar TensorBoard**:
```bash
# Adicionar ao PATH
export PATH="$HOME/.local/bin:$PATH"

# Iniciar servidor
tensorboard --logdir=runs

# Acessar no navegador
# http://localhost:6006
```

**Métricas visualizadas**:
- 📉 Training loss ao longo do tempo
- 📊 Learning rate schedule
- 🔊 Amostras de áudio (geradas vs referência)
- 📈 Gradientes e pesos do modelo

**Localização dos logs**:
- Diretório: `./runs/`
- Arquivos: `events.out.tfevents.*`

---

## 🎯 Workflow Recomendado

### 1️⃣ Primeiro Treinamento (do zero)
```bash
# Treinar com early stopping
python3 -m train.train_with_early_stopping
```

O treinamento:
- ✅ Carrega modelo pré-treinado pt-br (363/364 layers)
- ✅ Treina até 10 epochs OU até convergir
- ✅ Para automaticamente se não melhorar por 3 epochs
- ✅ Salva checkpoints a cada 100 updates
- ✅ Gera amostras de áudio a cada 500 updates

### 2️⃣ Continuar Treinamento
```bash
# Detecta automaticamente último checkpoint e continua
python3 -m train.run_training

# OU com early stopping
python3 -m train.train_with_early_stopping
```

### 3️⃣ Treinar Mais Epochs (se parou cedo)
```bash
# Aumentar epochs no config
vim train/config/train_config.yaml
# Alterar: epochs: 20

# Continuar treinamento
python3 -m train.run_training
```

### 4️⃣ Analisar Resultados
```bash
# Ver métricas completas
python3 -m train.scripts.test_model

# Visualizar no TensorBoard
export PATH="$HOME/.local/bin:$PATH"
tensorboard --logdir=runs
# Abrir http://localhost:6006
```

---

## ⚙️ Configuração

### Early Stopping

**Habilitar** (`train/config/train_config.yaml`):
```yaml
training:
  early_stop_patience: 3       # Parar após 3 epochs sem melhora
  early_stop_min_delta: 0.001  # Melhora mínima de 0.1%
```

**Desabilitar**:
```yaml
training:
  early_stop_patience: 0  # Desabilitado
```

### Checkpoints

**Frequência de salvamento**:
```yaml
checkpoints:
  save_per_updates: 500        # Checkpoint completo a cada 500 updates
  last_per_updates: 100        # Checkpoint "last" a cada 100 updates
  keep_last_n_checkpoints: 5   # Manter apenas 5 checkpoints
```

### TensorBoard

**Logging**:
```yaml
logging:
  logger: "tensorboard"  # ou "wandb" ou null
  log_samples: true      # Gerar amostras de áudio
```

---

## 📁 Estrutura de Outputs

```
train/output/ptbr_finetuned/
├── model_500.pt          # Checkpoint @ 500 updates
├── model_last.pt         # Último checkpoint (mais recente)
└── samples/
    ├── update_500_gen.wav  # Áudio gerado @ update 500
    └── update_500_ref.wav  # Áudio referência

runs/
└── None/
    └── events.out.tfevents.*  # Logs do TensorBoard

train/logs/
├── training.log               # Log completo
└── training_interactive.log   # Log interativo (últimas execuções)
```

---

## 🐛 Troubleshooting

### TensorBoard não inicia

**Problema**: `tensorboard: command not found`

**Solução**:
```bash
# Adicionar .local/bin ao PATH
export PATH="$HOME/.local/bin:$PATH"

# Testar
tensorboard --version
```

### Early Stopping muito agressivo

**Problema**: Para cedo demais

**Solução**: Aumentar patience
```yaml
training:
  early_stop_patience: 5  # Aumentar para 5 epochs
```

### Checkpoint não detectado

**Problema**: Não continua automaticamente

**Verificar**:
```bash
ls -lh train/output/ptbr_finetuned/
```

**Forçar manualmente**:
```bash
python3 -m train.run_training --resume train/output/ptbr_finetuned/model_last.pt
```

### Métricas não aparecem

**Problema**: `test_model.py` não mostra dados

**Verificar logs**:
```bash
# Log deve existir
ls -lh train/logs/training_interactive.log

# Ver conteúdo
tail -100 train/logs/training_interactive.log
```

---

## 📚 Documentação Adicional

- **README Principal**: `train/README.md` - Pipeline completo
- **Quick Start**: `train/QUICKSTART.md` - Comandos rápidos
- **Este arquivo**: `train/UPDATES.md` - Novas funcionalidades

---

## ✅ Checklist de Validação

Antes de treinar, verifique:

- [ ] TensorBoard instalado e funcionando
- [ ] Config atualizado (`train/config/train_config.yaml`)
- [ ] Dataset preparado (`train/data/f5_dataset/raw.arrow`)
- [ ] Modelo pré-treinado baixado (`models/f5tts/pt-br/`)
- [ ] Early stopping configurado (se desejado)

Após treinamento:

- [ ] Checkpoints salvos (`train/output/ptbr_finetuned/`)
- [ ] Métricas visualizadas (`python3 -m train.scripts.test_model`)
- [ ] TensorBoard conferido (http://localhost:6006)
- [ ] Amostras de áudio geradas (`train/output/ptbr_finetuned/samples/`)

---

**Data**: Dezembro 2024  
**Versão**: 2.0 - Early Stopping + Retomada Automática + Métricas Completas
