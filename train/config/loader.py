"""
Configuration loader for F5-TTS training pipeline.

Loads and validates configuration from multiple sources with proper hierarchy:
1. Base config file (base_config.yaml) - defaults
2. Environment variables (.env files) - overrides
3. CLI arguments - highest priority overrides

Author: F5-TTS Training Pipeline
Version: 1.0
Date: 2025-12-06
"""
import os
import sys
from pathlib import Path
from typing import Dict, Any, Optional
import yaml
from dotenv import load_dotenv
from pydantic import ValidationError

from train.config.schemas import F5TTSConfig


def load_yaml_config(config_path: str) -> Dict[str, Any]:
    """
    Load YAML configuration file.
    
    Args:
        config_path: Path to YAML config file
        
    Returns:
        Dictionary with config values
        
    Raises:
        FileNotFoundError: If config file doesn't exist
        yaml.YAMLError: If YAML is malformed
    """
    config_path = Path(config_path)
    
    if not config_path.exists():
        raise FileNotFoundError(f"Config file not found: {config_path}")
    
    with open(config_path, 'r', encoding='utf-8') as f:
        config_data = yaml.safe_load(f)
    
    return config_data or {}


def load_env_overrides() -> Dict[str, Any]:
    """
    Load environment variable overrides.
    
    Loads from:
    1. .env (root) - global settings
    2. train/.env - training-specific settings
    
    Returns:
        Dictionary with environment overrides in nested structure
    """
    # Load root .env first
    root_env = Path(".env")
    if root_env.exists():
        load_dotenv(root_env, override=False)
    
    # Load train/.env (higher priority)
    train_env = Path("train/.env")
    if train_env.exists():
        load_dotenv(train_env, override=True)
    
    # Map environment variables to config structure
    env_overrides = {}
    
    # Training hyperparameters
    if os.getenv("LEARNING_RATE"):
        env_overrides.setdefault("training", {})["learning_rate"] = float(os.getenv("LEARNING_RATE"))
    
    if os.getenv("BATCH_SIZE_PER_GPU"):
        env_overrides.setdefault("training", {})["batch_size_per_gpu"] = int(os.getenv("BATCH_SIZE_PER_GPU"))
    
    if os.getenv("GRAD_ACCUMULATION_STEPS"):
        env_overrides.setdefault("training", {})["grad_accumulation_steps"] = int(os.getenv("GRAD_ACCUMULATION_STEPS"))
    
    if os.getenv("MAX_GRAD_NORM"):
        env_overrides.setdefault("training", {})["max_grad_norm"] = float(os.getenv("MAX_GRAD_NORM"))
    
    if os.getenv("EPOCHS"):
        env_overrides.setdefault("training", {})["epochs"] = int(os.getenv("EPOCHS"))
    
    # Warmup
    if os.getenv("NUM_WARMUP_UPDATES"):
        env_overrides.setdefault("training", {})["num_warmup_updates"] = int(os.getenv("NUM_WARMUP_UPDATES"))
    
    if os.getenv("WARMUP_START_LR"):
        env_overrides.setdefault("training", {})["warmup_start_lr"] = float(os.getenv("WARMUP_START_LR"))
    
    if os.getenv("WARMUP_END_LR"):
        env_overrides.setdefault("training", {})["warmup_end_lr"] = float(os.getenv("WARMUP_END_LR"))
    
    # Optimizer
    if os.getenv("WEIGHT_DECAY"):
        env_overrides.setdefault("optimizer", {})["weight_decay"] = float(os.getenv("WEIGHT_DECAY"))
    
    # Checkpoints
    if os.getenv("SAVE_PER_UPDATES"):
        env_overrides.setdefault("checkpoints", {})["save_per_updates"] = int(os.getenv("SAVE_PER_UPDATES"))
    
    if os.getenv("LAST_PER_UPDATES"):
        env_overrides.setdefault("checkpoints", {})["last_per_updates"] = int(os.getenv("LAST_PER_UPDATES"))
    
    # Hardware
    if os.getenv("NUM_WORKERS"):
        env_overrides.setdefault("hardware", {})["num_workers"] = int(os.getenv("NUM_WORKERS"))
    
    if os.getenv("DATALOADER_WORKERS"):
        env_overrides.setdefault("hardware", {})["dataloader_workers"] = int(os.getenv("DATALOADER_WORKERS"))
    
    # Mixed precision
    if os.getenv("MIXED_PRECISION"):
        enabled = os.getenv("MIXED_PRECISION").lower() in ("true", "1", "yes")
        env_overrides.setdefault("mixed_precision", {})["enabled"] = enabled
    
    if os.getenv("MIXED_PRECISION_DTYPE"):
        env_overrides.setdefault("mixed_precision", {})["dtype"] = os.getenv("MIXED_PRECISION_DTYPE")
    
    # Logging
    if os.getenv("LOGGER"):
        env_overrides.setdefault("logging", {})["logger"] = os.getenv("LOGGER")
    
    if os.getenv("LOG_EVERY_N_STEPS"):
        env_overrides.setdefault("logging", {})["log_every_n_steps"] = int(os.getenv("LOG_EVERY_N_STEPS"))
    
    # WandB
    if os.getenv("WANDB_ENABLED"):
        enabled = os.getenv("WANDB_ENABLED").lower() in ("true", "1", "yes")
        env_overrides.setdefault("logging", {}).setdefault("wandb", {})["enabled"] = enabled
    
    if os.getenv("WANDB_PROJECT"):
        env_overrides.setdefault("logging", {}).setdefault("wandb", {})["project"] = os.getenv("WANDB_PROJECT")
    
    if os.getenv("WANDB_ENTITY"):
        env_overrides.setdefault("logging", {}).setdefault("wandb", {})["entity"] = os.getenv("WANDB_ENTITY")
    
    # Paths
    if os.getenv("DATASET_NAME"):
        env_overrides.setdefault("paths", {})["dataset_name"] = os.getenv("DATASET_NAME")
    
    if os.getenv("OUTPUT_DIR"):
        env_overrides.setdefault("paths", {})["output_dir"] = os.getenv("OUTPUT_DIR")
    
    if os.getenv("PRETRAINED_MODEL_PATH"):
        env_overrides.setdefault("paths", {})["pretrained_model_path"] = os.getenv("PRETRAINED_MODEL_PATH")
    
    # Experiment name
    if os.getenv("EXP_NAME"):
        env_overrides.setdefault("training", {})["exp_name"] = os.getenv("EXP_NAME")
    
    # Advanced
    if os.getenv("SEED"):
        env_overrides.setdefault("advanced", {})["seed"] = int(os.getenv("SEED"))
    
    if os.getenv("GRADIENT_CHECKPOINTING"):
        enabled = os.getenv("GRADIENT_CHECKPOINTING").lower() in ("true", "1", "yes")
        env_overrides.setdefault("advanced", {})["gradient_checkpointing"] = enabled
    
    return env_overrides


