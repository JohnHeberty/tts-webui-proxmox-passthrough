"""
Vocabulary management and validation utilities.

Provides functions to validate, compare, and consolidate vocabulary files
across the project to ensure consistency.

Author: F5-TTS Training Pipeline
Version: 1.0
Date: 2025-12-06
"""

import hashlib
from pathlib import Path


# ========================================
# CONSTANTS
# ========================================

# SOURCE OF TRUTH for vocabulary
CANONICAL_VOCAB_PATH = "train/config/vocab.txt"

# Expected hash of canonical vocab (PT-BR from firstpixel/F5-TTS-pt-br)
# This hash is computed from the official PT-BR vocab and serves as integrity check
CANONICAL_VOCAB_HASH = "2a05f992e00af9b0bd3800a8d23e78d520dbd705284ed2eedb5f4bd29398fa3c"


# ========================================
# HASH UTILITIES
# ========================================


def compute_vocab_hash(vocab_path: str | Path) -> str:
    """
    Compute SHA256 hash of vocabulary file.

    Args:
        vocab_path: Path to vocab.txt file

    Returns:
        SHA256 hash as hex string

    Raises:
        FileNotFoundError: If vocab file doesn't exist
    """
    vocab_path = Path(vocab_path)

    if not vocab_path.exists():
        raise FileNotFoundError(f"Vocab file not found: {vocab_path}")

    sha256 = hashlib.sha256()

    with open(vocab_path, "rb") as f:
        # Read in chunks for memory efficiency
        for chunk in iter(lambda: f.read(8192), b""):
            sha256.update(chunk)

    return sha256.hexdigest()


def load_vocab(vocab_path: str | Path) -> list[str]:
    """
    Load vocabulary from file.

    Args:
        vocab_path: Path to vocab.txt file

    Returns:
        List of vocabulary tokens (one per line)

    Raises:
        FileNotFoundError: If vocab file doesn't exist
    """
    vocab_path = Path(vocab_path)

    if not vocab_path.exists():
        raise FileNotFoundError(f"Vocab file not found: {vocab_path}")

    with open(vocab_path, encoding="utf-8") as f:
        vocab = [line.rstrip("\n") for line in f]

    return vocab


# ========================================
# VALIDATION
# ========================================


def validate_vocab(
    vocab_path: str, expected_hash: str | None = None, verbose: bool = True
) -> tuple[bool, str, dict]:
    """
    Validate vocabulary file integrity.

    Args:
        vocab_path: Path to vocab.txt to validate
        expected_hash: Expected SHA256 hash (default: CANONICAL_VOCAB_HASH)
        verbose: Print validation details

    Returns:
        Tuple of (is_valid, hash, info_dict)
        - is_valid: True if hash matches expected
        - hash: Computed SHA256 hash
        - info_dict: Additional information (size, line count, etc.)
    """
    if expected_hash is None:
        expected_hash = CANONICAL_VOCAB_HASH

    vocab_path = Path(vocab_path)

    # Check existence
    if not vocab_path.exists():
        if verbose:
            print(f"❌ Vocab file not found: {vocab_path}")
        return False, "", {"error": "File not found"}

    # Compute hash
    computed_hash = compute_vocab_hash(vocab_path)

    # Load vocab for stats
    vocab = load_vocab(vocab_path)
    vocab_size = len(vocab)
    file_size = vocab_path.stat().st_size

    # Compare
    is_valid = computed_hash == expected_hash

    info = {
        "path": str(vocab_path),
        "size_bytes": file_size,
        "vocab_size": vocab_size,
        "hash": computed_hash,
        "expected_hash": expected_hash,
        "valid": is_valid,
    }

    if verbose:
        if is_valid:
            print(f"✅ {vocab_path}")
            print(f"   Hash: {computed_hash}")
            print(f"   Size: {vocab_size} tokens ({file_size} bytes)")
        else:
            print(f"❌ {vocab_path}")
            print(f"   Computed: {computed_hash}")
            print(f"   Expected: {expected_hash}")
            print("   Status: HASH MISMATCH!")

    return is_valid, computed_hash, info


