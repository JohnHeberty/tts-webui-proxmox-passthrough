#!/usr/bin/env python3
"""
Teste de síntese XTTS dentro do Docker.
Usa código EXATO de app/services/xtts_service.py
"""

import numpy as np
import soundfile as sf
import tempfile
import os

# Importar TTS
from TTS.api import TTS

print("=" * 80)
print("🐳 TESTE DOCKER: PyTorch 2.4.0+cu118 (CUDA 11.8)")
print("=" * 80)
print()

# Verificar CUDA
import torch
print("🖥️  CUDA Status:")
print(f"   Available: {torch.cuda.is_available()}")
if torch.cuda.is_available():
    print(f"   Device: {torch.cuda.get_device_name(0)}")
    print(f"   PyTorch: {torch.__version__}")
print()

# Inicializar XTTS
print("📦 Carregando XTTS na GPU...")
model_name = "tts_models/multilingual/multi-dataset/xtts_v2"
tts = TTS(model_name=model_name, gpu=True, progress_bar=False)
print(f"✅ Modelo: {model_name}")
print()

# Criar áudio fake
print("🎤 Criando referência...")
test_audio = np.random.rand(48000).astype(np.float32)
with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as f:
    sf.write(f.name, test_audio, 24000)
    speaker_wav = f.name
print(f"✅ Referência: {speaker_wav}")
print()

# Síntese (código exato do app)
print("⚡ Testando síntese na GPU (código do app)...")
text = "Teste de síntese XTTS no Docker com GPU."
language = "pt"
params = {
    "temperature": 0.7,
    "speed": 1.0,
    "top_p": 0.85,
    "repetition_penalty": 5.0
}

try:
    wav = tts.tts(
        text=text,
        speaker_wav=str(speaker_wav),
        language=language,
        temperature=params["temperature"],
        speed=params["speed"],
        top_p=params["top_p"],
        repetition_penalty=params["repetition_penalty"]
    )
    
    print()
    print("=" * 80)
    print("✅ ✅ ✅ SÍNTESE FUNCIONOU NO DOCKER! ✅ ✅ ✅")
    print("=" * 80)
    
    audio_array = np.array(wav, dtype=np.float32)
    sample_rate = 24000
    duration = len(audio_array) / sample_rate
    
    print(f"Audio shape: {audio_array.shape}")
    print(f"Sample rate: {sample_rate} Hz")
    print(f"Duration: {duration:.2f}s")
    print()
    print("🎉 PyTorch 2.4.0+cu118 NÃO TEM O BUG cuFFT!")
    
except Exception as e:
    print()
    print("=" * 80)
    print("❌ SÍNTESE FALHOU NO DOCKER")
    print("=" * 80)
    print(f"Erro: {type(e).__name__}: {e}")
    print()
    import traceback
    traceback.print_exc()
    print()
    print("🔴 PyTorch 2.4.0+cu118 TAMBÉM TEM O BUG")

finally:
    os.unlink(speaker_wav)
