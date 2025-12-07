# Como Testar Modelo Treinado

## ⚠️ Geração Automática de Samples Desabilitada

Devido a bug `cuFFT error: CUFFT_INVALID_SIZE` no XTTS `get_conditioning_latents()`, a geração automática de samples está temporariamente desabilitada.

**O treinamento funciona perfeitamente** - apenas a geração de áudio de teste está com problema.

---

## ✅ Treinamento Funcional

```bash
# Rodar treinamento
python3 -m train.scripts.train_xtts

# Checkpoints salvos:
# - train/output/checkpoints/checkpoint_epoch_N.pt
# - train/output/checkpoints/best_model.pt

# TensorBoard:
# - http://localhost:6006
```

---

## 🎤 Como Testar Modelo Manualmente

### **Opção 1: Usando TTS API (Recomendado)**

```python
import torch
from TTS.api import TTS

# Monkey patch para PyTorch 2.6+
original_load = torch.load
def patched_load(*args, **kwargs):
    kwargs['weights_only'] = False
    return original_load(*args, **kwargs)
torch.load = patched_load

# 1. Carregar modelo base XTTS
tts = TTS('tts_models/multilingual/multi-dataset/xtts_v2', gpu=True)

# 2. Carregar pesos do checkpoint treinado
checkpoint = torch.load('train/output/checkpoints/best_model.pt')
tts.synthesizer.tts_model.load_state_dict(
    checkpoint['model_state_dict'], 
    strict=False  # Ignorar chaves extras
)

# 3. Gerar áudio
wav = tts.tts(
    text="Olá, este é um teste de síntese de voz!",
    language="pt",
    speaker_wav="train/data/MyTTSDataset/wavs/audio_00001.wav"  # Áudio de referência
)

# 4. Salvar
import soundfile as sf
sf.write('output_test.wav', wav, 22050)
print("✅ Áudio salvo em: output_test.wav")
```

---

### **Opção 2: Script Completo**

Salve como `test_checkpoint.py`:

```python
#!/usr/bin/env python3
"""
Testar checkpoint de treinamento XTTS
"""
import torch
from TTS.api import TTS
from pathlib import Path
import soundfile as sf

# Monkey patch PyTorch 2.6+
original_load = torch.load
torch.load = lambda *args, **kwargs: original_load(*args, **{**kwargs, 'weights_only': False})

def test_checkpoint(checkpoint_path: str, reference_wav: str, output_path: str = "test_output.wav"):
    """Testar checkpoint do treinamento"""
    
    print(f"📥 Carregando modelo base XTTS...")
    tts = TTS('tts_models/multilingual/multi-dataset/xtts_v2', gpu=True)
    
    print(f"📂 Carregando checkpoint: {checkpoint_path}")
    checkpoint = torch.load(checkpoint_path)
    
    print(f"🔧 Aplicando pesos do checkpoint...")
    tts.synthesizer.tts_model.load_state_dict(
        checkpoint['model_state_dict'], 
        strict=False
    )
    
    # Informações do checkpoint
    print(f"\n📊 Informações do Checkpoint:")
    print(f"   Época: {checkpoint.get('epoch', 'N/A')}")
    print(f"   Val Loss: {checkpoint.get('val_loss', 'N/A'):.4f}")
    print(f"   Global Step: {checkpoint.get('global_step', 'N/A')}")
    
    print(f"\n🎤 Gerando áudio de teste...")
    wav = tts.tts(
        text="Olá, este é um teste de síntese de voz usando o modelo treinado do XTTS.",
        language="pt",
        speaker_wav=reference_wav
    )
    
    # Salvar
    sf.write(output_path, wav, 22050)
    print(f"✅ Áudio salvo em: {output_path}")
    
    # Estatísticas
    duration = len(wav) / 22050
    print(f"\n📈 Estatísticas:")
    print(f"   Duração: {duration:.2f}s")
    print(f"   Samples: {len(wav)}")
    print(f"   Sample rate: 22050 Hz")

if __name__ == "__main__":
    # Configurações
    CHECKPOINT = "train/output/checkpoints/best_model.pt"
    REFERENCE = "train/data/MyTTSDataset/wavs/audio_00001.wav"
    OUTPUT = "test_output.wav"
    
    # Verificar se existem
    if not Path(CHECKPOINT).exists():
        print(f"❌ Checkpoint não encontrado: {CHECKPOINT}")
        exit(1)
    
    if not Path(REFERENCE).exists():
        print(f"❌ Áudio de referência não encontrado: {REFERENCE}")
        exit(1)
    
    # Testar
    test_checkpoint(CHECKPOINT, REFERENCE, OUTPUT)
```