def compare_vocabs(vocab_path1: str, vocab_path2: str, verbose: bool = True) -> bool:
    """
    Compare two vocabulary files.

    Args:
        vocab_path1: Path to first vocab
        vocab_path2: Path to second vocab
        verbose: Print comparison details

    Returns:
        True if vocabs are identical
    """
    hash1 = compute_vocab_hash(vocab_path1)
    hash2 = compute_vocab_hash(vocab_path2)

    are_equal = hash1 == hash2

    if verbose:
        print(f"\n{'='*80}")
        print("VOCAB COMPARISON")
        print(f"{'='*80}")
        print(f"File 1: {vocab_path1}")
        print(f"  Hash: {hash1}")
        print(f"\nFile 2: {vocab_path2}")
        print(f"  Hash: {hash2}")
        print(f"\nResult: {'✅ IDENTICAL' if are_equal else '❌ DIFFERENT'}")
        print(f"{'='*80}")

    return are_equal


# ========================================
# CONSOLIDATION
# ========================================


def find_all_vocabs(root_dir: str = ".") -> list[Path]:
    """
    Find all vocab.txt files in project.

    Args:
        root_dir: Root directory to search

    Returns:
        List of Path objects for vocab.txt files
    """
    root = Path(root_dir)
    vocabs = list(root.rglob("vocab.txt"))
    return vocabs


def audit_all_vocabs(root_dir: str = ".", verbose: bool = True) -> dict:
    """
    Audit all vocabulary files in project.

    Args:
        root_dir: Root directory to search
        verbose: Print audit results

    Returns:
        Dictionary with audit results
    """
    vocabs = find_all_vocabs(root_dir)

    if verbose:
        print(f"\n{'='*80}")
        print("VOCABULARY AUDIT")
        print(f"{'='*80}")
        print(f"Found {len(vocabs)} vocab.txt files:\n")

    results = {
        "canonical": CANONICAL_VOCAB_PATH,
        "canonical_hash": CANONICAL_VOCAB_HASH,
        "vocabs": [],
        "valid_count": 0,
        "invalid_count": 0,
    }

    for vocab_path in sorted(vocabs):
        is_valid, computed_hash, info = validate_vocab(
            str(vocab_path), expected_hash=CANONICAL_VOCAB_HASH, verbose=False
        )

        results["vocabs"].append(info)

        if is_valid:
            results["valid_count"] += 1
            status = "✅ VALID"
        else:
            results["invalid_count"] += 1
            status = "❌ INVALID"

        if verbose:
            print(f"{status:12} {vocab_path}")
            print(f"             Hash: {computed_hash}")
            if not is_valid:
                print(f"             Expected: {CANONICAL_VOCAB_HASH}")
            print()

    if verbose:
        print(f"{'='*80}")
        print(f"Summary: {results['valid_count']} valid, {results['invalid_count']} invalid")
        print(f"{'='*80}\n")

    return results


def sync_vocab_to_canonical(target_path: str, dry_run: bool = False, verbose: bool = True) -> bool:
    """
    Synchronize a vocab file to the canonical version.

    Args:
        target_path: Path to vocab file to sync
        dry_run: If True, don't actually copy (just report)
        verbose: Print sync details

    Returns:
        True if sync was successful (or would be in dry_run mode)
    """
    import shutil

    canonical_path = Path(CANONICAL_VOCAB_PATH)
    target_path = Path(target_path)

    # Validate canonical exists
    if not canonical_path.exists():
        if verbose:
            print(f"❌ Canonical vocab not found: {canonical_path}")
        return False

    # Check if target already matches
    if target_path.exists():
        target_hash = compute_vocab_hash(target_path)
        if target_hash == CANONICAL_VOCAB_HASH:
            if verbose:
                print(f"✅ {target_path} already synced (hash matches)")
            return True

    # Sync
    if dry_run:
        if verbose:
            print(f"🔄 [DRY RUN] Would sync: {canonical_path} → {target_path}")
        return True
    else:
        try:
            # Ensure target directory exists
            target_path.parent.mkdir(parents=True, exist_ok=True)

            # Copy canonical to target
            shutil.copy2(canonical_path, target_path)

            # Verify
            new_hash = compute_vocab_hash(target_path)
            if new_hash == CANONICAL_VOCAB_HASH:
                if verbose:
                    print(f"✅ Synced: {canonical_path} → {target_path}")
                return True
            else:
                if verbose:
                    print("❌ Sync failed: hash mismatch after copy")
                return False
        except Exception as e:
            if verbose:
                print(f"❌ Sync error: {e}")
            return False


