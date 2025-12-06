"""
Transcrição de áudio usando legendas do YouTube ou Whisper (XTTS-v2)

Este script:
1. Tenta baixar legendas do YouTube (se disponíveis)
2. Se não houver legendas, usa Whisper para transcrever
3. Aplica preprocessamento de texto (lowercase, normalização pt-BR etc.)
4. Opcionalmente, se o texto parecer muito "quebrado" (muitas palavras
   fora do vocabulário pt-BR) e veio do Whisper, retranscreve usando
   um modelo Whisper mais preciso.

Uso:
    python -m train.scripts.transcribe_audio

Dependências:
    - yt-dlp: pip install yt-dlp
    - whisper: pip install openai-whisper
    - num2words: pip install num2words
"""

import csv
import json
import logging
from pathlib import Path
import re
import sys

import yaml


# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

try:
    from num2words import num2words
    import whisper
    import yt_dlp
except ImportError as e:
    print(f"❌ Dependência não encontrada: {e}")
    print("Instale com: pip install yt-dlp openai-whisper num2words")
    sys.exit(1)

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[logging.FileHandler("train/logs/transcribe.log"), logging.StreamHandler()],
)
logger = logging.getLogger(__name__)

# Cache global do(s) modelo(s) Whisper para não recarregar a cada segmento
_WHISPER_MODEL = None  # modelo padrão
_WHISPER_HP_MODEL = None  # modelo de alta precisão (opcional)

# Vocabulário PT-BR básico embutido
_COMMON_PT_WORDS = {
    # Artigos / pronomes / preposições / conjunções
    "a",
    "o",
    "as",
    "os",
    "um",
    "uma",
    "uns",
    "umas",
    "de",
    "do",
    "da",
    "dos",
    "das",
    "em",
    "no",
    "na",
    "nos",
    "nas",
    "por",
    "para",
    "com",
    "sem",
    "sobre",
    "entre",
    "e",
    "ou",
    "mas",
    "porque",
    "que",
    "se",
    "quando",
    "eu",
    "tu",
    "ele",
    "ela",
    "nós",
    "vos",
    "eles",
    "elas",
    "me",
    "te",
    "lhe",
    "lhes",
    "isso",
    "isto",
    "aquilo",
    "aqui",
    "ali",
    "lá",
    # Verbos comuns
    "ser",
    "estar",
    "ter",
    "haver",
    "fazer",
    "ir",
    "vir",
    "poder",
    "dizer",
    "ver",
    "dar",
    "ficar",
    "querer",
    "saber",
    "dever",
    "passar",
    "chegar",
    "deixar",
    "precisar",
    # Coisas básicas
    "sim",
    "não",
    "talvez",
    "claro",
    "obrigado",
    "obrigada",
    "bom",
    "boa",
    "melhor",
    "pior",
    "grande",
    "pequeno",
    # Números por extenso
    "zero",
    "dois",
    "três",
    "quatro",
    "cinco",
    "seis",
    "sete",
    "oito",
    "nove",
    "dez",
    "onze",
    "doze",
    "treze",
    "quatorze",
    "quinze",
    "dezesseis",
    "dezessete",
    "dezoito",
    "dezenove",
    "vinte",
    "trinta",
    "quarenta",
    "cinquenta",
    "sessenta",
    "setenta",
    "oitenta",
    "noventa",
    "cem",
    "cento",
    "duzentos",
    "trezentos",
    "quatrocentos",
    "quinhentos",
    "seiscentos",
    "setecentos",
    "oitocentos",
    "novecentos",
    "mil",
    "milhão",
    "milhões",
    # Símbolos falados
    "arroba",
    "porcento",
    "barra",
    "mais",
    "menos",
    "dólar",
}
_PT_BR_VOCAB = None  # será carregado lazy a partir do embed + arquivo opcional


