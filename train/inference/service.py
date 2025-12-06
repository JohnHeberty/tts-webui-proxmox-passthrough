"""
F5-TTS Inference Service Layer

Singleton service with model caching and lifecycle management.
Provides efficient model loading/unloading for production use.

Author: F5-TTS Training Pipeline
Version: 1.0
Date: 2025-12-06
"""

import logging
from pathlib import Path
import threading
from typing import Optional, Union

from train.inference.api import F5TTSInference


logger = logging.getLogger(__name__)


class F5TTSInferenceService:
    """
    Singleton service for F5-TTS inference with model caching.

    Features:
    - Lazy loading: model loaded on first use
    - Singleton pattern: single instance across application
    - Memory management: explicit load/unload controls
    - Thread-safe: uses locking for concurrent access

    Example:
        >>> service = F5TTSInferenceService.get_instance()
        >>> service.configure(checkpoint_path="model.pt", vocab_file="vocab.txt")
        >>>
        >>> # Model loaded automatically on first generate()
        >>> audio = service.generate(text="Hello", ref_audio="ref.wav")
        >>>
        >>> # Unload when done
        >>> service.unload_model()
    """

    _instance: Optional["F5TTSInferenceService"] = None
    _lock = threading.Lock()

    def __init__(self):
        """Private constructor (use get_instance())."""
        self.inference: F5TTSInference | None = None
        self.config: dict = {}
        self._configured = False

    @classmethod
    def get_instance(cls) -> "F5TTSInferenceService":
        """
        Get singleton instance.

        Thread-safe lazy initialization.

        Returns:
            F5TTSInferenceService: Singleton instance
        """
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = cls()
                    logger.info("✅ F5TTSInferenceService singleton created")
        return cls._instance

    def configure(
        self,
        checkpoint_path: Union[str, Path],
        vocab_file: Union[str, Path],
        device: str = "cuda",
        config: dict | None = None,
        **kwargs,
    ):
        """
        Configure service parameters.

        Args:
            checkpoint_path: Path to model checkpoint
            vocab_file: Path to vocabulary file
            device: Device ('cuda', 'cpu', 'mps')
            config: Optional model configuration
            **kwargs: Additional F5TTSInference parameters
        """
        self.config = {
            "checkpoint_path": checkpoint_path,
            "vocab_file": vocab_file,
            "device": device,
            "config": config,
            **kwargs,
        }
        self._configured = True
        logger.info(f"✅ Service configured: {Path(checkpoint_path).name} on {device}")

    def load_model(self):
        """
        Explicitly load model into memory.

        Useful for pre-loading before first request.

        Raises:
            RuntimeError: If service not configured
        """
        if not self._configured:
            raise RuntimeError("Service not configured. Call configure() first.")

        if self.inference is None:
            with self._lock:
                if self.inference is None:
                    logger.info("⏳ Loading F5-TTS model...")
                    self.inference = F5TTSInference(**self.config)
                    logger.info("✅ Model loaded and cached")

    def unload_model(self):
        """
        Unload model from memory to free GPU/RAM.

        Next generate() call will reload model (lazy loading).
        """
        if self.inference is not None:
            with self._lock:
                if self.inference is not None:
                    self.inference.unload()
                    self.inference = None
                    logger.info("🗑️ Model unloaded from cache")

    def generate(self, *args, **kwargs):
        """
        Generate speech (lazy loads model if needed).

        Args:
            *args, **kwargs: Passed to F5TTSInference.generate()

        Returns:
            np.ndarray: Generated audio
        """
        # Lazy load
        if self.inference is None:
            self.load_model()

        assert self.inference is not None, "Model should be loaded"
        return self.inference.generate(*args, **kwargs)

    def save_audio(self, *args, **kwargs):
        """
        Save generated audio to file.

        Args:
            *args, **kwargs: Passed to F5TTSInference.save_audio()
        """
        if self.inference is None:
            raise RuntimeError("No model loaded. Call generate() first.")

        self.inference.save_audio(*args, **kwargs)

    def is_loaded(self) -> bool:
        """Check if model is currently loaded."""
        return self.inference is not None

    def is_configured(self) -> bool:
        """Check if service is configured."""
        return self._configured

    def __repr__(self) -> str:
        status = "loaded" if self.is_loaded() else "unloaded"
        config_status = "configured" if self.is_configured() else "not configured"
        return f"F5TTSInferenceService({config_status}, model={status})"


# Convenience function
def get_inference_service() -> F5TTSInferenceService:
    """Get singleton inference service instance."""
    return F5TTSInferenceService.get_instance()
