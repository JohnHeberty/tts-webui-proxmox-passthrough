"""
Experiment Metadata Management

Tools for tracking and saving experiment metadata for reproducibility.

Author: F5-TTS Training Pipeline
Sprint: 4 - Reproducibility and MLOps
"""

from datetime import datetime
import hashlib
import json
import logging
from pathlib import Path
import subprocess
from typing import Any


logger = logging.getLogger(__name__)


def get_git_commit() -> str | None:
    """
    Get current git commit hash.

    Returns:
        Commit hash string or None if not a git repo

    Example:
        >>> commit = get_git_commit()
        >>> print(f"Commit: {commit[:8]}")
    """
    try:
        result = subprocess.run(
            ["git", "rev-parse", "HEAD"], capture_output=True, text=True, timeout=5
        )
        if result.returncode == 0:
            return result.stdout.strip()
    except Exception as e:
        logger.debug(f"Could not get git commit: {e}")

    return None


def get_git_status() -> dict[str, Any]:
    """
    Get git repository status.

    Returns:
        Dictionary with branch, commit, dirty status
    """
    status = {
        "commit": get_git_commit(),
        "branch": None,
        "dirty": False,
    }

    # Get branch
    try:
        result = subprocess.run(
            ["git", "rev-parse", "--abbrev-ref", "HEAD"], capture_output=True, text=True, timeout=5
        )
        if result.returncode == 0:
            status["branch"] = result.stdout.strip()
    except Exception:
        pass

    # Check if dirty (uncommitted changes)
    try:
        result = subprocess.run(
            ["git", "status", "--porcelain"], capture_output=True, text=True, timeout=5
        )
        if result.returncode == 0:
            status["dirty"] = bool(result.stdout.strip())
    except Exception:
        pass

    return status


def compute_file_hash(file_path: Path) -> str:
    """
    Compute SHA256 hash of file.

    Args:
        file_path: Path to file

    Returns:
        SHA256 hex digest
    """
    sha256 = hashlib.sha256()

    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            sha256.update(chunk)

    return sha256.hexdigest()


def get_dataset_info(dataset_path: Path) -> dict[str, Any]:
    """
    Get dataset metadata.

    Args:
        dataset_path: Path to dataset directory

    Returns:
        Dictionary with dataset info (num_samples, total_duration, etc.)
    """
    info = {
        "path": str(dataset_path),
        "exists": dataset_path.exists(),
    }

    if not dataset_path.exists():
        return info

    # Count .list files (train/val split)
    list_files = list(dataset_path.glob("*.list"))
    info["list_files"] = [f.name for f in list_files]

    # Count audio files
    wav_dir = dataset_path / "wavs"
    if wav_dir.exists():
        wav_files = list(wav_dir.glob("*.wav"))
        info["num_audio_files"] = len(wav_files)

        # Calculate total size
        total_size = sum(f.stat().st_size for f in wav_files)
        info["total_size_gb"] = total_size / (1024**3)

    # Get metadata if exists
    metadata_file = dataset_path / "metadata.csv"
    if metadata_file.exists():
        info["metadata_file"] = str(metadata_file)
        info["metadata_hash"] = compute_file_hash(metadata_file)

        # Count lines (samples)
        with open(metadata_file) as f:
            info["num_samples"] = sum(1 for _ in f) - 1  # Exclude header

    return info


def get_dependencies_info() -> dict[str, str]:
    """
    Get installed package versions.

    Returns:
        Dictionary with package name -> version
    """
    import numpy
    import torch

    deps = {
        "python": __import__("sys").version.split()[0],
        "torch": torch.__version__,
        "numpy": numpy.__version__,
    }

    # Try to get F5-TTS version
    try:
        import f5_tts

        deps["f5_tts"] = f5_tts.__version__ if hasattr(f5_tts, "__version__") else "unknown"  # type: ignore
    except ImportError:
        pass

    # Try to get soundfile version
    try:
        import soundfile

        deps["soundfile"] = (
            soundfile.__version__ if hasattr(soundfile, "__version__") else "unknown"
        )
    except ImportError:
        pass

    return deps


def get_hardware_info() -> dict[str, Any]:
    """
    Get hardware information.

    Returns:
        Dictionary with GPU, CUDA info
    """
    import torch

    info: dict[str, Any] = {
        "cuda_available": torch.cuda.is_available(),
    }

    if torch.cuda.is_available():
        info["cuda_version"] = torch.version.cuda
        info["cudnn_version"] = str(torch.backends.cudnn.version())
        info["gpu_count"] = torch.cuda.device_count()
        info["gpus"] = [
            {
                "id": i,
                "name": torch.cuda.get_device_name(i),
                "memory_gb": torch.cuda.get_device_properties(i).total_memory / (1024**3),
            }
            for i in range(torch.cuda.device_count())
        ]

    return info


