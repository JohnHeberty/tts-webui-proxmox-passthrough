#!/usr/bin/env python3
"""
Script auxiliar para gerar samples em processo isolado.
USA CPU para evitar bug cuFFT persistente no ambiente CUDA.

Sprint 6 Task 6.2: Optimized for faster generation (<30s target)

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
import time

def main():
    start_time = time.time()
    
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
    load_start = time.time()
    
    # Carregar TTS
    from TTS.api import TTS
    tts = TTS(
        model_name="tts_models/multilingual/multi-dataset/xtts_v2",
        gpu=False,  # CPU por causa do bug cuFFT
        progress_bar=False  # Sprint 6 Task 6.2: Disable progress bar for faster execution
    )
    
    load_time = time.time() - load_start
    print(f"✅ Modelo carregado em {load_time:.1f}s", file=sys.stderr)
    
    # Gerar áudio
    print(f"🔊 Sintetizando áudio em CPU...", file=sys.stderr)
    synth_start = time.time()
    
    # Sprint 6 Task 6.2: Use shorter reference audio for faster conditioning
    wav = tts.tts(
        text=args.text,
        language="pt",
        speaker_wav=args.reference_wav,
        # Limit reference audio length to speed up conditioning
        split_sentences=False  # Don't split, faster for short texts
    )
    
    synth_time = time.time() - synth_start
    print(f"✅ Síntese concluída em {synth_time:.1f}s", file=sys.stderr)
    
    # Salvar
    import soundfile as sf
    sf.write(args.output, wav, 22050)
    
    total_time = time.time() - start_time
    print(f"✅ Sample gerado: {args.output} (total: {total_time:.1f}s)", file=sys.stderr)
    
    # Limpar
    del tts
    del wav
    
    # Sprint 6 Task 6.2: Force garbage collection before exit
    import gc
    gc.collect()
    
    print("SUCCESS")  # stdout para parent process

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"ERROR: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc(file=sys.stderr)
        sys.exit(1)
