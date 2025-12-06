"""
Audio Segmentation Module

Pure functions for splitting audio into segments based on voice regions.

Author: F5-TTS Training Pipeline
Sprint: 3 - Dataset Consolidation
"""


import numpy as np


def segment_audio(
    voice_regions: list[tuple[float, float]],
    min_duration: float = 3.0,
    max_duration: float = 7.0,
    overlap: float = 0.0,
) -> list[tuple[float, float]]:
    """
    Split voice regions into fixed-duration segments with optional overlap.

    This is a pure function that takes voice regions (from VAD) and splits them
    into segments suitable for TTS training.

    Args:
        voice_regions: List of (start_sec, end_sec) tuples from VAD
        min_duration: Minimum segment duration in seconds (default: 3.0)
        max_duration: Maximum segment duration in seconds (default: 7.0)
        overlap: Overlap between consecutive segments in seconds (default: 0.0)

    Returns:
        List of (start_sec, end_sec) tuples representing final segments.
        All segments will be between min_duration and max_duration.

    Example:
        >>> regions = [(0.0, 15.0), (20.0, 25.0)]
        >>> segments = segment_audio(regions, min_duration=3.0, max_duration=7.0)
        >>> print(segments)
        [(0.0, 7.0), (7.0, 14.0), (14.0, 15.0), (20.0, 25.0)]
    """
    if max_duration <= 0 or min_duration <= 0:
        raise ValueError("min_duration and max_duration must be > 0")

    if min_duration > max_duration:
        raise ValueError("min_duration cannot be greater than max_duration")

    segments: list[tuple[float, float]] = []
    step = max(0.1, max_duration - overlap)

    for region_start, region_end in voice_regions:
        region_dur = region_end - region_start

        # Skip regions shorter than min_duration
        if region_dur < min_duration:
            continue

        cur_start = region_start

        while True:
            # Check if we can fit at least min_duration from cur_start
            if cur_start + min_duration > region_end:
                break

            # Calculate segment end (up to max_duration, but not past region_end)
            seg_end = min(cur_start + max_duration, region_end)
            seg_dur = seg_end - cur_start

            # Only add if meets minimum duration
            if seg_dur >= min_duration:
                segments.append((cur_start, seg_end))

            # If we've reached the end of the region, stop
            if seg_end >= region_end:
                break

            # Move to next segment with overlap
            cur_start = seg_end - overlap

            # Prevent infinite loop
            if cur_start >= region_end - min_duration:
                break

    return segments


def merge_voice_regions(
    regions: list[tuple[float, float]],
    max_gap: float = 0.3,
) -> list[tuple[float, float]]:
    """
    Merge voice regions that are separated by less than max_gap seconds.

    This is useful for combining regions that VAD split due to brief pauses.

    Args:
        regions: List of (start_sec, end_sec) tuples
        max_gap: Maximum gap between regions to merge them (seconds)

    Returns:
        List of merged (start_sec, end_sec) tuples

    Example:
        >>> regions = [(0.0, 1.0), (1.2, 2.0), (5.0, 6.0)]
        >>> merged = merge_voice_regions(regions, max_gap=0.5)
        >>> print(merged)
        [(0.0, 2.0), (5.0, 6.0)]
    """
    if not regions:
        return []

    # Sort by start time
    sorted_regions = sorted(regions, key=lambda x: x[0])

    merged: list[tuple[float, float]] = []
    current_start, current_end = sorted_regions[0]

    for start, end in sorted_regions[1:]:
        if start - current_end <= max_gap:
            # Merge with current region
            current_end = max(current_end, end)
        else:
            # Save current region and start new one
            merged.append((current_start, current_end))
            current_start, current_end = start, end

    # Add final region
    merged.append((current_start, current_end))

    return merged


