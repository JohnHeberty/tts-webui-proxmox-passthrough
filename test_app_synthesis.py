#!/usr/bin/env python3
"""
Teste isolado: Simula EXATAMENTE o código de síntese do app/services/xtts_service.py
sem importar FastAPI e outras dependências do app.
"""

import os
import sys
import numpy as np
import soundfile as sf
import tempfile
from pathlib import Path

# 1. Monkey patch torch.load ANTES de importar TTS
import torch
original_load = torch.load
def patched_load(*args, **kwargs):
    if 'weights_only' not in kwargs:
        kwargs['weights_only'] = False
    return original_load(*args, **kwargs)
torch.load = patched_load

# 2. Importar TTS
from TTS.api import TTS

print("=" * 80)
print("🔍 TESTE REAL: Código EXATO de app/services/xtts_service.py")
print("=" * 80)
print()

# 3. Verificar CUDA
print("🖥️  CUDA Status:")
print(f"   Available: {torch.cuda.is_available()}")
if torch.cuda.is_available():
    print(f"   Device: {torch.cuda.get_device_name(0)}")
    print(f"   VRAM: {torch.cuda.get_device_properties(0).total_memory / 1024**3:.2f} GB")
print()

# 4. Inicializar XTTS (EXATAMENTE como XTTSService.initialize())
print("📦 Inicializando TTS (EXATAMENTE como app)...")
model_name = "tts_models/multilingual/multi-dataset/xtts_v2"
gpu = True  # App usa GPU por padrão
progress_bar = False

tts = TTS(
    model_name=model_name,
    gpu=gpu,
    progress_bar=progress_bar
)
print(f"✅ Modelo carregado: {model_name}")
print(f"✅ GPU habilitada: {gpu}")
print()

# 5. Criar áudio de referência fake
print("🎤 Criando áudio de referência fake...")
test_audio = np.random.rand(48000).astype(np.float32)
with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as f:
    sf.write(f.name, test_audio, 24000)
    speaker_wav = f.name
print(f"✅ Referência: {speaker_wav}")
print()

# 6. Síntese XTTS (EXATAMENTE como XTTSService.synthesize())
# Código copiado de app/services/xtts_service.py linha 181-188
print("🎯 Testando síntese (CÓDIGO EXATO DO APP)...")
text = "Teste de síntese em GPU usando o código do app."
language = "pt"

# Parâmetros padrão do perfil "balanced"
params = {
    "temperature": 0.7,
    "speed": 1.0,
    "top_p": 0.85,
    "repetition_penalty": 5.0
}

print(f"   Texto: {text}")
print(f"   Língua: {language}")
print(f"   Params: {params}")
print()

try:
    print("⚡ Executando tts.tts()...")
    
    # ===== CÓDIGO EXATO DE app/services/xtts_service.py linha 181-188 =====
    wav = tts.tts(
        text=text,
        speaker_wav=str(speaker_wav),
        language=language,
        temperature=params["temperature"],
        speed=params["speed"],
        top_p=params["top_p"],
        repetition_penalty=params["repetition_penalty"]
    )
    # ===== FIM DO CÓDIGO DO APP =====
    
    print()
    print("=" * 80)
    print("✅ ✅ ✅ SÍNTESE FUNCIONOU NA GPU! ✅ ✅ ✅")
    print("=" * 80)
    
    # Converter para numpy array (como app faz)
    audio_array = np.array(wav, dtype=np.float32)
    sample_rate = 24000  # XTTS sempre usa 24kHz
    
    duration = len(audio_array) / sample_rate
    print(f"Audio shape: {audio_array.shape}")
    print(f"Sample rate: {sample_rate} Hz")
    print(f"Duration: {duration:.2f}s")
    print()
    print("🎉 O APP REALMENTE FUNCIONA NA GPU!")
    
except Exception as e:
    print()
    print("=" * 80)
    print("❌ ❌ ❌ SÍNTESE FALHOU! ❌ ❌ ❌")
    print("=" * 80)
    print(f"Erro: {type(e).__name__}: {e}")
    print()
    
    import traceback
    print("Traceback completo:")
    traceback.print_exc()
    print()
    print("🔴 O APP TAMBÉM TEM O BUG cuFFT!")

finally:
    # Cleanup
    os.unlink(speaker_wav)