def deep_merge(base: Dict[str, Any], override: Dict[str, Any]) -> Dict[str, Any]:
    """
    Deep merge two dictionaries, with override taking precedence.
    
    Args:
        base: Base dictionary
        override: Override dictionary (higher priority)
        
    Returns:
        Merged dictionary
    """
    result = base.copy()
    
    for key, value in override.items():
        if key in result and isinstance(result[key], dict) and isinstance(value, dict):
            result[key] = deep_merge(result[key], value)
        else:
            result[key] = value
    
    return result


def apply_cli_overrides(config_dict: Dict[str, Any], cli_args: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """
    Apply CLI argument overrides to config.
    
    CLI args should be provided as nested dict matching config structure.
    Example:
        {"training": {"learning_rate": 2e-4}, "hardware": {"device": "cpu"}}
    
    Args:
        config_dict: Base config dictionary
        cli_args: CLI argument overrides
        
    Returns:
        Config with CLI overrides applied
    """
    if cli_args is None:
        return config_dict
    
    return deep_merge(config_dict, cli_args)


def load_config(
    config_path: str = "train/config/base_config.yaml",
    cli_overrides: Optional[Dict[str, Any]] = None,
    validate: bool = True
) -> F5TTSConfig:
    """
    Load complete F5-TTS configuration with validation.
    
    Configuration hierarchy (later sources override earlier):
    1. Base YAML config (base_config.yaml)
    2. Environment variables (.env files)
    3. CLI arguments (highest priority)
    
    Args:
        config_path: Path to base YAML config
        cli_overrides: Optional CLI argument overrides
        validate: Whether to validate with Pydantic (default: True)
        
    Returns:
        Validated F5TTSConfig object
        
    Raises:
        FileNotFoundError: If config file not found
        ValidationError: If config validation fails
        
    Example:
        >>> config = load_config()
        >>> print(config.training.learning_rate)
        0.0001
        
        >>> config = load_config(cli_overrides={"training": {"learning_rate": 2e-4}})
        >>> print(config.training.learning_rate)
        0.0002
    """
    # 1. Load base YAML config
    base_config = load_yaml_config(config_path)
    
    # 2. Load environment variable overrides
    env_overrides = load_env_overrides()
    
    # 3. Merge base + env
    merged_config = deep_merge(base_config, env_overrides)
    
    # 4. Apply CLI overrides
    final_config = apply_cli_overrides(merged_config, cli_overrides)
    
    # 5. Validate with Pydantic
    if validate:
        try:
            config = F5TTSConfig(**final_config)
            return config
        except ValidationError as e:
            print("❌ Configuration validation failed:", file=sys.stderr)
            print(e, file=sys.stderr)
            raise
    else:
        # Return unvalidated dict (for debugging)
        return final_config


def print_config_summary(config: F5TTSConfig):
    """
    Print human-readable config summary.
    
    Args:
        config: Validated config object
    """
    print("=" * 80)
    print("F5-TTS TRAINING CONFIGURATION")
    print("=" * 80)
    
    print("\n📁 PATHS:")
    print(f"  Dataset: {config.paths.dataset_path}")
    print(f"  Pretrained: {config.paths.pretrained_model_path}")
    print(f"  Output: {config.paths.output_dir}")
    print(f"  Vocab: {config.paths.vocab_file}")
    
    print("\n🧠 MODEL:")
    print(f"  Base: {config.model.base_model}")
    print(f"  Type: {config.model.model_type}")
    print(f"  Dim: {config.model.dim}, Depth: {config.model.depth}, Heads: {config.model.heads}")
    print(f"  EMA: {config.model.use_ema} (decay={config.model.ema_decay})")
    
    print("\n🎓 TRAINING:")
    print(f"  Experiment: {config.training.exp_name}")
    print(f"  Learning Rate: {config.training.learning_rate}")
    print(f"  Batch Size: {config.training.batch_size_per_gpu} (grad_accum={config.training.grad_accumulation_steps})")
    print(f"  Epochs: {config.training.epochs}")
    print(f"  Warmup: {config.training.num_warmup_updates} steps")
    
    print("\n💾 CHECKPOINTS:")
    print(f"  Save every: {config.checkpoints.save_per_updates} updates")
    print(f"  Keep last: {config.checkpoints.keep_last_n_checkpoints} checkpoints")
    
    print("\n⚡ HARDWARE:")
    print(f"  Device: {config.hardware.device} (GPUs: {config.hardware.num_gpus})")
    print(f"  Mixed Precision: {config.mixed_precision.enabled} ({config.mixed_precision.dtype})")
    print(f"  DataLoader Workers: {config.hardware.dataloader_workers}")
    
    print("\n📊 LOGGING:")
    print(f"  Logger: {config.logging.logger}")
    print(f"  Log every: {config.logging.log_every_n_steps} steps")
    if config.logging.wandb.enabled:
        print(f"  W&B Project: {config.logging.wandb.project}")
    
    print("\n🔧 ADVANCED:")
    print(f"  Seed: {config.advanced.seed}")
    print(f"  Gradient Checkpointing: {config.advanced.gradient_checkpointing}")
    print(f"  Compile Model: {config.advanced.compile_model}")
    
    print("=" * 80)


def save_config_to_yaml(config: F5TTSConfig, output_path: str):
    """
    Save validated config to YAML file.
    
    Useful for saving final merged config for reproducibility.
    
    Args:
        config: Validated config object
        output_path: Path to save YAML
    """
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Convert Pydantic model to dict
    config_dict = config.dict()
    
    with open(output_path, 'w', encoding='utf-8') as f:
        yaml.dump(config_dict, f, default_flow_style=False, allow_unicode=True, sort_keys=False)
    
    print(f"✅ Config saved to: {output_path}")


# ========================================
# CLI INTERFACE (optional)
# ========================================

if __name__ == "__main__":
    """
    Test config loader from command line.
    
    Usage:
        python -m train.config.loader
        python -m train.config.loader --config train/config/base_config.yaml
    """
    import argparse
    
    parser = argparse.ArgumentParser(description="Test F5-TTS config loader")
    parser.add_argument(
        "--config",
        type=str,
        default="train/config/base_config.yaml",
        help="Path to config file"
    )
    parser.add_argument(
        "--save",
        type=str,
        default=None,
        help="Save final merged config to file"
    )
    parser.add_argument(
        "--no-validate",
        action="store_true",
        help="Skip Pydantic validation"
    )
    
    args = parser.parse_args()
    
    try:
        config = load_config(
            config_path=args.config,
            validate=not args.no_validate
        )
        
        if args.no_validate:
            print("⚠️  Validation skipped, showing raw config:")
            print(yaml.dump(config, default_flow_style=False))
        else:
            print_config_summary(config)
            
            if args.save:
                save_config_to_yaml(config, args.save)
        
        print("\n✅ Config loaded successfully!")
        
    except Exception as e:
        print(f"\n❌ Error loading config: {e}", file=sys.stderr)
        sys.exit(1)
