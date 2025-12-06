# ✅ PROBLEMA RESOLVIDO: Checkpoints e Samples

**Data:** 2025-12-06  
**Status:** ✅ **CONFIGURAÇÃO ATUALIZADA**

---

## 📋 Resumo do Problema

**Sintoma:** Treinamento não estava salvando checkpoints numerados (`model_25000.pt`, etc.) nem gerando samples de áudio na pasta `samples/`.

**Causa:** Configuração com `save_per_updates: 500` (17.5min) era muito espaçada. O treinamento foi interrompido em update 25188, antes de chegar em 25500 onde geraria o primeiro checkpoint numerado e samples.

---

## ✅ Solução Aplicada

### Mudanças no `train/config/base_config.yaml`:

```diff
checkpoints:
- save_per_updates: 500          # A cada 17.5 minutos
+ save_per_updates: 200          # A cada 7 minutos ✅
  
- last_per_updates: 100          # Backup a cada 3.5min
+ last_per_updates: 50           # Backup a cada 1.7min ✅
  
- keep_last_n_checkpoints: 3     # Manter 3 checkpoints
+ keep_last_n_checkpoints: 5     # Manter 5 checkpoints ✅
  
- log_samples_per_updates: 500   # Samples a cada 17.5min
+ log_samples_per_updates: 200   # Samples a cada 7min ✅
```

---

## 🎯 Comportamento Esperado (Nova Config)

### Timeline de Salvamento:

```
Update 25000 ─────────────────────────────────────────────────
  ├─ 25050: Salva model_last.pt (backup rápido)
  ├─ 25100: Salva model_last.pt
  ├─ 25150: Salva model_last.pt
  ├─ 25200: ✨ SALVA model_25200.pt + GERA SAMPLES ✨
  │         ├─ update_25200_gen.wav (áudio gerado)
  │         └─ update_25200_ref.wav (áudio referência)
  ├─ 25250: Salva model_last.pt
  ├─ 25300: Salva model_last.pt
  ├─ 25350: Salva model_last.pt
  ├─ 25400: ✨ SALVA model_25400.pt + GERA SAMPLES ✨
  └─ ...
```

### Estrutura de Arquivos Esperada:

```
train/output/ptbr_finetuned2/
├── model_last.pt              # Sempre o mais recente (atualizado a cada 50 updates)
├── model_25200.pt            # Checkpoint numerado #1
├── model_25400.pt            # Checkpoint numerado #2
├── model_25600.pt            # Checkpoint numerado #3
├── model_25800.pt            # Checkpoint numerado #4
├── model_26000.pt            # Checkpoint numerado #5 (mantém só últimos 5)
├── model_last.metadata.json
└── samples/
    ├── update_25200_gen.wav  # Áudio gerado pelo modelo
    ├── update_25200_ref.wav  # Áudio de referência (ground truth)
    ├── update_25400_gen.wav
    ├── update_25400_ref.wav
    ├── update_25600_gen.wav
    ├── update_25600_ref.wav
    └── ... (todos os samples, não são rotacionados)
```

---

## 🚀 Como Reiniciar o Treinamento

### 1. Parar treinamento atual (se rodando)

```bash
pkill -f run_training.py
```

### 2. Limpar pasta samples (opcional)

```bash
rm -rf train/output/ptbr_finetuned2/samples/*
```

### 3. Iniciar novo treinamento

```bash
cd /home/tts-webui-proxmox-passthrough
python3 -m train.run_training --epochs 1000 --batch-size 2
```

**Ou em background:**

```bash
nohup python3 -m train.run_training --epochs 1000 --batch-size 2 > /tmp/train_realtime.log 2>&1 &
echo $! > /tmp/train.pid
```

### 4. Monitorar samples (nova ferramenta!)

```bash
# Monitor automático (atualiza a cada 30s)
./train/scripts/monitor_samples.sh

# OU: Ver manualmente
watch -n 10 'ls -lht train/output/ptbr_finetuned2/samples/ | head -15'
```

---

## ⏱️ Timing Esperado

Com `batch_size=2` e `grad_accumulation_steps=8`:

| Evento | Updates | Tempo | O que acontece |
|--------|---------|-------|----------------|
| Backup rápido | 50 | ~1.7min | Salva `model_last.pt` |
| Checkpoint + Samples | 200 | ~7min | Salva `model_{N}.pt` + gera 2 áudios |
| Rotação de checkpoints | 1000 | ~35min | Remove checkpoint mais antigo |
| 1 época completa | ~893 | ~31min | Com 14,284 samples |