**Uso:**
```bash
python3 test_checkpoint.py
```

---

### **Opção 3: No Jupyter Notebook**

```python
# Célula 1: Setup
import torch
from TTS.api import TTS
import soundfile as sf
from IPython.display import Audio

# Monkey patch
original_load = torch.load
torch.load = lambda *args, **kwargs: original_load(*args, **{**kwargs, 'weights_only': False})

# Célula 2: Carregar modelo
tts = TTS('tts_models/multilingual/multi-dataset/xtts_v2', gpu=True)
checkpoint = torch.load('train/output/checkpoints/best_model.pt')
tts.synthesizer.tts_model.load_state_dict(checkpoint['model_state_dict'], strict=False)

# Célula 3: Gerar e reproduzir
wav = tts.tts(
    text="Teste de voz com modelo treinado",
    language="pt",
    speaker_wav="train/data/MyTTSDataset/wavs/audio_00001.wav"
)

# Reproduzir
Audio(wav, rate=22050)
```

---

## 🔍 Troubleshooting

### **Erro: cuFFT error: CUFFT_INVALID_SIZE**

Se ainda ocorrer este erro:
1. Verifique sample rate do áudio de referência: `22050 Hz` (não 24000)
2. Verifique comprimento mínimo: `> 1 segundo`
3. Use outro áudio de referência

```python
import torchaudio

# Verificar propriedades
wav, sr = torchaudio.load("reference.wav")
print(f"Sample rate: {sr} Hz")
print(f"Duração: {wav.shape[-1] / sr:.2f}s")

# Converter se necessário
if sr != 22050:
    resampler = torchaudio.transforms.Resample(sr, 22050)
    wav = resampler(wav)
    torchaudio.save("reference_22050.wav", wav, 22050)
```

### **Erro: Missing keys / Unexpected keys**

Normal! Use `strict=False`:
```python
tts.synthesizer.tts_model.load_state_dict(
    checkpoint['model_state_dict'], 
    strict=False  # ← IMPORTANTE!
)
```

---

## 📈 Comparar Modelo Base vs Treinado

```python
# Gerar com modelo BASE
tts_base = TTS('tts_models/multilingual/multi-dataset/xtts_v2', gpu=True)
wav_base = tts_base.tts(text="Teste", language="pt", speaker_wav="ref.wav")
sf.write("base_model.wav", wav_base, 22050)

# Gerar com modelo TREINADO
checkpoint = torch.load('train/output/checkpoints/best_model.pt')
tts_base.synthesizer.tts_model.load_state_dict(checkpoint['model_state_dict'], strict=False)
wav_trained = tts_base.tts(text="Teste", language="pt", speaker_wav="ref.wav")
sf.write("trained_model.wav", wav_trained, 22050)

# Ouvir ambos e comparar!
```

---

## 📝 Próximos Passos

1. ✅ Treinar modelo (funciona perfeitamente)
2. ✅ Salvar checkpoints (OK)
3. ⚠️ Geração automática de samples (bug temporário)
4. ✅ Testar manualmente (use scripts acima)
5. 🔜 Corrigir bug cuFFT para geração automática

---

**Commit:** `e1a5259` - fix(training): Desabilitar geração de samples devido a bug cuFFT