def load_config() -> dict:
    """Carrega configuração do dataset"""
    config_path = project_root / "train" / "config" / "dataset_config.yaml"
    with open(config_path, encoding="utf-8") as f:
        return yaml.safe_load(f)


def load_videos_catalog(csv_path: Path) -> dict[str, dict]:
    """
    Carrega catálogo de vídeos do CSV, ignorando linhas comentadas (#)
    e linhas vazias.

    Retorna:
        Dict mapeando video_id (coluna 'id') -> row completa do CSV
    """
    videos: dict[str, dict] = {}

    if not csv_path.exists():
        logger.warning(f"⚠️ Arquivo de vídeos não encontrado: {csv_path}")
        return videos

    with open(csv_path, encoding="utf-8") as f:
        # Ignorar comentários e linhas vazias antes de passar para o DictReader
        filtered_lines = (line for line in f if line.strip() and not line.lstrip().startswith("#"))

        reader = csv.DictReader(filtered_lines)
        for row in reader:
            youtube_url = (row.get("youtube_url") or "").strip()
            vid = (row.get("id") or "").strip()

            # Pula linhas sem id ou sem youtube_url
            if not vid or not youtube_url:
                continue

            videos[vid] = row

    logger.info(f"📄 Catálogo de vídeos carregado: {len(videos)} entradas")
    return videos


