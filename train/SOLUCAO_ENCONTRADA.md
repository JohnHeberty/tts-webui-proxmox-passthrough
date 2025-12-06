# 🎯 PROBLEMA IDENTIFICADO - MODELO QUEBRADO PARA INFERÊNCIA

**Data**: 06/12/2024 13:00 PM  
**Status**: ⚠️ MODELO FINE-TUNED NÃO FUNCIONA PARA INFERÊNCIA

---

## 🔍 TESTES REALIZADOS

### ✅ Teste 1: Modelo Pre-trained Original
```bash
Checkpoint: train/pretrained/F5-TTS-pt-br/pt-br/model_200000.pt
Resultado: 19.9% similaridade ❌ FALHOU
```

### ✅ Teste 2: Conversão Áudio→MEL→Vocoder
```bash
Processo: audio → model.mel_spec() → vocoder.decode()
Transcrição: "Vamos! E essa coisa de viagem no tempo do Lock..."
Resultado: PERFEITO ✅
```

### ✅ Teste 3: model.sample() com Áudio Raw
```bash
Parâmetros: cond=audio, text=duplicated, duration=ref_len*2
Similaridade: 3.6% ❌ FALHOU
```

### ✅ Teste 4: model.sample() com MEL Direto
```bash
Parâmetros: cond=mel_spec, text=duplicated (sem pinyin)
Similaridade: 4.9% ❌ FALHOU
```

---

## 💥 CONCLUSÃO

**TODOS OS MODELOS FALHAM NA INFERÊNCIA:**
- ❌ Modelo fine-tuned (25400 steps)
- ❌ Modelo pre-trained original (200k steps)
- ❌ Com áudio raw ou MEL direto
- ❌ Com ou sem convert_char_to_pinyin()

**MAS:**
- ✅ Vocoder funciona perfeitamente
- ✅ Conversão áudio→MEL funciona
- ✅ Samples do trainer são PERFEITOS

---

## 🧩 DIFERENÇA CRÍTICA

### O que FUNCIONA (trainer.py):
```python
self.accelerator.unwrap_model(self.model).sample(
    cond=mel_spec[0][:ref_audio_len].unsqueeze(0),
    text=infer_text,
    ...
)
```

### O que FALHA (infer_process):
```python
model_obj.sample(
    cond=audio,  # ou mel_spec
    text=final_text_list,
    ...
)
```

**HIPÓTESE PRINCIPAL:**
O problema está no **Accelerator wrapping** ou na **forma como o modelo é carregado**.

---

## 📦 CHECKPOINT ANALYSIS

```
Checkpoint: model_25400.pt
- model_state_dict: 364 items
- ema_model_state_dict: 366 items (2 extras: "initted", "step")
- optimizer_state_dict: 2 items
- scheduler_state_dict: 4 items
```

**Modelo EMA carregado corretamente:**
```python
# load_checkpoint() com use_ema=True:
checkpoint["model_state_dict"] = {
    k.replace("ema_model.", ""): v
    for k, v in checkpoint["ema_model_state_dict"].items()
    if k not in ["initted", "step"]
}
model.load_state_dict(checkpoint["model_state_dict"])
```

---

## 🎯 PRÓXIMOS PASSOS RECOMENDADOS

### Opção A: Testar SEM Accelerator (Mais Provável)

Criar script que carrega modelo EXATAMENTE como trainer, mas SEM treinar:

```python
from accelerate import Accelerator
from f5_tts.model import DiT, CFM
import torch

# Setup accelerator
accelerator = Accelerator()

# Cria modelo
model = CFM(...)
checkpoint = torch.load('model_25400.pt')
model.load_state_dict(checkpoint['ema_model_state_dict'])

# Wrap com accelerator
model = accelerator.prepare(model)

# Gera como trainer faz
generated, _ = accelerator.unwrap_model(model).sample(...)
```

### Opção B: Verificar Vocab/Tokenizer

O trainer pode estar usando vocab diferente do infer_process:

```bash
# Verificar vocab usado no treinamento
cat train/data/f5_dataset/vocab.txt

# Comparar com vocab do infer
cat /root/.local/lib/python3.11/site-packages/f5_tts/infer/examples/vocab.txt
```

### Opção C: Testar Checkpoint Anterior

```bash
# Testar com checkpoint 25200
python3 train/test.py --checkpoint model_25200.pt
```

### Opção D: Reportar Bug na F5-TTS

Se nenhuma solução funcionar, é provável que seja um bug na biblioteca.

---

## 🚨 RESUMO EXECUTIVO

**O modelo fine-tuned NÃO funciona para inferência via `infer_process()`, e o modelo pre-trained TAMBÉM falha.**

Isso indica que:
1. ❌ NÃO é problema do fine-tuning
2. ❌ NÃO é problema do checkpoint
3. ❌ NÃO é problema do vocoder
4. ❌ NÃO é problema de texto/MEL

**Possível causa:**
- Diferença fundamental entre como trainer.py gera samples vs como infer_process gera
- Provável: **Accelerator wrapping** altera comportamento do modelo
- Alternativa: **Vocab/tokenizer diferente** entre train e infer

**Recomendação:**
1. Testar Opção A (Accelerator)
2. Se falhar, reportar bug na F5-TTS
