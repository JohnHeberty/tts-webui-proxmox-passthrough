#!/usr/bin/env python3
"""
Example 4: Resume Training from Checkpoint

Resume training from a saved checkpoint.
Useful for continuing interrupted training or fine-tuning.

Usage:
    python train/examples/04_resume_training.py --checkpoint models/f5tts/model_100.pt
    
Requirements:
    - Checkpoint file (.pt)
    - Original config.yaml
    - Dataset ready
"""
import argparse
import logging
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from train.config.loader import load_config
from train.utils.reproducibility import set_seed

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def main():
    """Resume training from checkpoint."""
    
    parser = argparse.ArgumentParser(description="Resume F5-TTS training")
    parser.add_argument(
        "--checkpoint",
        type=Path,
        required=True,
        help="Path to checkpoint file (.pt)"
    )
    parser.add_argument(
        "--config",
        type=Path,
        default=Path("train/config/config.yaml"),
        help="Path to config file"
    )
    parser.add_argument(
        "--additional-epochs",
        type=int,
        default=None,
        help="Train for N additional epochs (overrides config)"
    )
    
    args = parser.parse_args()
    
    print("=" * 60)
    print("F5-TTS Resume Training")
    print("=" * 60)
    print()
    
    # Validate checkpoint
    if not args.checkpoint.exists():
        logger.error(f"❌ Checkpoint not found: {args.checkpoint}")
        return 1
    
    # Load checkpoint info
    import torch
    checkpoint = torch.load(args.checkpoint, map_location="cpu")
    
    checkpoint_epoch = checkpoint.get("epoch", 0)
    checkpoint_step = checkpoint.get("step", 0)
    
    print("📦 Checkpoint Info:")
    print(f"  File: {args.checkpoint}")
    print(f"  Epoch: {checkpoint_epoch}")
    print(f"  Step: {checkpoint_step}")
    
    if "best_loss" in checkpoint:
        print(f"  Best loss: {checkpoint['best_loss']:.4f}")
    
    print()
    
    # Load config
    print("⚙️  Loading configuration...")
    config = load_config(str(args.config))
    
    # Override resume settings
    config.checkpoints.resume_from_checkpoint = str(args.checkpoint)
    
    if args.additional_epochs:
        total_epochs = checkpoint_epoch + args.additional_epochs
        config.training.epochs = total_epochs
        logger.info(f"Will train until epoch {total_epochs} ({args.additional_epochs} additional)")
    
    print(f"  Dataset: {config.paths.dataset_name}")
    print(f"  Total epochs: {config.training.epochs}")
    print(f"  Batch size: {config.training.batch_size_per_gpu}")
    print()
    
    # Set seed
    set_seed(config.advanced.seed)
    
    # Check dataset
    dataset_path = Path(config.paths.dataset_path)
    if not dataset_path.exists():
        logger.error(f"❌ Dataset not found: {dataset_path}")
        return 1
    
    # Start training
    print("🚀 Resuming training...")
    print("-" * 60)
    print()
    
    try:
        from train.run_training import main as train_main
        
        # Override sys.argv
        sys.argv = [
            "train.run_training",
            "--config", str(args.config),
        ]
        
        if args.additional_epochs:
            sys.argv.extend(["--epochs", str(config.training.epochs)])
        
        train_main()
        
        print()
        print("=" * 60)
        print("✅ Training resumed successfully!")
        print("=" * 60)
        return 0
        
    except Exception as e:
        logger.error(f"❌ Training failed: {e}", exc_info=True)
        return 1


if __name__ == "__main__":
    exit(main())