def extract_segments_from_audio(
    audio: np.ndarray,
    sample_rate: int,
    segments: list[tuple[float, float]],
) -> list[np.ndarray]:
    """
    Extract audio chunks corresponding to segment time ranges.

    Args:
        audio: Full audio as float32 numpy array (mono)
        sample_rate: Sample rate in Hz
        segments: List of (start_sec, end_sec) tuples

    Returns:
        List of audio arrays, one per segment

    Example:
        >>> audio = load_audio("speech.wav")
        >>> segments = [(0.0, 3.0), (5.0, 8.0)]
        >>> chunks = extract_segments_from_audio(audio, 24000, segments)
        >>> print(f"Extracted {len(chunks)} segments")
    """
    chunks: list[np.ndarray] = []

    for start_sec, end_sec in segments:
        start_sample = int(start_sec * sample_rate)
        end_sample = int(end_sec * sample_rate)

        # Clamp to audio bounds
        start_sample = max(0, start_sample)
        end_sample = min(len(audio), end_sample)

        if start_sample < end_sample:
            chunk = audio[start_sample:end_sample]
            chunks.append(chunk.copy())  # Copy to avoid reference issues

    return chunks


def calculate_segment_statistics(segments: list[tuple[float, float]]) -> dict:
    """
    Calculate statistics about segment durations.

    Args:
        segments: List of (start_sec, end_sec) tuples

    Returns:
        Dictionary with min, max, mean, median, total duration

    Example:
        >>> segments = [(0.0, 3.5), (5.0, 8.2), (10.0, 13.7)]
        >>> stats = calculate_segment_statistics(segments)
        >>> print(f"Average: {stats['mean']:.2f}s")
    """
    if not segments:
        return {
            "count": 0,
            "min": 0.0,
            "max": 0.0,
            "mean": 0.0,
            "median": 0.0,
            "total": 0.0,
        }

    durations = [end - start for start, end in segments]
    durations_sorted = sorted(durations)

    n = len(durations)
    median = (
        durations_sorted[n // 2]
        if n % 2 == 1
        else (durations_sorted[n // 2 - 1] + durations_sorted[n // 2]) / 2
    )

    return {
        "count": len(segments),
        "min": min(durations),
        "max": max(durations),
        "mean": sum(durations) / len(durations),
        "median": median,
        "total": sum(durations),
    }


def get_segmentation_config_from_dict(config: dict) -> dict:
    """
    Extract segmentation parameters from configuration dict.

    Args:
        config: Configuration dict with segmentation.* keys

    Returns:
        Dict with segmentation parameters ready for function calls

    Example:
        >>> config = load_config()
        >>> seg_params = get_segmentation_config_from_dict(config)
        >>> segments = segment_audio(regions, **seg_params)
    """
    seg = config.get("segmentation", {})

    return {
        "min_duration": float(seg.get("min_duration", 3.0)),
        "max_duration": float(seg.get("max_duration", 7.0)),
        "overlap": float(seg.get("segment_overlap", 0.0)),
    }


# CLI for testing
if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Segmentation testing utility")
    parser.add_argument(
        "--min-duration", type=float, default=3.0, help="Minimum segment duration (default: 3.0)"
    )
    parser.add_argument(
        "--max-duration", type=float, default=7.0, help="Maximum segment duration (default: 7.0)"
    )
    parser.add_argument(
        "--overlap", type=float, default=0.0, help="Overlap between segments (default: 0.0)"
    )

    args = parser.parse_args()

    # Test with sample regions
    test_regions = [
        (0.0, 15.5),  # Long region - should be split
        (20.0, 22.5),  # Short region - might be discarded
        (30.0, 35.2),  # Medium region
    ]

    print("Input regions:")
    for i, (start, end) in enumerate(test_regions, 1):
        print(f"  {i}. {start:.1f}s - {end:.1f}s ({end-start:.1f}s)")

    print()

    segments = segment_audio(
        test_regions,
        min_duration=args.min_duration,
        max_duration=args.max_duration,
        overlap=args.overlap,
    )

    print(f"Generated {len(segments)} segments:")
    for i, (start, end) in enumerate(segments, 1):
        print(f"  {i}. {start:.1f}s - {end:.1f}s ({end-start:.1f}s)")

    print()

    stats = calculate_segment_statistics(segments)
    print("Statistics:")
    print(f"  Count: {stats['count']}")
    print(f"  Min: {stats['min']:.2f}s")
    print(f"  Max: {stats['max']:.2f}s")
    print(f"  Mean: {stats['mean']:.2f}s")
    print(f"  Median: {stats['median']:.2f}s")
    print(f"  Total: {stats['total']:.2f}s")
