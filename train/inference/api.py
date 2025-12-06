"""
Unified F5-TTS Inference API

Provides a consistent interface for F5-TTS inference across:
- REST API endpoints
- Training/evaluation scripts
- CLI tools

Author: F5-TTS Training Pipeline
Version: 1.0
Date: 2025-12-06
"""

import logging
from pathlib import Path
import time
from typing import Union

import numpy as np
import torch
import torchaudio


logger = logging.getLogger(__name__)


class F5TTSInference:
    """
    Unified inference API for F5-TTS model.

    Encapsulates F5TTS model loading and generation with consistent interface.
    Handles device management, model loading, and audio generation.

    Example:
        >>> inference = F5TTSInference(
        ...     checkpoint_path="models/f5tts/model_last.pt",
        ...     vocab_file="train/config/vocab.txt",
        ...     device="cuda"
        ... )
        >>>
        >>> audio = inference.generate(
        ...     text="Olá, mundo!",
        ...     ref_audio="ref.wav",
        ...     ref_text="Texto de referência",
        ...     nfe_step=32
        ... )
        >>>
        >>> # Save output
        >>> inference.save_audio(audio, "output.wav")
    """

    def __init__(
        self,
        checkpoint_path: Union[str, Path],
        vocab_file: Union[str, Path],
        device: str = "cuda",
        config: dict | None = None,
        sample_rate: int = 24000,
        hop_length: int = 256,
        target_rms: float = 0.1,
    ):
        """
        Initialize F5-TTS inference engine.

        Args:
            checkpoint_path: Path to model checkpoint (.pt or .safetensors)
            vocab_file: Path to vocabulary file (vocab.txt)
            device: Device to run inference on ('cuda', 'cpu', 'mps')
            config: Optional model configuration dict
            sample_rate: Audio sample rate (default: 24000)
            hop_length: Mel spectrogram hop length (default: 256)
            target_rms: Target RMS for audio normalization (default: 0.1)

        Raises:
            FileNotFoundError: If checkpoint or vocab file not found
            RuntimeError: If model fails to load
        """
        self.checkpoint_path = Path(checkpoint_path)
        self.vocab_file = Path(vocab_file)
        self.device = device
        self.config = config or {}
        self.sample_rate = sample_rate
        self.hop_length = hop_length
        self.target_rms = target_rms

        # Validate files exist
        if not self.checkpoint_path.exists():
            raise FileNotFoundError(f"Checkpoint not found: {self.checkpoint_path}")
        if not self.vocab_file.exists():
            raise FileNotFoundError(f"Vocab file not found: {self.vocab_file}")

        # Initialize model
        self.model = None
        self._load_model()

        logger.info(f"✅ F5TTSInference initialized: {self.checkpoint_path.name} on {self.device}")

    def _load_model(self):
        """Load F5-TTS model from checkpoint."""
        try:
            from f5_tts.infer.utils_infer import load_model, load_vocoder

            logger.info(f"Loading model from: {self.checkpoint_path}")
            start_time = time.time()

            # Load model
            self.model = load_model(
                model_cls=None,  # Auto-detect from checkpoint
                model_cfg=self.config,
                ckpt_path=str(self.checkpoint_path),
                vocab_file=str(self.vocab_file),
                device=self.device,
            )

            # Load vocoder (BigVGAN)
            self.vocoder = load_vocoder(
                vocoder_name="bigvgan",
                is_local=False,
                local_path="",  # Empty string instead of None
                device=self.device,
            )

            load_time = time.time() - start_time
            logger.info(f"✅ Model loaded in {load_time:.2f}s")

        except Exception as e:
            logger.error(f"❌ Failed to load model: {e}")
            raise RuntimeError(f"Model loading failed: {e}") from e

    def generate(
        self,
        text: str,
        ref_audio: Union[str, Path],
        ref_text: str = "",
        nfe_step: int = 32,
        cfg_strength: float = 2.0,
        sway_sampling_coef: float = -1.0,
        speed: float = 1.0,
        fix_duration: float | None = None,
        remove_silence: bool = False,
    ) -> np.ndarray:
        """
        Generate speech from text using reference audio.

        Args:
            text: Text to synthesize
            ref_audio: Path to reference audio file (for voice cloning)
            ref_text: Transcription of reference audio (optional, auto-transcribed if empty)
            nfe_step: Number of function evaluations (higher = better quality, slower)
            cfg_strength: Classifier-free guidance strength (1.0-3.0, higher = more expressive)
            sway_sampling_coef: Sway sampling coefficient (-1.0 = auto)
            speed: Speech speed multiplier (0.5-2.0)
            fix_duration: Fix output duration in seconds (None = auto)
            remove_silence: Remove leading/trailing silence

        Returns:
            Generated audio as numpy array (shape: [samples,])

        Raises:
            FileNotFoundError: If reference audio not found
            ValueError: If text is empty or parameters invalid
        """
        if not text or not text.strip():
            raise ValueError("Text cannot be empty")

        ref_audio_path = Path(ref_audio)
        if not ref_audio_path.exists():
            raise FileNotFoundError(f"Reference audio not found: {ref_audio_path}")

        # Validate parameters
        if not (1 <= nfe_step <= 128):
            raise ValueError(f"nfe_step must be between 1 and 128, got {nfe_step}")
        if not (0.5 <= speed <= 2.0):
            raise ValueError(f"speed must be between 0.5 and 2.0, got {speed}")

        logger.info(f"🎙️ Generating speech: '{text[:50]}...'")
        logger.info(f"   Reference: {ref_audio_path.name}")
        logger.info(f"   NFE steps: {nfe_step}, CFG: {cfg_strength}, Speed: {speed}x")

        start_time = time.time()

        try:
            from f5_tts.infer.utils_infer import infer_process

            # Load reference audio
            ref_audio_array, ref_sr = torchaudio.load(str(ref_audio_path))

            # Resample if needed
            if ref_sr != self.sample_rate:
                resampler = torchaudio.transforms.Resample(ref_sr, self.sample_rate)
                ref_audio_array = resampler(ref_audio_array)

            # Convert to mono if stereo
            if ref_audio_array.shape[0] > 1:
                ref_audio_array = ref_audio_array.mean(dim=0, keepdim=True)

            # Run inference
            result = infer_process(
                ref_audio=ref_audio_array,
                ref_text=ref_text,
                gen_text=text,
                model_obj=self.model,
                vocoder=self.vocoder,
                mel_spec_type="vocos",  # Use Vocos mel spec
                show_info=lambda x: logger.debug(x),
                progress=None,  # type: ignore - No progress bar in API
                target_rms=self.target_rms,
                cross_fade_duration=0.15,
                nfe_step=nfe_step,
                cfg_strength=cfg_strength,
                sway_sampling_coef=sway_sampling_coef,
                speed=speed,
                fix_duration=fix_duration,
                device=self.device,
            )

            # Handle different return formats
            if isinstance(result, tuple) and len(result) >= 2:
                generated_audio = result[0]
                final_sample_rate = result[1]
            else:
                generated_audio = result
                final_sample_rate = self.sample_rate

            # Convert to numpy
            if isinstance(generated_audio, torch.Tensor):
                audio_np = generated_audio.cpu().numpy()
            else:
                audio_np = np.array(generated_audio)

            # Remove silence if requested
            if remove_silence:
                audio_np = self._remove_silence(audio_np)

            gen_time = time.time() - start_time
            duration = len(audio_np) / self.sample_rate
            rtf = gen_time / duration if duration > 0 else 0

            logger.info(f"✅ Generated {duration:.2f}s audio in {gen_time:.2f}s (RTF: {rtf:.2f}x)")

            return audio_np

        except Exception as e:
            logger.error(f"❌ Generation failed: {e}")
            raise RuntimeError(f"Speech generation failed: {e}") from e

    def _remove_silence(self, audio: np.ndarray, threshold: float = 0.01) -> np.ndarray:
        """
        Remove leading and trailing silence from audio.

        Args:
            audio: Audio array
            threshold: Silence threshold (RMS)

        Returns:
            Trimmed audio
        """
        # Find non-silent regions
        window_size = int(0.02 * self.sample_rate)  # 20ms windows
        hop = window_size // 2

        rms_values = []
        for i in range(0, len(audio) - window_size, hop):
            window = audio[i : i + window_size]
            rms = np.sqrt(np.mean(window**2))
            rms_values.append(rms)

        # Find start and end of speech
        rms_values = np.array(rms_values)
        speech_indices = np.where(rms_values > threshold)[0]

        if len(speech_indices) == 0:
            logger.warning("No speech detected, returning original audio")
            return audio

        start_idx = speech_indices[0] * hop
        end_idx = (speech_indices[-1] + 1) * hop + window_size

        return audio[start_idx:end_idx]

    def save_audio(
        self,
        audio: np.ndarray,
        output_path: Union[str, Path],
        sample_rate: int | None = None,
    ):
        """
        Save generated audio to file.

        Args:
            audio: Audio array to save
            output_path: Output file path (.wav)
            sample_rate: Sample rate (default: self.sample_rate)
        """
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        sr = sample_rate or self.sample_rate

        # Convert to tensor if needed
        if isinstance(audio, np.ndarray):
            audio_tensor = torch.from_numpy(audio).unsqueeze(0)
        else:
            audio_tensor = audio

        # Ensure 2D tensor [channels, samples]
        if audio_tensor.dim() == 1:
            audio_tensor = audio_tensor.unsqueeze(0)

        # Save
        torchaudio.save(str(output_path), audio_tensor.cpu(), sr)
        logger.info(f"💾 Saved audio to: {output_path}")

    def unload(self):
        """Unload model from memory to free GPU/RAM."""
        if self.model is not None:
            del self.model
            del self.vocoder
            self.model = None
            self.vocoder = None

            if torch.cuda.is_available():
                torch.cuda.empty_cache()

            logger.info("🗑️ Model unloaded from memory")

    def __del__(self):
        """Cleanup on deletion."""
        self.unload()

    def __repr__(self) -> str:
        return (
            f"F5TTSInference("
            f"checkpoint={self.checkpoint_path.name}, "
            f"device={self.device}, "
            f"sample_rate={self.sample_rate})"
        )
