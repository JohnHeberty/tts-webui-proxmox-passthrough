"""
Training Callbacks for F5-TTS

Callbacks for monitoring and improving training process.

Author: F5-TTS Training Pipeline
Sprint: 5 - Training Experience
"""

from collections.abc import Callable
import logging
from pathlib import Path
import shutil


logger = logging.getLogger(__name__)


class BestModelCallback:
    """
    Callback to save best model based on validation metric.

    Monitors validation loss (or other metric) and saves checkpoint
    when performance improves.

    Attributes:
        monitor: Metric to monitor (default: 'val_loss')
        mode: 'min' for loss (lower is better) or 'max' for accuracy
        save_path: Directory to save best model
        best_value: Best value seen so far
        best_epoch: Epoch where best value was achieved

    Example:
        >>> callback = BestModelCallback(
        ...     save_path=Path('train/output/exp001'),
        ...     monitor='val_loss',
        ...     mode='min'
        ... )
        >>> # In training loop:
        >>> callback.on_epoch_end(epoch=10, metrics={'val_loss': 0.123})
    """

    def __init__(
        self,
        save_path: Path,
        monitor: str = "val_loss",
        mode: str = "min",
        min_delta: float = 0.0,
        patience: int = 0,
        verbose: bool = True,
    ):
        """
        Initialize best model callback.

        Args:
            save_path: Directory to save best model
            monitor: Metric name to monitor
            mode: 'min' (lower is better) or 'max' (higher is better)
            min_delta: Minimum change to qualify as improvement
            patience: Number of epochs with no improvement before stopping
            verbose: Print when model is saved
        """
        self.save_path = Path(save_path)
        self.monitor = monitor
        self.mode = mode
        self.min_delta = min_delta
        self.patience = patience
        self.verbose = verbose

        # Track best value
        if mode == "min":
            self.best_value = float("inf")
            self.compare = lambda new, best: new < (best - min_delta)
        elif mode == "max":
            self.best_value = float("-inf")
            self.compare = lambda new, best: new > (best + min_delta)
        else:
            raise ValueError(f"mode must be 'min' or 'max', got: {mode}")

        self.best_epoch = 0
        self.epochs_no_improve = 0

        # Ensure save directory exists
        self.save_path.mkdir(parents=True, exist_ok=True)

    def on_epoch_end(
        self,
        epoch: int,
        metrics: dict[str, float],
        checkpoint_path: Path | None = None,
    ) -> bool:
        """
        Called at end of each epoch.

        Args:
            epoch: Current epoch number
            metrics: Dictionary of metric values
            checkpoint_path: Path to checkpoint file to copy (if improvement)

        Returns:
            True if model improved and was saved, False otherwise
        """
        if self.monitor not in metrics:
            logger.warning(f"Metric '{self.monitor}' not found in metrics: {list(metrics.keys())}")
            return False

        current_value = metrics[self.monitor]

        # Check if improved
        if self.compare(current_value, self.best_value):
            # Improvement detected
            old_best = self.best_value
            self.best_value = current_value
            self.best_epoch = epoch
            self.epochs_no_improve = 0

            if self.verbose:
                logger.info(
                    f"🎯 Epoch {epoch}: {self.monitor} improved from "
                    f"{old_best:.6f} to {current_value:.6f}"
                )

            # Save checkpoint
            if checkpoint_path and Path(checkpoint_path).exists():
                best_path = self.save_path / "model_best.pt"
                shutil.copy2(checkpoint_path, best_path)

                if self.verbose:
                    logger.info(f"   💾 Saved best model to: {best_path}")

            # Save metadata
            metadata_path = self.save_path / "best_model_info.txt"
            with open(metadata_path, "w") as f:
                f.write(f"Best epoch: {epoch}\n")
                f.write(f"Best {self.monitor}: {current_value:.6f}\n")
                f.write(f"Metrics: {metrics}\n")

            return True
        else:
            # No improvement
            self.epochs_no_improve += 1

            if self.verbose and self.epochs_no_improve > 0:
                logger.info(
                    f"   Epoch {epoch}: {self.monitor}={current_value:.6f} "
                    f"(no improvement for {self.epochs_no_improve} epochs, "
                    f"best={self.best_value:.6f} @ epoch {self.best_epoch})"
                )

            return False

    def should_stop_early(self) -> bool:
        """
        Check if training should stop due to no improvement.

        Returns:
            True if patience exceeded, False otherwise
        """
        if self.patience > 0 and self.epochs_no_improve >= self.patience:
            logger.info(
                f"🛑 Early stopping: no improvement in {self.monitor} "
                f"for {self.patience} epochs (best={self.best_value:.6f} @ epoch {self.best_epoch})"
            )
            return True
        return False


