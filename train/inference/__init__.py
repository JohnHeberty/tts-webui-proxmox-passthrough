"""
F5-TTS Inference API

Unified interface for F5-TTS inference used by:
- REST API (app/engines/f5tts_engine.py)
- Training scripts (train/scripts/*)
- CLI tools (train/cli/infer.py)

Author: F5-TTS Training Pipeline
Version: 1.0
Date: 2025-12-06
"""
from train.inference.api import F5TTSInference

__all__ = ['F5TTSInference']
