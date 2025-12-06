"""
YouTube Download Module

Functions for downloading audio from YouTube videos.

Author: F5-TTS Training Pipeline
Sprint: 3 - Dataset Consolidation
"""

from dataclasses import dataclass
import logging
from pathlib import Path
import time


logger = logging.getLogger(__name__)

# Optional dependency
try:
    import yt_dlp
except ImportError:
    yt_dlp = None


@dataclass
class VideoInfo:
    """Information about a YouTube video."""

    id: str
    title: str
    duration: float  # seconds
    url: str
    thumbnail_url: str | None = None
    uploader: str | None = None
    upload_date: str | None = None

    def __str__(self):
        return f"VideoInfo('{self.title}', {self.duration:.1f}s, {self.url})"


def get_video_info(url: str) -> VideoInfo:
    """
    Get information about a YouTube video without downloading it.

    Args:
        url: YouTube video URL

    Returns:
        VideoInfo object with video metadata

    Raises:
        ImportError: If yt-dlp is not installed
        RuntimeError: If video info cannot be retrieved

    Example:
        >>> info = get_video_info("https://youtube.com/watch?v=...")
        >>> print(f"Title: {info.title}, Duration: {info.duration}s")
    """
    if yt_dlp is None:
        raise ImportError("yt-dlp is required. Install with: pip install yt-dlp")

    ydl_opts = {
        "quiet": True,
        "no_warnings": True,
        "extract_flat": False,
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:  # type: ignore
            info_dict = ydl.extract_info(url, download=False)

            return VideoInfo(
                id=info_dict.get("id") or "",
                title=info_dict.get("title") or "Unknown",
                duration=float(info_dict.get("duration") or 0),
                url=url,
                thumbnail_url=info_dict.get("thumbnail"),
                uploader=info_dict.get("uploader"),
                upload_date=info_dict.get("upload_date"),
            )

    except Exception as e:
        raise RuntimeError(f"Failed to get video info: {e}") from e


def download_youtube_audio(
    url: str,
    output_path: Path,
    sample_rate: int = 24000,
    channels: int = 1,
    audio_format: str = "bestaudio",
    max_retries: int = 3,
    retry_delay: float = 2.0,
    force: bool = False,
    verbose: bool = False,
) -> Path | None:
    """
    Download audio from YouTube video and convert to WAV.

    Args:
        url: YouTube video URL
        output_path: Path to save audio file (will be .wav)
        sample_rate: Target sample rate in Hz (default: 24000)
        channels: Number of audio channels (default: 1 = mono)
        audio_format: yt-dlp audio format selector (default: 'bestaudio')
        max_retries: Maximum number of download attempts (default: 3)
        retry_delay: Delay between retries in seconds (default: 2.0)
        force: Overwrite existing file (default: False)
        verbose: Print detailed progress (default: False)

    Returns:
        Path to downloaded audio file, or None if failed

    Raises:
        ImportError: If yt-dlp is not installed

    Example:
        >>> audio_file = download_youtube_audio(
        ...     "https://youtube.com/watch?v=...",
        ...     Path("output/video_001.wav"),
        ...     sample_rate=24000
        ... )
        >>> if audio_file:
        ...     print(f"Downloaded: {audio_file}")
    """
    if yt_dlp is None:
        raise ImportError("yt-dlp is required. Install with: pip install yt-dlp")

    output_path = Path(output_path)

    # Check if already exists
    if output_path.exists() and not force:
        if verbose:
            logger.info(f"✓ File already exists: {output_path.name}")
        return output_path

    # Ensure parent directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # Remove .wav extension for yt-dlp (it adds it automatically)
    output_template = str(output_path.with_suffix(""))

    # yt-dlp options
    ydl_opts = {
        "format": audio_format,
        "outtmpl": output_template,
        "noplaylist": True,
        "quiet": not verbose,
        "no_warnings": not verbose,
        "extract_flat": False,
        "retries": max_retries,
        "fragment_retries": max_retries,
        "postprocessors": [
            {
                "key": "FFmpegExtractAudio",
                "preferredcodec": "wav",
                "preferredquality": "0",
            }
        ],
        "postprocessor_args": [
            "-ar",
            str(sample_rate),
            "-ac",
            str(channels),
        ],
    }

    # Download with retry logic
    for attempt in range(max_retries):
        try:
            if verbose:
                logger.info(f"⬇️  Downloading audio (attempt {attempt + 1}/{max_retries}): {url}")

            with yt_dlp.YoutubeDL(ydl_opts) as ydl:  # type: ignore
                info_dict = ydl.extract_info(url, download=True)

                if verbose:
                    title = info_dict.get("title") or "Unknown"
                    duration = info_dict.get("duration") or 0
                    logger.info(f"✅ Downloaded '{title}' ({duration:.1f}s)")

            # Verify file was created
            if output_path.exists():
                return output_path
            else:
                logger.warning(f"⚠️  File not created: {output_path}")

        except Exception as e:
            logger.warning(f"❌ Download failed (attempt {attempt + 1}/{max_retries}): {e}")

            if attempt < max_retries - 1:
                if verbose:
                    logger.info(f"   Retrying in {retry_delay}s...")
                time.sleep(retry_delay)
            else:
                logger.error(f"   All {max_retries} attempts failed")
                return None

    return None


def batch_download_youtube(
    urls: list[str],
    output_dir: Path,
    name_prefix: str = "video",
    sample_rate: int = 24000,
    max_retries: int = 3,
    verbose: bool = False,
) -> list[Path]:
    """
    Download multiple YouTube videos in batch.

    Args:
        urls: List of YouTube video URLs
        output_dir: Directory to save audio files
        name_prefix: Prefix for output filenames (default: 'video')
        sample_rate: Target sample rate (default: 24000)
        max_retries: Maximum retries per video (default: 3)
        verbose: Print detailed progress (default: False)

    Returns:
        List of paths to successfully downloaded files

    Example:
        >>> urls = [
        ...     "https://youtube.com/watch?v=...",
        ...     "https://youtube.com/watch?v=...",
        ... ]
        >>> files = batch_download_youtube(urls, Path("output/"))
        >>> print(f"Downloaded {len(files)}/{len(urls)} videos")
    """
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    downloaded = []

    for i, url in enumerate(urls, 1):
        if verbose:
            logger.info(f"\n[{i}/{len(urls)}] Processing: {url}")

        # Generate filename
        filename = f"{name_prefix}_{str(i).zfill(5)}.wav"
        output_path = output_dir / filename

        # Download
        result = download_youtube_audio(
            url, output_path, sample_rate=sample_rate, max_retries=max_retries, verbose=verbose
        )

        if result:
            downloaded.append(result)

    if verbose:
        logger.info(f"\n✅ Successfully downloaded {len(downloaded)}/{len(urls)} videos")

    return downloaded


def get_youtube_config_from_dict(config: dict) -> dict:
    """
    Extract YouTube download parameters from configuration dict.

    Args:
        config: Configuration dict with youtube.* keys

    Returns:
        Dict with download parameters ready for function calls

    Example:
        >>> config = load_config()
        >>> youtube_params = get_youtube_config_from_dict(config)
        >>> download_youtube_audio(url, path, **youtube_params)
    """
    youtube = config.get("youtube", {})

    return {
        "sample_rate": int(config.get("audio", {}).get("target_sample_rate", 24000)),
        "audio_format": youtube.get("audio_format", "bestaudio"),
        "max_retries": int(youtube.get("max_retries", 3)),
        "retry_delay": float(youtube.get("retry_delay", 2.0)),
    }


# CLI for testing
if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="YouTube download utility")

    subparsers = parser.add_subparsers(dest="command", help="Command to execute")

    # Info command
    info_parser = subparsers.add_parser("info", help="Get video information")
    info_parser.add_argument("url", help="YouTube video URL")

    # Download command
    download_parser = subparsers.add_parser("download", help="Download video audio")
    download_parser.add_argument("url", help="YouTube video URL")
    download_parser.add_argument("output", help="Output file path")
    download_parser.add_argument(
        "--sample-rate", type=int, default=24000, help="Sample rate in Hz (default: 24000)"
    )
    download_parser.add_argument("--force", action="store_true", help="Overwrite existing file")

    # Batch command
    batch_parser = subparsers.add_parser("batch", help="Batch download from URL list")
    batch_parser.add_argument("urls_file", help="File with URLs (one per line)")
    batch_parser.add_argument("output_dir", help="Output directory")
    batch_parser.add_argument("--prefix", default="video", help="Filename prefix (default: video)")
    batch_parser.add_argument(
        "--sample-rate", type=int, default=24000, help="Sample rate in Hz (default: 24000)"
    )

    args = parser.parse_args()

    if args.command == "info":
        info = get_video_info(args.url)
        print("\nVideo Information:")
        print(f"  Title: {info.title}")
        print(f"  Duration: {info.duration:.1f}s ({info.duration/60:.1f}min)")
        print(f"  ID: {info.id}")
        print(f"  URL: {info.url}")
        if info.uploader:
            print(f"  Uploader: {info.uploader}")
        if info.upload_date:
            print(f"  Upload date: {info.upload_date}")

    elif args.command == "download":
        result = download_youtube_audio(
            args.url,
            Path(args.output),
            sample_rate=args.sample_rate,
            force=args.force,
            verbose=True,
        )

        if result:
            print(f"\n✅ Downloaded successfully: {result}")
        else:
            print("\n❌ Download failed")

    elif args.command == "batch":
        # Load URLs from file
        urls_file = Path(args.urls_file)
        if not urls_file.exists():
            print(f"Error: File not found: {urls_file}")
            exit(1)

        urls = [
            line.strip()
            for line in urls_file.read_text().split("\n")
            if line.strip() and not line.startswith("#")
        ]

        print(f"Downloading {len(urls)} videos...")

        results = batch_download_youtube(
            urls,
            Path(args.output_dir),
            name_prefix=args.prefix,
            sample_rate=args.sample_rate,
            verbose=True,
        )

        print(f"\n✅ Downloaded {len(results)}/{len(urls)} videos")

    else:
        parser.print_help()
