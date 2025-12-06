#!/usr/bin/env python3
"""
Script de validação de qualidade de áudio gerado.
Usa Whisper para transcrever e verificar se está inteligível.
"""

import argparse
import sys
from pathlib import Path


def main():
    parser = argparse.ArgumentParser(description="Valida áudio transcrevendo com Whisper")
    parser.add_argument("audio_file", help="Arquivo de áudio para validar")
    parser.add_argument("--model", default="base", choices=["tiny", "base", "small", "medium", "large"])
    parser.add_argument("--language", default="pt", help="Código do idioma")
    
    args = parser.parse_args()
    
    audio_path = Path(args.audio_file)
    if not audio_path.exists():
        print(f"❌ Arquivo não encontrado: {audio_path}")
        return 1
    
    print(f"🎤 Carregando modelo Whisper '{args.model}'...")
    try:
        import whisper
    except ImportError:
        print("❌ Whisper não instalado. Rode: pip install openai-whisper")
        return 1
    
    model = whisper.load_model(args.model)
    
    print(f"🔊 Transcrevendo: {audio_path.name}")
    result = model.transcribe(str(audio_path), language=args.language)
    
    transcription = result["text"].strip()
    
    print("\n" + "=" * 80)
    print("TRANSCRIÇÃO")
    print("=" * 80)
    print(transcription)
    print("=" * 80)
    
    # Análise básica
    words = transcription.split()
    num_words = len(words)
    
    print(f"\n📊 Estatísticas:")
    print(f"  Palavras: {num_words}")
    print(f"  Caracteres: {len(transcription)}")
    
    # Verifica se parece inteligível (heurística simples)
    if num_words < 3:
        print(f"\n❌ SUSPEITO: Muito poucas palavras ({num_words})")
        print("   Possível áudio ruim ou muito curto")
        return 1
    
    # Verifica caracteres estranhos (indicativo de ruído)
    import re
    weird_chars = len(re.findall(r'[^\w\s\.,!?áàâãéèêíïóôõöúçñ-]', transcription, re.IGNORECASE))
    weird_ratio = weird_chars / (len(transcription) + 1)
    
    if weird_ratio > 0.1:
        print(f"\n⚠️  ALERTA: {weird_ratio*100:.1f}% caracteres estranhos")
        print("   Áudio pode ter ruído ou qualidade baixa")
    
    print(f"\n✅ Transcrição completa!")
    print(f"\n💡 Dica: Ouça o áudio para validar qualidade:")
    print(f"   ffplay -nodisp -autoexit {audio_path}")
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
