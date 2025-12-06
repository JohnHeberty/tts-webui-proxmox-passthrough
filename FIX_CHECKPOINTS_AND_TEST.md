# 🔧 Correções Implementadas - Checkpoints e Test Script

**Data:** 2025-12-06  
**Status:** ✅ **RESOLVIDO**

---

## 📋 Problemas Corrigidos

### 1. ❌ Checkpoint `pretrained_model_last.pt` criado incorretamente

**Problema:**
Arquivo `pretrained_model_last.pt` sendo criado na pasta de output junto com `model_last.pt`.

**Causa:**
A biblioteca F5-TTS (`/root/.local/lib/python3.11/site-packages/f5_tts/train/finetune_cli.py` linha 147-150) automaticamente adiciona o prefixo `pretrained_` ao copiar checkpoints para fine-tuning:

```python
file_checkpoint = os.path.basename(ckpt_path)
if not file_checkpoint.startswith("pretrained_"):
    file_checkpoint = "pretrained_" + file_checkpoint  # ← Adiciona prefixo
file_checkpoint = os.path.join(checkpoint_path, file_checkpoint)
if not os.path.isfile(file_checkpoint):
    shutil.copy2(ckpt_path, file_checkpoint)
```

**Comportamento:**
Quando passamos `model_last.pt` para continuar o treinamento, a lib copia para `pretrained_model_last.pt`.

**Solução:**
Isso é **comportamento esperado** da lib F5-TTS original. Não é um bug, mas sim um "backup" que a biblioteca cria. 

**Ação:** Script de limpeza criado (`train/scripts/cleanup_checkpoints.sh`) para remover checkpoints duplicados.

---

### 2. ❌ Test script usando sample inexistente (hardcoded)

**Problema Original:**
```python
ref_audio_path = SAMPLES_DIR / "update_33200_ref.wav"  # ❌ Hardcoded e não existe
```

**Erro:**
```
❌ Áudio de referência não encontrado: .../samples/update_33200_ref.wav
```

**Causa:**
- Path hardcoded para `update_33200_ref.wav` 
- Samples reais são: `update_25200_ref.wav`, `update_25400_ref.wav`, etc.
- Update number muda a cada treinamento

**Solução Implementada:**

```python
# ✅ CORREÇÃO: Buscar sample mais recente automaticamente
samples_list = sorted(SAMPLES_DIR.glob("update_*_ref.wav"), reverse=True)

if not samples_list:
    print(f"❌ Nenhum sample de referência encontrado em: {SAMPLES_DIR}")
    print(f"\n💡 Dica: Execute o treinamento primeiro para gerar samples:")
    print(f"   python3 -m train.run_training --epochs 1000 --batch-size 2")
    return 1

ref_audio_path = samples_list[0]  # Mais recente
update_num = ref_audio_path.stem.split("_")[1]  # Extrair número do update

print(f"\n✅ Áudio de referência (update {update_num}): {ref_audio_path.name}")
```

**Benefícios:**
- ✅ Sempre usa o sample mais recente disponível
- ✅ Funciona independente do número de updates
- ✅ Mensagem de erro útil se não houver samples
- ✅ Exibe qual update está sendo usado

---

## 🎯 Estrutura de Arquivos Correta

### Checkpoints (train/output/ptbr_finetuned2/)

```
✅ CORRETOS (mantidos):
├── model_last.pt              # Checkpoint mais recente (sempre sobrescrito)
├── model_25200.pt            # Checkpoint do update 25200
├── model_25400.pt            # Checkpoint do update 25400
└── model_{N}.pt              # Checkpoints numerados (rotação de 5)

⚠️ DUPLICADOS (podem ser removidos):
├── pretrained_model_last.pt       # Cópia feita pela lib F5-TTS
└── pretrained_model_200000.pt     # Modelo inicial baixado
```

### Samples (train/output/ptbr_finetuned2/samples/)

```
✅ CORRETOS:
├── update_25200_gen.wav      # Áudio gerado pelo modelo (update 25200)
├── update_25200_ref.wav      # Áudio de referência (ground truth)
├── update_25400_gen.wav
├── update_25400_ref.wav
└── update_{N}_*.wav          # Samples de cada checkpoint
```

**Padrão de nomenclatura:**
- `update_{N}_gen.wav`: Áudio **gerado** pelo modelo
- `update_{N}_ref.wav`: Áudio de **referência** (do dataset)

---

## 🧹 Limpeza de Checkpoints Duplicados

### Script Automático

```bash
# Executar limpeza
./train/scripts/cleanup_checkpoints.sh
```

**O que faz:**
- Remove todos os `pretrained_model_*.pt`
- Remove metadatas correspondentes (`.metadata.json`)
- Exibe espaço liberado
- Mantém checkpoints importantes (`model_*.pt`)

### Limpeza Manual

```bash
cd train/output/ptbr_finetuned2

# Remover checkpoints com prefixo pretrained_
rm -f pretrained_model_*.pt
rm -f pretrained_model_*.metadata.json

# Verificar espaço liberado
du -sh .
```

**Espaço economizado:** ~5-10GB por checkpoint duplicado

---

## ✅ Validação das Correções

### Teste 1: Script de Geração de Áudio

```bash
# Testar com checkpoint específico
python3 -m train.test --checkpoint model_25400.pt
```

**Resultado:**
```
✅ Áudio de referência (update 25400): update_25400_ref.wav
📊 Sample rate: 24000 Hz | Duration: 9.99s

================================================================================
✅ ÁUDIO GERADO COM SUCESSO!
================================================================================
💾 Arquivo: train/f5tts_test_20251206_112056.wav
⏱️  Tempo de geração: 7.34s
📊 Duração do áudio: 31.52s
📊 RTF (Real-Time Factor): 0.23x (4.3x mais rápido que tempo real!)
```

