"""
Audio Effects Module

Pure functions for applying audio effects (fade, filters, etc).

Author: F5-TTS Training Pipeline
Sprint: 3 - Dataset Consolidation
"""
import numpy as np
from typing import Optional

# Optional dependency
try:
    from scipy import signal
except ImportError:
    signal = None


def apply_fade(
    audio: np.ndarray,
    sample_rate: int,
    fade_in_ms: float = 5.0,
    fade_out_ms: float = 5.0,
) -> np.ndarray:
    """
    Apply fade-in and fade-out to audio to prevent clicks and pops.
    
    This is essential for segmented audio to avoid audible artifacts at
    segment boundaries.
    
    Args:
        audio: Audio samples as float32 numpy array
        sample_rate: Sample rate in Hz
        fade_in_ms: Fade-in duration in milliseconds (default: 5.0)
        fade_out_ms: Fade-out duration in milliseconds (default: 5.0)
        
    Returns:
        Audio with fades applied as float32 numpy array
        
    Example:
        >>> audio = load_audio("segment.wav")
        >>> faded = apply_fade(audio, 24000, fade_in_ms=10.0, fade_out_ms=10.0)
        >>> # Audio now has smooth 10ms fade-in and fade-out
    """
    if len(audio) == 0:
        return audio
    
    audio_faded = audio.copy()
    
    # Apply fade-in
    if fade_in_ms > 0:
        n_fade_in = int(sample_rate * fade_in_ms / 1000.0)
        if n_fade_in > 0 and len(audio) >= n_fade_in:
            fade_in_curve = np.linspace(0.0, 1.0, n_fade_in, dtype=np.float32)
            audio_faded[:n_fade_in] *= fade_in_curve
    
    # Apply fade-out
    if fade_out_ms > 0:
        n_fade_out = int(sample_rate * fade_out_ms / 1000.0)
        if n_fade_out > 0 and len(audio) >= n_fade_out:
            fade_out_curve = np.linspace(1.0, 0.0, n_fade_out, dtype=np.float32)
            audio_faded[-n_fade_out:] *= fade_out_curve
    
    return audio_faded


def apply_high_pass_filter(
    audio: np.ndarray,
    sample_rate: int,
    cutoff_hz: float = 80.0,
    order: int = 5,
) -> np.ndarray:
    """
    Apply high-pass filter to remove low-frequency rumble and noise.
    
    Requires scipy. If not available, returns audio unchanged.
    
    Args:
        audio: Audio samples as float32 numpy array
        sample_rate: Sample rate in Hz
        cutoff_hz: Cutoff frequency in Hz (default: 80.0)
        order: Filter order (default: 5)
        
    Returns:
        Filtered audio as float32 numpy array
        
    Example:
        >>> audio = load_audio("speech.wav")
        >>> filtered = apply_high_pass_filter(audio, 24000, cutoff_hz=100.0)
        >>> # Low frequencies below 100Hz are attenuated
    """
    if len(audio) == 0:
        return audio
    
    if signal is None:
        import warnings
        warnings.warn("scipy not available, skipping high-pass filter", UserWarning)
        return audio
    
    try:
        # Design Butterworth high-pass filter
        nyquist = sample_rate / 2.0
        normalized_cutoff = cutoff_hz / nyquist
        
        # Ensure cutoff is in valid range
        if normalized_cutoff <= 0 or normalized_cutoff >= 1:
            import warnings
            warnings.warn(f"Invalid cutoff frequency {cutoff_hz}Hz for sample rate {sample_rate}Hz", UserWarning)
            return audio
        
        b, a = signal.butter(order, normalized_cutoff, btype='high')  # type: ignore
        
        # Apply filter
        filtered = signal.filtfilt(b, a, audio)  # type: ignore
        
        return filtered.astype(np.float32)
        
    except Exception as e:
        import warnings
        warnings.warn(f"High-pass filter failed: {e}", UserWarning)
        return audio


def apply_low_pass_filter(
    audio: np.ndarray,
    sample_rate: int,
    cutoff_hz: float = 8000.0,
    order: int = 5,
) -> np.ndarray:
    """
    Apply low-pass filter to remove high-frequency noise.
    
    Requires scipy. If not available, returns audio unchanged.
    
    Args:
        audio: Audio samples as float32 numpy array
        sample_rate: Sample rate in Hz
        cutoff_hz: Cutoff frequency in Hz (default: 8000.0)
        order: Filter order (default: 5)
        
    Returns:
        Filtered audio as float32 numpy array
        
    Example:
        >>> audio = load_audio("speech.wav")
        >>> filtered = apply_low_pass_filter(audio, 24000, cutoff_hz=7000.0)
        >>> # Frequencies above 7kHz are attenuated
    """
    if len(audio) == 0:
        return audio
    
    if signal is None:
        import warnings
        warnings.warn("scipy not available, skipping low-pass filter", UserWarning)
        return audio
    
    try:
        # Design Butterworth low-pass filter
        nyquist = sample_rate / 2.0
        normalized_cutoff = cutoff_hz / nyquist
        
        # Ensure cutoff is in valid range
        if normalized_cutoff <= 0 or normalized_cutoff >= 1:
            import warnings
            warnings.warn(f"Invalid cutoff frequency {cutoff_hz}Hz for sample rate {sample_rate}Hz", UserWarning)
            return audio
        
        b, a = signal.butter(order, normalized_cutoff, btype='low')  # type: ignore
        
        # Apply filter
        filtered = signal.filtfilt(b, a, audio)  # type: ignore
        
        return filtered.astype(np.float32)
        
    except Exception as e:
        import warnings
        warnings.warn(f"Low-pass filter failed: {e}", UserWarning)
        return audio


