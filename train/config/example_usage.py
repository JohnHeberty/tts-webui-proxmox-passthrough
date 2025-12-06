"""
Example usage of the F5-TTS config loader.

Demonstrates different ways to load and use configuration.

Author: F5-TTS Training Pipeline
Version: 1.0
Date: 2025-12-06
"""

from train.config.loader import load_config, save_config_to_yaml


def example_1_basic_load():
    """Example 1: Load default configuration."""
    print("\n" + "=" * 80)
    print("EXAMPLE 1: Basic Configuration Load")
    print("=" * 80)

    # Load with all defaults from base_config.yaml + .env overrides
    config = load_config()

    # Access config values (type-safe!)
    print(f"\nLearning Rate: {config.training.learning_rate}")
    print(f"Batch Size: {config.training.batch_size_per_gpu}")
    print(f"Device: {config.hardware.device}")
    print(f"Output Dir: {config.paths.output_dir}")

    return config


def example_2_cli_overrides():
    """Example 2: Override config with CLI arguments."""
    print("\n" + "=" * 80)
    print("EXAMPLE 2: CLI Overrides")
    print("=" * 80)

    # Simulate CLI arguments (e.g., from argparse)
    cli_overrides = {
        "training": {
            "learning_rate": 2e-4,  # Override learning rate
            "batch_size_per_gpu": 4,  # Override batch size
            "exp_name": "my_experiment",  # Override experiment name
        },
        "hardware": {"device": "cpu"},  # Force CPU for testing
        "logging": {"wandb": {"enabled": True, "project": "my-f5tts-project"}},
    }

    config = load_config(cli_overrides=cli_overrides)

    print(f"\nOverridden Learning Rate: {config.training.learning_rate}")
    print(f"Overridden Batch Size: {config.training.batch_size_per_gpu}")
    print(f"Overridden Device: {config.hardware.device}")
    print(f"W&B Enabled: {config.logging.wandb.enabled}")
    print(f"W&B Project: {config.logging.wandb.project}")

    return config


def example_3_accessing_nested_values():
    """Example 3: Accessing deeply nested configuration."""
    print("\n" + "=" * 80)
    print("EXAMPLE 3: Accessing Nested Values")
    print("=" * 80)

    config = load_config()

    # Model configuration
    print("\n🧠 Model Config:")
    print(f"  Architecture: {config.model.model_type}")
    print(f"  Dimensions: {config.model.dim}")
    print(f"  Depth: {config.model.depth}")
    print(f"  Attention Heads: {config.model.heads}")

    # Audio processing
    print("\n🎵 Audio Config:")
    print(f"  Sample Rate: {config.audio.target_sample_rate} Hz")
    print(f"  Normalize: {config.audio.normalize_audio}")
    print(f"  Target LUFS: {config.audio.target_lufs}")

    # Segmentation
    print("\n✂️  Segmentation Config:")
    print(f"  Min Duration: {config.segmentation.min_duration}s")
    print(f"  Max Duration: {config.segmentation.max_duration}s")
    print(f"  Target Duration: {config.segmentation.target_duration}s")
    print(f"  Use VAD: {config.segmentation.use_vad}")

    # Transcription
    print("\n📝 Transcription Config:")
    print(f"  Whisper Model: {config.transcription.asr.model}")
    print(f"  Language: {config.transcription.asr.language}")
    print(f"  Beam Size: {config.transcription.asr.beam_size}")

    return config


def example_4_validation_errors():
    """Example 4: Handling validation errors."""
    print("\n" + "=" * 80)
    print("EXAMPLE 4: Validation Errors")
    print("=" * 80)

    # This will fail validation (invalid learning rate)
    invalid_overrides = {
        "training": {
            "learning_rate": -0.001,  # ❌ Must be > 0
        }
    }

    try:
        config = load_config(cli_overrides=invalid_overrides)
    except Exception as e:
        print("\n❌ Validation failed (as expected):")
        print(f"   {type(e).__name__}: {str(e)[:200]}")

    # This will also fail (invalid split ratios)
    invalid_overrides2 = {
        "split": {
            "train_ratio": 0.8,
            "val_ratio": 0.3,  # ❌ 0.8 + 0.3 != 1.0
        }
    }

    try:
        config = load_config(cli_overrides=invalid_overrides2)
    except Exception as e:
        print("\n❌ Validation failed (as expected):")
        print(f"   {type(e).__name__}: {str(e)[:200]}")


