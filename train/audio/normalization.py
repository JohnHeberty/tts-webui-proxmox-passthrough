"""
Audio Normalization Module

Pure functions for normalizing audio loudness.

Author: F5-TTS Training Pipeline
Sprint: 3 - Dataset Consolidation
"""
import math
import warnings
from typing import Optional
import numpy as np

# Optional dependency
try:
    import pyloudnorm as pyln
except ImportError:
    pyln = None


def normalize_rms(
    audio: np.ndarray,
    target_db: float = -20.0,
    eps: float = 1e-10,
) -> np.ndarray:
    """
    Normalize audio using RMS (Root Mean Square) to target dB level.
    
    This is a simple, fast normalization method that adjusts overall loudness.
    
    Args:
        audio: Audio samples as float32 numpy array
        target_db: Target RMS level in dB (default: -20.0)
        eps: Small value to avoid log(0) (default: 1e-10)
        
    Returns:
        Normalized audio as float32 numpy array
        
    Example:
        >>> audio = load_audio("speech.wav")
        >>> normalized = normalize_rms(audio, target_db=-20.0)
        >>> # Audio is now normalized to -20dB RMS
    """
    if len(audio) == 0:
        return audio
    
    # Calculate current RMS level in dB
    rms = float(np.sqrt(np.mean(audio * audio) + eps))
    current_db = 20.0 * math.log10(rms + eps)
    
    # Calculate gain needed
    gain_db = target_db - current_db
    gain_linear = 10.0 ** (gain_db / 20.0)
    
    # Apply gain
    audio_norm = audio * gain_linear
    
    # Prevent clipping
    max_val = float(np.max(np.abs(audio_norm)))
    if max_val > 0.99:
        audio_norm = audio_norm * (0.99 / max_val)
    
    return audio_norm.astype(np.float32)


def normalize_loudness(
    audio: np.ndarray,
    sample_rate: int,
    target_lufs: float = -20.0,
    meter: Optional[object] = None,
) -> np.ndarray:
    """
    Normalize audio using ITU-R BS.1770-4 loudness standard (LUFS).
    
    This is a perceptually accurate normalization method. Requires pyloudnorm.
    Falls back to RMS normalization if pyloudnorm is not available.
    
    Args:
        audio: Audio samples as float32 numpy array
        sample_rate: Sample rate in Hz
        target_lufs: Target loudness in LUFS (default: -20.0)
        meter: Optional pre-created pyloudnorm meter for efficiency
        
    Returns:
        Normalized audio as float32 numpy array
        
    Example:
        >>> audio = load_audio("speech.wav")
        >>> normalized = normalize_loudness(audio, 24000, target_lufs=-23.0)
        >>> # Audio is now normalized to -23 LUFS (broadcast standard)
    """
    if len(audio) == 0:
        return audio
    
    # Try pyloudnorm if available
    if pyln is not None:
        try:
            # Create meter if not provided
            if meter is None:
                meter = pyln.Meter(sample_rate)  # type: ignore
            
            # Measure current loudness
            loudness = meter.integrated_loudness(audio)  # type: ignore
            
            # Normalize to target LUFS
            with warnings.catch_warnings():
                warnings.simplefilter("ignore", UserWarning)
                audio_norm = pyln.normalize.loudness(audio, loudness, target_lufs)  # type: ignore
            
            # Prevent clipping
            max_val = float(np.max(np.abs(audio_norm)))
            if max_val > 0.99:
                audio_norm = audio_norm * (0.99 / max_val)
            
            return audio_norm.astype(np.float32)
            
        except Exception as e:
            warnings.warn(f"pyloudnorm failed: {e}, falling back to RMS", UserWarning)
    
    # Fallback to RMS normalization
    return normalize_rms(audio, target_db=target_lufs)


def create_loudness_meter(sample_rate: int) -> Optional[object]:
    """
    Create a pyloudnorm meter for efficient batch processing.
    
    When normalizing many audio files, create the meter once and reuse it.
    
    Args:
        sample_rate: Sample rate in Hz
        
    Returns:
        Meter object if pyloudnorm available, None otherwise
        
    Example:
        >>> meter = create_loudness_meter(24000)
        >>> for audio in audio_files:
        >>>     normalized = normalize_loudness(audio, 24000, meter=meter)
    """
    if pyln is None:
        return None
    
    try:
        return pyln.Meter(sample_rate)
    except Exception:
        return None


