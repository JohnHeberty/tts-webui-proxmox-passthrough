# SOLUÇÃO DEFINITIVA - F5-TTS AUDIO RUIM

**Data**: 06/12/2024 12:15 PM  
**Status**: 🔴 PROBLEMA CONFIRMADO - SOLUÇÃO EM ANDAMENTO

---

## ✅ CONFIRMAÇÃO DO PROBLEMA

### Validação com Whisper

**Sample de Treinamento (BOM)** ✅
```
Transcrição: "Vamos, e essa coisa de viagem no Tedloque. A primeira temporada 
de Loki pra mim, aquela última cena lá é tipo, sensação sabe?"

Palavras: 32
Inteligível: SIM ✅
```

**Test.py Standard (RUIM)** ❌
```
Transcrição: "Não é louquão de eu, do mantente de dar, está o joguoso loto 
usando o vio dos dolder, do dote, enquanto não, trusa..."

Palavras: 93
Inteligível: NÃO ❌
Classificação: GIBBERISH (sem sentido)
```

---

## 🔍 ROOT CAUSE REAL

### O Problema É o TEXTO DE GERAÇÃO

Analisando o código do trainer vs test.py:

#### Trainer (FUNCIONA):
```python
# trainer.py linha 406-407
ref_audio_len = mel_lengths[0]  # Ex: 938 frames (10s)
infer_text = [text_inputs[0] + " " + text_inputs[0]]  # DUPLICA texto do BATCH

# Importante: text_inputs[0] vem do DATASET DE TREINAMENTO
# É o TEXTO REAL correspondente ao áudio de referência!
```

#### Test.py (QUEBRADO):
```python
# test.py linha 178-186
ref_text = "Olá, este é um teste de síntese..."  # ❌ HARDCODED!
gen_text = """Bem-vindo ao teste de geração... [300 chars]"""  # ❌ TEXTO INVENTADO!

# Problema:
# 1. ref_text NÃO corresponde ao ref_audio
# 2. gen_text é texto LONGO e DIFERENTE
# 3. Modelo foi fine-tuned em português BR mas com OUTROS textos
```

---

## 💡 SOLUÇÃO

### Opção 1: Usar Texto do Dataset (RECOMENDADO)

```python
# test.py (CORRETO)
import random
from pathlib import Path

# Carregar lista de textos do dataset de treinamento
dataset_dir = Path("caminho/do/dataset")
metadata_file = dataset_dir / "metadata.list"

# Ler um exemplo do dataset
with open(metadata_file) as f:
    lines = f.readlines()
    sample = random.choice(lines)
    audio_file, text = sample.strip().split("|")

# Usar texto REAL do dataset
ref_audio_path = dataset_dir / audio_file
ref_text = text
gen_text = text  # Duplica (como trainer faz)

# Gerar
audio_output, sr, _ = infer_process(
    ref_audio=str(ref_audio_path),
    ref_text=ref_text,
    gen_text=gen_text,  # MESMO texto
    ...
)
```

### Opção 2: Texto Curto e Simples

```python
# Para testar rapidamente
ref_text = "Olá"  # MUITO CURTO
gen_text = "Olá"  # MESMO

# OU usar texto correspondente ao sample:
ref_text = "E essa coisa de viagem no tempo do Lock..."  # Do Whisper
gen_text = ref_text  # Duplica
```

### Opção 3: Fine-tuning com Prompt Engineering

```python
# Ajustar cfg_strength para controlar fidelidade
audio_output, sr, _ = infer_process(
    ref_audio=str(ref_audio_path),
    ref_text=ref_text,
    gen_text=gen_text,
    cfg_strength=3.0,  # ↑ Aumentar para mais fidelidade ao ref
    nfe_step=64,  # ↑ Mais steps = melhor qualidade
    ...
)
```

---

## 🧪 EXPERIMENTO PARA VALIDAR SOLUÇÃO

### Teste 1: Duplicar Texto do Sample

```bash
cd /home/tts-webui-proxmox-passthrough/train

python3 << 'EOF'
from f5_tts.infer.utils_infer import infer_process, load_model, load_vocoder
from f5_tts.model import DiT
import soundfile as sf

# Carrega modelo
model_cfg = dict(dim=1024, depth=22, heads=16, ff_mult=2, text_dim=512, conv_layers=4)
model = load_model(DiT, model_cfg, 'output/ptbr_finetuned2/model_25400.pt', 'vocos', '', 'euler', True, 'cuda')
vocoder = load_vocoder("vocos", False, "")

# Usa sample e seu TEXTO REAL
ref_audio = "output/ptbr_finetuned2/samples/update_25400_ref.wav"
ref_text = "E essa coisa de viagem no tempo do Lock, a primeira temporada de Lock, pra mim aquela última cena lá é tipo o sensacional, sabe? Mas eu desligo a chavinha, mas eu sinto que"

# DUPLICA (como trainer faz)
gen_text = ref_text

print(f"Gerando com texto CORRETO duplicado...")
audio, sr, _ = infer_process(
    ref_audio=ref_audio,
    ref_text=ref_text,
    gen_text=gen_text,
    model_obj=model,
    vocoder=vocoder,
    mel_spec_type="vocos",
    nfe_step=32,
    cfg_strength=2.0,
    sway_sampling_coef=-1.0,
    device="cuda"
)

sf.write("TEST_CORRETO_duplicado.wav", audio, sr)
print("✅ Salvo: TEST_CORRETO_duplicado.wav")
EOF
```

### Teste 2: Validar com Whisper

```bash
python3 validar_audio.py TEST_CORRETO_duplicado.wav

# Esperado:
# Transcrição: "E essa coisa de viagem..." (similar ao original)
# Inteligível: SIM ✅
```

---

## 📋 CHECKLIST DE CORREÇÃO

- [ ] 1. Encontrar dataset de treinamento
- [ ] 2. Carregar metadata com pares (audio, texto)
- [ ] 3. Modificar test.py para usar texto REAL
- [ ] 4. Testar com duplicação (ref_text = gen_text)
- [ ] 5. Validar com Whisper (>80% similaridade)
- [ ] 6. Se funcionar, expandir para novos textos curtos
- [ ] 7. Documentar processo de geração correto

---

## 🎯 PRÓXIMO COMANDO

```bash
# Encontrar dataset
find /home/tts-webui-proxmox-passthrough -name "metadata.list" -o -name "*.txt" | grep -i dataset

# Se encontrar, usar para pegar textos reais
# Se NÃO encontrar, usar transcrição Whisper do ref_audio
```

---

**Status**: Problema identificado! Próximo passo é usar textos reais do dataset.
