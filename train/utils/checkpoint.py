"""
Checkpoint management utilities for F5-TTS training.

Provides intelligent checkpoint resolution, validation, and metadata handling
to ensure consistent checkpoint usage across training and inference.

Author: F5-TTS Training Pipeline
Version: 1.0
Date: 2025-12-06
"""
import os
import json
import torch
import shutil
from pathlib import Path
from typing import Optional, Dict, Any, Tuple
from dataclasses import dataclass
import logging

logger = logging.getLogger(__name__)


# ========================================
# DATA CLASSES
# ========================================

@dataclass
class CheckpointInfo:
    """Information about a checkpoint file."""
    path: Path
    exists: bool
    size_bytes: int
    size_gb: float
    is_valid: bool
    has_ema: bool
    num_keys: int
    metadata: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    
    def __str__(self):
        if not self.exists:
            return f"CheckpointInfo(path={self.path}, exists=False)"
        
        status = "✅ VALID" if self.is_valid else "❌ INVALID"
        ema_str = " + EMA" if self.has_ema else ""
        
        return (
            f"CheckpointInfo({status}, {self.size_gb:.2f}GB, "
            f"{self.num_keys} keys{ema_str}, {self.path.name})"
        )


# ========================================
# CHECKPOINT VALIDATION
# ========================================

def validate_checkpoint(
    checkpoint_path: str,
    min_size_gb: float = 1.0,
    check_keys: bool = True,
    verbose: bool = True
) -> CheckpointInfo:
    """
    Validate checkpoint file integrity.
    
    Args:
        checkpoint_path: Path to checkpoint file
        min_size_gb: Minimum expected size in GB (default: 1.0)
        check_keys: Whether to check for expected keys (default: True)
        verbose: Print validation details (default: True)
        
    Returns:
        CheckpointInfo object with validation results
    """
    checkpoint_path = Path(checkpoint_path)
    
    # Check existence
    if not checkpoint_path.exists():
        info = CheckpointInfo(
            path=checkpoint_path,
            exists=False,
            size_bytes=0,
            size_gb=0.0,
            is_valid=False,
            has_ema=False,
            num_keys=0,
            error="File not found"
        )
        if verbose:
            logger.warning(f"❌ Checkpoint not found: {checkpoint_path}")
        return info
    
    # Check size
    size_bytes = checkpoint_path.stat().st_size
    size_gb = size_bytes / (1024 ** 3)
    
    if size_gb < min_size_gb:
        info = CheckpointInfo(
            path=checkpoint_path,
            exists=True,
            size_bytes=size_bytes,
            size_gb=size_gb,
            is_valid=False,
            has_ema=False,
            num_keys=0,
            error=f"File too small ({size_gb:.2f}GB < {min_size_gb}GB)"
        )
        if verbose:
            logger.warning(f"❌ Checkpoint too small: {checkpoint_path} ({size_gb:.2f}GB)")
        return info
    
    # Try to load checkpoint
    try:
        checkpoint = torch.load(checkpoint_path, map_location='cpu')
        
        # Check if it's a dict with expected structure
        if not isinstance(checkpoint, dict):
            raise ValueError(f"Checkpoint is {type(checkpoint)}, expected dict")
        
        # Count keys
        num_keys = len(checkpoint.keys())
        
        # Check for EMA
        has_ema = 'ema_model_state_dict' in checkpoint or 'ema' in checkpoint
        
        # Check for essential keys
        if check_keys:
            essential_keys = ['model_state_dict', 'vocab_char_map']
            missing_keys = [k for k in essential_keys if k not in checkpoint]
            
            if missing_keys:
                raise ValueError(f"Missing essential keys: {missing_keys}")
        
        # Try to load metadata if exists
        metadata_path = checkpoint_path.parent / f"{checkpoint_path.stem}.metadata.json"
        metadata = None
        if metadata_path.exists():
            try:
                with open(metadata_path, 'r') as f:
                    metadata = json.load(f)
            except Exception as e:
                logger.warning(f"Could not load metadata: {e}")
        
        info = CheckpointInfo(
            path=checkpoint_path,
            exists=True,
            size_bytes=size_bytes,
            size_gb=size_gb,
            is_valid=True,
            has_ema=has_ema,
            num_keys=num_keys,
            metadata=metadata,
            error=None
        )
        
        if verbose:
            logger.info(f"✅ Valid checkpoint: {checkpoint_path.name}")
            logger.info(f"   Size: {size_gb:.2f}GB")
            logger.info(f"   Keys: {num_keys}")
            if has_ema:
                logger.info(f"   EMA: Yes")
            if metadata:
                logger.info(f"   Metadata: {metadata_path.name}")
        
        return info
        
    except Exception as e:
        error_msg = f"Failed to load: {str(e)}"
        info = CheckpointInfo(
            path=checkpoint_path,
            exists=True,
            size_bytes=size_bytes,
            size_gb=size_gb,
            is_valid=False,
            has_ema=False,
            num_keys=0,
            error=error_msg
        )
        
        if verbose:
            logger.error(f"❌ Checkpoint validation failed: {checkpoint_path}")
            logger.error(f"   Error: {error_msg}")
        
        return info


