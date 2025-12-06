# 🔍 Análise: Checkpoints e Samples não sendo Gerados

**Data:** 2025-12-06  
**Problema:** Treinamento não está salvando checkpoints numerados nem gerando samples de áudio

---

## 📊 Estado Atual

### Checkpoints Encontrados
```
train/output/ptbr_finetuned2/
├── model_last.pt                (5.1GB - update 25100)
├── model_last.metadata.json
├── pretrained_model_200000.pt   (5.1GB - modelo base)
└── samples/                     (vazio!)
```

### Configuração Atual
```yaml
# train/config/base_config.yaml
checkpoints:
  save_per_updates: 500          # Salvar checkpoint numerado a cada 500 updates
  last_per_updates: 100          # Salvar model_last.pt a cada 100 updates
  keep_last_n_checkpoints: 3     # Manter últimos 3 checkpoints
  log_samples: true              # Gerar samples de áudio
  log_samples_per_updates: 500   # Gerar samples a cada 500 updates
```

---

## 🐛 Causa Raiz

### Fluxo de Salvamento da Lib F5-TTS

O código em `/root/.local/lib/python3.11/site-packages/f5_tts/model/trainer.py` funciona assim:

```python
# A cada last_per_updates (100 updates)
if global_update % self.last_per_updates == 0:
    self.save_checkpoint(global_update, last=True)  # Salva model_last.pt

# A cada save_per_updates (500 updates)  
if global_update % self.save_per_updates == 0:
    self.save_checkpoint(global_update)  # Salva model_{update}.pt
    
    # E gera samples
    if self.log_samples:
        # Gera audio inference
        torchaudio.save(f"{samples}/update_{global_update}_gen.wav", ...)
        torchaudio.save(f"{samples}/update_{global_update}_ref.wav", ...)
```

### Por que não funcionou?

#### 1. Update 25000 (do checkpoint pré-treinado)
- ✅ 25000 % 100 == 0 → Salvou `model_last.pt`
- ❌ 25000 % 500 == 0 → MAS era o checkpoint inicial, não gerou sample
- **Razão:** O update 25000 veio do modelo pré-treinado carregado, não de treinamento real

#### 2. Treinamento interrompido em 25188
- ✅ Salvou `model_last.pt` em 25100 (25100 % 100 == 0)
- ❌ Não chegou em 25500 para salvar checkpoint numerado
- ❌ Não gerou samples (só aconteceria em 25500)

---

## ✅ Soluções

### Opção 1: Reduzir `save_per_updates` (RECOMENDADO)

Mudar de 500 para 100 updates para alinhar com `last_per_updates`:

```yaml
# train/config/base_config.yaml
checkpoints:
  save_per_updates: 100          # ← Mudar de 500 para 100
  last_per_updates: 100
  log_samples_per_updates: 100   # ← Mudar de 500 para 100
```

**Vantagens:**
- ✅ Gera samples a cada 2-3 minutos (100 updates ≈ 3.5min com batch=2)
- ✅ Checkpoints mais frequentes (menos perda em caso de crash)
- ✅ Melhor monitoramento da qualidade de áudio

**Desvantagens:**
- ⚠️ Mais espaço em disco (mas `keep_last_n_checkpoints: 3` limita)
- ⚠️ Overhead de I/O (mas mínimo)

---

### Opção 2: Manter 500 updates mas ajustar `last_per_updates`

```yaml
checkpoints:
  save_per_updates: 500
  last_per_updates: 500          # ← Igualar com save_per_updates
  log_samples_per_updates: 500
```

**Vantagens:**
- ✅ Menos I/O (salva menos vezes)
- ✅ Menos espaço temporário usado

**Desvantagens:**
- ❌ Samples só a cada 17-18 minutos (500 updates ≈ 17.5min)
- ❌ Maior risco de perder progresso em crash

---

### Opção 3: Valores intermediários (BALANCED)

```yaml
checkpoints:
  save_per_updates: 200          # Checkpoint numerado a cada 200 updates
  last_per_updates: 50           # model_last.pt a cada 50 updates (backup)
  log_samples_per_updates: 200   # Samples a cada 200 updates
  keep_last_n_checkpoints: 5     # Manter 5 checkpoints (1000 updates = ~35min)
```

**Vantagens:**
- ✅ Balance entre frequência e performance
- ✅ Samples a cada 7 minutos (200 updates ≈ 7min)
- ✅ Backup frequente com `model_last.pt` (50 updates ≈ 1.7min)

**Timing estimado** (batch_size=2, grad_accum=8):
- 1 update ≈ 2.1 segundos
- 50 updates ≈ 1.7 minutos
- 100 updates ≈ 3.5 minutos
- 200 updates ≈ 7 minutos
- 500 updates ≈ 17.5 minutos

