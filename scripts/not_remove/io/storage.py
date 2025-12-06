"""
File Storage and Management Utilities

Safe file operations for dataset management.

Author: F5-TTS Training Pipeline
Sprint: 3 - Dataset Consolidation
"""

import hashlib
import logging
from pathlib import Path
import re
import shutil
import tempfile
from typing import Union


logger = logging.getLogger(__name__)


def ensure_directory(path: Union[str, Path]) -> Path:
    """
    Ensure directory exists, create if needed.

    Args:
        path: Directory path

    Returns:
        Path object for the directory

    Example:
        >>> ensure_directory("/tmp/test/nested/dir")
        PosixPath('/tmp/test/nested/dir')
    """
    path = Path(path)
    path.mkdir(parents=True, exist_ok=True)
    return path


def safe_filename(
    filename: str,
    max_length: int = 255,
    replacement: str = "_",
) -> str:
    """
    Convert string to safe filename.

    Removes or replaces characters that are invalid in filenames.

    Args:
        filename: Original filename
        max_length: Maximum filename length (default: 255)
        replacement: Replacement for invalid chars (default: '_')

    Returns:
        Safe filename string

    Example:
        >>> safe_filename("Hello/World?.txt")
        'Hello_World_.txt'
        >>> safe_filename("a" * 300)  # Length truncation
        'aaa...'  # (255 chars)
    """
    # Remove or replace invalid characters
    # Invalid: / \ : * ? " < > |
    invalid_chars = r'[/\\:*?"<>|]'
    safe = re.sub(invalid_chars, replacement, filename)

    # Remove leading/trailing dots and spaces
    safe = safe.strip(". ")

    # Truncate if too long
    if len(safe) > max_length:
        # Keep extension if present
        name = Path(safe).stem
        ext = Path(safe).suffix

        # Calculate max name length
        max_name_len = max_length - len(ext)

        if max_name_len > 0:
            safe = name[:max_name_len] + ext
        else:
            # No room for extension
            safe = safe[:max_length]

    # Fallback if empty
    if not safe:
        safe = "unnamed"

    return safe


def atomic_write(
    path: Union[str, Path],
    content: Union[str, bytes],
    encoding: str | None = "utf-8",
) -> None:
    """
    Write file atomically using temp file + rename.

    This prevents partial writes if the process is interrupted.

    Args:
        path: Target file path
        content: Content to write (str or bytes)
        encoding: Text encoding (default: 'utf-8'), None for binary

    Example:
        >>> atomic_write("/tmp/test.txt", "Hello World")
        >>> atomic_write("/tmp/test.bin", b"\\x00\\x01\\x02", encoding=None)
    """
    path = Path(path)

    # Ensure directory exists
    path.parent.mkdir(parents=True, exist_ok=True)

    # Write to temp file in same directory (same filesystem)
    # This ensures rename is atomic
    with tempfile.NamedTemporaryFile(
        mode="wb" if encoding is None else "w",
        dir=path.parent,
        delete=False,
        encoding=encoding,
    ) as tmp:
        tmp_path = Path(tmp.name)
        tmp.write(content)

    # Atomic rename
    try:
        tmp_path.replace(path)
    except Exception as e:
        # Clean up temp file on error
        tmp_path.unlink(missing_ok=True)
        raise e


def get_file_hash(
    path: Union[str, Path],
    algorithm: str = "sha256",
    chunk_size: int = 8192,
) -> str:
    """
    Calculate file hash.

    Args:
        path: File path
        algorithm: Hash algorithm (default: 'sha256')
        chunk_size: Read chunk size in bytes (default: 8192)

    Returns:
        Hex digest string

    Example:
        >>> hash_val = get_file_hash("/tmp/test.txt")
        >>> len(hash_val)
        64  # SHA256 hex digest
    """
    path = Path(path)

    hasher = hashlib.new(algorithm)

    with open(path, "rb") as f:
        while chunk := f.read(chunk_size):
            hasher.update(chunk)

    return hasher.hexdigest()


def copy_with_progress(
    src: Union[str, Path],
    dst: Union[str, Path],
    chunk_size: int = 1024 * 1024,  # 1MB
) -> None:
    """
    Copy file with progress logging.

    Args:
        src: Source file path
        dst: Destination file path
        chunk_size: Copy chunk size in bytes (default: 1MB)

    Example:
        >>> copy_with_progress("/tmp/large_file.bin", "/tmp/backup.bin")
    """
    src = Path(src)
    dst = Path(dst)

    if not src.exists():
        raise FileNotFoundError(f"Source file not found: {src}")

    # Ensure destination directory exists
    dst.parent.mkdir(parents=True, exist_ok=True)

    total_size = src.stat().st_size
    copied = 0

    with open(src, "rb") as f_src, open(dst, "wb") as f_dst:
        while chunk := f_src.read(chunk_size):
            f_dst.write(chunk)
            copied += len(chunk)

            # Log progress every 10%
            progress = (copied / total_size) * 100
            if progress % 10 < (chunk_size / total_size) * 100:
                logger.info(f"Progress: {progress:.1f}% ({copied}/{total_size} bytes)")

    logger.info(f"✅ Copied {src} -> {dst} ({total_size} bytes)")


