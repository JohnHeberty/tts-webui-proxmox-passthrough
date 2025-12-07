"""
Training Settings using Pydantic
Consolidates train_config.yaml into type-safe Python configuration
"""
from pathlib import Path
from typing import Optional
from pydantic import BaseModel, Field, field_validator, model_validator


class TrainingSettings(BaseModel):
    """XTTS Fine-tuning Training Settings"""
    
    # === Hardware ===
    device: str = Field(default="cuda", description="Training device")
    cuda_device_id: int = Field(default=0, description="CUDA device ID")
    
    # === Model ===
    model_name: str = Field(
        default="tts_models/multilingual/multi-dataset/xtts_v2",
        description="Base XTTS model"
    )
    use_lora: bool = Field(default=True, description="Enable LoRA fine-tuning")
    lora_rank: int = Field(default=8, description="LoRA rank")
    lora_alpha: int = Field(default=16, description="LoRA alpha")
    lora_dropout: float = Field(default=0.1, description="LoRA dropout")
    
    # === Dataset ===
    dataset_dir: Path = Field(
        default=Path("train/data/MyTTSDataset"),
        description="Dataset directory"
    )
    train_metadata: str = Field(default="metadata_train.csv")
    val_metadata: str = Field(default="metadata_val.csv")
    sample_rate: int = Field(default=24000, description="Audio sample rate")
    batch_size: int = Field(default=2, description="Training batch size")
    num_workers: int = Field(default=2, description="DataLoader workers")
    
    # === Training Hyperparameters ===
    num_epochs: int = Field(default=1000, description="Number of epochs")
    learning_rate: float = Field(default=1.0e-5, description="Learning rate")
    adam_beta1: float = Field(default=0.9)
    adam_beta2: float = Field(default=0.999)
    adam_epsilon: float = Field(default=1.0e-8)
    weight_decay: float = Field(default=0.01)
    max_grad_norm: float = Field(default=1.0, description="Gradient clipping")
    use_amp: bool = Field(default=False, description="Use mixed precision")
    lr_scheduler: str = Field(default="cosine", description="LR scheduler type")
    warmup_steps: int = Field(default=100, description="Warmup steps")
    
    # === Logging ===
    log_every_n_steps: int = Field(default=10)
    save_every_n_epochs: int = Field(default=1, description="Checkpoint frequency")
    use_tensorboard: bool = Field(default=True)
    log_dir: Path = Field(default=Path("train/runs"), description="TensorBoard logs")
    
    # === Output ===
    output_dir: Path = Field(
        default=Path("train/output"),
        description="Output directory"
    )
    checkpoint_dir: Path = Field(
        default=Path("train/output/checkpoints"),
        description="Checkpoint directory"
    )
    samples_dir: Path = Field(
        default=Path("train/output/samples"),
        description="Audio samples directory"
    )
    
    @model_validator(mode='after')
    def create_all_directories(self):
        """Create all directories after model initialization"""
        # Create main directories
        self.dataset_dir.mkdir(parents=True, exist_ok=True)
        self.log_dir.mkdir(parents=True, exist_ok=True)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # Create output subdirectories
        self.checkpoint_dir.mkdir(parents=True, exist_ok=True)
        self.samples_dir.mkdir(parents=True, exist_ok=True)
        
        return self
    
    @field_validator("dataset_dir", "log_dir")
    @classmethod
    def validate_paths(cls, v: Path) -> Path:
        """Validate paths are Path objects"""
        return v
    
    @field_validator("sample_rate")
    @classmethod
    def validate_sample_rate(cls, v: int) -> int:
        """Validate sample rate matches XTTS (24kHz)"""
        if v != 24000:
            raise ValueError("XTTS requires 24kHz sample rate")
        return v
    
    class Config:
        arbitrary_types_allowed = True


# Singleton instance
_train_settings: Optional[TrainingSettings] = None


def get_train_settings() -> TrainingSettings:
    """Get training settings singleton"""
    global _train_settings
    if _train_settings is None:
        _train_settings = TrainingSettings()
    return _train_settings
