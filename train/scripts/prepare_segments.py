"""
Transcrição de áudio usando legendas do YouTube ou Whisper

Este script:
1. Tenta baixar legendas do YouTube (se disponíveis)
2. Se não houver legendas, usa Whisper para transcrever
3. Aplica preprocessamento de texto (lowercase, normalização pt-BR etc.)
4. Opcionalmente, se o texto parecer muito "quebrado" (muitas palavras
   fora do vocabulário pt-BR) e veio do Whisper, retranscreve usando
   um modelo Whisper mais preciso.

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

# Cache global do modelo Whisper para não recarregar a cada segmento
_WHISPER_MODEL = None
_WHISPER_HP_MODEL = None

# Vocabulário PT-BR básico embutido (pode ser expandido via arquivo externo)
_COMMON_PT_WORDS = {
    # Artigos / pronomes / preposições / conjunções
    "a", "o", "as", "os", "um", "uma", "uns", "umas",
    "de", "do", "da", "dos", "das",
    "em", "no", "na", "nos", "nas",
    "por", "para", "com", "sem", "sobre", "entre",
    "e", "ou", "mas", "porque", "que", "se", "quando",
    "eu", "tu", "ele", "ela", "nós", "vos", "eles", "elas",
    "me", "te", "lhe", "nos", "vos", "lhes",
    "isso", "isto", "aquilo", "aqui", "ali", "lá",

    # Verbos comuns
    "ser", "estar", "ter", "haver", "fazer", "ir", "vir",
    "poder", "dizer", "ver", "dar", "ficar", "querer",
    "saber", "dever", "passar", "chegar", "deixar", "precisar",

    # Coisas básicas
    "sim", "não", "talvez", "claro", "obrigado", "obrigada",
    "bom", "boa", "melhor", "pior", "grande", "pequeno",

    # Números (coerentes com num2words pt_BR)
    "zero", "um", "dois", "três", "quatro", "cinco", "seis",
    "sete", "oito", "nove", "dez", "onze", "doze", "treze",
    "quatorze", "quinze", "dezesseis", "dezessete", "dezoito", "dezenove",
    "vinte", "trinta", "quarenta", "cinquenta", "sessenta", "setenta",
    "oitenta", "noventa",
    "cem", "cento", "duzentos", "trezentos", "quatrocentos",
    "quinhentos", "seiscentos", "setecentos", "oitocentos", "novecentos",
    "mil", "milhão", "milhões",

    # Símbolos falados
    "arroba", "porcento", "barra", "mais", "menos", "dólar",
}
_PT_BR_VOCAB = None  # carregado lazy a partir de _COMMON_PT_WORDS + arquivo, se existir


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
    """
    subtitle_config = config['youtube']['subtitles']

    # Nome do arquivo de saída
    output_template = str(output_dir / f'video_{video_id.zfill(5)}')

    # yt-dlp options
    ydl_opts = {
        'skip_download': True,
        'writesubtitles': True,
        'writeautomaticsub': subtitle_config.get('download_auto_subs', True),
        'subtitleslangs': subtitle_config.get('subtitle_langs', ['pt']),
        'subtitlesformat': subtitle_config.get('subtitle_formats', ['vtt'])[0],
        'outtmpl': output_template,
        'quiet': True,
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([youtube_url])

        # Procurar arquivo de legendas gerado
        for ext in subtitle_config.get('subtitle_formats', ['vtt', 'srt']):
            for lang in subtitle_config.get('subtitle_langs', ['pt']):
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
    """
    with open(subtitle_path, 'r', encoding='utf-8') as f:
        content = f.read()

    # Remover cabeçalho VTT
    content = re.sub(r'WEBVTT.*?\n\n', '', content, flags=re.DOTALL)

    # Remover números de sequência (linhas só com número)
    content = re.sub(r'\n\d+\n', '\n', content)

    # Remover timestamps
    content = re.sub(
        r'\d{2}:\d{2}:\d{2}[,.]\d{3}\s*-->\s*\d{2}:\d{2}:\d{2}[,.]\d{3}.*?\n',
        '',
        content
    )

    # Remover tags HTML (<c>, <i>, etc.)
    content = re.sub(r'<[^>]+>', '', content)

    # Remover linhas vazias múltiplas
    content = re.sub(r'\n\n+', '\n', content)

    return content.strip()


def transcribe_with_whisper(
    audio_path: Path,
    config: dict,
    high_precision: bool = False
) -> str:
    """
    Transcreve áudio usando Whisper.

    Se high_precision=True e um modelo mais preciso estiver configurado
    (transcription.asr.high_precision_model), usa esse modelo e pode
    usar parâmetros mais pesados (hp_beam_size, hp_best_of, hp_temperature).
    """
    global _WHISPER_MODEL, _WHISPER_HP_MODEL

    asr_config = config['transcription']['asr']
    device = asr_config.get('device', 'cuda')

    if high_precision and asr_config.get('high_precision_model'):
        # Modelo de alta precisão
        model_name = asr_config['high_precision_model']
        if _WHISPER_HP_MODEL is None:
            logger.info(f"   🎤 Carregando modelo Whisper de alta precisão ({model_name})...")
            try:
                _WHISPER_HP_MODEL = whisper.load_model(model_name, device=device)
            except Exception as e:
                logger.error(f"   ❌ Erro ao carregar modelo Whisper de alta precisão: {e}")
                return ""
        model = _WHISPER_HP_MODEL
        beam_size = asr_config.get('hp_beam_size', asr_config.get('beam_size', 5))
        best_of = asr_config.get('hp_best_of', asr_config.get('best_of', 5))
        temperature = asr_config.get('hp_temperature', asr_config.get('temperature', 0.0))
        logger.info("   🎧 Retranscrevendo com modelo de alta precisão...")
    else:
        # Modelo padrão
        model_name = asr_config['model']
        if _WHISPER_MODEL is None:
            logger.info(f"   🎤 Carregando modelo Whisper ({model_name})...")
            try:
                _WHISPER_MODEL = whisper.load_model(model_name, device=device)
            except Exception as e:
                logger.error(f"   ❌ Erro ao carregar modelo Whisper: {e}")
                return ""
        model = _WHISPER_MODEL
        beam_size = asr_config.get('beam_size', 5)
        best_of = asr_config.get('best_of', 5)
        temperature = asr_config.get('temperature', 0.0)
        if high_precision:
            logger.info("   🎧 Retranscrevendo com mesmo modelo, mas parâmetros mais precisos...")

    try:
        result = model.transcribe(
            str(audio_path),
            language=asr_config.get('language', 'pt'),
            task=asr_config.get('task', 'transcribe'),
            beam_size=beam_size,
            best_of=best_of,
            temperature=temperature,
        )
        return result.get('text', '').strip()
    except Exception as e:
        logger.error(f"   ❌ Erro ao transcrever com Whisper: {e}")
        return ""


# ==========================
# NORMALIZAÇÃO DE TEXTO PT-BR
# ==========================

# Mapeamento de símbolos para forma falada
SYMBOLS_TO_WORDS_PT_BR = {
    "@": "arroba",
    "%": "porcento",
    "&": "e comercial",
    "+": "mais",
    "-": "menos",
    "/": "barra",
    "#": "jogo da velha",
    "$": "dólar",
    "=": "igual",
}


def _normalize_numbers_and_symbols(text: str, text_config: dict) -> str:
    """
    Normaliza números e símbolos em PT-BR de forma inteligente.

    Exemplos:
        "3%"   -> "três porcento"
        "2025" -> "dois mil e vinte e cinco"
        "email@dominio.com" -> "email arroba dominio ponto com"
    """
    lang = text_config.get('numbers_lang', 'pt_BR')

    # 1) Casos especiais: número seguido de %
    def repl_number_percent(match: re.Match) -> str:
        num_str = match.group(1)
        try:
            n = int(num_str)
            ext = num2words(n, lang=lang)
            return f"{ext} porcento"
        except Exception:
            return match.group(0)

    text = re.sub(r"\b(\d+)\s*%", repl_number_percent, text)

    # 2) Substituir símbolos isolados ou misturados
    def repl_symbol(match: re.Match) -> str:
        s = match.group(0)
        word = SYMBOLS_TO_WORDS_PT_BR.get(s)
        if not word:
            return " "
        # Garante que não grude nas palavras vizinhas
        return f" {word} "

    text = re.sub(r"[@%&+\-/#$=]", repl_symbol, text)

    # 3) Números "puros": 1 -> um, 2025 -> dois mil e vinte e cinco
    if text_config.get('convert_numbers_to_words', True):
        def repl_number(match: re.Match) -> str:
            num_str = match.group(0)
            try:
                n = int(num_str)
                return num2words(n, lang=lang)
            except Exception:
                return num_str

        text = re.sub(r"\b\d+\b", repl_number, text)

    return text


def _cleanup_segment_edges(text: str, text_config: dict) -> str:
    """
    Remove pedaços claramente bugados no começo/fim do segmento,
    normalmente causados por cortes no meio das palavras.

    Heurísticas:
    - Remove palavras do início/fim que:
        * tenham >= 3 letras e nenhuma vogal (ex: "lkj", "pff")
        * tenham 1 letra que não seja artigo/conjunção comum ("a", "e", "o", "é")
    """
    words = text.split()
    if not words:
        return text

    def is_probably_broken(w: str) -> bool:
        w_clean = re.sub(r"[^a-záéíóúâêôãõç]", "", w)
        if not w_clean:
            return False

        # só consoantes e tamanho >= 3 -> provavelmente bug
        if len(w_clean) >= 3 and not re.search(r"[aeiouáéíóúâêôãõ]", w_clean):
            return True

        # tokens de 1 letra que não são comuns em pt-BR
        if len(w_clean) == 1 and w_clean not in {"a", "e", "o", "é"}:
            return True

        return False

    if not text_config.get("cleanup_segment_edges", True):
        return text

    # Limpa início
    while words and is_probably_broken(words[0]):
        words.pop(0)

    # Limpa fim
    while words and is_probably_broken(words[-1]):
        words.pop()

    return " ".join(words)


def _get_pt_vocab(text_config: dict) -> set:
    """
    Retorna um set de palavras válidas em pt-BR.

    Usa:
    - Um vocabulário básico embutido (_COMMON_PT_WORDS)
    - Opcional: um arquivo de vocabulário extra (um termo por linha),
      configurado em text_preprocessing.vocab_file.
    """
    global _PT_BR_VOCAB
    if _PT_BR_VOCAB is not None:
        return _PT_BR_VOCAB

    vocab = set(w.lower() for w in _COMMON_PT_WORDS)

    vocab_file = text_config.get("vocab_file")
    if vocab_file:
        vocab_path = Path(vocab_file)
        if not vocab_path.is_absolute():
            vocab_path = project_root / vocab_file
        if vocab_path.exists():
            try:
                with open(vocab_path, 'r', encoding='utf-8') as f:
                    for line in f:
                        w = line.strip().lower()
                        if w:
                            vocab.add(w)
                logger.info(f"   📚 Vocabulário extra carregado: {vocab_path}")
            except Exception as e:
                logger.warning(f"   ⚠️  Erro ao carregar vocab_file {vocab_path}: {e}")
        else:
            logger.warning(f"   ⚠️  vocab_file não encontrado: {vocab_path}")

    _PT_BR_VOCAB = vocab
    return _PT_BR_VOCAB


def _should_retry_with_high_precision(text: str, config: dict) -> bool:
    """
    Decide se vale a pena retranscrever com modelo mais preciso,
    baseado em proporção de palavras fora do vocabulário pt-BR.
    """
    text_config = config['text_preprocessing']

    if not text_config.get("retranscribe_on_oov", True):
        return False

    words = re.findall(r"[a-záéíóúâêôãõç]+", text.lower())
    # Ignorar tokens de 1 letra, exceto alguns comuns
    words = [w for w in words if len(w) > 1 or w in {"a", "e", "o", "é"}]

    min_total = int(text_config.get("oov_min_total_words", 8))
    if len(words) < min_total:
        return False

    vocab = _get_pt_vocab(text_config)
    if not vocab:
        return False

    unknown = [w for w in words if w not in vocab]
    unknown_count = len(unknown)
    if unknown_count == 0:
        return False

    ratio = unknown_count / len(words)
    max_ratio = float(text_config.get("oov_ratio_threshold", 0.6))  # 60% default
    min_unknowns = int(text_config.get("oov_min_unknowns", 4))

    if unknown_count >= min_unknowns and ratio >= max_ratio:
        logger.info(
            f"   🔍 OOV detectado: {unknown_count}/{len(words)} palavras desconhecidas "
            f"({ratio:.0%}), acima dos limites ({min_unknowns}, {max_ratio:.0%})"
        )
        # Loga algumas desconhecidas para debug
        logger.info(f"   Exemplos de OOV: {', '.join(unknown[:10])}")
        return True

    return False


def preprocess_text(text: str, config: dict) -> str:
    """
    Preprocessa texto conforme recomendações do F5-TTS pt-br

    Inclui:
    - lowercase
    - normalização de números e símbolos (pt-BR)
    - normalização de pontuação
    - remoção de caracteres especiais (opcional)
    - limpeza de bordas bugadas (segmentos cortados)
    """
    text_config = config['text_preprocessing']

    # 1) Lowercase
    if text_config.get('lowercase', True):
        text = text.lower()

    # 2) Normalizar números e símbolos primeiro (para não perder %/@ etc)
    text = _normalize_numbers_and_symbols(text, text_config)

    # 3) Normalizar pontuação via tabela de replacements
    if text_config.get('normalize_punctuation', True):
        for old, new in text_config.get('replacements', {}).items():
            text = text.replace(old, new)

    # 4) Remover caracteres especiais não permitidos (se configurado)
    if text_config.get('remove_special_chars', False):
        allowed_chars = text_config.get('allowed_chars')
        if allowed_chars:
            allowed = set(allowed_chars)
            text = ''.join(c if c in allowed else ' ' for c in text)

    # 5) Remover espaços múltiplos
    text = re.sub(r'\s+', ' ', text).strip()

    # 6) Limpar bordas bugadas de segmento (palavras estranhas no começo/fim)
    text = _cleanup_segment_edges(text, text_config)

    # 7) Espaços finais
    text = re.sub(r'\s+', ' ', text).strip()

    return text


def get_subtitle_for_segment(
    segment_info: dict,
    subtitles_text: str,
    config: dict
) -> str:
    """
    Extrai trecho de legenda correspondente a um segmento de áudio.

    ATUALMENTE: retorna o texto completo.
    TODO: implementar parsing de timestamps para matching mais preciso.
    """
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

    subtitles_cache: Dict[str, str] = {}

    if config['transcription'].get('prefer_youtube_subtitles', True):
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

    transcriptions: List[dict] = []

    for i, segment in enumerate(segments, 1):
        logger.info(f"[{i}/{len(segments)}] {segment['audio_path']}")

        # Caminho do áudio do segmento
        audio_path = project_root / "train" / "data" / segment['audio_path']

        # Extrair video_id do nome do arquivo original (ex: video_00001.wav)
        original_file = segment['original_file']
        try:
            video_id_part = original_file.split('_')[1].split('.')[0]
        except IndexError:
            video_id_part = "0"
        video_id = video_id_part.lstrip('0') or '0'

        text = ""
        from_whisper = False

        # Tentar usar legendas se disponíveis
        if video_id in subtitles_cache:
            logger.info(f"   📝 Usando legendas do YouTube")
            text = get_subtitle_for_segment(segment, subtitles_cache[video_id], config)
            from_whisper = False

        # Se não tem legendas, usar Whisper
        if not text:
            text_raw = transcribe_with_whisper(audio_path, config, high_precision=False)
            text = text_raw
            from_whisper = True

        # Preprocessar texto
        if text:
            text = preprocess_text(text, config)

        # Se veio do Whisper e o texto parece ruim (muitas palavras OOV),
        # tenta retranscrever com modelo mais preciso
        if text and from_whisper and _should_retry_with_high_precision(text, config):
            logger.info("   🔁 Texto suspeito, retranscrevendo com modelo Whisper mais preciso...")
            text_hp_raw = transcribe_with_whisper(audio_path, config, high_precision=True)
            if text_hp_raw:
                text = preprocess_text(text_hp_raw, config)

        # Validações de comprimento
        text_config = config['text_preprocessing']
        min_len = text_config.get('min_text_length', 1)
        max_len = text_config.get('max_text_length', 10_000)

        if len(text) < min_len:
            logger.warning(f"   ⚠️  Texto muito curto ({len(text)} chars), pulando")
            continue

        if len(text) > max_len:
            logger.warning(f"   ⚠️  Texto muito longo ({len(text)} chars), truncando")
            text = text[:max_len]

        # Opcional: validar número mínimo de palavras (se configurado)
        min_word_count = text_config.get('min_word_count')
        if min_word_count is not None:
            word_count = len(text.split())
            if word_count < int(min_word_count):
                logger.warning(
                    f"   ⚠️  Poucas palavras ({word_count}), min_word_count={min_word_count}, pulando"
                )
                continue

        # Filtrar linhas com termos indesejados
        skip = False
        for term in text_config.get('remove_lines_with', []):
            if term.lower() in text.lower():
                logger.warning(f"   ⚠️  Termo indesejado encontrado: {term}, pulando")
                skip = True
                break

        if skip:
            continue

        # Adicionar transcrição final
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