def move_with_backup(
    src: Union[str, Path],
    dst: Union[str, Path],
    backup_suffix: str = ".bak",
) -> Path | None:
    """
    Move file, backing up destination if it exists.

    Args:
        src: Source file path
        dst: Destination file path
        backup_suffix: Suffix for backup file (default: '.bak')

    Returns:
        Path to backup file if created, None otherwise

    Example:
        >>> backup = move_with_backup("/tmp/new.txt", "/tmp/old.txt")
        >>> # /tmp/old.txt -> /tmp/old.txt.bak
        >>> # /tmp/new.txt -> /tmp/old.txt
    """
    src = Path(src)
    dst = Path(dst)

    if not src.exists():
        raise FileNotFoundError(f"Source file not found: {src}")

    backup_path = None

    # Backup existing destination
    if dst.exists():
        backup_path = dst.with_suffix(dst.suffix + backup_suffix)
        shutil.copy2(dst, backup_path)
        logger.info(f"📦 Backed up {dst} -> {backup_path}")

    # Ensure destination directory exists
    dst.parent.mkdir(parents=True, exist_ok=True)

    # Move file
    shutil.move(str(src), str(dst))
    logger.info(f"✅ Moved {src} -> {dst}")

    return backup_path


def clean_directory(
    path: Union[str, Path],
    pattern: str = "*",
    recursive: bool = False,
    dry_run: bool = False,
) -> int:
    """
    Remove files matching pattern from directory.

    Args:
        path: Directory path
        pattern: Glob pattern (default: '*' for all files)
        recursive: Search recursively (default: False)
        dry_run: Only show what would be deleted (default: False)

    Returns:
        Number of files deleted

    Example:
        >>> # Remove all .tmp files
        >>> count = clean_directory("/tmp/cache", pattern="*.tmp")
        >>> print(f"Deleted {count} files")
    """
    path = Path(path)

    if not path.exists():
        logger.warning(f"Directory not found: {path}")
        return 0

    if not path.is_dir():
        raise ValueError(f"Not a directory: {path}")

    # Find matching files
    if recursive:
        files = path.rglob(pattern)
    else:
        files = path.glob(pattern)

    # Filter to files only (exclude directories)
    files = [f for f in files if f.is_file()]

    count = 0
    for file_path in files:
        if dry_run:
            logger.info(f"Would delete: {file_path}")
        else:
            file_path.unlink()
            logger.debug(f"Deleted: {file_path}")
        count += 1

    if dry_run:
        logger.info(f"Dry run: Would delete {count} files")
    else:
        logger.info(f"✅ Deleted {count} files")

    return count


def get_directory_size(path: Union[str, Path]) -> int:
    """
    Calculate total size of directory.

    Args:
        path: Directory path

    Returns:
        Total size in bytes

    Example:
        >>> size = get_directory_size("/tmp/cache")
        >>> print(f"Size: {size / 1024 / 1024:.2f} MB")
    """
    path = Path(path)

    total_size = 0

    for item in path.rglob("*"):
        if item.is_file():
            total_size += item.stat().st_size

    return total_size


def format_size(size_bytes: int) -> str:
    """
    Format byte size to human-readable string.

    Args:
        size_bytes: Size in bytes

    Returns:
        Formatted string (e.g., "1.5 GB")

    Example:
        >>> format_size(1536)
        '1.50 KB'
        >>> format_size(1024 * 1024 * 1024)
        '1.00 GB'
    """
    units = ["B", "KB", "MB", "GB", "TB"]
    size = float(size_bytes)
    unit_index = 0

    while size >= 1024 and unit_index < len(units) - 1:
        size /= 1024
        unit_index += 1

    return f"{size:.2f} {units[unit_index]}"


# CLI for testing
if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="File storage utilities")

    subparsers = parser.add_subparsers(dest="command", help="Command to execute")

    # Hash command
    hash_parser = subparsers.add_parser("hash", help="Calculate file hash")
    hash_parser.add_argument("file", help="File path")
    hash_parser.add_argument(
        "--algorithm",
        default="sha256",
        choices=["md5", "sha1", "sha256", "sha512"],
        help="Hash algorithm",
    )

    # Clean command
    clean_parser = subparsers.add_parser("clean", help="Clean directory")
    clean_parser.add_argument("directory", help="Directory path")
    clean_parser.add_argument("--pattern", default="*", help="File pattern")
    clean_parser.add_argument("--recursive", action="store_true", help="Search recursively")
    clean_parser.add_argument("--dry-run", action="store_true", help="Show what would be deleted")

    # Size command
    size_parser = subparsers.add_parser("size", help="Calculate directory size")
    size_parser.add_argument("directory", help="Directory path")

    # Safe filename command
    safe_parser = subparsers.add_parser("safe", help="Convert to safe filename")
    safe_parser.add_argument("filename", help="Filename to convert")

    args = parser.parse_args()

    if args.command == "hash":
        file_path = Path(args.file)
        if not file_path.exists():
            print(f"Error: File not found: {file_path}")
            exit(1)

        hash_val = get_file_hash(file_path, algorithm=args.algorithm)
        print(f"{args.algorithm.upper()}: {hash_val}")

    elif args.command == "clean":
        count = clean_directory(
            args.directory, pattern=args.pattern, recursive=args.recursive, dry_run=args.dry_run
        )

        if args.dry_run:
            print(f"\nWould delete {count} files")
        else:
            print(f"\n✅ Deleted {count} files")

    elif args.command == "size":
        dir_path = Path(args.directory)
        if not dir_path.exists():
            print(f"Error: Directory not found: {dir_path}")
            exit(1)

        size_bytes = get_directory_size(dir_path)
        print(f"Total size: {format_size(size_bytes)} ({size_bytes:,} bytes)")

    elif args.command == "safe":
        safe = safe_filename(args.filename)
        print(f"Original: {args.filename}")
        print(f"Safe:     {safe}")

    else:
        parser.print_help()
