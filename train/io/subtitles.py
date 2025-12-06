"""
Subtitle Extraction and Parsing Module

Functions for working with video subtitles (SRT, VTT formats).

Author: F5-TTS Training Pipeline
Sprint: 3 - Dataset Consolidation
"""
import re
from pathlib import Path
from typing import List, Optional, Tuple
from dataclasses import dataclass
import logging

logger = logging.getLogger(__name__)

# Optional dependency
try:
    import yt_dlp
except ImportError:
    yt_dlp = None


@dataclass
class Subtitle:
    """A single subtitle entry."""
    index: int
    start_time: float  # seconds
    end_time: float    # seconds
    text: str
    
    def __str__(self):
        return f"Subtitle({self.start_time:.1f}s-{self.end_time:.1f}s: '{self.text[:30]}...')"
    
    @property
    def duration(self) -> float:
        """Duration of subtitle in seconds."""
        return self.end_time - self.start_time


def parse_srt_timestamp(timestamp: str) -> float:
    """
    Parse SRT timestamp to seconds.
    
    Args:
        timestamp: SRT timestamp (e.g., "00:01:23,456")
        
    Returns:
        Time in seconds
        
    Example:
        >>> parse_srt_timestamp("00:01:23,456")
        83.456
    """
    # Format: HH:MM:SS,mmm
    time_parts = timestamp.replace(',', '.').split(':')
    hours = int(time_parts[0])
    minutes = int(time_parts[1])
    seconds = float(time_parts[2])
    
    return hours * 3600 + minutes * 60 + seconds


def parse_vtt_timestamp(timestamp: str) -> float:
    """
    Parse WebVTT timestamp to seconds.
    
    Args:
        timestamp: VTT timestamp (e.g., "00:01:23.456" or "01:23.456")
        
    Returns:
        Time in seconds
        
    Example:
        >>> parse_vtt_timestamp("00:01:23.456")
        83.456
        >>> parse_vtt_timestamp("01:23.456")
        83.456
    """
    # Format can be HH:MM:SS.mmm or MM:SS.mmm
    parts = timestamp.split(':')
    
    if len(parts) == 3:
        # HH:MM:SS.mmm
        hours = int(parts[0])
        minutes = int(parts[1])
        seconds = float(parts[2])
        return hours * 3600 + minutes * 60 + seconds
    elif len(parts) == 2:
        # MM:SS.mmm
        minutes = int(parts[0])
        seconds = float(parts[1])
        return minutes * 60 + seconds
    else:
        raise ValueError(f"Invalid VTT timestamp: {timestamp}")


def parse_srt(content: str) -> List[Subtitle]:
    """
    Parse SRT subtitle file content.
    
    Args:
        content: SRT file content as string
        
    Returns:
        List of Subtitle objects
        
    Example:
        >>> srt_content = '''1
        ... 00:00:01,000 --> 00:00:03,000
        ... Hello world
        ... 
        ... 2
        ... 00:00:04,000 --> 00:00:06,000
        ... Second subtitle
        ... '''
        >>> subtitles = parse_srt(srt_content)
        >>> len(subtitles)
        2
    """
    subtitles = []
    
    # Split into blocks (separated by blank lines)
    blocks = re.split(r'\n\s*\n', content.strip())
    
    for block in blocks:
        if not block.strip():
            continue
        
        lines = block.strip().split('\n')
        
        if len(lines) < 3:
            continue  # Invalid block
        
        try:
            # Line 1: index
            index = int(lines[0].strip())
            
            # Line 2: timestamps
            timestamp_line = lines[1].strip()
            match = re.match(r'(\d{2}:\d{2}:\d{2},\d{3})\s*-->\s*(\d{2}:\d{2}:\d{2},\d{3})', timestamp_line)
            
            if not match:
                continue
            
            start_time = parse_srt_timestamp(match.group(1))
            end_time = parse_srt_timestamp(match.group(2))
            
            # Line 3+: text
            text = '\n'.join(lines[2:]).strip()
            
            # Remove HTML tags if present
            text = re.sub(r'<[^>]+>', '', text)
            
            subtitles.append(Subtitle(
                index=index,
                start_time=start_time,
                end_time=end_time,
                text=text
            ))
        
        except (ValueError, IndexError) as e:
            logger.warning(f"Failed to parse SRT block: {e}")
            continue
    
    return subtitles


