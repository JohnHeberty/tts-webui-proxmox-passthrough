"""
Reproducibility Utilities for ML Training

Provides tools to ensure reproducible training runs.

Author: F5-TTS Training Pipeline
Sprint: 4 - Reproducibility and MLOps
"""
import os
import random
import logging
from typing import Optional

import numpy as np
import torch

logger = logging.getLogger(__name__)


def set_seed(seed: int, deterministic: bool = True) -> None:
    """
    Set random seed for reproducibility across all libraries.
    
    Sets seeds for:
    - Python random module
    - NumPy
    - PyTorch (CPU and GPU)
    - CUDA (if available)
    
    Args:
        seed: Random seed value
        deterministic: If True, use deterministic algorithms (slower but fully reproducible)
        
    Warning:
        deterministic=True may reduce training speed by ~10% but ensures
        complete reproducibility across runs.
        
    Example:
        >>> set_seed(42, deterministic=True)
        >>> # All random operations are now deterministic
    """
    logger.info(f"🎲 Setting random seed: {seed}")
    
    # Python random module
    random.seed(seed)
    
    # NumPy
    np.random.seed(seed)
    
    # PyTorch
    torch.manual_seed(seed)
    
    # CUDA (all GPUs)
    if torch.cuda.is_available():
        torch.cuda.manual_seed(seed)
        torch.cuda.manual_seed_all(seed)
        logger.info(f"   ✅ CUDA seed set on {torch.cuda.device_count()} GPU(s)")
    
    # Deterministic mode
    if deterministic:
        # Make CuDNN deterministic
        torch.backends.cudnn.deterministic = True
        torch.backends.cudnn.benchmark = False
        
        # Set environment variable for additional determinism
        os.environ['CUBLAS_WORKSPACE_CONFIG'] = ':4096:8'
        
        # Enable deterministic algorithms (PyTorch 1.8+)
        if hasattr(torch, 'use_deterministic_algorithms'):
            try:
                torch.use_deterministic_algorithms(True)
                logger.info("   ✅ Deterministic algorithms enabled")
            except Exception as e:
                logger.warning(f"   ⚠️  Could not enable deterministic algorithms: {e}")
        
        logger.warning(
            "   ⚠️  Deterministic mode enabled - training may be ~10% slower "
            "but fully reproducible"
        )
    else:
        # Benchmark mode for speed (non-deterministic)
        torch.backends.cudnn.benchmark = True
        logger.info("   ⚡ Benchmark mode enabled for faster training (non-deterministic)")
    
    logger.info("   ✅ Random seed configuration complete")


def get_worker_seed(worker_id: int, base_seed: Optional[int] = None) -> int:
    """
    Generate deterministic seed for DataLoader workers.
    
    Ensures each worker has a different but deterministic seed.
    
    Args:
        worker_id: Worker ID from DataLoader
        base_seed: Base random seed (default: from PyTorch initial seed)
        
    Returns:
        Seed for this specific worker
        
    Example:
        >>> def worker_init_fn(worker_id):
        ...     worker_seed = get_worker_seed(worker_id)
        ...     np.random.seed(worker_seed)
        ...     random.seed(worker_seed)
        >>> 
        >>> DataLoader(..., worker_init_fn=worker_init_fn)
    """
    if base_seed is None:
        base_seed = torch.initial_seed()
    
    # Combine base seed with worker ID
    worker_seed = (base_seed + worker_id) % (2**32)
    
    return worker_seed


def worker_init_fn(worker_id: int) -> None:
    """
    Worker initialization function for DataLoader.
    
    Sets deterministic seeds for each worker based on worker ID.
    
    Args:
        worker_id: Worker ID from DataLoader
        
    Usage:
        >>> loader = DataLoader(
        ...     dataset,
        ...     batch_size=32,
        ...     num_workers=4,
        ...     worker_init_fn=worker_init_fn,
        ... )
    """
    worker_seed = get_worker_seed(worker_id)
    np.random.seed(worker_seed)
    random.seed(worker_seed)


def log_environment_info() -> dict:
    """
    Log current environment information for reproducibility.
    
    Returns:
        Dictionary with environment details
        
    Example:
        >>> env_info = log_environment_info()
        >>> print(f"PyTorch: {env_info['torch_version']}")
    """
    env_info = {
        'python_version': os.sys.version,
        'torch_version': torch.__version__,
        'numpy_version': np.__version__,
        'cuda_available': torch.cuda.is_available(),
    }
    
    if torch.cuda.is_available():
        env_info.update({
            'cuda_version': torch.version.cuda,
            'cudnn_version': torch.backends.cudnn.version(),
            'gpu_count': torch.cuda.device_count(),
            'gpu_names': [torch.cuda.get_device_name(i) for i in range(torch.cuda.device_count())],
        })
    
    logger.info("📊 Environment Information:")
    logger.info(f"   Python: {env_info['python_version'].split()[0]}")
    logger.info(f"   PyTorch: {env_info['torch_version']}")
    logger.info(f"   NumPy: {env_info['numpy_version']}")
    
    if env_info['cuda_available']:
        logger.info(f"   CUDA: {env_info['cuda_version']}")
        logger.info(f"   cuDNN: {env_info['cudnn_version']}")
        logger.info(f"   GPUs: {env_info['gpu_count']}x {env_info['gpu_names'][0] if env_info['gpu_names'] else 'Unknown'}")
    else:
        logger.info("   CUDA: Not available (CPU only)")
    
    return env_info


# CLI for testing
if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Test reproducibility utilities")
    parser.add_argument('--seed', type=int, default=42, help='Random seed')
    parser.add_argument('--deterministic', action='store_true', help='Use deterministic mode')
    parser.add_argument('--test-random', action='store_true', help='Test random number generation')
    
    args = parser.parse_args()
    
    # Setup logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(message)s'
    )
    
    # Log environment
    print("\n" + "="*60)
    log_environment_info()
    
    # Set seed
    print("\n" + "="*60)
    set_seed(args.seed, deterministic=args.deterministic)
    
    # Test random generation
    if args.test_random:
        print("\n" + "="*60)
        print("🧪 Testing Random Number Generation:")
        print(f"   Python random: {random.random():.10f}")
        print(f"   NumPy random:  {np.random.random():.10f}")
        print(f"   PyTorch CPU:   {torch.rand(1).item():.10f}")
        
        if torch.cuda.is_available():
            print(f"   PyTorch CUDA:  {torch.rand(1, device='cuda').item():.10f}")
        
        print("\n   💡 Run this script multiple times with the same --seed")
        print("      to verify these numbers are identical (reproducible)")
    
    print("\n" + "="*60)
    print("✅ Reproducibility setup complete!\n")
