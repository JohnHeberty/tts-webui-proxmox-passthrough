#!/usr/bin/env python3
"""
Teste de qualidade de clonagem de voz com F5-TTS
Compara o modelo fine-tunado com o modelo base
"""
import asyncio
import sys
import logging
from pathlib import Path

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Add app to path
sys.path.insert(0, str(Path(__file__).parent))

async def test_voice_cloning():
    """Teste completo de clonagem de voz"""
    
    logger.info("="*80)
    logger.info("🎤 TESTE DE QUALIDADE DE CLONAGEM DE VOZ - F5-TTS")
    logger.info("="*80)
    
    # Verificar áudio de referência
    ref_audio = Path("/app/uploads/clone_20251205000306901554.wav")
    if not ref_audio.exists():
        logger.error(f"❌ Áudio de referência não encontrado: {ref_audio}")
        return False
    
    logger.info(f"\n✅ Áudio de referência: {ref_audio.name}")
    logger.info(f"   Tamanho: {ref_audio.stat().st_size / 1024:.1f} KB")
    
    # Texto para teste
    test_text = "Olá! Este é um teste de clonagem de voz usando o modelo fine-tunado em português brasileiro."
    
    # CRITICAL: ref_text deve ter tamanho proporcional ao áudio de referência!
    # Se áudio = 12s (clipped), ref_text deve ter ~100-150 chars para max_chars adequado
    ref_text = """Este é um exemplo de texto de referência para clonagem de voz.
    O texto deve ter aproximadamente o mesmo tamanho e características do áudio original,
    garantindo que a síntese funcione corretamente sem dividir em chunks muito pequenos."""
    
    logger.info(f"\n📝 Texto a gerar: {test_text}")
    logger.info(f"📝 Texto de referência: {ref_text}")
    
    try:
        # Importar engine
        from app.engines.f5tts_engine import F5TtsEngine
        
        logger.info("\n" + "="*80)
        logger.info("TESTE 1: Modelo Fine-Tunado (custom checkpoint)")
        logger.info("="*80)
        
        # Inicializar engine com checkpoint customizado
        custom_ckpt = "/app/train/output/ptbr_finetuned2/model_last.pt"
        
        logger.info(f"\n🔧 Inicializando engine com checkpoint: {Path(custom_ckpt).name}")
        engine = F5TtsEngine(
            device='cuda',
            custom_ckpt_path=custom_ckpt
        )
        
        logger.info("✅ Engine inicializado")
        
        # Criar voice profile
        logger.info(f"\n🎙️ Criando voice profile do áudio de referência...")
        voice_profile = await engine.clone_voice(
            audio_path=str(ref_audio),
            language='pt-BR',
            voice_name='test_clone',
            description='Clone para teste de qualidade',
            ref_text=ref_text
        )
        
        logger.info(f"✅ Voice profile criado: {voice_profile.name}")
        
        # Gerar áudio com voice clone
        logger.info(f"\n🎤 Gerando áudio com voz clonada...")
        from app.models import QualityProfile
        
        audio_bytes, duration = await engine.generate_dubbing(
            text=test_text,
            language='pt-BR',
            voice_profile=voice_profile,
            quality_profile=QualityProfile.BALANCED,
            speed=1.0
        )
        
        logger.info(f"✅ Áudio gerado!")
        logger.info(f"   Duração: {duration:.2f}s")
        logger.info(f"   Tamanho: {len(audio_bytes) / 1024:.1f} KB")
        
        # Salvar áudio
        output_dir = Path("/app/temp")
        output_dir.mkdir(exist_ok=True)
        
        output_file = output_dir / "test_clone_finetuned.wav"
        with open(output_file, 'wb') as f:
            f.write(audio_bytes)
        
        logger.info(f"💾 Salvo em: {output_file}")
        
        # TESTE 2: Sem voice profile (voz padrão)
        logger.info("\n" + "="*80)
        logger.info("TESTE 2: Sem Clonagem (voz padrão do modelo)")
        logger.info("="*80)
        
        audio_bytes_default, duration_default = await engine.generate_dubbing(
            text=test_text,
            language='pt-BR',
            voice_profile=None,  # Sem clonagem
            quality_profile=QualityProfile.BALANCED,
            speed=1.0
        )
        
        logger.info(f"✅ Áudio gerado!")
        logger.info(f"   Duração: {duration_default:.2f}s")
        logger.info(f"   Tamanho: {len(audio_bytes_default) / 1024:.1f} KB")
        
        output_file_default = output_dir / "test_no_clone_default.wav"
        with open(output_file_default, 'wb') as f:
            f.write(audio_bytes_default)
        
        logger.info(f"💾 Salvo em: {output_file_default}")
        
        # Comparação
        logger.info("\n" + "="*80)
        logger.info("📊 COMPARAÇÃO DE RESULTADOS")
        logger.info("="*80)
        logger.info(f"\nCOM CLONAGEM:")
        logger.info(f"  - Arquivo: {output_file.name}")
        logger.info(f"  - Duração: {duration:.2f}s")
        logger.info(f"  - Taxa: {len(test_text) / duration:.1f} chars/s")
        
        logger.info(f"\nSEM CLONAGEM (voz padrão):")
        logger.info(f"  - Arquivo: {output_file_default.name}")
        logger.info(f"  - Duração: {duration_default:.2f}s")
        logger.info(f"  - Taxa: {len(test_text) / duration_default:.1f} chars/s")
        
        logger.info("\n" + "="*80)
        logger.info("✅✅✅ TESTES CONCLUÍDOS COM SUCESSO! ✅✅✅")
        logger.info("="*80)
        logger.info("\n📁 Arquivos para audição:")
        logger.info(f"   1. {output_file}")
        logger.info(f"   2. {output_file_default}")
        logger.info("\n💡 Copie os arquivos do container para ouvir:")
        logger.info(f"   docker cp audio-voice-celery:{output_file} ./")
        logger.info(f"   docker cp audio-voice-celery:{output_file_default} ./")
        
        return True
        
    except Exception as e:
        logger.error(f"\n❌ Erro durante teste: {e}", exc_info=True)
        return False

if __name__ == "__main__":
    success = asyncio.run(test_voice_cloning())
    sys.exit(0 if success else 1)