def mark_checkpoint_corrupted(checkpoint_path: str, verbose: bool = True) -> bool:
    """
    Mark a corrupted checkpoint by renaming it.
    
    Args:
        checkpoint_path: Path to corrupted checkpoint
        verbose: Print details (default: True)
        
    Returns:
        True if successfully renamed
    """
    checkpoint_path = Path(checkpoint_path)
    
    if not checkpoint_path.exists():
        if verbose:
            logger.warning(f"Checkpoint not found: {checkpoint_path}")
        return False
    
    corrupted_path = checkpoint_path.parent / f"{checkpoint_path.name}.corrupted"
    
    try:
        shutil.move(str(checkpoint_path), str(corrupted_path))
        if verbose:
            logger.warning(f"🗑️  Marked as corrupted: {checkpoint_path.name} → {corrupted_path.name}")
        return True
    except Exception as e:
        if verbose:
            logger.error(f"Failed to mark as corrupted: {e}")
        return False


# ========================================
# CHECKPOINT RESOLUTION
# ========================================

def resolve_checkpoint_path(
    config,
    checkpoint_name: Optional[str] = None,
    auto_download: bool = True,
    verbose: bool = True
) -> Optional[str]:
    """
    Intelligently resolve checkpoint path with priority fallback.
    
    Priority order:
    1. Custom checkpoint (config.model.custom_checkpoint)
    2. Specified checkpoint_name in output_dir
    3. model_best.pt in output_dir (if exists)
    4. model_last.pt in output_dir (if exists)
    5. Latest checkpoint by update number (model_XXXXX.pt)
    6. Pretrained model (config.paths.pretrained_model_path)
    7. Auto-download from HuggingFace (if enabled)
    
    Args:
        config: F5TTSConfig object
        checkpoint_name: Specific checkpoint filename (optional)
        auto_download: Download from HF if no checkpoint found (default: True)
        verbose: Print resolution process (default: True)
        
    Returns:
        Absolute path to checkpoint, or None if not found
    """
    from pathlib import Path
    
    if verbose:
        logger.info("=" * 80)
        logger.info("🔍 CHECKPOINT RESOLUTION")
        logger.info("=" * 80)
    
    # Get base paths
    try:
        project_root = Path(__file__).parent.parent.parent.resolve()
    except:
        project_root = Path.cwd()
    
    output_dir = project_root / config.paths.output_dir
    
    candidates = []
    
    # 1. Custom checkpoint (highest priority)
    if config.model.custom_checkpoint:
        custom_path = Path(config.model.custom_checkpoint)
        if not custom_path.is_absolute():
            custom_path = project_root / custom_path
        
        candidates.append(("Custom checkpoint", custom_path))
    
    # 2. Specified checkpoint name
    if checkpoint_name:
        specified_path = output_dir / checkpoint_name
        candidates.append(("Specified checkpoint", specified_path))
    
    # 3. model_best.pt (best performing)
    best_path = output_dir / "model_best.pt"
    candidates.append(("Best model", best_path))
    
    # 4. model_last.pt (most recent training)
    last_path = output_dir / "model_last.pt"
    candidates.append(("Last model", last_path))
    
    # 5. Latest checkpoint by update number
    if output_dir.exists():
        update_checkpoints = sorted(
            output_dir.glob("model_[0-9]*.pt"),
            key=lambda p: int(p.stem.split('_')[1]),
            reverse=True
        )
        if update_checkpoints:
            candidates.append(("Latest update checkpoint", update_checkpoints[0]))
    
    # 6. Pretrained model
    if config.paths.pretrained_model_path:
        pretrained_path = Path(config.paths.pretrained_model_path)
        if not pretrained_path.is_absolute():
            pretrained_path = project_root / pretrained_path
        
        candidates.append(("Pretrained model", pretrained_path))
    
    # Try each candidate
    for name, path in candidates:
        if verbose:
            logger.info(f"\n🔎 Checking {name}: {path}")
        
        info = validate_checkpoint(path, verbose=False)
        
        if info.is_valid:
            if verbose:
                logger.info(f"✅ Using {name}")
                logger.info(f"   Path: {path}")
                logger.info(f"   Size: {info.size_gb:.2f}GB")
                logger.info(f"   Keys: {info.num_keys}")
                if info.has_ema:
                    logger.info(f"   EMA: Yes")
                logger.info("=" * 80)
            return str(path.absolute())
        
        elif info.exists:
            # Exists but invalid - mark as corrupted
            if verbose:
                logger.warning(f"⚠️  {name} exists but is invalid: {info.error}")
            
            # Optionally mark as corrupted
            if "too small" not in str(info.error).lower():
                mark_checkpoint_corrupted(path, verbose=verbose)
    
    # 7. Auto-download from HuggingFace
    if auto_download and config.model.auto_download_pretrained:
        if verbose:
            logger.info(f"\n📥 No valid checkpoint found, attempting download...")
            logger.info(f"   Model: {config.model.base_model}")
        
        downloaded_path = download_pretrained_model(config, verbose=verbose)
        if downloaded_path:
            if verbose:
                logger.info(f"✅ Downloaded successfully")
                logger.info("=" * 80)
            return downloaded_path
    
    # No checkpoint found
    if verbose:
        logger.error(f"\n❌ No valid checkpoint found!")
        logger.error(f"   Searched in: {output_dir}")
        logger.error(f"   Candidates tried: {len(candidates)}")
        logger.info("=" * 80)
    
    return None


