"""
Audio Processing Module for F5-TTS Training Pipeline

This module provides pure, testable functions for audio processing:
- Voice Activity Detection (VAD)
- Audio segmentation
- Loudness normalization
- Effects (fade, filters)
- Audio I/O operations

All functions are designed to be:
- Pure (no side effects, no I/O except in io.py)
- Testable (clear inputs/outputs)
- Composable (can be chained together)
- Memory-efficient (support streaming where possible)

Author: F5-TTS Training Pipeline
Sprint: 3 - Dataset Consolidation
Date: December 6, 2025
"""

from .effects import apply_fade, apply_high_pass_filter
from .io import load_audio, load_audio_chunk, save_audio
from .normalization import normalize_loudness, normalize_rms
from .segmentation import merge_voice_regions, segment_audio
from .vad import detect_voice_in_chunk, detect_voice_regions


__all__ = [
    # VAD
    "detect_voice_regions",
    "detect_voice_in_chunk",
    # Segmentation
    "segment_audio",
    "merge_voice_regions",
    # Normalization
    "normalize_loudness",
    "normalize_rms",
    # Effects
    "apply_fade",
    "apply_high_pass_filter",
    # I/O
    "load_audio",
    "save_audio",
    "load_audio_chunk",
]

__version__ = "1.0.0"
