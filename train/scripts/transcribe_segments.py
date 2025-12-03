"""
Transcrição de segmentos de áudio usando Whisper

Este script transcreve os segmentos de áudio já processados e salvos.
Usa Whisper para ASR (Automatic Speech Recognition) em português.

Uso:
    python -m train.scripts.transcribe_segments

Dependências:
    - openai-whisper: pip install openai-whisper
    - num2words: pip install num2words
"""
import json
import logging
import re
import sys
from pathlib import Path
from typing import List, Dict
import gc

import yaml

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

try:
    import whisper
    import torch
    from num2words import num2words
except ImportError as e:
    print(f"❌ Dependência não encontrada: {e}")
    print("Instale com: pip install openai-whisper num2words")
    sys.exit(1)

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('train/logs/transcribe.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


def load_config() -> dict:
    """Carrega configuração do dataset"""
    config_path = project_root / "train" / "config" / "dataset_config.yaml"
    with open(config_path, 'r', encoding='utf-8') as f:
        return yaml.safe_load(f)


def preprocess_text(text: str, config: dict) -> str:
    """
    Preprocessa texto de transcrição
    
    Args:
        text: Texto original
        config: Configuração
    
    Returns:
        Texto preprocessado
    """
    preproc_config = config['text_preprocessing']
    
    # Lowercase
    if preproc_config['lowercase']:
        text = text.lower()
    
    # Converter números para palavras
    if preproc_config['convert_numbers_to_words']:
        def replace_number(match):
            num = match.group()
            try:
                # Tentar converter para número
                if ',' in num or '.' in num:
                    # Número decimal
                    num_clean = num.replace(',', '.')
                    num_float = float(num_clean)
                    return num2words(num_float, lang='pt_BR')
                else:
                    # Número inteiro
                    num_int = int(num)
                    return num2words(num_int, lang='pt_BR')
            except:
                return num
        
        # Substituir números
        text = re.sub(r'\d+[.,]?\d*', replace_number, text)
    
    # Normalizar pontuação
    if preproc_config['normalize_punctuation']:
        for old, new in preproc_config['replacements'].items():
            text = text.replace(old, new)
    
    # Remover múltiplos espaços
    text = re.sub(r'\s+', ' ', text)
    
    # Remover espaços no início/fim
    text = text.strip()
    
    # Filtrar por comprimento
    if len(text) < preproc_config['min_text_length']:
        return ""
    if len(text) > preproc_config['max_text_length']:
        text = text[:preproc_config['max_text_length']]
    
    return text


def transcribe_segment_whisper(
    audio_path: Path,
    model: whisper.Whisper,
    config: dict
) -> str:
    """
    Transcreve um segmento de áudio usando Whisper
    
    Args:
        audio_path: Path do arquivo de áudio
        model: Modelo Whisper carregado
        config: Configuração
    
    Returns:
        Texto transcrito
    """
    asr_config = config['transcription']['asr']
    
    try:
        # Transcrever
        result = model.transcribe(
            str(audio_path),
            language=asr_config['language'],
            task=asr_config['task'],
            beam_size=asr_config['beam_size'],
            best_of=asr_config['best_of'],
            temperature=asr_config['temperature'],
            fp16=torch.cuda.is_available()
        )
        
        text = result['text'].strip()
        return text
        
    except Exception as e:
        logger.error(f"   ❌ Erro ao transcrever: {e}")
        return ""


def transcribe_segments_batch(
    segments: List[Dict],
    model: whisper.Whisper,
    config: dict,
    batch_size: int = 10
) -> List[Dict]:
    """
    Transcreve segmentos em batches para economizar memória
    
    Args:
        segments: Lista de segmentos
        model: Modelo Whisper
        config: Configuração
        batch_size: Tamanho do batch
    
    Returns:
        Lista de segmentos com transcrições
    """
    transcribed_segments = []
    total = len(segments)
    
    for i in range(0, total, batch_size):
        batch = segments[i:i+batch_size]
        batch_end = min(i + batch_size, total)
        
        logger.info(f"\n📦 Processando batch {i//batch_size + 1} ({i+1}-{batch_end}/{total})")
        
        for j, segment in enumerate(batch, 1):
            segment_idx = i + j
            audio_rel_path = segment['audio_path']
            audio_path = project_root / "train" / "data" / audio_rel_path
            
            if not audio_path.exists():
                logger.warning(f"   ⚠️  [{segment_idx}/{total}] Arquivo não encontrado: {audio_rel_path}")
                continue
            
            logger.info(f"   🎤 [{segment_idx}/{total}] Transcrevendo: {audio_path.name}")
            
            # Transcrever
            text = transcribe_segment_whisper(audio_path, model, config)
            
            if not text:
                logger.warning(f"   ⚠️  Transcrição vazia")
                continue
            
            # Preprocessar texto
            processed_text = preprocess_text(text, config)
            
            if not processed_text:
                logger.warning(f"   ⚠️  Texto muito curto após preprocessamento")
                continue
            
            # Adicionar transcrição ao segmento
            segment_with_text = segment.copy()
            segment_with_text['text'] = processed_text
            segment_with_text['text_raw'] = text
            transcribed_segments.append(segment_with_text)
            
            logger.info(f"   ✅ \"{processed_text[:80]}...\"")
        
        # Limpar memória após cada batch
        gc.collect()
        if torch.cuda.is_available():
            torch.cuda.empty_cache()
    
    return transcribed_segments


def main():
    """Main function"""
    logger.info("=" * 80)
    logger.info("TRANSCRIÇÃO DE SEGMENTOS DE ÁUDIO")
    logger.info("=" * 80)
    
    # Load config
    config = load_config()
    
    # Paths
    data_dir = project_root / "train" / "data"
    processed_dir = data_dir / "processed"
    segments_mapping_file = processed_dir / "segments_mapping.json"
    transcriptions_file = processed_dir / "transcriptions.json"
    
    # Verificar se existem segmentos
    if not segments_mapping_file.exists():
        logger.error(f"❌ Arquivo não encontrado: {segments_mapping_file}")
        logger.error("   Execute primeiro: python -m train.scripts.prepare_segments_optimized")
        sys.exit(1)
    
    # Carregar segmentos
    with open(segments_mapping_file, 'r', encoding='utf-8') as f:
        segments = json.load(f)
    
    logger.info(f"📋 {len(segments)} segmentos para transcrever")
    
    # Verificar se já existem transcrições
    skip_existing = True
    existing_transcriptions = []
    
    if transcriptions_file.exists():
        logger.info(f"📄 Arquivo de transcrições existente encontrado")
        with open(transcriptions_file, 'r', encoding='utf-8') as f:
            existing_transcriptions = json.load(f)
        logger.info(f"   {len(existing_transcriptions)} transcrições já existentes")
        
        if skip_existing:
            # Filtrar segmentos já transcritos
            existing_paths = {t['audio_path'] for t in existing_transcriptions}
            segments = [s for s in segments if s['audio_path'] not in existing_paths]
            logger.info(f"   {len(segments)} segmentos restantes para transcrever")
    
    if not segments:
        logger.info("✅ Todos os segmentos já foram transcritos!")
        return
    
    # Carregar modelo Whisper
    asr_config = config['transcription']['asr']
    model_path = asr_config['model']
    
    # Extrair nome do modelo (ex: "openai/whisper-base" -> "base")
    if '/' in model_path:
        model_name = model_path.split('/')[-1].replace('whisper-', '')
    else:
        model_name = model_path
    
    logger.info(f"\n🔧 Carregando modelo Whisper: {model_name}")
    
    device = "cuda" if torch.cuda.is_available() else "cpu"
    logger.info(f"   Device: {device}")
    
    model = whisper.load_model(model_name, device=device)
    logger.info(f"   ✅ Modelo carregado\n")
    
    # Transcrever segmentos
    logger.info("=" * 80)
    logger.info("TRANSCREVENDO SEGMENTOS")
    logger.info("=" * 80)
    
    transcribed = transcribe_segments_batch(
        segments,
        model,
        config,
        batch_size=10  # Processar 10 por vez para economizar memória
    )
    
    # Combinar com transcrições existentes
    all_transcriptions = existing_transcriptions + transcribed
    
    # Salvar transcrições
    with open(transcriptions_file, 'w', encoding='utf-8') as f:
        json.dump(all_transcriptions, f, indent=2, ensure_ascii=False)
    
    # Summary
    logger.info("\n" + "=" * 80)
    logger.info("RESUMO DA TRANSCRIÇÃO")
    logger.info("=" * 80)
    logger.info(f"✅ Segmentos transcritos nesta execução: {len(transcribed)}")
    logger.info(f"📊 Total de transcrições: {len(all_transcriptions)}")
    logger.info(f"📁 Arquivo salvo em: {transcriptions_file}")
    
    if transcribed:
        text_lengths = [len(t['text']) for t in transcribed]
        logger.info(f"📝 Tamanho médio do texto: {sum(text_lengths) / len(text_lengths):.0f} caracteres")
        logger.info(f"📝 Texto mais curto: {min(text_lengths)} caracteres")
        logger.info(f"📝 Texto mais longo: {max(text_lengths)} caracteres")
    
    logger.info("=" * 80)


if __name__ == "__main__":
    main()