def parse_vtt(content: str) -> List[Subtitle]:
    """
    Parse WebVTT subtitle file content.
    
    Args:
        content: VTT file content as string
        
    Returns:
        List of Subtitle objects
        
    Example:
        >>> vtt_content = '''WEBVTT
        ... 
        ... 00:01.000 --> 00:03.000
        ... Hello world
        ... 
        ... 00:04.000 --> 00:06.000
        ... Second subtitle
        ... '''
        >>> subtitles = parse_vtt(vtt_content)
        >>> len(subtitles)
        2
    """
    subtitles = []
    
    # Remove WEBVTT header
    content = re.sub(r'^WEBVTT[^\n]*\n', '', content, flags=re.MULTILINE)
    
    # Split into blocks
    blocks = re.split(r'\n\s*\n', content.strip())
    
    index = 0
    for block in blocks:
        if not block.strip():
            continue
        
        lines = block.strip().split('\n')
        
        # Find timestamp line
        timestamp_line = None
        text_start = 0
        
        for i, line in enumerate(lines):
            if '-->' in line:
                timestamp_line = line
                text_start = i + 1
                break
        
        if not timestamp_line:
            continue
        
        try:
            # Parse timestamps
            match = re.match(r'([\d:\.]+)\s*-->\s*([\d:\.]+)', timestamp_line)
            
            if not match:
                continue
            
            start_time = parse_vtt_timestamp(match.group(1))
            end_time = parse_vtt_timestamp(match.group(2))
            
            # Get text
            text = '\n'.join(lines[text_start:]).strip()
            
            # Remove HTML tags if present
            text = re.sub(r'<[^>]+>', '', text)
            
            index += 1
            subtitles.append(Subtitle(
                index=index,
                start_time=start_time,
                end_time=end_time,
                text=text
            ))
        
        except (ValueError, IndexError) as e:
            logger.warning(f"Failed to parse VTT block: {e}")
            continue
    
    return subtitles


def extract_subtitles(
    url: str,
    output_path: Optional[Path] = None,
    lang: str = 'pt',
    auto_generated: bool = True,
) -> Optional[List[Subtitle]]:
    """
    Extract subtitles from YouTube video.
    
    Args:
        url: YouTube video URL
        output_path: Optional path to save subtitle file
        lang: Language code (default: 'pt' for Portuguese)
        auto_generated: Accept auto-generated subtitles (default: True)
        
    Returns:
        List of Subtitle objects, or None if no subtitles found
        
    Raises:
        ImportError: If yt-dlp is not installed
        
    Example:
        >>> subtitles = extract_subtitles(
        ...     "https://youtube.com/watch?v=...",
        ...     lang='pt'
        ... )
        >>> if subtitles:
        ...     print(f"Found {len(subtitles)} subtitle entries")
    """
    if yt_dlp is None:
        raise ImportError("yt-dlp is required. Install with: pip install yt-dlp")
    
    ydl_opts = {
        'skip_download': True,
        'writesubtitles': True,
        'writeautomaticsub': auto_generated,
        'subtitleslangs': [lang],
        'subtitlesformat': 'vtt',
        'quiet': True,
    }
    
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:  # type: ignore
            info_dict = ydl.extract_info(url, download=False)
            
            # Get subtitle content
            subtitles_dict = info_dict.get('subtitles', {})
            auto_subs_dict = info_dict.get('automatic_captions', {})
            
            # Try manual subtitles first, then auto-generated
            subtitle_content = None
            
            if lang in subtitles_dict:
                # Manual subtitles
                for sub_info in subtitles_dict[lang]:
                    if sub_info.get('ext') == 'vtt':
                        # Download subtitle
                        subtitle_url = sub_info.get('url')
                        if subtitle_url:
                            import urllib.request
                            with urllib.request.urlopen(subtitle_url) as response:
                                subtitle_content = response.read().decode('utf-8')
                            break
            
            elif auto_generated and lang in auto_subs_dict:
                # Auto-generated subtitles
                for sub_info in auto_subs_dict[lang]:
                    if sub_info.get('ext') == 'vtt':
                        subtitle_url = sub_info.get('url')
                        if subtitle_url:
                            import urllib.request
                            with urllib.request.urlopen(subtitle_url) as response:
                                subtitle_content = response.read().decode('utf-8')
                            break
            
            if not subtitle_content:
                logger.warning(f"No subtitles found for language: {lang}")
                return None
            
            # Parse subtitles
            subtitles = parse_vtt(subtitle_content)
            
            # Save to file if requested
            if output_path:
                output_path = Path(output_path)
                output_path.parent.mkdir(parents=True, exist_ok=True)
                output_path.write_text(subtitle_content, encoding='utf-8')
                logger.info(f"✅ Saved subtitles to: {output_path}")
            
            return subtitles
    
    except Exception as e:
        logger.error(f"Failed to extract subtitles: {e}")
        return None


