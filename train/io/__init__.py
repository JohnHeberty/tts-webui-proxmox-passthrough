"""
I/O Module for F5-TTS Training Pipeline

This module provides functions for external data sources:
- YouTube video/audio download
- Subtitle extraction and parsing
- File storage and management

Author: F5-TTS Training Pipeline
Sprint: 3 - Dataset Consolidation
Date: December 6, 2025
"""

from .youtube import (
    VideoInfo,
    download_youtube_audio,
    get_video_info,
    batch_download_youtube,
    get_youtube_config_from_dict,
)
from .subtitles import (
    Subtitle,
    extract_subtitles,
    parse_srt,
    parse_vtt,
    merge_subtitle_lines,
    parse_srt_timestamp,
    parse_vtt_timestamp,
)
from .storage import (
    ensure_directory,
    safe_filename,
    atomic_write,
    get_file_hash,
    copy_with_progress,
    move_with_backup,
    clean_directory,
    get_directory_size,
    format_size,
)

__all__ = [
    # YouTube
    'VideoInfo',
    'download_youtube_audio',
    'get_video_info',
    'batch_download_youtube',
    'get_youtube_config_from_dict',
    
    # Subtitles
    'Subtitle',
    'extract_subtitles',
    'parse_srt',
    'parse_vtt',
    'merge_subtitle_lines',
    'parse_srt_timestamp',
    'parse_vtt_timestamp',
    
    # Storage
    'ensure_directory',
    'safe_filename',
    'atomic_write',
    'get_file_hash',
    'copy_with_progress',
    'move_with_backup',
    'clean_directory',
    'get_directory_size',
    'format_size',
]

__version__ = '1.0.0'