def download_pretrained_model(config, verbose: bool = True) -> Optional[str]:
    """
    Download pretrained model from HuggingFace.
    
    Args:
        config: F5TTSConfig object
        verbose: Print download progress (default: True)
        
    Returns:
        Path to downloaded model, or None if failed
    """
    try:
        from huggingface_hub import hf_hub_download
        from pathlib import Path
        
        # Get project root
        try:
            project_root = Path(__file__).parent.parent.parent.resolve()
        except:
            project_root = Path.cwd()
        
        # Setup download paths
        pretrained_dir = project_root / "train" / "pretrained"
        model_name = config.model.base_model.split('/')[-1]
        model_dir = pretrained_dir / model_name
        model_dir.mkdir(parents=True, exist_ok=True)
        
        # Download model file
        model_filename = config.model.model_filename
        
        if verbose:
            logger.info(f"   Downloading: {model_filename}")
            logger.info(f"   Repository: {config.model.base_model}")
            logger.info(f"   Destination: {model_dir}")
        
        downloaded_file = hf_hub_download(
            repo_id=config.model.base_model,
            filename=model_filename,
            local_dir=str(model_dir),
            local_dir_use_symlinks=False
        )
        
        if verbose:
            logger.info(f"   Downloaded to: {downloaded_file}")
        
        # Validate downloaded checkpoint
        info = validate_checkpoint(downloaded_file, verbose=False)
        
        if info.is_valid:
            return downloaded_file
        else:
            if verbose:
                logger.error(f"   Downloaded checkpoint is invalid: {info.error}")
            return None
        
    except ImportError:
        if verbose:
            logger.error(f"   huggingface_hub not installed!")
            logger.error(f"   Install with: pip install huggingface_hub")
        return None
    
    except Exception as e:
        if verbose:
            logger.error(f"   Download failed: {e}")
        return None


# ========================================
# CHECKPOINT METADATA
# ========================================

