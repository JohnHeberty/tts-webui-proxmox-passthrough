"""
Download de áudio de vídeos do YouTube

Este script baixa o áudio dos vídeos listados em videos.csv,
converte para WAV mono 22050Hz (XTTS-v2) e salva em train/data/raw/.

Uso:
    python -m train.scripts.download_youtube

Dependências:
    - yt-dlp: pip install yt-dlp
    - ffmpeg: Deve estar instalado no sistema
"""

import csv
import logging
import os
from pathlib import Path
import sys
import time

import yaml


# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

try:
    import yt_dlp
except ImportError:
    print("❌ yt-dlp não encontrado. Instale com: pip install yt-dlp")
    sys.exit(1)

# Setup logging
os.makedirs(project_root / "train" / "logs", exist_ok=True)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler(project_root / "train" / "logs" / "download_youtube.log"),
        logging.StreamHandler(),
    ],
)
logger = logging.getLogger(__name__)


def load_config() -> dict:
    """Carrega configuração do dataset"""
    config_path = project_root / "train" / "config" / "dataset_config.yaml"
    with open(config_path, encoding="utf-8") as f:
        return yaml.safe_load(f)


def load_videos_catalog(csv_path: Path) -> list[dict]:
    """
    Carrega catálogo de vídeos do CSV

    Returns:
        Lista de dicts com informações dos vídeos
    """
    videos = []
    with open(csv_path, encoding="utf-8") as f:
        # Filtrar linhas de comentário e linhas vazias
        lines = []
        for line in f:
            stripped = line.strip()
            if stripped and not stripped.startswith("#"):
                lines.append(line)

        # Parse CSV
        reader = csv.DictReader(lines)
        for row in reader:
            if row.get("youtube_url", "").strip():  # Ignora linhas vazias
                videos.append(row)

    logger.info(f"📋 {len(videos)} vídeos encontrados no catálogo")
    return videos


def download_audio(video_info: dict, output_dir: Path, config: dict, force: bool = False) -> bool:
    """
    Baixa áudio de um vídeo do YouTube

    Args:
        video_info: Dict com informações do vídeo (id, youtube_url, etc.)
        output_dir: Diretório de saída
        config: Configuração do dataset
        force: Se True, redownload mesmo se já existir

    Returns:
        True se sucesso, False se falhou
    """
    video_id = video_info["id"]
    url = video_info["youtube_url"]

    # Nome do arquivo de saída (sem extensão, yt-dlp adiciona automaticamente)
    output_filename = f"video_{video_id.zfill(5)}"
    output_path = output_dir / f"{output_filename}.wav"

    # Skip se já existe (e não é force)
    if output_path.exists() and not force:
        logger.info(f"✓ {output_filename}.wav já existe (pulando)")
        return True

    # Get sample rate from config (XTTS-v2: 22050Hz)
    target_sr = config["audio"]["target_sample_rate"]

    # yt-dlp options
    ydl_opts = {
        "format": config["youtube"]["audio_format"],
        "outtmpl": str(output_dir / f"{output_filename}"),
        "noplaylist": True,  # Download only the video, not the playlist
        "postprocessors": [
            {
                "key": "FFmpegExtractAudio",
                "preferredcodec": "wav",
                "preferredquality": "0",
            }
        ],
        "postprocessor_args": [
            "-ar",
            str(target_sr),  # XTTS-v2: 22050Hz (não 24000!)
            "-ac",
            "1",  # mono
        ],
        "quiet": False,
        "no_warnings": False,
        "extract_flat": False,
        "retries": config["youtube"]["max_retries"],
        "fragment_retries": config["youtube"]["max_retries"],
    }

    # Download com retry logic
    max_retries = config["youtube"]["max_retries"]
    retry_delay = config["youtube"]["retry_delay"]

    for attempt in range(max_retries):
        try:
            logger.info(
                f"⬇️  Baixando [{video_id}]: {url} (tentativa {attempt + 1}/{max_retries})"
            )

            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                # Download
                info_dict = ydl.extract_info(url, download=True)
                title = info_dict.get("title", "Unknown")
                duration = info_dict.get("duration", 0)

                # Verificar se arquivo foi criado
                if not output_path.exists():
                    raise FileNotFoundError(
                        f"Arquivo {output_filename}.wav não foi criado após o download"
                    )

                logger.info(f"✅ {output_filename}.wav baixado com sucesso!")
                logger.info(f"   Título: {title}")
                logger.info(f"   Duração: {duration:.1f}s")

                return True

        except Exception as e:
            logger.error(f"❌ Erro ao baixar video_{video_id} (tentativa {attempt + 1}): {e}")

            if attempt < max_retries - 1:
                logger.info(f"⏳ Aguardando {retry_delay}s antes de tentar novamente...")
                time.sleep(retry_delay)
            else:
                logger.error(f"❌ Falha permanente ao baixar video_{video_id}")
                return False

    return False


