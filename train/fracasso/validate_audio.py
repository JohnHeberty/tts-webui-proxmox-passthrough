"""
Script de validação de áudio usando Whisper.
Valida se o áudio gerado corresponde ao texto esperado com precisão ≥ threshold.
"""

import argparse
import whisper
from pathlib import Path
from difflib import SequenceMatcher


def calculate_similarity(text1: str, text2: str) -> float:
    """
    Calcula similaridade entre dois textos usando SequenceMatcher.
    
    Args:
        text1: Texto original (esperado)
        text2: Texto transcrito (resultado)
    
    Returns:
        float: Similaridade de 0.0 a 1.0
    """
    # Normaliza textos
    text1_norm = text1.lower().strip()
    text2_norm = text2.lower().strip()
    
    # Calcula similaridade
    matcher = SequenceMatcher(None, text1_norm, text2_norm)
    similarity = matcher.ratio()
    
    return similarity


def validate_transcription(
    audio_path: str,
    expected_text: str,
    threshold: float = 0.8,
    model_name: str = "base",
    language: str = "pt"
) -> tuple[str, float, bool]:
    """
    Valida áudio transcrevendo com Whisper e comparando com texto esperado.
    
    Args:
        audio_path: Caminho do arquivo de áudio
        expected_text: Texto esperado
        threshold: Limite mínimo de precisão (default: 0.8 = 80%)
        model_name: Modelo Whisper ("tiny", "base", "small", "medium", "large")
        language: Código da língua (default: "pt" para português)
    
    Returns:
        tuple: (transcription, accuracy, passed)
            - transcription: Texto transcrito pelo Whisper
            - accuracy: Precisão de 0.0 a 1.0
            - passed: True se accuracy >= threshold
    """
    print(f"🎤 Carregando modelo Whisper '{model_name}'...")
    model = whisper.load_model(model_name)
    
    print(f"🔊 Transcrevendo áudio: {audio_path}")
    result = model.transcribe(audio_path, language=language)
    transcription = result["text"].strip()
    
    print(f"📝 Texto esperado: {expected_text}")
    print(f"📝 Texto transcrito: {transcription}")
    
    # Calcula similaridade
    accuracy = calculate_similarity(expected_text, transcription)
    passed = accuracy >= threshold
    
    print(f"\n{'✅' if passed else '❌'} Precisão: {accuracy:.2%} (threshold: {threshold:.2%})")
    
    return transcription, accuracy, passed


def main():
    parser = argparse.ArgumentParser(
        description="Valida áudio comparando transcrição Whisper com texto esperado"
    )
    parser.add_argument(
        "--audio",
        type=str,
        required=True,
        help="Caminho do arquivo de áudio a validar"
    )
    parser.add_argument(
        "--expected",
        type=str,
        required=True,
        help="Texto esperado (ou caminho de arquivo com --expected-file)"
    )
    parser.add_argument(
        "--expected-file",
        action="store_true",
        help="Se --expected é um caminho de arquivo (não texto direto)"
    )
    parser.add_argument(
        "--threshold",
        type=float,
        default=0.8,
        help="Limite mínimo de precisão (default: 0.8 = 80%%)"
    )
    parser.add_argument(
        "--model",
        type=str,
        default="base",
        choices=["tiny", "base", "small", "medium", "large"],
        help="Modelo Whisper a usar (default: base)"
    )
    parser.add_argument(
        "--language",
        type=str,
        default="pt",
        help="Código da língua (default: pt)"
    )
    
    args = parser.parse_args()
    
    # Lê expected_text de arquivo se necessário
    if args.expected_file:
        expected_text = Path(args.expected).read_text(encoding="utf-8").strip()
    else:
        expected_text = args.expected
    
    # Valida áudio
    transcription, accuracy, passed = validate_transcription(
        audio_path=args.audio,
        expected_text=expected_text,
        threshold=args.threshold,
        model_name=args.model,
        language=args.language
    )
    
    # Exit code: 0 se passou, 1 se falhou
    exit(0 if passed else 1)


if __name__ == "__main__":
    main()