def merge_subtitle_lines(
    subtitles: List[Subtitle],
    max_gap: float = 0.5,
) -> List[Subtitle]:
    """
    Merge consecutive subtitle lines with small gaps.
    
    Useful for combining subtitles that were split across multiple lines.
    
    Args:
        subtitles: List of Subtitle objects
        max_gap: Maximum gap in seconds to merge (default: 0.5)
        
    Returns:
        List of merged Subtitle objects
        
    Example:
        >>> subs = [
        ...     Subtitle(1, 0.0, 2.0, "Hello"),
        ...     Subtitle(2, 2.1, 4.0, "world"),
        ... ]
        >>> merged = merge_subtitle_lines(subs, max_gap=0.5)
        >>> len(merged)
        1
        >>> merged[0].text
        'Hello world'
    """
    if not subtitles:
        return []
    
    merged = []
    current = subtitles[0]
    
    for next_sub in subtitles[1:]:
        gap = next_sub.start_time - current.end_time
        
        if gap <= max_gap:
            # Merge with current
            current = Subtitle(
                index=current.index,
                start_time=current.start_time,
                end_time=next_sub.end_time,
                text=current.text + ' ' + next_sub.text
            )
        else:
            # Save current and start new
            merged.append(current)
            current = next_sub
    
    # Add last subtitle
    merged.append(current)
    
    return merged


# CLI for testing
if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Subtitle extraction utility")
    
    subparsers = parser.add_subparsers(dest='command', help='Command to execute')
    
    # Extract command
    extract_parser = subparsers.add_parser('extract', help='Extract subtitles from YouTube')
    extract_parser.add_argument('url', help='YouTube video URL')
    extract_parser.add_argument('--output', help='Output file path')
    extract_parser.add_argument('--lang', default='pt', help='Language code (default: pt)')
    extract_parser.add_argument('--no-auto', action='store_true',
                               help='Disable auto-generated subtitles')
    
    # Parse command
    parse_parser = subparsers.add_parser('parse', help='Parse subtitle file')
    parse_parser.add_argument('file', help='Subtitle file (SRT or VTT)')
    parse_parser.add_argument('--merge', type=float, default=0.0,
                             help='Merge lines with gap <= N seconds')
    
    args = parser.parse_args()
    
    if args.command == 'extract':
        subtitles = extract_subtitles(
            args.url,
            output_path=Path(args.output) if args.output else None,
            lang=args.lang,
            auto_generated=not args.no_auto
        )
        
        if subtitles:
            print(f"\n✅ Extracted {len(subtitles)} subtitle entries")
            print(f"\nFirst 5 entries:")
            for sub in subtitles[:5]:
                print(f"  [{sub.start_time:.1f}s - {sub.end_time:.1f}s] {sub.text[:50]}...")
        else:
            print(f"\n❌ No subtitles found")
    
    elif args.command == 'parse':
        file_path = Path(args.file)
        if not file_path.exists():
            print(f"Error: File not found: {file_path}")
            exit(1)
        
        content = file_path.read_text(encoding='utf-8')
        
        # Detect format
        if content.startswith('WEBVTT'):
            subtitles = parse_vtt(content)
            print(f"Format: WebVTT")
        else:
            subtitles = parse_srt(content)
            print(f"Format: SRT")
        
        print(f"Parsed {len(subtitles)} subtitle entries")
        
        # Merge if requested
        if args.merge > 0:
            merged = merge_subtitle_lines(subtitles, max_gap=args.merge)
            print(f"Merged to {len(merged)} entries (gap <= {args.merge}s)")
            subtitles = merged
        
        # Show sample
        print(f"\nFirst 5 entries:")
        for sub in subtitles[:5]:
            print(f"  {sub.index}. [{sub.start_time:.1f}s - {sub.end_time:.1f}s] ({sub.duration:.1f}s)")
            print(f"     {sub.text}")
    
    else:
        parser.print_help()