### Teste 2: Checkpoint Auto-Resume

```bash
# Reiniciar treinamento - deve continuar do model_last.pt
python3 -m train.run_training --epochs 1000 --batch-size 2
```

**Resultado:**
```
✅ Using Last model
   Path: train/output/ptbr_finetuned2/model_last.pt
   
✅ Auto-resume from: model_last.pt
🔄 Modo: Continuar treinamento do checkpoint

Epoch 29/1000: ... [loss=0.868, update=25422]  ✅
```

---

## 📊 Comparação: Antes vs Depois

| Aspecto | ❌ Antes | ✅ Depois |
|---------|----------|-----------|
| **Test script** | Hardcoded `update_33200_ref.wav` | Auto-detecta sample mais recente |
| **Samples** | Erro se não existir | Mensagem útil + dica de comando |
| **Checkpoints** | `pretrained_model_last.pt` duplicado | Entendido como backup da lib |
| **Limpeza** | Manual | Script automatizado |
| **Mensagens de erro** | Genérica | Específica com update number |

---

## 🚀 Uso Atualizado

### Gerar Áudio com Checkpoint Específico

```bash
# Usar checkpoint específico
python3 -m train.test --checkpoint model_25400.pt

# Usar último checkpoint (padrão)
python3 -m train.test

# Custom text
python3 -m train.test --text "Olá, teste de voz em português brasileiro."

# CPU fallback
python3 -m train.test --device cpu
```

### Limpar Checkpoints Duplicados

```bash
# Script automático
./train/scripts/cleanup_checkpoints.sh

# OU manual
cd train/output/ptbr_finetuned2
rm -f pretrained_model_*.pt pretrained_model_*.metadata.json
```

### Monitorar Samples Gerados

```bash
# Ver samples disponíveis
ls -lht train/output/ptbr_finetuned2/samples/

# Ouvir último sample gerado
ls -t train/output/ptbr_finetuned2/samples/*_gen.wav | head -1 | \
  xargs -I {} ffplay -nodisp -autoexit {}

# Comparar com referência
LAST=$(ls -t train/output/ptbr_finetuned2/samples/*_gen.wav | head -1)
UPDATE=$(basename $LAST | cut -d_ -f2)
echo "Generated: $LAST"
echo "Reference: train/output/ptbr_finetuned2/samples/update_${UPDATE}_ref.wav"
```

---

## 📚 Arquivos Modificados

### 1. `train/test.py`

**Linhas 153-167:** Detecção automática de sample de referência

```python
# Antes
ref_audio_path = SAMPLES_DIR / "update_33200_ref.wav"
if not ref_audio_path.exists():
    print(f"❌ Áudio de referência não encontrado: {ref_audio_path}")
    return 1

# Depois
samples_list = sorted(SAMPLES_DIR.glob("update_*_ref.wav"), reverse=True)
if not samples_list:
    print(f"❌ Nenhum sample encontrado em: {SAMPLES_DIR}")
    print(f"\n💡 Execute treinamento primeiro: python3 -m train.run_training")
    return 1

ref_audio_path = samples_list[0]  # Mais recente
update_num = ref_audio_path.stem.split("_")[1]
print(f"\n✅ Áudio de referência (update {update_num}): {ref_audio_path.name}")
```

### 2. `train/scripts/cleanup_checkpoints.sh` (NOVO)

Script para remover checkpoints duplicados com prefixo `pretrained_`.

---

## 🔍 Entendendo o Prefixo `pretrained_`

### Por que existe?

A lib F5-TTS usa essa convenção para diferenciar:

- **`model_*.pt`**: Checkpoints gerados durante o treinamento atual
- **`pretrained_model_*.pt`**: Checkpoints usados como base (fine-tuning)

### Quando é criado?

Sempre que você inicia fine-tuning com `--pretrain path/to/checkpoint.pt`:

```bash
# Você passa: model_last.pt
python3 -m train.run_training --pretrain model_last.pt

# Lib cria cópia: pretrained_model_last.pt
# E treina a partir dela
```

### É necessário?

**Não para usuário final.** É um backup interno da biblioteca. Pode ser removido após treinamento começar.

### Impacto no disco

Cada checkpoint: **~5GB**
- `model_last.pt`: 5.1GB ✅ Necessário
- `pretrained_model_last.pt`: 5.1GB ⚠️ Duplicado (pode remover)
- `pretrained_model_200000.pt`: 5.1GB ⚠️ Modelo base (pode remover após treinar)

**Total recuperável:** ~10GB

---

## ✅ Status Final

- ✅ **Test script corrigido** - Auto-detecta samples mais recentes
- ✅ **Checkpoints duplicados** - Entendidos como backup da lib
- ✅ **Script de limpeza** - Automatiza remoção de duplicados
- ✅ **Mensagens úteis** - Erros explicam o que fazer
- ✅ **Validação completa** - Teste passou com sucesso

---

## 🎯 Próximos Passos

1. ✅ **Correções aplicadas** - Test script e limpeza funcionando
2. 🔄 **Continuar treinamento** - Sistema stable, pode treinar
3. 🎧 **Testar qualidade** - Comparar `_gen.wav` vs `_ref.wav`
4. 🧹 **Limpar disco** - Executar `cleanup_checkpoints.sh` periodicamente

---

**Documentação gerada automaticamente**  
**Data:** 2025-12-06 11:22