def consolidate_all_vocabs(root_dir: str = ".", dry_run: bool = False, verbose: bool = True):
    """
    Consolidate all vocab files to match canonical version.

    Args:
        root_dir: Root directory to search
        dry_run: If True, don't actually sync (just report)
        verbose: Print consolidation details
    """
    vocabs = find_all_vocabs(root_dir)

    # Filter out canonical itself
    canonical_path = Path(CANONICAL_VOCAB_PATH).resolve()
    vocabs_to_sync = [v for v in vocabs if v.resolve() != canonical_path]

    if verbose:
        print(f"\n{'='*80}")
        print("VOCAB CONSOLIDATION")
        print(f"{'='*80}")
        print(f"Canonical: {CANONICAL_VOCAB_PATH}")
        print(f"Hash: {CANONICAL_VOCAB_HASH}")
        print(f"\nFound {len(vocabs_to_sync)} vocab files to sync:\n")

    success_count = 0
    fail_count = 0
    skip_count = 0

    for vocab_path in sorted(vocabs_to_sync):
        # Check if already synced
        if vocab_path.exists():
            current_hash = compute_vocab_hash(vocab_path)
            if current_hash == CANONICAL_VOCAB_HASH:
                if verbose:
                    print(f"⏭️  SKIP (already synced): {vocab_path}")
                skip_count += 1
                continue

        # Sync
        success = sync_vocab_to_canonical(vocab_path, dry_run=dry_run, verbose=verbose)
        if success:
            success_count += 1
        else:
            fail_count += 1

    if verbose:
        print(f"\n{'='*80}")
        print("Summary:")
        print(f"  ✅ Synced: {success_count}")
        print(f"  ⏭️  Skipped: {skip_count}")
        print(f"  ❌ Failed: {fail_count}")
        if dry_run:
            print("\n⚠️  DRY RUN MODE - No files were actually modified")
        print(f"{'='*80}\n")


# ========================================
# CLI INTERFACE
# ========================================

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Vocabulary management utilities")

    subparsers = parser.add_subparsers(dest="command", help="Command to execute")

    # Hash command
    hash_parser = subparsers.add_parser("hash", help="Compute vocab hash")
    hash_parser.add_argument("vocab_path", help="Path to vocab.txt")

    # Validate command
    validate_parser = subparsers.add_parser("validate", help="Validate vocab against canonical")
    validate_parser.add_argument("vocab_path", help="Path to vocab.txt")

    # Compare command
    compare_parser = subparsers.add_parser("compare", help="Compare two vocabs")
    compare_parser.add_argument("vocab1", help="First vocab.txt")
    compare_parser.add_argument("vocab2", help="Second vocab.txt")

    # Audit command
    audit_parser = subparsers.add_parser("audit", help="Audit all vocabs in project")
    audit_parser.add_argument("--root", default=".", help="Root directory")

    # Sync command
    sync_parser = subparsers.add_parser("sync", help="Sync vocab to canonical")
    sync_parser.add_argument("target_path", help="Target vocab.txt to sync")
    sync_parser.add_argument("--dry-run", action="store_true", help="Dry run (no changes)")

    # Consolidate command
    consolidate_parser = subparsers.add_parser("consolidate", help="Consolidate all vocabs")
    consolidate_parser.add_argument("--root", default=".", help="Root directory")
    consolidate_parser.add_argument("--dry-run", action="store_true", help="Dry run (no changes)")

    args = parser.parse_args()

    if args.command == "hash":
        hash_val = compute_vocab_hash(args.vocab_path)
        print(f"SHA256: {hash_val}")

    elif args.command == "validate":
        validate_vocab(args.vocab_path, verbose=True)

    elif args.command == "compare":
        compare_vocabs(args.vocab1, args.vocab2, verbose=True)

    elif args.command == "audit":
        audit_all_vocabs(args.root, verbose=True)

    elif args.command == "sync":
        sync_vocab_to_canonical(args.target_path, dry_run=args.dry_run, verbose=True)

    elif args.command == "consolidate":
        consolidate_all_vocabs(args.root, dry_run=args.dry_run, verbose=True)

    else:
        parser.print_help()
