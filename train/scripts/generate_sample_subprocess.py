#!/usr/bin/env python3
"""
Script auxiliar para gerar samples em processo isolado.
USA CPU para evitar bug cuFFT persistente no ambiente CUDA.

Usage:
    python3 generate_sample_subprocess.py \
        --reference_wav audio.wav \
        --text "texto" \
        --output sample.wav
"""
import sys
import argparse
import torch
from pathlib import Path

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--reference_wav', required=True)
    parser.add_argument('--text', required=True)
    parser.add_argument('--output', required=True)
    args = parser.parse_args()
    
    # Monkey patch PyTorch 2.6+
    original_load = torch.load
    def patched_load(*args, **kwargs):
        kwargs['weights_only'] = False
        return original_load(*args, **kwargs)
    torch.load = patched_load
    
    # Usar CPU (GPU tem bug cuFFT persistente)
    print("📥 Carregando XTTS em CPU...", file=sys.stderr)
    
    # Carregar TTS
    from TTS.api import TTS
    tts = TTS(
        model_name="tts_models/multilingual/multi-dataset/xtts_v2",
        gpu=False  # CPU por causa do bug cuFFT
    )
    
    # Gerar áudio
    print(f"🔊 Sintetizando áudio em CPU (mais lento mas evita cuFFT bug)...", file=sys.stderr)
    wav = tts.tts(
        text=args.text,
        language="pt",
        speaker_wav=args.reference_wav
    )
    
    # Salvar
    import soundfile as sf
    sf.write(args.output, wav, 22050)
    print(f"✅ Sample gerado: {args.output}", file=sys.stderr)
    
    # Limpar
    del tts
    
    print("SUCCESS")  # stdout para parent process

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"ERROR: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc(file=sys.stderr)
        sys.exit(1)