def apply_effects_chain(
    audio: np.ndarray,
    sample_rate: int,
    fade_in_ms: float = 5.0,
    fade_out_ms: float = 5.0,
    high_pass_hz: Optional[float] = None,
    low_pass_hz: Optional[float] = None,
) -> np.ndarray:
    """
    Apply a chain of effects to audio in optimal order.
    
    Order: filters first, then fades (to avoid filtering fade curves).
    
    Args:
        audio: Audio samples as float32 numpy array
        sample_rate: Sample rate in Hz
        fade_in_ms: Fade-in duration in ms (0 to disable)
        fade_out_ms: Fade-out duration in ms (0 to disable)
        high_pass_hz: High-pass cutoff in Hz (None to disable)
        low_pass_hz: Low-pass cutoff in Hz (None to disable)
        
    Returns:
        Processed audio as float32 numpy array
        
    Example:
        >>> audio = load_audio("speech.wav")
        >>> processed = apply_effects_chain(
        ...     audio, 24000,
        ...     fade_in_ms=10.0,
        ...     fade_out_ms=10.0,
        ...     high_pass_hz=80.0
        ... )
    """
    result = audio.copy()
    
    # Apply filters first
    if high_pass_hz is not None and high_pass_hz > 0:
        result = apply_high_pass_filter(result, sample_rate, cutoff_hz=high_pass_hz)
    
    if low_pass_hz is not None and low_pass_hz > 0:
        result = apply_low_pass_filter(result, sample_rate, cutoff_hz=low_pass_hz)
    
    # Apply fades last
    if fade_in_ms > 0 or fade_out_ms > 0:
        result = apply_fade(result, sample_rate, fade_in_ms=fade_in_ms, fade_out_ms=fade_out_ms)
    
    return result


def get_effects_config_from_dict(config: dict) -> dict:
    """
    Extract audio effects parameters from configuration dict.
    
    Args:
        config: Configuration dict with audio.* keys
        
    Returns:
        Dict with effects parameters ready for function calls
        
    Example:
        >>> config = load_config()
        >>> effects_params = get_effects_config_from_dict(config)
        >>> processed = apply_effects_chain(audio, sr, **effects_params)
    """
    audio = config.get('audio', {})
    
    return {
        'fade_in_ms': float(audio.get('fade_ms', 5.0)),
        'fade_out_ms': float(audio.get('fade_ms', 5.0)),
        'high_pass_hz': audio.get('high_pass_hz'),  # None if not set
        'low_pass_hz': audio.get('low_pass_hz'),    # None if not set
    }


# CLI for testing
if __name__ == "__main__":
    import argparse
    import soundfile as sf
    
    parser = argparse.ArgumentParser(description="Audio effects utility")
    parser.add_argument('input_file', help='Input audio file')
    parser.add_argument('output_file', help='Output audio file')
    parser.add_argument('--fade-in', type=float, default=5.0,
                       help='Fade-in duration in ms (default: 5.0)')
    parser.add_argument('--fade-out', type=float, default=5.0,
                       help='Fade-out duration in ms (default: 5.0)')
    parser.add_argument('--high-pass', type=float,
                       help='High-pass cutoff frequency in Hz')
    parser.add_argument('--low-pass', type=float,
                       help='Low-pass cutoff frequency in Hz')
    
    args = parser.parse_args()
    
    # Load audio
    audio, sr = sf.read(args.input_file, dtype='float32')
    if audio.ndim > 1:
        audio = audio.mean(axis=1)
    
    print(f"Input: {args.input_file}")
    print(f"Sample rate: {sr}Hz")
    print(f"Duration: {len(audio)/sr:.2f}s")
    print()
    
    # Apply effects
    effects = []
    if args.fade_in > 0:
        effects.append(f"fade-in {args.fade_in}ms")
    if args.fade_out > 0:
        effects.append(f"fade-out {args.fade_out}ms")
    if args.high_pass:
        effects.append(f"high-pass {args.high_pass}Hz")
    if args.low_pass:
        effects.append(f"low-pass {args.low_pass}Hz")
    
    if effects:
        print(f"Applying: {', '.join(effects)}")
    else:
        print("No effects specified")
    
    processed = apply_effects_chain(
        audio, sr,
        fade_in_ms=args.fade_in,
        fade_out_ms=args.fade_out,
        high_pass_hz=args.high_pass,
        low_pass_hz=args.low_pass
    )
    
    # Save
    sf.write(args.output_file, processed, sr)
    print(f"✅ Saved to: {args.output_file}")
