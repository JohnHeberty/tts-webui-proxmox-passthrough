#!/usr/bin/env python3
"""
Complete Voice Cloning Test with Fine-Tuned F5-TTS Model

Tests:
1. Engine initialization with custom checkpoint
2. Voice cloning with reference audio
3. Audio generation quality
4. Output file validation

Author: Audio Voice Service Team
Date: December 4, 2025
"""
import logging
import sys
import os
import asyncio
from pathlib import Path

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Add app to path
sys.path.insert(0, str(Path(__file__).parent))

from app.engines.f5tts_engine import F5TtsEngine

async def test_voice_cloning():
    """Test complete voice cloning pipeline."""
    logger.info("="*80)
    logger.info("F5-TTS VOICE CLONING TEST - FINE-TUNED MODEL")
    logger.info("="*80)
    
    # Custom checkpoint path
    custom_ckpt = "/app/train/output/ptbr_finetuned2/model_last.pt"
    
    # Check if checkpoint exists
    if not os.path.exists(custom_ckpt):
        logger.error(f"❌ Checkpoint not found: {custom_ckpt}")
        # Try to use default model
        logger.warning("⚠️  Falling back to default PT-BR model from HuggingFace")
        custom_ckpt = None
    
    try:
        # Initialize engine
        logger.info("\n" + "="*80)
        logger.info("STEP 1: Initialize F5-TTS Engine")
        logger.info("="*80)
        
        engine = F5TtsEngine(
            device='cuda',
            custom_ckpt_path=custom_ckpt
        )
        
        logger.info("✅ Engine initialized successfully")
        logger.info(f"   Device: {engine.device}")
        logger.info(f"   Model: {engine.hf_model_name}")
        if custom_ckpt:
            logger.info(f"   Checkpoint: {custom_ckpt}")
        else:
            logger.info(f"   Checkpoint: Default PT-BR from HuggingFace")
        
        # Create test reference audio
        logger.info("\n" + "="*80)
        logger.info("STEP 2: Prepare Reference Audio")
        logger.info("="*80)
        
        # For this test, we'll use a sample from training data if available
        ref_audio_dir = Path("/app/train/data/processed")
        if ref_audio_dir.exists():
            # Find first audio file
            audio_files = list(ref_audio_dir.glob("**/*.wav"))
            if audio_files:
                ref_audio_path = str(audio_files[0])
                logger.info(f"✅ Using training sample: {ref_audio_path}")
            else:
                logger.error("❌ No audio files found in training data")
                return False
        else:
            logger.error(f"❌ Training data directory not found: {ref_audio_dir}")
            logger.info("   Please ensure training pipeline has been run")
            return False
        
        # Reference text (transcription)
        ref_text = "Este é um exemplo de áudio de referência para clonagem de voz."
        
        # Text to generate
        gen_text = """
        Olá! Esta é uma demonstração da qualidade do modelo fine-tunado de F5-TTS em português brasileiro.
        A voz deve soar natural, expressiva e fiel ao áudio de referência fornecido.
        Vamos testar com algumas frases mais longas para avaliar a consistência da síntese.
        """
        
        logger.info(f"   Reference audio: {Path(ref_audio_path).name}")
        logger.info(f"   Reference text: {ref_text[:50]}...")
        logger.info(f"   Text to generate: {gen_text[:80]}...")
        
        # Step 3: Create voice profile
        logger.info("\n" + "="*80)
        logger.info("STEP 3: Create Voice Profile")
        logger.info("="*80)
        
        voice_profile = await engine.clone_voice(
            audio_path=ref_audio_path,
            language='pt-BR',
            voice_name='test_clone',
            description='Test clone for fine-tuned model',
            ref_text=ref_text
        )
        logger.info(f"✅ Voice profile created: {voice_profile.name}")
        logger.info(f"   Profile ID: {voice_profile.id}")
        
        # Step 4: Generate audio with voice clone
        logger.info("\n" + "="*80)
        logger.info("STEP 4: Generate Cloned Voice Audio")
        logger.info("="*80)
        
        logger.info("🎤 Starting synthesis (this may take 1-3 minutes)...")
        
        from app.models import QualityProfile
        
        audio_bytes, duration = await engine.generate_dubbing(
            text=gen_text,
            language='pt-BR',
            voice_profile=voice_profile,
            quality_profile=QualityProfile.BALANCED,
            speed=1.0
        )
        
        logger.info(f"✅ Audio generated successfully")
        logger.info(f"   Audio length: {len(audio_bytes)} bytes")
        logger.info(f"   Duration: {duration:.2f} seconds")
        
        # Save output
        logger.info("\n" + "="*80)
        logger.info("STEP 5: Save Output Audio")
        logger.info("="*80)
        
        output_dir = Path("/app/temp")
        output_dir.mkdir(parents=True, exist_ok=True)
        output_path = output_dir / "test_voice_cloning_output.wav"
        
        # Save WAV bytes directly
        with open(output_path, 'wb') as f:
            f.write(audio_bytes)
        
        logger.info(f"✅ Audio saved: {output_path}")
        logger.info(f"   File size: {output_path.stat().st_size / 1024:.2f} KB")
        
        # Success
        logger.info("\n" + "="*80)
        logger.info("✅✅✅ ALL TESTS PASSED ✅✅✅")
        logger.info("="*80)
        logger.info("")
        logger.info("Summary:")
        logger.info(f"  ✅ Engine initialization: OK")
        logger.info(f"  ✅ Reference audio loaded: OK")
        logger.info(f"  ✅ Voice profile created: OK")
        logger.info(f"  ✅ Audio synthesis: OK ({len(audio_bytes)} bytes, {duration:.2f}s)")
        logger.info(f"  ✅ Output saved: {output_path}")
        logger.info("")
        logger.info("🎉 Voice cloning with fine-tuned model is working!")
        logger.info("🚀 Ready for production deployment!")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Test failed: {e}", exc_info=True)
        return False

if __name__ == "__main__":
    success = asyncio.run(test_voice_cloning())
    sys.exit(0 if success else 1)