---

## 📈 Comportamento Esperado (após fix)

### Com Opção 1 (save_per_updates=100):

```
train/output/ptbr_finetuned2/
├── model_last.pt              (sempre o mais recente)
├── model_25100.pt            (checkpoint numerado)
├── model_25200.pt
├── model_25300.pt            (só mantém últimos 3)
└── samples/
    ├── update_25100_gen.wav  (gerado)
    ├── update_25100_ref.wav  (referência)
    ├── update_25200_gen.wav
    ├── update_25200_ref.wav
    ├── update_25300_gen.wav
    └── update_25300_ref.wav
```

### Com Opção 3 (save_per_updates=200):

```
train/output/ptbr_finetuned2/
├── model_last.pt              (atualizado a cada 50 updates)
├── model_25200.pt            (checkpoint numerado)
├── model_25400.pt
├── model_25600.pt
├── model_25800.pt
├── model_26000.pt            (só mantém últimos 5)
└── samples/
    ├── update_25200_gen.wav
    ├── update_25200_ref.wav
    ├── update_25400_gen.wav
    ├── update_25400_ref.wav
    └── ...
```

---

## 🎯 Recomendação Final

**Use Opção 3 (Balanced):**

```yaml
checkpoints:
  save_per_updates: 200
  last_per_updates: 50
  keep_last_n_checkpoints: 5
  log_samples: true
  log_samples_per_updates: 200
  log_samples_per_epochs: 1
```

**Justificativa:**
1. ✅ **Samples a cada 7min** - Rápido feedback de qualidade
2. ✅ **Backup a cada 1.7min** - Segurança contra crashes
3. ✅ **5 checkpoints = 1000 updates ≈ 35min** - Histórico razoável
4. ✅ **Uso de disco controlado** - ~25GB para 5 checkpoints
5. ✅ **Performance OK** - Overhead mínimo de I/O

---

## 🔧 Como Aplicar o Fix

### 1. Editar configuração

```bash
nano train/config/base_config.yaml
```

Alterar seção `checkpoints`:

```yaml
checkpoints:
  # Checkpoint paths
  checkpoint_base_dir: "train/output"
  checkpoint_dir: "ptbr_finetuned2"
  
  # Save frequency
  save_per_updates: 200          # ← MUDOU de 500
  last_per_updates: 50           # ← MUDOU de 100
  keep_last_n_checkpoints: 5     # ← MUDOU de 3
  
  # Samples
  log_samples: true
  log_samples_per_updates: 200   # ← MUDOU de 500
  log_samples_per_epochs: 1
```

### 2. Reiniciar treinamento

```bash
# Parar treinamento atual (se rodando)
pkill -f run_training.py

# Iniciar novo treinamento
cd /home/tts-webui-proxmox-passthrough
python3 -m train.run_training --epochs 1000 --batch-size 2
```

### 3. Monitorar samples

```bash
# Ver samples gerados
watch -n 10 'ls -lh train/output/ptbr_finetuned2/samples/'

# Ouvir último sample gerado
ls -t train/output/ptbr_finetuned2/samples/*_gen.wav | head -1 | xargs -I {} ffplay -nodisp -autoexit {}
```

---

## 📊 Uso de Disco Projetado

### Com save_per_updates=200, keep_last_n=5:

```
Checkpoints:
- model_last.pt:     5.1GB (sempre)
- model_{N}.pt × 5:  25.5GB (rotacionados)
- Samples (200):     ~2GB (200 epochs × ~10MB)
─────────────────────────────
Total:              ~32.6GB
```

**Espaço disponível:** 85.4GB  
**Margem de segurança:** 52.8GB (61% livre) ✅

---

## ✅ Checklist de Validação

Após aplicar o fix e reiniciar treinamento:

- [ ] `model_last.pt` atualiza a cada 50 updates (~1.7min)
- [ ] Checkpoint numerado salvo a cada 200 updates (~7min)
- [ ] Samples gerados em `samples/update_{N}_gen.wav` e `samples/update_{N}_ref.wav`
- [ ] Apenas 5 checkpoints numerados mantidos (rotação automática)
- [ ] Espaço em disco controlado (~30-35GB total)

---

**Próximos Passos:**
1. Aplicar Opção 3 (editar base_config.yaml)
2. Reiniciar treinamento
3. Validar após 200 updates (~7min) se samples foram gerados
4. Monitorar TensorBoard para ver progresso

---

**Referências:**
- F5-TTS Trainer: `/root/.local/lib/python3.11/site-packages/f5_tts/model/trainer.py`
- Config Schema: `train/config/schemas.py`
- Run Training: `train/run_training.py`
