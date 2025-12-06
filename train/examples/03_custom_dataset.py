#!/usr/bin/env python3
"""
Example 3: Custom Dataset Creation

Create a custom dataset from audio files and transcriptions.
Demonstrates the complete data processing pipeline.

Usage:
    python train/examples/03_custom_dataset.py --audio-dir /path/to/audio --output-dir /path/to/output
    
Requirements:
    - Audio files (.wav, .mp3, .flac)
    - Transcriptions (same name as audio, .txt extension)
"""
import argparse
import logging
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from train.audio.io import load_audio, save_audio
from train.audio.segmentation import split_audio_into_chunks
from train.audio.vad import load_vad_model, detect_voice_segments
from train.audio.normalization import normalize_audio_volume
from train.text.normalizer import TextNormalizer
from train.text.qa import TextQualityAssurance

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def process_file(
    audio_file: Path,
    text_file: Path,
    output_dir: Path,
    vad_model,
    normalizer: TextNormalizer,
    qa: TextQualityAssurance,
) -> list[dict]:
    """Process single audio+text pair into dataset segments."""
    
    logger.info(f"Processing: {audio_file.name}")
    
    # Read transcription
    if not text_file.exists():
        logger.warning(f"Skipping {audio_file.name}: no transcription found")
        return []
    
    text = text_file.read_text(encoding="utf-8").strip()
    
    # Normalize text
    text = normalizer.normalize(text)
    
    # Quality check
    issues = qa.check_quality(text)
    if any(issue["severity"] == "error" for issue in issues):
        logger.warning(f"Skipping {audio_file.name}: text quality issues")
        for issue in issues:
            logger.warning(f"  - {issue['message']}")
        return []
    
    # Load and normalize audio
    audio, sr = load_audio(str(audio_file), target_sr=24000)
    audio = normalize_audio_volume(audio, sr, target_lufs=-23.0)
    
    # Detect voice segments
    voice_segments = detect_voice_segments(
        audio, sr, vad_model,
        min_silence_duration=0.3,
        speech_pad=0.1
    )
    
    if not voice_segments:
        logger.warning(f"Skipping {audio_file.name}: no voice detected")
        return []
    
    # Split into chunks (max 30s)
    chunks = split_audio_into_chunks(
        audio, sr, voice_segments,
        max_duration=30.0,
        min_duration=1.0
    )
    
    # Save segments
    segments = []
    for i, chunk in enumerate(chunks):
        # Save audio
        segment_name = f"{audio_file.stem}_{i:04d}"
        segment_path = output_dir / "wavs" / f"{segment_name}.wav"
        segment_path.parent.mkdir(parents=True, exist_ok=True)
        
        save_audio(chunk, str(segment_path), sr)
        
        # Calculate duration
        duration = len(chunk) / sr
        
        segments.append({
            "audio_path": f"wavs/{segment_name}.wav",
            "text": text,
            "duration": duration,
            "speaker_id": audio_file.stem,
        })
    
    logger.info(f"  Created {len(segments)} segments ({sum(s['duration'] for s in segments):.1f}s)")
    return segments


def main():
    """Create custom dataset from audio files."""
    
    parser = argparse.ArgumentParser(description="Create custom F5-TTS dataset")
    parser.add_argument(
        "--audio-dir",
        type=Path,
        required=True,
        help="Directory with audio files (.wav, .mp3, .flac)"
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("train/data/custom"),
        help="Output directory for dataset"
    )
    parser.add_argument(
        "--audio-extensions",
        nargs="+",
        default=[".wav", ".mp3", ".flac"],
        help="Audio file extensions to process"
    )
    
    args = parser.parse_args()
    
    print("=" * 60)
    print("F5-TTS Custom Dataset Creation")
    print("=" * 60)
    print()
    
    # Validate input
    if not args.audio_dir.exists():
        logger.error(f"❌ Audio directory not found: {args.audio_dir}")
        return 1
    
    # Find audio files
    audio_files = []
    for ext in args.audio_extensions:
        audio_files.extend(args.audio_dir.glob(f"*{ext}"))
    
    if not audio_files:
        logger.error(f"❌ No audio files found in: {args.audio_dir}")
        return 1
    
    logger.info(f"Found {len(audio_files)} audio files")
    print()
    
    # Initialize processors
    print("⏳ Loading models...")
    vad_model = load_vad_model()
    normalizer = TextNormalizer()
    qa = TextQualityAssurance()
    print("✅ Models loaded!")
    print()
    
    # Process files
    print("🔄 Processing files...")
    print("-" * 60)
    
    all_segments = []
    for audio_file in audio_files:
        text_file = audio_file.with_suffix(".txt")
        
        segments = process_file(
            audio_file, text_file, args.output_dir,
            vad_model, normalizer, qa
        )
        all_segments.extend(segments)
    
    print()
    
    if not all_segments:
        logger.error("❌ No valid segments created!")
        return 1
    
    # Create metadata.csv
    print("💾 Saving metadata...")
    metadata_path = args.output_dir / "metadata.csv"
    metadata_path.parent.mkdir(parents=True, exist_ok=True)
    
    import pandas as pd
    df = pd.DataFrame(all_segments)
    df.to_csv(metadata_path, sep="|", index=False)
    
    # Statistics
    total_duration = df["duration"].sum()
    num_speakers = df["speaker_id"].nunique()
    
    print()
    print("=" * 60)
    print("✅ Dataset created!")
    print(f"  Segments: {len(all_segments)}")
    print(f"  Total duration: {total_duration / 3600:.2f}h")
    print(f"  Speakers: {num_speakers}")
    print(f"  Output: {args.output_dir}")
    print(f"  Metadata: {metadata_path}")
    print()
    print("Next steps:")
    print("  1. Review metadata.csv")
    print("  2. Update config.yaml with dataset path")
    print("  3. Start training!")
    print("=" * 60)
    
    return 0


if __name__ == "__main__":
    exit(main())