def download_youtube_subtitles(
    youtube_url: str, output_dir: Path, video_id: str, config: dict
) -> Path | None:
    """
    Tenta baixar legendas do YouTube.

    Em caso de HTTP 429 (rate limit), lança RuntimeError("YOUTUBE_RATE_LIMIT_429")
    para que o caller possa interromper o processo de legendas e seguir só com Whisper.
    """
    subtitle_config = config["youtube"]["subtitles"]

    # Nome do arquivo de saída
    output_template = str(output_dir / f"video_{video_id.zfill(5)}")

    # yt-dlp options
    ydl_opts = {
        "skip_download": True,
        "writesubtitles": True,
        "writeautomaticsub": subtitle_config.get("download_auto_subs", True),
        "subtitleslangs": subtitle_config.get("subtitle_langs", ["pt"]),
        "subtitlesformat": subtitle_config.get("subtitle_formats", ["vtt"])[0],
        "outtmpl": output_template,
        "quiet": True,
        # Tenta reduzir exigência de JS runtime / impersonation
        "extractor_args": {"youtube": ["player_client=default"]},
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([youtube_url])

        # Procurar arquivo de legendas gerado
        for ext in subtitle_config.get("subtitle_formats", ["vtt", "srt"]):
            for lang in subtitle_config.get("subtitle_langs", ["pt"]):
                subtitle_file = Path(f"{output_template}.{lang}.{ext}")
                if subtitle_file.exists():
                    logger.info(f"   ✅ Legendas encontradas: {subtitle_file.name}")
                    return subtitle_file

        logger.warning(f"   ⚠️  Legendas não encontradas para video_{video_id}")
        return None

    except Exception as e:
        msg = str(e)
        # Se for rate limit, sinaliza pro caller parar de insistir
        if "HTTP Error 429" in msg:
            logger.error(
                "   ❌ YouTube retornou HTTP 429 (Too Many Requests) ao tentar baixar legendas."
            )
            # Sinaliza explicitamente pro laço externo parar
            raise RuntimeError("YOUTUBE_RATE_LIMIT_429")
        # Outros erros: apenas loga e segue
        logger.warning(f"   ⚠️  Erro ao baixar legendas: {e}")
        return None


def parse_subtitle_file(subtitle_path: Path) -> str:
    """
    Extrai texto de arquivo de legendas (VTT ou SRT)
    """
    with open(subtitle_path, encoding="utf-8") as f:
        content = f.read()

    # Remover cabeçalho VTT
    content = re.sub(r"WEBVTT.*?\n\n", "", content, flags=re.DOTALL)

    # Remover números de sequência e timestamps
    content = re.sub(r"\n\d+\n", "\n", content)
    content = re.sub(
        r"\d{2}:\d{2}:\d{2}[,.]\d{3}\s*-->\s*\d{2}:\d{2}:\d{2}[,.]\d{3}.*?\n", "", content
    )

    # Remover tags HTML (<c>, <i>, etc.)
    content = re.sub(r"<[^>]+>", "", content)

    # Remover linhas vazias múltiplas
    content = re.sub(r"\n\n+", "\n", content)

    return content.strip()


def transcribe_with_whisper(audio_path: Path, config: dict, high_precision: bool = False) -> str:
    """
    Transcreve áudio usando Whisper.

    Se high_precision=True, usa whisper_hp_model; caso contrário, usa whisper_model padrão.
    """
    global _WHISPER_MODEL, _WHISPER_HP_MODEL

    trans_config = config["transcription"]
    
    # Auto-detect device (CUDA se disponível, senão CPU)
    import torch
    device = "cuda" if torch.cuda.is_available() else "cpu"

    if high_precision and trans_config.get("whisper_hp_model"):
        # Modelo de alta precisão separado
        model_name = trans_config["whisper_hp_model"]
        if _WHISPER_HP_MODEL is None:
            logger.info(f"   🎤 Carregando modelo Whisper de alta precisão ({model_name})...")
            try:
                _WHISPER_HP_MODEL = whisper.load_model(model_name, device=device)
            except Exception as e:
                logger.error(f"   ❌ Erro ao carregar modelo Whisper de alta precisão: {e}")
                return ""
        model = _WHISPER_HP_MODEL
        logger.info("   🎧 Retranscrevendo com modelo de alta precisão...")
    else:
        # Modelo padrão
        model_name = trans_config.get("whisper_model", "base")
        if _WHISPER_MODEL is None:
            logger.info(f"   🎤 Carregando modelo Whisper ({model_name})...")
            try:
                _WHISPER_MODEL = whisper.load_model(model_name, device=device)
            except Exception as e:
                logger.error(f"   ❌ Erro ao carregar modelo Whisper: {e}")
                return ""
        model = _WHISPER_MODEL

    # Parâmetros de transcrição
    language = trans_config.get("language", "pt")
    temperature = trans_config.get("temperature", 0.0)

    try:
        result = model.transcribe(
            str(audio_path),
            language=language,
            temperature=temperature,
        )

        return result.get("text", "").strip()

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

    Faz:
      - 3%     -> "três porcento"
      - 2025   -> "dois mil e vinte e cinco"
      - b80    -> "oitenta" (por causa da limpeza de ruído + normalização)
      - 80mil  -> "oitenta mil" (pois converte "80" mesmo grudado)

    Também garante que os números não ficam colados em letras
    (tipo "pdoisp"), inserindo espaços quando necessário.
    """
    lang = text_config.get("numbers_lang", "pt_BR")

    # 0) Ruído comum: letra solta grudada em número (b80, k200, etc.)
    #    Remove a letra e deixa só o número.
    text = re.sub(r"\b([bcdfghjklmnpqrstvwxyz])(?=\d)", "", text, flags=re.IGNORECASE)

    # 1) Casos especiais: número seguido de %  -> "três porcento"
    def repl_number_percent(match: re.Match) -> str:
        num_str = match.group(1)
        try:
            n = int(num_str)
            ext = num2words(n, lang=lang)
            return f"{ext} porcento"
        except Exception:
            return match.group(0)

    text = re.sub(r"\b(\d+)\s*%", repl_number_percent, text)

    # 2) Substituir símbolos isolados por forma falada
    def repl_symbol(match: re.Match) -> str:
        s = match.group(0)
        word = SYMBOLS_TO_WORDS_PT_BR.get(s)
        if not word:
            return " "
        # sempre coloca espaços ao redor pra não colar
        return f" {word} "

    text = re.sub(r"[@%&+\-/#$=]", repl_symbol, text)

    # 3) Números em geral (em qualquer lugar, mesmo grudados em letras)
    #    Usa contexto pra inserir espaços quando precisa.
    def repl_number(match: re.Match) -> str:
        num_str = match.group(0)
        try:
            n = int(num_str)
            spoken = num2words(n, lang=lang)
        except Exception:
            return num_str

        start, end = match.span()
        src = match.string  # string original usada nesse re.sub

        # Caracter anterior e posterior (no texto original)
        before = src[start - 1] if start > 0 else " "
        after = src[end] if end < len(src) else " "

        # Precisamos de espaço à esquerda se antes é letra ou número
        add_left_space = before.isalnum()

        # Precisamos de espaço à direita se depois é letra ou número
        add_right_space = after.isalnum()

        result = spoken
        if add_left_space:
            result = " " + result
        if add_right_space:
            result = result + " "

        return result

    # \d+ pega QUALQUER sequência de dígitos, mesmo dentro de "abc123def"
    text = re.sub(r"\d+", repl_number, text)

    return text


def _cleanup_segment_edges(text: str, text_config: dict) -> str:
    """
    Remove pedaços claramente bugados no começo/fim do segmento,
    normalmente causados por cortes no meio das palavras.
    """
    words = text.split()
    if not words:
        return text

    def is_probably_broken(w: str) -> bool:
        # remover pontuação para análise
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

    # Aplica limpeza apenas se ativado na config (default: True)
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
    - Vocabulário básico embutido (_COMMON_PT_WORDS)
    - Opcional: arquivo externo text_preprocessing.vocab_file (um termo por linha)
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
                with open(vocab_path, encoding="utf-8") as f:
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
    baseado na proporção de palavras fora do vocabulário pt-BR.
    """
    text_config = config["text_processing"]

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
    - remoção de caracteres especiais
    - limpeza de bordas bugadas (segmentos cortados)
    """
    text_config = config["text_processing"]

    # 1) Lowercase
    if text_config.get("lowercase", True):
        text = text.lower()

    # 2) Normalizar números e símbolos primeiro (para não perder %/@ etc)
    text = _normalize_numbers_and_symbols(text, text_config)

    # 3) Normalizar pontuação via tabela de replacements
    if text_config.get("normalize_punctuation", True):
        for old, new in text_config.get("replacements", {}).items():
            text = text.replace(old, new)

    # 4) Remover caracteres especiais não permitidos (se configurado)
    if text_config.get("remove_special_chars", False):
        allowed_chars = text_config.get("allowed_chars")
        if allowed_chars:
            allowed = set(allowed_chars)
            text = "".join(c if c in allowed else " " for c in text)

    # 5) Remover espaços múltiplos
    text = re.sub(r"\s+", " ", text).strip()

    # 6) Limpar bordas bugadas de segmento (palavras estranhas no começo/fim)
    text = _cleanup_segment_edges(text, text_config)

    # 7) Espaços finais
    text = re.sub(r"\s+", " ", text).strip()

    return text


def get_subtitle_for_segment(segment_info: dict, subtitles_text: str, config: dict) -> str:
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
    with open(segments_mapping_file, encoding="utf-8") as f:
        segments = json.load(f)

    logger.info(f"📋 {len(segments)} segmentos para transcrever\n")

    # Carregar catálogo de vídeos
    videos_catalog = load_videos_catalog(videos_csv)

    # Passo 1: Tentar baixar legendas do YouTube
    logger.info("=" * 80)
    logger.info("ETAPA 1: DOWNLOAD DE LEGENDAS DO YOUTUBE")
    logger.info("=" * 80 + "\n")

    subtitles_cache: dict[str, str] = {}

    if config["transcription"].get("prefer_youtube_subtitles", True):
        rate_limited = False

        for video_id, video_info in videos_catalog.items():
            if rate_limited:
                break

            logger.info(f"🔍 Buscando legendas para video_{video_id}...")

            try:
                subtitle_file = download_youtube_subtitles(
                    video_info["youtube_url"], subtitles_dir, video_id, config
                )
            except RuntimeError as e:
                # Se recebemos o sentinela de rate limit (429), paramos o loop
                if str(e) == "YOUTUBE_RATE_LIMIT_429":
                    logger.warning(
                        "⚠️ YouTube aplicou rate limit (HTTP 429). "
                        "Parando download de legendas e prosseguindo apenas com Whisper "
                        "para os demais segmentos desta execução."
                    )
                    rate_limited = True
                    break
                else:
                    # Qualquer outro erro inesperado, re-levanta
                    raise

            if subtitle_file:
                subtitle_text = parse_subtitle_file(subtitle_file)
                subtitles_cache[video_id] = subtitle_text
                logger.info(f"   ✅ {len(subtitle_text)} caracteres extraídos\n")

        logger.info(f"📄 Legendas carregadas para {len(subtitles_cache)} vídeos\n")

    # Passo 2: Transcrever segmentos
    logger.info("\n" + "=" * 80)
    logger.info("ETAPA 2: TRANSCRIÇÃO DE SEGMENTOS")
    logger.info("=" * 80 + "\n")

    transcriptions: list[dict] = []

    for i, segment in enumerate(segments, 1):
        logger.info(f"[{i}/{len(segments)}] {segment['audio_path']}")

        # Caminho do áudio do segmento
        audio_path = project_root / "train" / "data" / segment["audio_path"]

        # Extrair video_id do nome do arquivo original (ex: video_00001.wav)
        original_file = segment["original_file"]
        try:
            video_id_part = original_file.split("_")[1].split(".")[0]
        except IndexError:
            video_id_part = "0"
        video_id = video_id_part.lstrip("0") or "0"

        text = ""
        from_whisper = False

        # Tentar usar legendas se disponíveis
        if video_id in subtitles_cache:
            logger.info("   📝 Usando legendas do YouTube")
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

        # Se veio do Whisper e parece ruim (muito OOV), tenta retranscrever com modelo mais preciso
        if text and from_whisper and _should_retry_with_high_precision(text, config):
            logger.info("   🔁 Texto suspeito, retranscrevendo com modelo Whisper mais preciso...")
            text_hp_raw = transcribe_with_whisper(audio_path, config, high_precision=True)
            if text_hp_raw:
                text = preprocess_text(text_hp_raw, config)

        # Validações de comprimento
        text_config = config["text_processing"]
        min_len = text_config.get("min_text_length", 1)
        max_len = text_config.get("max_text_length", 10_000)

        if len(text) < min_len:
            logger.warning(f"   ⚠️  Texto muito curto ({len(text)} chars), pulando")
            continue

        if len(text) > max_len:
            logger.warning(f"   ⚠️  Texto muito longo ({len(text)} chars), truncando")
            text = text[:max_len]

        # Opcional: validar número mínimo de palavras (se configurado)
        min_word_count = text_config.get("min_word_count")
        if min_word_count is not None:
            word_count = len(text.split())
            if word_count < int(min_word_count):
                logger.warning(
                    f"   ⚠️  Poucas palavras ({word_count}), min_word_count={min_word_count}, pulando"
                )
                continue

        # Filtrar linhas com termos indesejados
        skip = False
        for term in text_config.get("remove_lines_with", []):
            if term.lower() in text.lower():
                logger.warning(f"   ⚠️  Termo indesejado encontrado: {term}, pulando")
                skip = True
                break

        if skip:
            continue

        # Adicionar transcrição final
        transcriptions.append({**segment, "text": text, "char_count": len(text)})

        logger.info(f"   ✅ {len(text)} caracteres: {text[:80]}...\n")

    # Salvar transcrições
    transcriptions_file = processed_dir / "transcriptions.json"
    with open(transcriptions_file, "w", encoding="utf-8") as f:
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
