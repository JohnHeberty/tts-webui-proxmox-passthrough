#!/usr/bin/env python3
"""
Test de Inferência com Modelo Pré-treinado F5-TTS

Testa a geração de áudio usando o modelo pré-treinado PT-BR.
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
    """Run inference test with pretrained model."""
    
    print("=" * 60)
    print("F5-TTS Pretrained Model Inference Test")
    print("=" * 60)
    print()
    
    # Configuration
    checkpoint_path = "train/pretrained/F5-TTS-pt-br/pt-br/model_200000.pt"
    vocab_file = "train/config/vocab.txt"
    
    # Use first audio from dataset as reference
    ref_audio = "train/data/f5_dataset/wavs/audio_00001.wav"
    
    # Text to synthesize
    text = "Olá! Este é um teste de síntese de voz usando F5-TTS com o modelo pré-treinado em português brasileiro."
    ref_text = "salve família bem vindos a mais um flor"
    
    # Output
    output_path = "output_pretrained_test.wav"
    
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
        return 1
    
    if not Path(vocab_file).exists():
        logger.error(f"❌ Vocab not found: {vocab_file}")
        return 1
    
    if not Path(ref_audio).exists():
        logger.error(f"❌ Reference audio not found: {ref_audio}")
        return 1
    
    # Initialize inference API
    print("⏳ Loading pretrained model...")
    try:
        inference = F5TTSInference(
            checkpoint_path=checkpoint_path,
            vocab_file=vocab_file,
            device="cuda",  # Use "cpu" if no GPU
        )
        print("✅ Model loaded!")
        print()
    except Exception as e:
        logger.error(f"❌ Failed to load model: {e}", exc_info=True)
        return 1
    
    # Generate speech
    print("🎙️ Generating speech...")
    try:
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
    except Exception as e:
        logger.error(f"❌ Generation failed: {e}", exc_info=True)
        return 1
    
    # Save output
    print(f"💾 Saving to: {output_path}")
    try:
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
    except Exception as e:
        logger.error(f"❌ Failed to save audio: {e}", exc_info=True)
        return 1


if __name__ == "__main__":
    exit(main())