class AudioSampleCallback:
    """
    Callback to generate audio samples during training.

    Periodically generates audio samples with fixed reference text
    to monitor quality improvement over time.

    Example:
        >>> callback = AudioSampleCallback(
        ...     save_path=Path('train/output/exp001/samples'),
        ...     sample_text="Olá, este é um teste de qualidade.",
        ...     ref_audio_path=Path('reference.wav'),
        ...     generate_fn=model.generate,
        ...     every_n_epochs=10,
        ... )
    """

    def __init__(
        self,
        save_path: Path,
        sample_text: str,
        ref_audio_path: Path,
        generate_fn: Callable,
        every_n_epochs: int = 10,
        sample_rate: int = 24000,
        verbose: bool = True,
    ):
        """
        Initialize audio sample callback.

        Args:
            save_path: Directory to save audio samples
            sample_text: Text to synthesize for quality check
            ref_audio_path: Reference audio for voice cloning
            generate_fn: Function to generate audio (model.generate)
            every_n_epochs: Generate sample every N epochs
            sample_rate: Audio sample rate
            verbose: Print when sample is generated
        """
        self.save_path = Path(save_path)
        self.sample_text = sample_text
        self.ref_audio_path = Path(ref_audio_path)
        self.generate_fn = generate_fn
        self.every_n_epochs = every_n_epochs
        self.sample_rate = sample_rate
        self.verbose = verbose

        # Ensure save directory exists
        self.save_path.mkdir(parents=True, exist_ok=True)

        # Verify reference audio exists
        if not self.ref_audio_path.exists():
            logger.warning(f"Reference audio not found: {ref_audio_path}")

    def on_epoch_end(self, epoch: int, **kwargs) -> None:
        """
        Called at end of each epoch.

        Args:
            epoch: Current epoch number
        """
        # Check if we should generate sample this epoch
        if epoch % self.every_n_epochs != 0:
            return

        try:
            if self.verbose:
                logger.info(f"🎵 Generating audio sample for epoch {epoch}...")

            # Generate audio
            audio = self.generate_fn(
                text=self.sample_text,
                ref_audio=self.ref_audio_path,
            )

            # Save audio
            sample_path = self.save_path / f"sample_epoch_{epoch:04d}.wav"

            import soundfile as sf

            sf.write(sample_path, audio, self.sample_rate)

            if self.verbose:
                logger.info(f"   💾 Saved audio sample to: {sample_path}")

        except Exception as e:
            logger.error(f"Failed to generate audio sample: {e}", exc_info=True)


class MetricsLogger:
    """
    Callback to log metrics to file and console.

    Saves metrics history to JSON/CSV for analysis.

    Example:
        >>> callback = MetricsLogger(save_path=Path('train/output/exp001'))
        >>> callback.on_epoch_end(epoch=1, metrics={'loss': 0.5, 'val_loss': 0.6})
    """

    def __init__(
        self,
        save_path: Path,
        log_every_n_steps: int = 100,
        verbose: bool = True,
    ):
        """
        Initialize metrics logger.

        Args:
            save_path: Directory to save metrics
            log_every_n_steps: Log to console every N steps
            verbose: Print metrics to console
        """
        self.save_path = Path(save_path)
        self.log_every_n_steps = log_every_n_steps
        self.verbose = verbose

        self.metrics_history: dict[str, list] = {}

        # Ensure save directory exists
        self.save_path.mkdir(parents=True, exist_ok=True)

    def on_epoch_end(self, epoch: int, metrics: dict[str, float]) -> None:
        """
        Log metrics at end of epoch.

        Args:
            epoch: Current epoch number
            metrics: Dictionary of metric values
        """
        # Add epoch to metrics
        metrics_with_epoch = {"epoch": epoch, **metrics}

        # Update history
        for key, value in metrics_with_epoch.items():
            if key not in self.metrics_history:
                self.metrics_history[key] = []
            self.metrics_history[key].append(value)

        # Save to CSV
        csv_path = self.save_path / "metrics.csv"

        import csv

        # Write header on first epoch
        if epoch == 1:
            with open(csv_path, "w", newline="") as f:
                writer = csv.DictWriter(f, fieldnames=metrics_with_epoch.keys())
                writer.writeheader()
                writer.writerow(metrics_with_epoch)
        else:
            with open(csv_path, "a", newline="") as f:
                writer = csv.DictWriter(f, fieldnames=metrics_with_epoch.keys())
                writer.writerow(metrics_with_epoch)

        # Print to console
        if self.verbose:
            metrics_str = " | ".join([f"{k}={v:.6f}" for k, v in metrics.items()])
            logger.info(f"📊 Epoch {epoch}: {metrics_str}")

    def save_json(self) -> None:
        """Save metrics history to JSON file."""
        import json

        json_path = self.save_path / "metrics.json"

        with open(json_path, "w") as f:
            json.dump(self.metrics_history, f, indent=2)

        logger.info(f"💾 Saved metrics history to: {json_path}")


# CLI for testing
if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Test training callbacks")
    parser.add_argument("--test-best-model", action="store_true", help="Test BestModelCallback")
    parser.add_argument("--test-metrics", action="store_true", help="Test MetricsLogger")

    args = parser.parse_args()

    # Setup logging
    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")

    if args.test_best_model:
        print("\n" + "=" * 60)
        print("Testing BestModelCallback...")

        callback = BestModelCallback(
            save_path=Path("/tmp/test_callbacks"),
            monitor="val_loss",
            mode="min",
            verbose=True,
        )

        # Simulate training epochs
        for epoch in range(1, 11):
            import random

            val_loss = 1.0 - (epoch * 0.05) + random.uniform(-0.02, 0.02)

            metrics = {"val_loss": val_loss, "train_loss": val_loss - 0.1}
            improved = callback.on_epoch_end(epoch, metrics)

            if callback.should_stop_early():
                print("Early stopping triggered!")
                break

        print(f"\nBest value: {callback.best_value:.6f} @ epoch {callback.best_epoch}")

    elif args.test_metrics:
        print("\n" + "=" * 60)
        print("Testing MetricsLogger...")

        callback = MetricsLogger(save_path=Path("/tmp/test_callbacks"))

        # Simulate training epochs
        for epoch in range(1, 6):
            import random

            metrics = {
                "train_loss": 1.0 - (epoch * 0.1),
                "val_loss": 1.0 - (epoch * 0.08),
                "learning_rate": 0.001 * (0.9**epoch),
            }

            callback.on_epoch_end(epoch, metrics)

        callback.save_json()
        print("\n✅ Metrics saved to /tmp/test_callbacks/")

    else:
        parser.print_help()