def save_checkpoint_metadata(
    checkpoint_path: str,
    metadata: Dict[str, Any],
    verbose: bool = True
) -> bool:
    """
    Save metadata JSON alongside checkpoint.
    
    Args:
        checkpoint_path: Path to checkpoint file
        metadata: Dictionary with metadata to save
        verbose: Print details (default: True)
        
    Returns:
        True if successfully saved
    """
    checkpoint_path = Path(checkpoint_path)
    metadata_path = checkpoint_path.parent / f"{checkpoint_path.stem}.metadata.json"
    
    try:
        with open(metadata_path, 'w') as f:
            json.dump(metadata, f, indent=2)
        
        if verbose:
            logger.info(f"💾 Saved metadata: {metadata_path.name}")
        
        return True
        
    except Exception as e:
        if verbose:
            logger.error(f"Failed to save metadata: {e}")
        return False


def load_checkpoint_metadata(checkpoint_path: str) -> Optional[Dict[str, Any]]:
    """
    Load metadata JSON from checkpoint.
    
    Args:
        checkpoint_path: Path to checkpoint file
        
    Returns:
        Metadata dict, or None if not found
    """
    checkpoint_path = Path(checkpoint_path)
    metadata_path = checkpoint_path.parent / f"{checkpoint_path.stem}.metadata.json"
    
    if not metadata_path.exists():
        return None
    
    try:
        with open(metadata_path, 'r') as f:
            return json.load(f)
    except Exception as e:
        logger.warning(f"Failed to load metadata: {e}")
        return None


# ========================================
# CLI INTERFACE
# ========================================

if __name__ == "__main__":
    import argparse
    from train.config.loader import load_config
    
    parser = argparse.ArgumentParser(description="Checkpoint management utilities")
    
    subparsers = parser.add_subparsers(dest='command', help='Command to execute')
    
    # Validate command
    validate_parser = subparsers.add_parser('validate', help='Validate checkpoint')
    validate_parser.add_argument('checkpoint_path', help='Path to checkpoint')
    validate_parser.add_argument('--min-size', type=float, default=1.0,
                                  help='Minimum size in GB')
    
    # Resolve command
    resolve_parser = subparsers.add_parser('resolve', help='Resolve checkpoint path')
    resolve_parser.add_argument('--name', help='Specific checkpoint name')
    resolve_parser.add_argument('--no-download', action='store_true',
                                help='Disable auto-download')
    
    # Info command
    info_parser = subparsers.add_parser('info', help='Show checkpoint info')
    info_parser.add_argument('checkpoint_path', help='Path to checkpoint')
    
    args = parser.parse_args()
    
    if args.command == 'validate':
        info = validate_checkpoint(
            args.checkpoint_path,
            min_size_gb=args.min_size,
            verbose=True
        )
        print(f"\n{info}")
        exit(0 if info.is_valid else 1)
    
    elif args.command == 'resolve':
        config = load_config()
        checkpoint_path = resolve_checkpoint_path(
            config,
            checkpoint_name=args.name,
            auto_download=not args.no_download,
            verbose=True
        )
        
        if checkpoint_path:
            print(f"\n✅ Resolved: {checkpoint_path}")
            exit(0)
        else:
            print(f"\n❌ No checkpoint found")
            exit(1)
    
    elif args.command == 'info':
        info = validate_checkpoint(args.checkpoint_path, verbose=False)
        
        print(f"\n{'='*80}")
        print("CHECKPOINT INFO")
        print(f"{'='*80}")
        print(f"Path: {info.path}")
        print(f"Exists: {info.exists}")
        
        if info.exists:
            print(f"Size: {info.size_gb:.2f}GB ({info.size_bytes:,} bytes)")
            print(f"Valid: {info.is_valid}")
            print(f"Keys: {info.num_keys}")
            print(f"EMA: {info.has_ema}")
            
            if info.metadata:
                print(f"\nMetadata:")
                for key, value in info.metadata.items():
                    print(f"  {key}: {value}")
            
            if info.error:
                print(f"\nError: {info.error}")
        
        print(f"{'='*80}\n")
        exit(0 if info.is_valid else 1)
    
    else:
        parser.print_help()
