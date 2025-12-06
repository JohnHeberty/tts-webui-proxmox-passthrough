"""
Voice Activity Detection (VAD) Module

Pure functions for detecting speech regions in audio using energy-based methods.

Author: F5-TTS Training Pipeline
Sprint: 3 - Dataset Consolidation
"""

import math

import numpy as np


def detect_voice_in_chunk(
    audio_chunk: np.ndarray,
    sample_rate: int,
    frame_size: int = 512,
    hop_size: int = 256,
    threshold_db: float = -40.0,
    min_silence_duration: float = 0.3,
) -> list[tuple[float, float]]:
    """
    Detect voice regions in an audio chunk using RMS energy in dB.

    This is a pure function that operates on a numpy array and returns
    time ranges where voice is detected.

    Args:
        audio_chunk: Audio samples as float32 numpy array (mono)
        sample_rate: Sample rate in Hz
        frame_size: Frame size for energy calculation (default: 512)
        hop_size: Hop size between frames (default: 256)
        threshold_db: dB threshold above which is considered voice (default: -40.0)
        min_silence_duration: Minimum silence duration to split regions (seconds)

    Returns:
        List of (start_sec, end_sec) tuples representing voice regions.
        Times are relative to the start of the chunk.

    Example:
        >>> audio = np.random.randn(48000).astype(np.float32)  # 1 second at 48kHz
        >>> regions = detect_voice_in_chunk(audio, 48000)
        >>> print(regions)
        [(0.12, 0.85)]
    """
    if frame_size <= 0 or hop_size <= 0:
        raise ValueError("frame_size and hop_size must be > 0")

    if len(audio_chunk) == 0:
        return []

    # Calculate number of frames
    num_frames = max(0, (len(audio_chunk) - frame_size) // hop_size + 1)

    if num_frames == 0:
        return []

    # State machine for voice detection
    segments: list[tuple[float, float]] = []
    in_voice = False
    voice_start = 0.0

    min_silence_frames = max(1, int(min_silence_duration * sample_rate / hop_size))
    silence_count = 0
    eps = 1e-10

    for i in range(num_frames):
        start_idx = i * hop_size
        end_idx = start_idx + frame_size
        frame = audio_chunk[start_idx:end_idx]

        # Calculate RMS energy in dB
        rms = float(np.sqrt(np.mean(frame * frame) + eps))
        db = 20.0 * math.log10(rms + eps)

        has_voice = db > threshold_db
        time = start_idx / sample_rate  # Time relative to chunk start

        if has_voice:
            if not in_voice:
                # Voice starts
                voice_start = time
                in_voice = True
            silence_count = 0
        else:
            if in_voice:
                # Potential voice end, but wait for min_silence_duration
                silence_count += 1
                if silence_count >= min_silence_frames:
                    # Confirmed voice end
                    voice_end = time
                    if voice_end > voice_start:
                        segments.append((voice_start, voice_end))
                    in_voice = False
                    silence_count = 0

    # If chunk ends while still in voice
    if in_voice:
        voice_end = (num_frames * hop_size) / sample_rate
        if voice_end > voice_start:
            segments.append((voice_start, voice_end))

    return segments


def detect_voice_regions(
    audio: np.ndarray,
    sample_rate: int,
    frame_size: int = 512,
    hop_size: int = 256,
    threshold_db: float = -40.0,
    min_silence_duration: float = 0.3,
    merge_gap: float = 0.3,
) -> list[tuple[float, float]]:
    """
    Detect voice regions in full audio array with merging of close regions.

    This function processes the entire audio and merges regions that are
    separated by less than merge_gap seconds.

    Args:
        audio: Full audio as float32 numpy array (mono)
        sample_rate: Sample rate in Hz
        frame_size: Frame size for energy calculation (default: 512)
        hop_size: Hop size between frames (default: 256)
        threshold_db: dB threshold for voice detection (default: -40.0)
        min_silence_duration: Minimum silence to split regions (seconds)
        merge_gap: Maximum gap between regions to merge them (seconds)

    Returns:
        List of (start_sec, end_sec) tuples representing merged voice regions.

    Example:
        >>> audio = load_audio("speech.wav")
        >>> regions = detect_voice_regions(audio, 24000)
        >>> print(f"Found {len(regions)} speech regions")
        Found 3 speech regions
    """
    # Detect initial regions
    raw_segments = detect_voice_in_chunk(
        audio,
        sample_rate,
        frame_size=frame_size,
        hop_size=hop_size,
        threshold_db=threshold_db,
        min_silence_duration=min_silence_duration,
    )

    if not raw_segments:
        return []

    # Merge regions that are close together
    merged: list[tuple[float, float]] = []
    current_start, current_end = raw_segments[0]

    for start, end in raw_segments[1:]:
        if start - current_end <= merge_gap:
            # Merge with current region
            current_end = max(current_end, end)
        else:
            # Save current region and start new one
            merged.append((current_start, current_end))
            current_start, current_end = start, end

    # Add final region
    merged.append((current_start, current_end))

    return merged


def get_vad_config_from_dict(config: dict) -> dict:
    """
    Extract VAD parameters from configuration dict.

    Args:
        config: Configuration dict with segmentation.vad_* keys

    Returns:
        Dict with VAD parameters ready for function calls

    Example:
        >>> config = load_config()
        >>> vad_params = get_vad_config_from_dict(config)
        >>> regions = detect_voice_regions(audio, sr, **vad_params)
    """
    seg = config.get("segmentation", {})

    return {
        "frame_size": int(seg.get("vad_frame_size", 512)),
        "hop_size": int(seg.get("vad_frame_size", 512)) // 2,
        "threshold_db": float(seg.get("vad_threshold", -40.0)),
        "min_silence_duration": float(seg.get("min_silence_duration", 0.3)),
        "merge_gap": float(seg.get("min_silence_duration", 0.3)),
    }


# CLI for testing
if __name__ == "__main__":
    import argparse

    import soundfile as sf

    parser = argparse.ArgumentParser(description="VAD testing utility")
    parser.add_argument("audio_file", help="Audio file to analyze")
    parser.add_argument(
        "--threshold", type=float, default=-40.0, help="dB threshold (default: -40.0)"
    )
    parser.add_argument(
        "--min-silence", type=float, default=0.3, help="Minimum silence duration in seconds"
    )

    args = parser.parse_args()

    # Load audio
    audio, sr = sf.read(args.audio_file, dtype="float32")
    if audio.ndim > 1:
        audio = audio.mean(axis=1)

    print(f"Loaded: {args.audio_file}")
    print(f"Duration: {len(audio)/sr:.2f}s")
    print(f"Sample rate: {sr}Hz")
    print()

    # Detect regions
    regions = detect_voice_regions(
        audio, sr, threshold_db=args.threshold, min_silence_duration=args.min_silence
    )

    print(f"Found {len(regions)} voice regions:")
    total_voice = 0.0
    for i, (start, end) in enumerate(regions, 1):
        duration = end - start
        total_voice += duration
        print(f"  {i}. {start:.2f}s - {end:.2f}s ({duration:.2f}s)")

    print()
    print(f"Total voice: {total_voice:.2f}s ({total_voice/(len(audio)/sr)*100:.1f}%)")
