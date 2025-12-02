"""
Transcrição de áudio usando legendas do YouTube ou Whisper

Este script:
1. Tenta baixar legendas do YouTube (se disponíveis)
2. Se não houver legendas, usa Whisper para transcrever
3. Aplica preprocessamento de texto (lowercase, num2words, etc.)

Uso:
    python -m train.scripts.transcribe_or_subtitles

Dependências:
    - yt-dlp: pip install yt-dlp
    - whisper: pip install openai-whisper
    - num2words: pip install num2words
"""
import csv
import json
import logging
import re
import sys
from pathlib import Path
from typing import Dict, List, Optional

import yaml

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

try:
    import yt_dlp
    from num2words import num2words
    import whisper
except ImportError as e:
    print(f"❌ Dependência não encontrada: {e}")
    print("Instale com: pip install yt-dlp openai-whisper num2words")
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


def load_videos_catalog(csv_path: Path) -> Dict[str, dict]:
    """
    Carrega catálogo de vídeos do CSV
    
    Returns:
        Dict mapeando video_id -> info do vídeo
    """
    videos = {}
    with open(csv_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            if row['youtube_url'].strip():
                videos[row['id']] = row
    
    return videos


def download_youtube_subtitles(
    youtube_url: str,
    output_dir: Path,
    video_id: str,
    config: dict
) -> Optional[Path]:
    """
    Tenta baixar legendas do YouTube
    
    Args:
        youtube_url: URL do vídeo
        output_dir: Diretório de saída
        video_id: ID do vídeo
        config: Configuração
    
    Returns:
        Path do arquivo de legendas, ou None se falhou
    """
    subtitle_config = config['youtube']['subtitles']
    
    # Nome do arquivo de saída
    output_template = str(output_dir / f'video_{video_id.zfill(5)}')
    
    # yt-dlp options
    ydl_opts = {
        'skip_download': True,
        'writesubtitles': True,
        'writeautomaticsub': subtitle_config['download_auto_subs'],
        'subtitleslangs': subtitle_config['subtitle_langs'],
        'subtitlesformat': subtitle_config['subtitle_formats'][0],  # vtt ou srt
        'outtmpl': output_template,
        'quiet': True,
    }
    
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([youtube_url])
        
        # Procurar arquivo de legendas gerado
        for ext in subtitle_config['subtitle_formats']:
            for lang in subtitle_config['subtitle_langs']:
                subtitle_file = Path(f"{output_template}.{lang}.{ext}")
                if subtitle_file.exists():
                    logger.info(f"   ✅ Legendas encontradas: {subtitle_file.name}")
                    return subtitle_file
        
        logger.warning(f"   ⚠️  Legendas não encontradas para video_{video_id}")
        return None
        
    except Exception as e:
        logger.warning(f"   ⚠️  Erro ao baixar legendas: {e}")
        return None


def parse_subtitle_file(subtitle_path: Path) -> str:
    """
    Extrai texto de arquivo de legendas (VTT ou SRT)
    
    Args:
        subtitle_path: Path do arquivo de legendas
    
    Returns:
        Texto completo das legendas
    """
    with open(subtitle_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Remover cabeçalhos e timestamps
    # Padrão VTT: WEBVTT, timestamps no formato 00:00:00.000 --> 00:00:00.000
    # Padrão SRT: números, timestamps no formato 00:00:00,000 --> 00:00:00,000
    
    # Remover cabeçalho VTT
    content = re.sub(r'WEBVTT.*?\n\n', '', content, flags=re.DOTALL)
    
    # Remover números de sequência e timestamps
    content = re.sub(r'\d+\n', '', content)
    content = re.sub(r'\d{2}:\d{2}:\d{2}[,.]\d{3}\s*-->\s*\d{2}:\d{2}:\d{2}[,.]\d{3}.*?\n', '', content)
    
    # Remover tags HTML (<c>, <i>, etc.)
    content = re.sub(r'<[^>]+>', '', content)
    
    # Remover linhas vazias múltiplas
    content = re.sub(r'\n\n+', '\n', content)
    
    return content.strip()


def transcribe_with_whisper(
    audio_path: Path,
    config: dict
) -> str:
    """
    Transcreve áudio usando Whisper
    
    Args:
        audio_path: Path do arquivo de áudio
        config: Configuração
    
    Returns:
        Texto transcrito
    """
    asr_config = config['transcription']['asr']
    
    # Carregar modelo Whisper
    logger.info(f"   🎤 Transcrevendo com Whisper ({asr_config['model']})...")
    
    try:
        model = whisper.load_model(
            asr_config['model'],
            device=asr_config.get('device', 'cuda')
        )
        
        # Transcrever
        result = model.transcribe(
            str(audio_path),
            language=asr_config.get('language', 'pt'),
            task=asr_config.get('task', 'transcribe'),
            beam_size=asr_config.get('beam_size', 5),
            best_of=asr_config.get('best_of', 5),
            temperature=asr_config.get('temperature', 0.0),
        )
        
        return result['text'].strip()
        
    except Exception as e:
        logger.error(f"   ❌ Erro ao transcrever com Whisper: {e}")
        return ""


def preprocess_text(text: str, config: dict) -> str:
    """
    Preprocessa texto conforme recomendações do F5-TTS pt-br
    
    Args:
        text: Texto original
        config: Configuração
    
    Returns:
        Texto preprocessado
    """
    text_config = config['text_preprocessing']
    
    # Lowercase
    if text_config['lowercase']:
        text = text.lower()
    
    # Converter números para palavras
    if text_config['convert_numbers_to_words']:
        def replace_number(match):
            try:
                number = int(match.group())
                return num2words(number, lang=text_config['numbers_lang'])
            except:
                return match.group()
        
        text = re.sub(r'\b\d+\b', replace_number, text)
    
    # Normalizar pontuação
    if text_config['normalize_punctuation']:
        for old, new in text_config['replacements'].items():
            text = text.replace(old, new)
    
    # Remover caracteres especiais
    if text_config['remove_special_chars']:
        # Manter apenas caracteres permitidos
        allowed = set(text_config['allowed_chars'])
        text = ''.join(c if c in allowed else ' ' for c in text)
    
    # Remover espaços múltiplos
    text = re.sub(r'\s+', ' ', text).strip()
    
    return text


def get_subtitle_for_segment(
    segment_info: dict,
    subtitles_text: str,
    config: dict
) -> str:
    """
    Extrai trecho de legenda correspondente a um segmento de áudio
    
    Args:
        segment_info: Info do segmento (start_time, end_time, duration)
        subtitles_text: Texto completo das legendas
        config: Configuração
    
    Returns:
        Texto da legenda para o segmento
    """
    # Para simplificar, vamos dividir as legendas proporcionalmente
    # (uma solução mais sofisticada parsearia timestamps das legendas)
    
    # TODO: Implementar parsing de timestamps para matching preciso
    # Por hora, retorna texto completo (Whisper vai lidar com isso depois)
    
    return subtitles_text


def main():
    """Main function"""
    logger.info("=" * 80)
    logger.info("TRANSCRIÇÃO DE ÁUDIO")
    logger.info("=" * 80)
    
    # Load config
    config = load_config()
    
    # Paths
    data_dir = project_root / "train" / "data"
    videos_csv = data_dir / "videos.csv"
    processed_dir = data_dir / "processed"
    wavs_dir = processed_dir / "wavs"
    subtitles_dir = data_dir / "subtitles"
    
    # Criar diretório de legendas
    subtitles_dir.mkdir(parents=True, exist_ok=True)
    
    # Verificar se existem segmentos
    segments_mapping_file = processed_dir / "segments_mapping.json"
    
    if not segments_mapping_file.exists():
        logger.error(f"❌ Arquivo não encontrado: {segments_mapping_file}")
        logger.error("   Execute primeiro: python -m train.scripts.prepare_segments")
        sys.exit(1)
    
    # Carregar mapping de segmentos
    with open(segments_mapping_file, 'r', encoding='utf-8') as f:
        segments = json.load(f)
    
    logger.info(f"📋 {len(segments)} segmentos para transcrever\n")
    
    # Carregar catálogo de vídeos
    videos_catalog = load_videos_catalog(videos_csv)
    
    # Passo 1: Tentar baixar legendas do YouTube
    logger.info("=" * 80)
    logger.info("ETAPA 1: DOWNLOAD DE LEGENDAS DO YOUTUBE")
    logger.info("=" * 80 + "\n")
    
    subtitles_cache = {}
    
    if config['transcription']['prefer_youtube_subtitles']:
        for video_id, video_info in videos_catalog.items():
            logger.info(f"🔍 Buscando legendas para video_{video_id}...")
            
            subtitle_file = download_youtube_subtitles(
                video_info['youtube_url'],
                subtitles_dir,
                video_id,
                config
            )
            
            if subtitle_file:
                subtitle_text = parse_subtitle_file(subtitle_file)
                subtitles_cache[video_id] = subtitle_text
                logger.info(f"   ✅ {len(subtitle_text)} caracteres extraídos\n")
    
    # Passo 2: Transcrever segmentos
    logger.info("\n" + "=" * 80)
    logger.info("ETAPA 2: TRANSCRIÇÃO DE SEGMENTOS")
    logger.info("=" * 80 + "\n")
    
    transcriptions = []
    
    for i, segment in enumerate(segments, 1):
        logger.info(f"[{i}/{len(segments)}] {segment['audio_path']}")
        
        # Extrair video_id do nome do arquivo original
        original_file = segment['original_file']  # ex: video_00001.wav
        video_id = original_file.split('_')[1].split('.')[0].lstrip('0') or '0'
        
        text = ""
        
        # Tentar usar legendas se disponíveis
        if video_id in subtitles_cache:
            logger.info(f"   📝 Usando legendas do YouTube")
            # Por simplificação, usar legendas completas
            # (idealmente, faria matching de timestamps)
            text = subtitles_cache[video_id]
        
        # Se não tem legendas, usar Whisper
        if not text:
            audio_path = project_root / "train" / "data" / segment['audio_path']
            text = transcribe_with_whisper(audio_path, config)
        
        # Preprocessar texto
        if text:
            text = preprocess_text(text, config)
        
        # Validar comprimento
        text_config = config['text_preprocessing']
        if len(text) < text_config['min_text_length']:
            logger.warning(f"   ⚠️  Texto muito curto ({len(text)} chars), pulando")
            continue
        
        if len(text) > text_config['max_text_length']:
            logger.warning(f"   ⚠️  Texto muito longo ({len(text)} chars), truncando")
            text = text[:text_config['max_text_length']]
        
        # Filtrar linhas com termos indesejados
        skip = False
        for term in text_config.get('remove_lines_with', []):
            if term.lower() in text.lower():
                logger.warning(f"   ⚠️  Termo indesejado encontrado: {term}, pulando")
                skip = True
                break
        
        if skip:
            continue
        
        # Adicionar transcrição
        transcriptions.append({
            **segment,
            'text': text,
            'char_count': len(text)
        })
        
        logger.info(f"   ✅ {len(text)} caracteres: {text[:80]}...\n")
    
    # Salvar transcrições
    transcriptions_file = processed_dir / "transcriptions.json"
    with open(transcriptions_file, 'w', encoding='utf-8') as f:
        json.dump(transcriptions, f, indent=2, ensure_ascii=False)
    
    # Summary
    logger.info("\n" + "=" * 80)
    logger.info("RESUMO DA TRANSCRIÇÃO")
    logger.info("=" * 80)
    logger.info(f"📝 Segmentos transcritos: {len(transcriptions)}")
    logger.info(f"📊 Legendas do YouTube: {len(subtitles_cache)} vídeos")
    logger.info(f"📄 Transcrições salvas em: {transcriptions_file}")
    logger.info("=" * 80)


if __name__ == "__main__":
    main()