def main():
    """Main function"""
    logger.info("=" * 80)
    logger.info("DOWNLOAD DE ÁUDIO DO YOUTUBE (XTTS-v2)")
    logger.info("=" * 80)

    # Load config
    config = load_config()
    logger.info(
        f"📝 Config carregada: {config['audio']['target_sample_rate']}Hz, "
        f"{config['audio']['channels']} canal(is)"
    )

    # Paths
    data_dir = project_root / "train" / "data"
    videos_csv = data_dir / "videos.csv"
    raw_dir = data_dir / "raw"

    # Criar diretório de saída
    raw_dir.mkdir(parents=True, exist_ok=True)

    # Verificar se ffmpeg está disponível
    try:
        import subprocess

        subprocess.run(["ffmpeg", "-version"], capture_output=True, check=True)
        logger.info("✓ ffmpeg encontrado")
    except (subprocess.CalledProcessError, FileNotFoundError):
        logger.error(
            "❌ ffmpeg não encontrado. Instale com: apt install ffmpeg (Linux) "
            "ou brew install ffmpeg (Mac)"
        )
        sys.exit(1)

    # Verificar se videos.csv existe
    if not videos_csv.exists():
        logger.error(f"❌ Arquivo não encontrado: {videos_csv}")
        logger.error("   Crie o arquivo videos.csv com a lista de vídeos do YouTube")
        logger.error("   Exemplo: copie de scripts/not_remove/videos.csv")
        sys.exit(1)

    # Carregar catálogo de vídeos
    videos = load_videos_catalog(videos_csv)

    if not videos:
        logger.warning("⚠️  Nenhum vídeo encontrado em videos.csv")
        logger.info("   Adicione URLs de vídeos do YouTube ao arquivo train/data/videos.csv")
        return

    # Download de cada vídeo
    logger.info(f"\n📥 Iniciando download de {len(videos)} vídeos...\n")

    success_count = 0
    failed_count = 0
    skipped_count = 0

    for i, video_info in enumerate(videos, 1):
        logger.info(f"\n[{i}/{len(videos)}] Processando vídeo {video_info['id']}...")

        output_filename = f"video_{video_info['id'].zfill(5)}.wav"
        output_path = raw_dir / output_filename

        if output_path.exists():
            logger.info(f"✓ {output_filename} já existe (pulando)")
            skipped_count += 1
            continue

        success = download_audio(video_info, raw_dir, config)

        if success:
            success_count += 1
        else:
            failed_count += 1

        # Pequeno delay entre downloads para evitar rate limiting
        if i < len(videos):
            time.sleep(2)

    # Summary
    logger.info("\n" + "=" * 80)
    logger.info("RESUMO DO DOWNLOAD")
    logger.info("=" * 80)
    logger.info(f"✅ Sucessos: {success_count}")
    logger.info(f"⏭️  Pulados (já existentes): {skipped_count}")
    logger.info(f"❌ Falhas: {failed_count}")
    logger.info(f"📁 Arquivos salvos em: {raw_dir}")
    logger.info("=" * 80)


if __name__ == "__main__":
    main()
