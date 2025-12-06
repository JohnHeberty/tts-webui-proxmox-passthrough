"""
Audio I/O Module

Functions for loading and saving audio files with proper error handling.

Author: F5-TTS Training Pipeline
Sprint: 3 - Dataset Consolidation
"""

import math
from pathlib import Path
from typing import Union

import numpy as np


try:
    import soundfile as sf
except ImportError:
    sf = None

try:
    from scipy import signal
except ImportError:
    signal = None


def load_audio(
    file_path: Union[str, Path],
    sample_rate: int | None = None,
    mono: bool = True,
    dtype: str = "float32",
) -> tuple[np.ndarray, int]:
    """
    Load audio file with optional resampling and mono conversion.

    Args:
        file_path: Path to audio file
        sample_rate: Target sample rate (None = keep original)
        mono: Convert to mono if True (default: True)
        dtype: Output dtype (default: 'float32')

    Returns:
        Tuple of (audio_array, sample_rate)

    Raises:
        ImportError: If soundfile is not installed
        FileNotFoundError: If file doesn't exist
        RuntimeError: If file cannot be read

    Example:
        >>> audio, sr = load_audio("speech.wav", sample_rate=24000)
        >>> print(f"Loaded {len(audio)/sr:.2f}s at {sr}Hz")
    """
    if sf is None:
        raise ImportError("soundfile is required. Install with: pip install soundfile")

    file_path = Path(file_path)
    if not file_path.exists():
        raise FileNotFoundError(f"Audio file not found: {file_path}")

    try:
        # Load audio
        audio, orig_sr = sf.read(str(file_path), dtype=dtype)

        # Convert to mono if needed
        if mono and audio.ndim > 1:
            audio = audio.mean(axis=1)

        # Resample if needed
        if sample_rate is not None and sample_rate != orig_sr:
            audio, orig_sr = resample_audio(audio, orig_sr, sample_rate)

        return audio, orig_sr

    except Exception as e:
        raise RuntimeError(f"Failed to load audio from {file_path}: {e}") from e


def save_audio(
    file_path: Union[str, Path],
    audio: np.ndarray,
    sample_rate: int,
    subtype: str = "PCM_16",
) -> None:
    """
    Save audio to file.

    Args:
        file_path: Path to save audio file
        audio: Audio samples as numpy array
        sample_rate: Sample rate in Hz
        subtype: Audio format subtype (default: 'PCM_16')

    Raises:
        ImportError: If soundfile is not installed
        RuntimeError: If file cannot be written

    Example:
        >>> save_audio("output.wav", audio, 24000)
    """
    if sf is None:
        raise ImportError("soundfile is required. Install with: pip install soundfile")

    file_path = Path(file_path)

    # Create parent directory if needed
    file_path.parent.mkdir(parents=True, exist_ok=True)

    try:
        sf.write(str(file_path), audio, sample_rate, subtype=subtype)
    except Exception as e:
        raise RuntimeError(f"Failed to save audio to {file_path}: {e}") from e


def load_audio_chunk(
    file_path: Union[str, Path],
    start_sec: float,
    end_sec: float,
    sample_rate: int | None = None,
    mono: bool = True,
) -> tuple[np.ndarray, int]:
    """
    Load a specific time range from an audio file.

    This is more memory-efficient than loading the entire file.

    Args:
        file_path: Path to audio file
        start_sec: Start time in seconds
        end_sec: End time in seconds
        sample_rate: Target sample rate (None = keep original)
        mono: Convert to mono if True (default: True)

    Returns:
        Tuple of (audio_chunk, sample_rate)

    Example:
        >>> # Load 3-second chunk starting at 10 seconds
        >>> chunk, sr = load_audio_chunk("long_audio.wav", 10.0, 13.0)
    """
    if sf is None:
        raise ImportError("soundfile is required. Install with: pip install soundfile")

    file_path = Path(file_path)
    if not file_path.exists():
        raise FileNotFoundError(f"Audio file not found: {file_path}")

    try:
        with sf.SoundFile(str(file_path)) as f:
            orig_sr = f.samplerate

            # Calculate frame indices
            start_frame = int(start_sec * orig_sr)
            end_frame = int(end_sec * orig_sr)

            # Clamp to file bounds
            start_frame = max(0, start_frame)
            end_frame = min(len(f), end_frame)

            if start_frame >= end_frame:
                return np.array([], dtype="float32"), orig_sr

            # Seek and read
            f.seek(start_frame)
            audio = f.read(frames=end_frame - start_frame, dtype="float32")

            # Convert to mono if needed
            if mono and audio.ndim > 1:
                audio = audio.mean(axis=1)

            # Resample if needed
            if sample_rate is not None and sample_rate != orig_sr:
                audio, orig_sr = resample_audio(audio, orig_sr, sample_rate)

            return audio, orig_sr

    except Exception as e:
        raise RuntimeError(f"Failed to load audio chunk from {file_path}: {e}") from e