def calculate_loudness_stats(
    audio: np.ndarray,
    sample_rate: int,
) -> dict:
    """
    Calculate various loudness metrics for audio.
    
    Args:
        audio: Audio samples as float32 numpy array
        sample_rate: Sample rate in Hz
        
    Returns:
        Dictionary with loudness statistics
        
    Example:
        >>> audio = load_audio("speech.wav")
        >>> stats = calculate_loudness_stats(audio, 24000)
        >>> print(f"LUFS: {stats['lufs']:.1f}, Peak: {stats['peak_db']:.1f}dB")
    """
    eps = 1e-10
    
    # RMS in dB
    rms = float(np.sqrt(np.mean(audio * audio) + eps))
    rms_db = 20.0 * math.log10(rms + eps)
    
    # Peak in dB
    peak = float(np.max(np.abs(audio)))
    peak_db = 20.0 * math.log10(peak + eps) if peak > 0 else -np.inf
    
    # LUFS if available
    lufs = None
    if pyln is not None:
        try:
            meter = pyln.Meter(sample_rate)
            lufs = meter.integrated_loudness(audio)
        except Exception:
            pass
    
    return {
        'rms_db': rms_db,
        'peak_db': peak_db,
        'lufs': lufs,
        'peak_value': peak,
        'has_clipping': peak >= 0.99,
    }


def get_normalization_config_from_dict(config: dict) -> dict:
    """
    Extract normalization parameters from configuration dict.
    
    Args:
        config: Configuration dict with audio.* keys
        
    Returns:
        Dict with normalization parameters ready for function calls
        
    Example:
        >>> config = load_config()
        >>> norm_params = get_normalization_config_from_dict(config)
        >>> normalized = normalize_loudness(audio, sr, **norm_params)
    """
    audio = config.get('audio', {})
    
    return {
        'target_lufs': float(audio.get('target_lufs', -20.0)),
    }


# CLI for testing
if __name__ == "__main__":
    import argparse
    import soundfile as sf
    
    parser = argparse.ArgumentParser(description="Audio normalization utility")
    parser.add_argument('input_file', help='Input audio file')
    parser.add_argument('output_file', help='Output audio file')
    parser.add_argument('--target-lufs', type=float, default=-20.0,
                       help='Target LUFS level (default: -20.0)')
    parser.add_argument('--method', choices=['lufs', 'rms'], default='lufs',
                       help='Normalization method (default: lufs)')
    parser.add_argument('--stats', action='store_true',
                       help='Show loudness statistics')
    
    args = parser.parse_args()
    
    # Load audio
    audio, sr = sf.read(args.input_file, dtype='float32')
    if audio.ndim > 1:
        audio = audio.mean(axis=1)
    
    print(f"Input: {args.input_file}")
    print(f"Sample rate: {sr}Hz")
    print(f"Duration: {len(audio)/sr:.2f}s")
    
    # Show stats before normalization
    if args.stats:
        print("\nBefore normalization:")
        stats = calculate_loudness_stats(audio, sr)
        print(f"  RMS: {stats['rms_db']:.2f}dB")
        print(f"  Peak: {stats['peak_db']:.2f}dB")
        if stats['lufs'] is not None:
            print(f"  LUFS: {stats['lufs']:.2f}")
        if stats['has_clipping']:
            print(f"  ⚠️  Clipping detected!")
    
    # Normalize
    print(f"\nNormalizing to {args.target_lufs:.1f} LUFS using {args.method} method...")
    
    if args.method == 'lufs':
        normalized = normalize_loudness(audio, sr, target_lufs=args.target_lufs)
    else:
        normalized = normalize_rms(audio, target_db=args.target_lufs)
    
    # Show stats after normalization
    if args.stats:
        print("\nAfter normalization:")
        stats = calculate_loudness_stats(normalized, sr)
        print(f"  RMS: {stats['rms_db']:.2f}dB")
        print(f"  Peak: {stats['peak_db']:.2f}dB")
        if stats['lufs'] is not None:
            print(f"  LUFS: {stats['lufs']:.2f}")
        if stats['has_clipping']:
            print(f"  ⚠️  Clipping detected!")
    
    # Save
    sf.write(args.output_file, normalized, sr)
    print(f"\n✅ Saved to: {args.output_file}")
