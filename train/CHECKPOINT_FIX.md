# 🔧 Correção: Checkpoint Corrompido no Treinamento

## ❌ Problema Identificado

```
RuntimeError: PytorchStreamReader failed reading zip archive: failed finding central directory
```

### Causa Raiz

1. **Checkpoint corrompido**: `pretrained_model_200000.pt` tinha apenas 1.7GB (vs 5.1GB esperado)
2. **Workers excessivos**: DataLoader criando 16 workers em sistema com 12 cores
3. **Falta de validação**: Script não verificava integridade antes de usar checkpoint

## ✅ Correções Implementadas

### 1. Validação Automática de Checkpoints

```python
def validate_checkpoint(self, checkpoint_path: str) -> bool:
    """Valida se checkpoint pode ser carregado"""
    try:
        checkpoint = torch.load(checkpoint_path, map_location='cpu')
        
        # Verificar tamanho (checkpoints válidos ~5GB)
        file_size_gb = Path(checkpoint_path).stat().st_size / (1024**3)
        if file_size_gb < 1.0:
            logger.error(f"❌ Checkpoint muito pequeno ({file_size_gb:.1f}GB)")
            return False
        
        return True
    except Exception as e:
        logger.error(f"❌ Checkpoint corrompido: {e}")
        return False
```

**Benefícios:**
- ✅ Detecta checkpoints corrompidos automaticamente
- ✅ Renomeia arquivos inválidos (.pt → .pt.corrupted)
- ✅ Busca próximo checkpoint válido disponível

### 2. Ajuste Automático de Workers

```python
import multiprocessing
cpu_count = multiprocessing.cpu_count()
max_workers = max(1, cpu_count - 4)  # Deixa 4 cores livres

if self.config['dataloader_workers'] > max_workers:
    logger.warning(f"⚠️  Ajustando workers: {config} → {max_workers}")
    self.config['dataloader_workers'] = max_workers
```

**Antes:**
```
UserWarning: This DataLoader will create 16 worker processes in total.
Our suggested max number of worker in current system is 12
```

**Depois:**
- Sistema com 12 cores → 8 workers (12 - 4)
- Sistema com 8 cores → 4 workers (8 - 4)
- Evita sobrecarga e freeze

### 3. Priorização de Checkpoints

**Nova ordem de busca:**

1. ✅ `train/output/ptbr_finetuned2/model_last.pt` (mais recente, validado)
2. ✅ `train/output/ptbr_finetuned2/model_*.pt` (numerados, validados)
3. ✅ `ckpts/ptbr_finetuned2/model_last.pt` (F5-TTS dir, validado)
4. ✅ `models/f5tts/pt-br/model_last.pt` (pré-treinado local, validado)

**Cada checkpoint é validado antes de ser usado!**

### 4. Recuperação de Checkpoint Válido

```bash
# Checkpoint corrompido renomeado
pretrained_model_200000.pt → pretrained_model_200000.pt.corrupted (1.7GB)

# Checkpoint válido copiado
cp train/output/ptbr_finetuned/model_last.pt \
   train/output/ptbr_finetuned2/model_last.pt (5.1GB ✓)
```

## 🎯 Como Usar

### Opção 1: Continuar do Checkpoint Válido

```bash
# O script agora detecta automaticamente
python3 -m train.run_training

# Saída esperada:
# ✅ Checkpoint válido encontrado: model_last.pt
# 🔄 Modo: Continuar treinamento do checkpoint
```

### Opção 2: Começar do Zero

```bash
# Remova checkpoints corrompidos primeiro
rm train/output/ptbr_finetuned2/*.pt.corrupted

# Execute
python3 -m train.run_training
```

### Opção 3: Ajustar Workers Manualmente

```bash
# Edite train/.env
DATALOADER_WORKERS=4  # Reduzir se necessário
```

## 📊 Validação de Checkpoints

```bash
# Validar checkpoint manualmente
python3 -c "
import torch
from pathlib import Path

ckpt_path = 'train/output/ptbr_finetuned2/model_last.pt'
ckpt = torch.load(ckpt_path, map_location='cpu', weights_only=False)

file_size_gb = Path(ckpt_path).stat().st_size / (1024**3)
print(f'✓ Checkpoint válido ({file_size_gb:.1f}GB)')
print(f'Keys: {list(ckpt.keys())}')
if 'update' in ckpt:
    print(f'Update: {ckpt[\"update\"]}')
"
```

**Saída esperada:**
```
✓ Checkpoint válido (5.1GB)
Keys: ['model_state_dict', 'optimizer_state_dict', 'ema_model_state_dict', 'scheduler_state_dict', 'update']
Update: 200000
```

## 🛡️ Prevenção de Problemas Futuros

### 1. Monitorar Espaço em Disco

```bash
# Checkpoints precisam ~5GB cada
df -h /home/tts-webui-proxmox-passthrough/train/output
```

### 2. Backup de Checkpoints Válidos

```bash
# Backup periódico
cp train/output/ptbr_finetuned2/model_last.pt \
   train/output/backups/model_$(date +%Y%m%d_%H%M%S).pt
```

### 3. Verificar Logs de Treinamento

```bash
# Logs em tempo real
tail -f train/logs/training.log

# Buscar erros
grep -i "error\|warning" train/logs/training.log
```

## 📚 Arquivos Modificados

1. **`train/run_training.py`**
   - ✅ Adicionado `validate_checkpoint()`
   - ✅ Ajuste automático de workers
   - ✅ Validação em todas as buscas de checkpoint

2. **`train/utils/env_loader.py`**
   - ✅ Adicionado `DATALOADER_WORKERS` config

3. **Checkpoints**
   - ✅ `pretrained_model_200000.pt.corrupted` (renomeado)
   - ✅ `model_last.pt` (copiado, válido)

## ✅ Status Atual

- ✅ Checkpoint corrompido detectado e renomeado
- ✅ Checkpoint válido (5.1GB) pronto para uso
- ✅ Workers ajustados automaticamente
- ✅ Validação implementada
- ✅ Pronto para retomar treinamento

## 🚀 Próximos Passos

```bash
# 1. Verificar configuração
cat train/.env | grep -E "DATALOADER_WORKERS|OUTPUT_DIR"

# 2. Executar treinamento
python3 -m train.run_training

# 3. Monitorar
watch -n 2 'ls -lh train/output/ptbr_finetuned2/ | grep model'
```

---

**Data da Correção:** 2025-12-05  
**Status:** ✅ Resolvido e testado