def resample_audio(
    audio: np.ndarray,
    orig_sr: int,
    target_sr: int,
) -> tuple[np.ndarray, int]:
    """
    Resample audio to target sample rate.

    Uses scipy.signal.resample_poly if available, otherwise simple decimation/repetition.

    Args:
        audio: Audio samples as numpy array
        orig_sr: Original sample rate in Hz
        target_sr: Target sample rate in Hz

    Returns:
        Tuple of (resampled_audio, target_sr)

    Example:
        >>> audio_48k = np.random.randn(48000).astype('float32')
        >>> audio_24k, sr = resample_audio(audio_48k, 48000, 24000)
        >>> print(f"Resampled to {sr}Hz, length {len(audio_24k)}")
    """
    if orig_sr == target_sr:
        return audio, orig_sr

    # Try high-quality resampling with scipy
    if signal is not None:
        try:
            gcd = math.gcd(orig_sr, target_sr)
            up = target_sr // gcd
            down = orig_sr // gcd

            audio_resampled = signal.resample_poly(audio, up, down)
            return audio_resampled.astype("float32"), target_sr

        except Exception as e:
            import warnings

            warnings.warn(f"scipy resampling failed: {e}, using simple method", UserWarning)

    # Fallback to simple resampling
    if orig_sr > target_sr:
        # Downsample by decimation
        step = max(1, int(round(orig_sr / target_sr)))
        audio_resampled = audio[::step]
    else:
        # Upsample by repetition
        factor = max(1, int(round(target_sr / orig_sr)))
        audio_resampled = np.repeat(audio, factor)

    return audio_resampled.astype("float32"), target_sr


def get_audio_info(file_path: Union[str, Path]) -> dict:
    """
    Get information about an audio file without loading it.

    Args:
        file_path: Path to audio file

    Returns:
        Dictionary with audio file information

    Example:
        >>> info = get_audio_info("speech.wav")
        >>> print(f"Duration: {info['duration']:.2f}s")
        >>> print(f"Sample rate: {info['sample_rate']}Hz")
    """
    if sf is None:
        raise ImportError("soundfile is required. Install with: pip install soundfile")

    file_path = Path(file_path)
    if not file_path.exists():
        raise FileNotFoundError(f"Audio file not found: {file_path}")

    try:
        with sf.SoundFile(str(file_path)) as f:
            return {
                "sample_rate": f.samplerate,
                "channels": f.channels,
                "frames": len(f),
                "duration": len(f) / f.samplerate,
                "format": f.format,
                "subtype": f.subtype,
                "file_size": file_path.stat().st_size,
            }
    except Exception as e:
        raise RuntimeError(f"Failed to get info from {file_path}: {e}") from e


# CLI for testing
if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Audio I/O utility")

    subparsers = parser.add_subparsers(dest="command", help="Command to execute")

    # Info command
    info_parser = subparsers.add_parser("info", help="Show audio file information")
    info_parser.add_argument("file", help="Audio file path")

    # Convert command
    convert_parser = subparsers.add_parser("convert", help="Convert audio file")
    convert_parser.add_argument("input", help="Input audio file")
    convert_parser.add_argument("output", help="Output audio file")
    convert_parser.add_argument("--sample-rate", type=int, help="Target sample rate")
    convert_parser.add_argument("--mono", action="store_true", help="Convert to mono")

    # Extract command
    extract_parser = subparsers.add_parser("extract", help="Extract audio chunk")
    extract_parser.add_argument("input", help="Input audio file")
    extract_parser.add_argument("output", help="Output audio file")
    extract_parser.add_argument("--start", type=float, required=True, help="Start time in seconds")
    extract_parser.add_argument("--end", type=float, required=True, help="End time in seconds")
    extract_parser.add_argument("--sample-rate", type=int, help="Target sample rate")

    args = parser.parse_args()

    if args.command == "info":
        info = get_audio_info(args.file)
        print("\nAudio File Information:")
        print(f"  File: {args.file}")
        print(f"  Duration: {info['duration']:.2f}s")
        print(f"  Sample rate: {info['sample_rate']}Hz")
        print(f"  Channels: {info['channels']}")
        print(f"  Frames: {info['frames']:,}")
        print(f"  Format: {info['format']}/{info['subtype']}")
        print(f"  File size: {info['file_size']:,} bytes")

    elif args.command == "convert":
        print(f"Loading: {args.input}")
        audio, sr = load_audio(args.input, sample_rate=args.sample_rate, mono=args.mono)
        print(f"  Duration: {len(audio)/sr:.2f}s")
        print(f"  Sample rate: {sr}Hz")
        print(f"  Channels: {'mono' if audio.ndim == 1 else 'stereo'}")

        print(f"Saving: {args.output}")
        save_audio(args.output, audio, sr)
        print("✅ Done")

    elif args.command == "extract":
        print(f"Extracting {args.start}s - {args.end}s from {args.input}")
        chunk, sr = load_audio_chunk(
            args.input, args.start, args.end, sample_rate=args.sample_rate, mono=True
        )
        print(f"  Duration: {len(chunk)/sr:.2f}s")
        print(f"  Sample rate: {sr}Hz")

        print(f"Saving: {args.output}")
        save_audio(args.output, chunk, sr)
        print("✅ Done")

    else:
        parser.print_help()
