"""
Text Processing Module for F5-TTS Training Pipeline

This module provides pure, testable functions for text processing:
- Text normalization (numbers, symbols, currency)
- Quality assurance (OOV detection, length validation)
- Vocabulary management

All functions are designed to be:
- Pure (no side effects, deterministic)
- Testable (clear inputs/outputs)
- Composable (can be chained together)
- Language-aware (PT-BR optimized)

Author: F5-TTS Training Pipeline
Sprint: 3 - Dataset Consolidation
Date: December 6, 2025
"""

from .normalizer import TextNormalizer, normalize_text
from .qa import TextQualityReport, check_text_quality, validate_text_for_training
from .vocab import compute_vocab_hash, load_vocab, validate_vocab


__all__ = [
    # Normalizer
    "TextNormalizer",
    "normalize_text",
    # Quality Assurance
    "check_text_quality",
    "validate_text_for_training",
    "TextQualityReport",
    # Vocabulary
    "load_vocab",
    "validate_vocab",
    "compute_vocab_hash",
]

__version__ = "1.0.0"
