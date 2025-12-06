#!/usr/bin/env python3
"""
Example 1: Quick Training Test

Minimal training example to test the pipeline with 1 epoch.
Useful for validating environment and configuration.

Usage:
    python train/examples/01_quick_train.py
    
Requirements:
    - Dataset prepared in train/data/processed/
    - Config file at train/config/config.yaml
"""
import logging
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from train.config.loader import load_config
from train.utils.reproducibility import set_seed
from train.scripts.health_check import check_environment

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def main():
    """Run quick training test (1 epoch)."""
    
    print("=" * 60)
    print("F5-TTS Quick Training Test")
    print("=" * 60)
    print()
    
    # 1. Validate environment
    print("📋 Step 1: Environment check")
    print("-" * 60)
    health_ok = check_environment()
    
    if not health_ok:
        logger.error("❌ Environment check failed! Fix issues before training.")
        return 1
    
    print()
    
    # 2. Load config
    print("⚙️  Step 2: Load configuration")
    print("-" * 60)
    config = load_config("train/config/config.yaml")
    
    # Override for quick test
    config.training.epochs = 1
    config.checkpoints.save_per_updates = 10
    config.logging.log_every_n_steps = 5
    
    logger.info(f"Dataset: {config.paths.dataset_name}")
    logger.info(f"Epochs: {config.training.epochs}")
    logger.info(f"Batch size: {config.training.batch_size_per_gpu}")
    print()
    
    # 3. Set seed for reproducibility
    print("🎲 Step 3: Set random seed")
    print("-" * 60)
    set_seed(config.advanced.seed)
    logger.info(f"Seed: {config.advanced.seed}")
    print()
    
    # 4. Check dataset exists
    print("📦 Step 4: Validate dataset")
    print("-" * 60)
    dataset_path = Path(config.paths.dataset_path)
    
    if not dataset_path.exists():
        logger.error(f"❌ Dataset not found: {dataset_path}")
        logger.error("Run dataset preparation first!")
        return 1
    
    metadata_file = dataset_path / "metadata.csv"
    if not metadata_file.exists():
        logger.error(f"❌ Metadata not found: {metadata_file}")
        return 1
    
    # Count samples
    import pandas as pd
    df = pd.read_csv(metadata_file, sep="|")
    num_samples = len(df)
    total_duration = df["duration"].sum() / 3600
    
    logger.info(f"✅ Dataset found: {num_samples} samples ({total_duration:.1f}h)")
    print()
    
    # 5. Start training
    print("🚀 Step 5: Start training (1 epoch)")
    print("-" * 60)
    print()
    print("NOTE: This is a quick test. For full training, use:")
    print("  python -m train.run_training --config train/config/config.yaml")
    print()
    
    # Import and run training
    try:
        from train.run_training import main as train_main
        
        # Override sys.argv for training script
        sys.argv = [
            "train.run_training",
            "--config", "train/config/config.yaml",
            "--epochs", "1"
        ]
        
        train_main()
        
        print()
        print("=" * 60)
        print("✅ Quick training test complete!")
        print("=" * 60)
        return 0
        
    except Exception as e:
        logger.error(f"❌ Training failed: {e}", exc_info=True)
        return 1


if __name__ == "__main__":
    exit(main())
