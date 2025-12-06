#!/usr/bin/env python3
"""
Example 2: Simple Inference

Basic inference example using the unified F5TTSInference API.
Demonstrates loading a model and generating speech.

Usage:
    python train/examples/02_inference_simple.py
    
Requirements:
    - Trained checkpoint at models/f5tts/model_last.pt
    - Vocab file at train/config/vocab.txt
    - Reference audio file
"""
import logging
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from train.inference.api import F5TTSInference

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def main():
    """Run simple inference example."""
    
    print("=" * 60)
    print("F5-TTS Simple Inference Example")
    print("=" * 60)
    print()
    
    # Configuration
    checkpoint_path = "models/f5tts/model_last.pt"
    vocab_file = "train/config/vocab.txt"
    ref_audio = "train/data/processed/wavs/segment_0001.wav"
    
    # Text to synthesize
    text = "Olá! Este é um exemplo de síntese de voz usando F5-TTS."
    ref_text = "Texto de referência para voice cloning."
    
    # Output
    output_path = "output_example.wav"
    
    print("📋 Configuration:")
    print(f"  Checkpoint: {checkpoint_path}")
    print(f"  Vocab: {vocab_file}")
    print(f"  Reference: {ref_audio}")
    print(f"  Text: {text}")
    print(f"  Output: {output_path}")
    print()
    
    # Check files exist
    if not Path(checkpoint_path).exists():
        logger.error(f"❌ Checkpoint not found: {checkpoint_path}")
        logger.info("Train a model first or download pretrained model!")
        return 1
    
    if not Path(vocab_file).exists():
        logger.error(f"❌ Vocab not found: {vocab_file}")
        return 1
    
    if not Path(ref_audio).exists():
        logger.error(f"❌ Reference audio not found: {ref_audio}")
        logger.info("Use any audio file as reference (3-30s recommended)")
        return 1
    
    # Initialize inference API
    print("⏳ Loading model...")
    inference = F5TTSInference(
        checkpoint_path=checkpoint_path,
        vocab_file=vocab_file,
        device="cuda",  # Use "cpu" if no GPU
    )
    print("✅ Model loaded!")
    print()
    
    # Generate speech
    print("🎙️ Generating speech...")
    audio = inference.generate(
        text=text,
        ref_audio=ref_audio,
        ref_text=ref_text,
        nfe_step=32,  # Quality: 16=fast, 32=balanced, 64=high
        cfg_strength=2.0,  # Expressiveness: 1.0=stable, 3.0=expressive
        speed=1.0,  # Speed: 0.5-2.0
        remove_silence=True,
    )
    print("✅ Speech generated!")
    print()
    
    # Save output
    print(f"💾 Saving to: {output_path}")
    inference.save_audio(audio, output_path)
    
    # Info
    duration = len(audio) / 24000  # F5-TTS uses 24kHz
    file_size = Path(output_path).stat().st_size / 1024  # KB
    
    print()
    print("=" * 60)
    print("✅ Inference complete!")
    print(f"  Duration: {duration:.2f}s")
    print(f"  File size: {file_size:.1f} KB")
    print(f"  Output: {output_path}")
    print("=" * 60)
    
    return 0


if __name__ == "__main__":
    exit(main())