def save_experiment_metadata(
    output_dir: Path,
    config: dict[str, Any],
    dataset_path: Path | None = None,
    vocab_path: Path | None = None,
    extra_info: dict[str, Any] | None = None,
) -> Path:
    """
    Save experiment metadata to JSON file.

    Args:
        output_dir: Experiment output directory
        config: Training configuration dictionary
        dataset_path: Path to dataset (optional)
        vocab_path: Path to vocabulary file (optional)
        extra_info: Additional information to save (optional)

    Returns:
        Path to saved experiment.json file

    Example:
        >>> save_experiment_metadata(
        ...     output_dir=Path('train/output/exp001'),
        ...     config={'learning_rate': 1e-4, 'batch_size': 32},
        ...     dataset_path=Path('train/data/f5_dataset'),
        ...     vocab_path=Path('train/config/vocab.txt'),
        ... )
    """
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    metadata = {
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "git": get_git_status(),
        "config": config,
        "dependencies": get_dependencies_info(),
        "hardware": get_hardware_info(),
    }

    # Add dataset info
    if dataset_path:
        metadata["dataset"] = get_dataset_info(Path(dataset_path))

    # Add vocab hash
    if vocab_path:
        vocab_path = Path(vocab_path)
        if vocab_path.exists():
            metadata["vocab"] = {
                "path": str(vocab_path),
                "hash": f"sha256:{compute_file_hash(vocab_path)}",
            }

    # Add extra info
    if extra_info:
        metadata["extra"] = extra_info

    # Save to file
    output_file = output_dir / "experiment.json"

    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(metadata, f, indent=2, ensure_ascii=False)

    logger.info(f"💾 Saved experiment metadata to: {output_file}")

    # Log important info
    if metadata["git"]["commit"]:
        dirty_marker = " (dirty)" if metadata["git"]["dirty"] else ""
        logger.info(f"   Git commit: {metadata['git']['commit'][:8]}{dirty_marker}")

    if "dataset" in metadata and metadata["dataset"].get("num_samples"):
        logger.info(f"   Dataset: {metadata['dataset']['num_samples']} samples")

    if "vocab" in metadata:
        logger.info(f"   Vocab hash: {metadata['vocab']['hash'][:16]}...")

    return output_file


def load_experiment_metadata(experiment_dir: Path) -> dict[str, Any]:
    """
    Load experiment metadata from JSON file.

    Args:
        experiment_dir: Path to experiment directory

    Returns:
        Experiment metadata dictionary

    Raises:
        FileNotFoundError: If experiment.json does not exist
    """
    metadata_file = Path(experiment_dir) / "experiment.json"

    if not metadata_file.exists():
        raise FileNotFoundError(f"Experiment metadata not found: {metadata_file}")

    with open(metadata_file, encoding="utf-8") as f:
        metadata = json.load(f)

    logger.info(f"📂 Loaded experiment metadata from: {metadata_file}")

    return metadata


# CLI for testing
if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Experiment metadata utilities")
    parser.add_argument("--test-save", action="store_true", help="Test saving metadata")
    parser.add_argument("--output-dir", default="/tmp/test_experiment", help="Output directory")

    args = parser.parse_args()

    # Setup logging
    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")

    if args.test_save:
        # Test saving
        test_config = {
            "learning_rate": 1e-4,
            "batch_size": 32,
            "epochs": 100,
        }

        output_file = save_experiment_metadata(
            output_dir=Path(args.output_dir), config=test_config, extra_info={"test_run": True}
        )

        print(f"\n✅ Saved to: {output_file}")
        print("\nContent:")
        print(output_file.read_text())
    else:
        # Show current environment info
        print("\n" + "=" * 60)
        print("Git Status:")
        git_status = get_git_status()
        for key, value in git_status.items():
            print(f"  {key}: {value}")

        print("\n" + "=" * 60)
        print("Dependencies:")
        deps = get_dependencies_info()
        for pkg, version in deps.items():
            print(f"  {pkg}: {version}")

        print("\n" + "=" * 60)
        print("Hardware:")
        hw = get_hardware_info()
        print(f"  CUDA available: {hw['cuda_available']}")
        if hw["cuda_available"]:
            print(f"  CUDA version: {hw['cuda_version']}")
            print(f"  GPU count: {hw['gpu_count']}")
            for gpu in hw["gpus"]:
                print(f"    - {gpu['name']} ({gpu['memory_gb']:.1f} GB)")

        print("\n" + "=" * 60)
