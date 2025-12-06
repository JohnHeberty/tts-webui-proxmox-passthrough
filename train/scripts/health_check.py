#!/usr/bin/env python3
"""
Health Check Script for F5-TTS Training Environment

Validates system requirements and configuration before training.

Author: F5-TTS Training Pipeline
Sprint: 5 - Training Experience

Usage:
    python train/scripts/health_check.py
    python train/scripts/health_check.py --verbose
"""
import sys
import os
from pathlib import Path
import logging

# Add train directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

logger = logging.getLogger(__name__)


class HealthCheck:
    """System health check for training environment."""
    
    def __init__(self, verbose: bool = False):
        self.verbose = verbose
        self.checks_passed = 0
        self.checks_failed = 0
        self.warnings = 0
    
    def print_header(self, text: str) -> None:
        """Print section header."""
        print(f"\n{'='*60}")
        print(f"  {text}")
        print('='*60)
    
    def check_pass(self, message: str) -> None:
        """Print success message."""
        print(f"✅ {message}")
        self.checks_passed += 1
    
    def check_fail(self, message: str) -> None:
        """Print failure message."""
        print(f"❌ {message}")
        self.checks_failed += 1
    
    def check_warn(self, message: str) -> None:
        """Print warning message."""
        print(f"⚠️  {message}")
        self.warnings += 1
    
    def check_cuda(self) -> bool:
        """Check CUDA availability."""
        try:
            import torch
            
            if torch.cuda.is_available():
                gpu_count = torch.cuda.device_count()
                gpu_name = torch.cuda.get_device_name(0)
                cuda_version = torch.version.cuda
                
                self.check_pass(f"CUDA {cuda_version} available")
                self.check_pass(f"Found {gpu_count}x {gpu_name}")
                
                # Check GPU memory
                gpu_mem_gb = torch.cuda.get_device_properties(0).total_memory / (1024**3)
                if gpu_mem_gb >= 16:
                    self.check_pass(f"GPU memory: {gpu_mem_gb:.1f} GB (sufficient)")
                elif gpu_mem_gb >= 8:
                    self.check_warn(f"GPU memory: {gpu_mem_gb:.1f} GB (may be tight, 16GB+ recommended)")
                else:
                    self.check_fail(f"GPU memory: {gpu_mem_gb:.1f} GB (insufficient, need 8GB+ minimum)")
                
                return True
            else:
                self.check_fail("CUDA not available (GPU required for training)")
                return False
        
        except ImportError:
            self.check_fail("PyTorch not installed")
            return False
    
    def check_disk_space(self) -> bool:
        """Check available disk space."""
        try:
            import shutil
            
            # Check current directory
            stat = shutil.disk_usage('.')
            free_gb = stat.free / (1024**3)
            
            if free_gb >= 50:
                self.check_pass(f"Disk space: {free_gb:.1f} GB free (sufficient)")
                return True
            elif free_gb >= 20:
                self.check_warn(f"Disk space: {free_gb:.1f} GB free (low, 50GB+ recommended)")
                return True
            else:
                self.check_fail(f"Disk space: {free_gb:.1f} GB free (insufficient, need 20GB+ minimum)")
                return False
        
        except Exception as e:
            self.check_fail(f"Could not check disk space: {e}")
            return False
    
    def check_memory(self) -> bool:
        """Check system RAM."""
        try:
            import psutil
            
            mem = psutil.virtual_memory()
            mem_gb = mem.total / (1024**3)
            avail_gb = mem.available / (1024**3)
            
            if mem_gb >= 16:
                self.check_pass(f"RAM: {mem_gb:.1f} GB total ({avail_gb:.1f} GB available)")
                return True
            elif mem_gb >= 8:
                self.check_warn(f"RAM: {mem_gb:.1f} GB total (low, 16GB+ recommended)")
                return True
            else:
                self.check_fail(f"RAM: {mem_gb:.1f} GB total (insufficient, need 8GB+ minimum)")
                return False
        
        except ImportError:
            self.check_warn("psutil not installed, cannot check RAM")
            return True
        except Exception as e:
            self.check_warn(f"Could not check RAM: {e}")
            return True
    
    def check_dependencies(self) -> bool:
        """Check required Python packages."""
        required = [
            ('torch', 'PyTorch'),
            ('numpy', 'NumPy'),
            ('soundfile', 'SoundFile'),
        ]
        
        optional = [
            ('f5_tts', 'F5-TTS'),
            ('pyloudnorm', 'PyLoudnorm'),
            ('scipy', 'SciPy'),
            ('yt_dlp', 'yt-dlp'),
        ]
        
        all_ok = True
        
        # Check required
        for module, name in required:
            try:
                __import__(module)
                self.check_pass(f"{name} installed")
            except ImportError:
                self.check_fail(f"{name} NOT installed (required)")
                all_ok = False
        
        # Check optional
        for module, name in optional:
            try:
                mod = __import__(module)
                version = getattr(mod, '__version__', 'unknown')
                if self.verbose:
                    print(f"   {name} {version} installed")
            except ImportError:
                if self.verbose:
                    print(f"   {name} not installed (optional)")
        
        return all_ok
    
    def check_dataset(self, dataset_path: str = 'train/data/f5_dataset') -> bool:
        """Check dataset existence and structure."""
        dataset_path = Path(dataset_path)
        
        if not dataset_path.exists():
            self.check_warn(f"Dataset not found: {dataset_path}")
            return False
        
        self.check_pass(f"Dataset directory exists: {dataset_path}")
        
        # Check for metadata
        metadata_file = dataset_path / 'metadata.csv'
        if metadata_file.exists():
            # Count samples
            with open(metadata_file) as f:
                num_samples = sum(1 for _ in f) - 1  # Exclude header
            
            if num_samples > 0:
                self.check_pass(f"Found {num_samples} samples in metadata.csv")
            else:
                self.check_warn("metadata.csv is empty")
        else:
            self.check_warn("metadata.csv not found")
        
        # Check for audio files
        wavs_dir = dataset_path / 'wavs'
        if wavs_dir.exists():
            wav_files = list(wavs_dir.glob('*.wav'))
            if wav_files:
                self.check_pass(f"Found {len(wav_files)} audio files in wavs/")
            else:
                self.check_warn("No .wav files found in wavs/")
        else:
            self.check_warn(f"Audio directory not found: wavs/")
        
        return True
    
    def check_vocab(self, vocab_path: str = 'train/config/vocab.txt') -> bool:
        """Check vocabulary file."""
        vocab_path = Path(vocab_path)
        
        if not vocab_path.exists():
            self.check_fail(f"Vocabulary file not found: {vocab_path}")
            return False
        
        self.check_pass(f"Vocabulary file exists: {vocab_path}")
        
        # Load and validate
        try:
            from train.text import load_vocab
            
            vocab = load_vocab(str(vocab_path))
            vocab_size = len(vocab)
            
            if vocab_size > 0:
                self.check_pass(f"Vocabulary loaded: {vocab_size} tokens")
            else:
                self.check_fail("Vocabulary file is empty")
                return False
            
            # Check hash if train/text/vocab.py has validation
            try:
                from train.text import validate_vocab
                
                is_valid, computed_hash, info = validate_vocab(str(vocab_path), verbose=False)
                
                if is_valid:
                    self.check_pass(f"Vocabulary hash valid: {computed_hash[:16]}...")
                else:
                    self.check_warn("Vocabulary hash mismatch (using custom vocab)")
            except Exception:
                pass  # Hash validation optional
            
            return True
        
        except Exception as e:
            self.check_fail(f"Could not load vocabulary: {e}")
            return False
    
    def check_config(self, config_path: str = 'train/config/base_config.yaml') -> bool:
        """Check configuration file."""
        config_path = Path(config_path)
        
        if not config_path.exists():
            self.check_warn(f"Config file not found: {config_path}")
            return False
        
        self.check_pass(f"Config file exists: {config_path}")
        
        # Try to load
        try:
            import yaml
            
            with open(config_path) as f:
                config = yaml.safe_load(f)
            
            if config:
                self.check_pass("Config file is valid YAML")
            else:
                self.check_warn("Config file is empty")
            
            return True
        
        except Exception as e:
            self.check_fail(f"Could not load config: {e}")
            return False
    
    def run_all_checks(self) -> bool:
        """Run all health checks."""
        self.print_header("🏥 F5-TTS Training Environment Health Check")
        
        # Hardware checks
        self.print_header("⚙️  Hardware")
        self.check_cuda()
        self.check_memory()
        self.check_disk_space()
        
        # Software checks
        self.print_header("📦 Dependencies")
        self.check_dependencies()
        
        # Data checks
        self.print_header("📊 Data & Configuration")
        self.check_dataset()
        self.check_vocab()
        self.check_config()
        
        # Summary
        self.print_header("📋 Summary")
        print(f"✅ Passed: {self.checks_passed}")
        print(f"❌ Failed: {self.checks_failed}")
        print(f"⚠️  Warnings: {self.warnings}")
        
        if self.checks_failed == 0:
            print("\n🎉 All critical checks passed! Ready to train.")
            return True
        else:
            print(f"\n⛔ {self.checks_failed} critical check(s) failed. Fix issues before training.")
            return False


def main():
    """Main entry point."""
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Health check for F5-TTS training environment",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        '--verbose', '-v',
        action='store_true',
        help='Show detailed information'
    )
    parser.add_argument(
        '--dataset-path',
        default='train/data/f5_dataset',
        help='Path to dataset directory'
    )
    parser.add_argument(
        '--vocab-path',
        default='train/config/vocab.txt',
        help='Path to vocabulary file'
    )
    parser.add_argument(
        '--config-path',
        default='train/config/base_config.yaml',
        help='Path to config file'
    )
    
    args = parser.parse_args()
    
    # Run health check
    checker = HealthCheck(verbose=args.verbose)
    success = checker.run_all_checks()
    
    # Exit with appropriate code
    sys.exit(0 if success else 1)


if __name__ == '__main__':
    main()