def example_5_save_config():
    """Example 5: Save final merged config."""
    print("\n" + "=" * 80)
    print("EXAMPLE 5: Save Configuration")
    print("=" * 80)

    # Load with some overrides
    cli_overrides = {"training": {"learning_rate": 3e-4, "exp_name": "saved_experiment"}}

    config = load_config(cli_overrides=cli_overrides)

    # Save to file for reproducibility
    output_path = "train/output/example_config.yaml"
    save_config_to_yaml(config, output_path)

    print(f"\n💾 Configuration saved to: {output_path}")
    print("   This file can be used to reproduce the exact training setup!")


def example_6_config_hierarchy():
    """Example 6: Demonstrate config hierarchy."""
    print("\n" + "=" * 80)
    print("EXAMPLE 6: Configuration Hierarchy")
    print("=" * 80)

    print("\n📋 Config loading order (priority: low → high):")
    print("   1. base_config.yaml (defaults)")
    print("   2. .env files (environment overrides)")
    print("   3. CLI arguments (highest priority)")

    print("\n🔍 Example:")
    print("   - base_config.yaml:  learning_rate = 1e-4")
    print("   - train/.env:        LEARNING_RATE=2e-4")
    print("   - CLI args:          --learning_rate 3e-4")
    print("   → Final value:       3e-4 (CLI wins)")

    # Load without overrides (base + env)
    config_base = load_config()
    print(f"\n   Base + Env: LR = {config_base.training.learning_rate}")

    # Load with CLI override
    config_cli = load_config(cli_overrides={"training": {"learning_rate": 3e-4}})
    print(f"   Base + Env + CLI: LR = {config_cli.training.learning_rate}")


def example_7_using_in_training_script():
    """Example 7: How to use in actual training script."""
    print("\n" + "=" * 80)
    print("EXAMPLE 7: Using in Training Script")
    print("=" * 80)

    print(
        """
# In your training script (e.g., run_training.py):

from train.config.loader import load_config
import argparse

def main():
    # Parse CLI arguments
    parser = argparse.ArgumentParser()
    parser.add_argument('--lr', type=float, help='Learning rate')
    parser.add_argument('--batch-size', type=int, help='Batch size')
    parser.add_argument('--device', type=str, help='Device')
    args = parser.parse_args()
    
    # Convert argparse to config overrides
    cli_overrides = {}
    if args.lr:
        cli_overrides.setdefault('training', {})['learning_rate'] = args.lr
    if args.batch_size:
        cli_overrides.setdefault('training', {})['batch_size_per_gpu'] = args.batch_size
    if args.device:
        cli_overrides.setdefault('hardware', {})['device'] = args.device
    
    # Load validated config
    config = load_config(cli_overrides=cli_overrides)
    
    # Use type-safe config throughout training
    print(f"Training with LR={config.training.learning_rate}")
    
    # Access paths
    dataset_path = config.paths.dataset_path
    output_dir = config.paths.output_dir
    
    # Access all training params
    batch_size = config.training.batch_size_per_gpu
    epochs = config.training.epochs
    
    # Train model...
    
if __name__ == '__main__':
    main()
    """
    )


if __name__ == "__main__":
    """Run all examples."""

    # Example 1: Basic loading
    example_1_basic_load()

    # Example 2: CLI overrides
    example_2_cli_overrides()

    # Example 3: Accessing nested values
    example_3_accessing_nested_values()

    # Example 4: Validation errors
    example_4_validation_errors()

    # Example 5: Save config
    example_5_save_config()

    # Example 6: Config hierarchy
    example_6_config_hierarchy()

    # Example 7: Using in training
    example_7_using_in_training_script()

    print("\n" + "=" * 80)
    print("✅ All examples completed!")
    print("=" * 80)
