#!/usr/bin/env python3
"""
F5-TTS Test Script - Geração de áudio direto via CLI
Baseado no notebook.ipynb convertido para execução standalone
Refatorado para usar sistema de configuração unificado
"""

import argparse
from datetime import datetime
from pathlib import Path
import sys
import time

import soundfile as sf
import torch


# Add project root to path
PROJECT_ROOT = Path(__file__).parent.parent.resolve()
sys.path.insert(0, str(PROJECT_ROOT))

# F5-TTS imports
from f5_tts.infer.utils_infer import (
    infer_process,
    load_model,
    load_vocoder,
)
from f5_tts.model import DiT

# Unified config
from train.config.loader import load_config


def main():
    # Parse arguments
    parser = argparse.ArgumentParser(
        description="F5-TTS Test - Direct Audio Generation",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Basic test with defaults
  python -m train.test
  
  # Custom checkpoint
  python -m train.test --checkpoint model_50000.pt
  
  # Custom text
  python -m train.test --text "Olá, este é um teste de síntese de voz."
  
  # Force CPU
  python -m train.test --device cpu
        """,
    )

    parser.add_argument(
        "--checkpoint",
        type=str,
        default="model_last.pt",
        help="Checkpoint filename (default: model_last.pt)",
    )
    parser.add_argument("--text", type=str, help="Text to synthesize (overrides ref text)")
    parser.add_argument("--ref-audio", type=str, help="Reference audio file")
    parser.add_argument("--ref-text", type=str, help="Reference audio transcription")
    parser.add_argument(
        "--device", type=str, choices=["cuda", "cpu", "auto"], help="Device (default: from config)"
    )
    parser.add_argument(
        "--output",
        type=str,
        default="test_output.wav",
        help="Output filename (default: test_output.wav)",
    )

    args = parser.parse_args()

    # Load unified config
    cli_overrides = {}
    if args.device:
        cli_overrides["hardware"] = {"device": args.device}

    config = load_config(cli_overrides=cli_overrides if cli_overrides else None)

    print("=" * 80)
    print("🎙️  F5-TTS TEST - GERAÇÃO DE ÁUDIO NATIVA")
    print("=" * 80)

    # 1. Device configuration
    device = config.hardware.device
    if device == "auto":
        device = "cuda" if torch.cuda.is_available() else "cpu"

    print(f"\n🎯 Device: {device}")
    if torch.cuda.is_available():
        print(f"✅ CUDA: {torch.cuda.get_device_name(0)}")
        print(f"✅ VRAM: {torch.cuda.get_device_properties(0).total_memory / 1e9:.2f} GB")

    # 2. Paths from config
    TRAIN_DIR = PROJECT_ROOT / "train"
    OUTPUT_DIR = PROJECT_ROOT / config.paths.output_dir
    CHECKPOINT_PATH = OUTPUT_DIR / args.checkpoint
    SAMPLES_DIR = OUTPUT_DIR / "samples"
    TEST_OUTPUT_DIR = TRAIN_DIR
    VOCAB_FILE = PROJECT_ROOT / config.paths.vocab_file

    print(f"\n📁 Checkpoint: {CHECKPOINT_PATH}")
    print(f"📁 Output dir: {TEST_OUTPUT_DIR}")
    print(f"📁 Vocab: {VOCAB_FILE}")

    if not CHECKPOINT_PATH.exists():
        print("❌ Checkpoint não encontrado!")
        print(f"\nAvailable checkpoints in {OUTPUT_DIR}:")
        if OUTPUT_DIR.exists():
            for f in sorted(OUTPUT_DIR.glob("*.pt")):
                size_gb = f.stat().st_size / (1024**3)
                print(f"  - {f.name} ({size_gb:.2f} GB)")
        return 1

    checkpoint_size = CHECKPOINT_PATH.stat().st_size / (1024**3)
    print(f"📊 Checkpoint: {checkpoint_size:.2f} GB")

    # 3. Load model
    print("\n🔄 Carregando modelo F5-TTS...")

    # Use model config from unified config
    model_cfg = dict(
        dim=config.model.dim,
        depth=config.model.depth,
        heads=config.model.heads,
        ff_mult=config.model.ff_mult,
        text_dim=config.model.text_dim,
        conv_layers=config.model.conv_layers,
    )

    model = load_model(
        model_cls=DiT,
        model_cfg=model_cfg,
        ckpt_path=str(CHECKPOINT_PATH),
        mel_spec_type=config.mel_spec.mel_spec_type,
        vocab_file=str(VOCAB_FILE) if VOCAB_FILE.exists() else "",
        ode_method="euler",
        use_ema=config.model.use_ema,
        device=device,
    )
    print(
        f"✅ Modelo carregado! Parâmetros: {sum(p.numel() for p in model.parameters()) / 1e6:.1f}M"
    )

    # 4. Load vocoder
    print("\n🔄 Carregando vocoder Vocos...")
    vocoder = load_vocoder(vocoder_name="vocos", is_local=False, local_path="")
    print("✅ Vocoder carregado!")

    # 5. Reference audio
    ref_audio_path = SAMPLES_DIR / "update_33200_ref.wav"
    if not ref_audio_path.exists():
        print(f"❌ Áudio de referência não encontrado: {ref_audio_path}")
        return 1

    audio_info, sr_info = sf.read(str(ref_audio_path))
    duration_info = len(audio_info) / sr_info
    print(f"\n✅ Áudio de referência: {ref_audio_path.name}")
    print(f"📊 Sample rate: {sr_info} Hz | Duration: {duration_info:.2f}s")

    # 6. Texts
    ref_text = "Olá, este é um teste de síntese de voz com o modelo F5-TTS fine-tuned em português brasileiro."

    gen_text = """
    Bem-vindo ao teste de geração de voz usando F5-TTS. 
    Este modelo foi treinado especificamente para português brasileiro, 
    garantindo naturalidade e expressividade em cada palavra falada.
    A tecnologia de flow matching permite uma síntese de alta qualidade, 
    mantendo as características únicas da voz de referência.
    """.strip()

    print(f"\n📝 Texto de referência: {ref_text[:80]}...")
    print(f"📝 Texto para gerar: {len(gen_text)} caracteres")

    # 7. Generate audio
    print("\n" + "=" * 80)
    print("🎙️  GERANDO ÁUDIO COM GPU...")
    print("=" * 80)

    start_time = time.time()

    # Tentar usar GPU (device original do modelo)
    inference_device = device
    print(f"🚀 Usando device: {inference_device}")

    try:
        audio_output, sample_rate, _ = infer_process(
            ref_audio=str(ref_audio_path),
            ref_text=ref_text,
            gen_text=gen_text,
            model_obj=model,
            vocoder=vocoder,
            mel_spec_type="vocos",
            show_info=print,
            progress=None,
            target_rms=0.1,
            cross_fade_duration=0.0,
            nfe_step=32,  # Training match
            cfg_strength=2.0,  # Training match
            sway_sampling_coef=-1.0,  # Training match
            speed=1.0,
            fix_duration=None,
            device=inference_device,
        )
        print(f"✅ Geração concluída com {inference_device.upper()}")

    except RuntimeError as e:
        if "cuFFT" in str(e) or "CUDA" in str(e):
            print(f"\n⚠️  Erro CUDA detectado: {e}")
            print("🔄 Tentando novamente com CPU...")

            # Fallback para CPU
            model.to("cpu")
            audio_output, sample_rate, _ = infer_process(
                ref_audio=str(ref_audio_path),
                ref_text=ref_text,
                gen_text=gen_text,
                model_obj=model,
                vocoder=vocoder,
                mel_spec_type="vocos",
                show_info=print,
                progress=None,
                target_rms=0.1,
                cross_fade_duration=0.0,
                nfe_step=32,
                cfg_strength=2.0,
                sway_sampling_coef=-1.0,
                speed=1.0,
                fix_duration=None,
                device="cpu",
            )
            model.to(device)  # Restaurar para GPU
            print("✅ Geração concluída com CPU (fallback)")
        else:
            raise  # Re-raise se não for erro CUDA

    generation_time = time.time() - start_time

    # 8. Save audio
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_filename = f"f5tts_test_{timestamp}.wav"
    output_path = TEST_OUTPUT_DIR / output_filename

    sf.write(str(output_path), audio_output, sample_rate)

    # 9. Stats
    audio_duration = len(audio_output) / sample_rate if sample_rate > 0 else 0
    rtf = generation_time / audio_duration if audio_duration > 0 else 0

    print("\n" + "=" * 80)
    print("✅ ÁUDIO GERADO COM SUCESSO!")
    print("=" * 80)
    print(f"💾 Arquivo: {output_path}")
    print(f"⏱️  Tempo de geração: {generation_time:.2f}s")
    print(f"📊 Sample rate: {sample_rate} Hz")
    print(f"📊 Duração do áudio: {audio_duration:.2f}s")
    print(f"📊 RTF (Real-Time Factor): {rtf:.2f}x")
    print(f"📊 Tamanho: {output_path.stat().st_size / 1024:.1f} KB")
    print("=" * 80)

    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print("\n⚠️  Interrompido pelo usuário")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Erro: {e}")
        import traceback

        traceback.print_exc()
        sys.exit(1)