**Primeiro sample esperado:** ~7 minutos após início do treino (update ~25200)

---

## 📊 Uso de Disco

### Estimativa com nova config:

```
Checkpoints:
├── model_last.pt:           5.1 GB  (sempre)
├── model_{N}.pt × 5:       25.5 GB  (últimos 5, rotacionados)
└── samples/ (200 epochs):   ~2.0 GB  (200 × 10MB, não rotacionados)
────────────────────────────────────
Total estimado:             ~32.6 GB
```

**Espaço disponível:** 85.4 GB  
**Uso após 1 época:** ~32.6 GB  
**Margem:** 52.8 GB (62% livre) ✅

---

## ✅ Checklist de Validação

Após reiniciar o treinamento, verificar:

- [ ] **~1.7min**: `model_last.pt` atualizado (check via `ls -lh`)
- [ ] **~7min**: Primeiro checkpoint `model_25200.pt` criado
- [ ] **~7min**: Samples gerados em `samples/update_25200_*.wav`
- [ ] **~14min**: Segundo checkpoint `model_25400.pt` criado
- [ ] **~35min**: Apenas 5 checkpoints mantidos (rotação funcionando)

### Comandos de Validação:

```bash
# Ver último checkpoint salvo
ls -lht train/output/ptbr_finetuned2/model_*.pt | head -5

# Contar checkpoints numerados (esperado: max 5)
ls -1 train/output/ptbr_finetuned2/model_[0-9]*.pt | wc -l

# Contar samples (esperado: 2 por checkpoint)
ls -1 train/output/ptbr_finetuned2/samples/*.wav | wc -l

# Ouvir último sample gerado
ls -t train/output/ptbr_finetuned2/samples/*_gen.wav | head -1 | \
  xargs -I {} ffplay -nodisp -autoexit {}
```

---

## 🎧 Comparação de Qualidade

Os samples salvam **2 arquivos por update**:

1. **`update_{N}_gen.wav`**: Áudio gerado pelo modelo (sua síntese)
2. **`update_{N}_ref.wav`**: Áudio de referência (ground truth do dataset)

**Como comparar:**

```bash
# Ouvir gerado
ffplay train/output/ptbr_finetuned2/samples/update_25200_gen.wav

# Ouvir referência
ffplay train/output/ptbr_finetuned2/samples/update_25200_ref.wav
```

**Esperado:**
- Início: `gen` bem diferente de `ref` (modelo ainda aprendendo)
- Progresso: `gen` cada vez mais parecido com `ref`
- Convergência: `gen` praticamente igual a `ref` (overfitting se dataset pequeno)

---

## 🔧 Troubleshooting

### Samples não aparecem após 10 minutos

```bash
# Ver log do treinamento
tail -100 /tmp/train_realtime.log | grep -E "Saved|update_"

# Verificar processo rodando
ps aux | grep run_training
```

### Checkpoints numerados não aparecem

```bash
# Ver config carregado
grep -A5 "save_per_updates" train/config/base_config.yaml

# Ver argumentos passados para F5-TTS
tail -50 /tmp/train_realtime.log | grep "save_per_updates"
```

### Disco cheio

```bash
# Ver uso de disco
du -sh train/output/ptbr_finetuned2/*

# Limpar samples antigos (manter últimos 50)
cd train/output/ptbr_finetuned2/samples
ls -t *.wav | tail -n +101 | xargs rm -f
```

---

## 📚 Referências

- **Análise completa:** `TRAINING_CHECKPOINT_ANALYSIS.md`
- **Config atualizado:** `train/config/base_config.yaml`
- **Monitor de samples:** `train/scripts/monitor_samples.sh`

---

## 🎉 Próximos Passos

1. ✅ **Configuração atualizada** - `save_per_updates: 200`
2. 🔄 **Reiniciar treinamento** - `python3 -m train.run_training`
3. ⏳ **Aguardar ~7min** - Primeiro checkpoint + samples
4. 🎧 **Validar qualidade** - Ouvir `update_{N}_gen.wav` vs `update_{N}_ref.wav`
5. 📊 **Monitorar TensorBoard** - http://localhost:6006

**Tempo até primeira validação de qualidade:** ~7 minutos ⏱️

---

**Status:** ✅ Pronto para reiniciar treinamento com nova configuração!
