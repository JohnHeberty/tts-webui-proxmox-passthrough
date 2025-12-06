"""
Pydantic schemas for F5-TTS training configuration.

Provides type-safe, validated configuration models for all aspects of
F5-TTS training and dataset preparation.

Author: F5-TTS Training Pipeline
Version: 1.0
Date: 2025-12-06
"""


from pydantic import BaseModel, Field, field_validator, model_validator


# ========================================
# PATHS CONFIGURATION
# ========================================


class PathsConfig(BaseModel):
    """Configuration for all project paths."""

    train_root: str = Field("train", description="Training root directory")
    dataset_base: str = Field("train/data", description="Dataset base directory")
    dataset_name: str = Field("f5_dataset", description="Dataset name")
    dataset_path: str = Field("train/data/f5_dataset", description="Full dataset path")

    raw_data_dir: str = Field("train/data/raw", description="Raw audio directory")
    processed_data_dir: str = Field("train/data/processed", description="Processed data directory")
    videos_csv: str = Field("train/data/videos.csv", description="Videos catalog CSV")

    vocab_file: str = Field(
        "train/config/vocab.txt", description="Vocabulary file (SOURCE OF TRUTH)"
    )

    pretrained_dir: str = Field("train/pretrained", description="Pretrained models directory")
    output_dir: str = Field(
        "train/output/ptbr_finetuned2", description="Output checkpoints directory"
    )
    pretrained_model_path: str = Field(
        "train/pretrained/F5-TTS-pt-br/pt-br/model_200000_fixed.pt",
        description="Pretrained model path",
    )

    log_dir: str = Field("train/logs", description="Logs directory")
    tensorboard_dir: str = Field("train/runs", description="TensorBoard logs directory")
    cache_dir: str = Field("train/data/cache", description="Cache directory")
    config_dir: str = Field("train/config", description="Config directory")

    class Config:
        extra = "forbid"  # Não permite campos extras


# ========================================
# MODEL CONFIGURATION
# ========================================


class EMAConfig(BaseModel):
    """Exponential Moving Average configuration."""

    use_ema: bool = Field(True, description="Use EMA for model weights")
    ema_decay: float = Field(0.9999, ge=0.0, le=1.0, description="EMA decay rate")
    ema_update_every: int = Field(10, ge=1, description="Update EMA every N steps")
    ema_update_after_step: int = Field(100, ge=0, description="Start EMA updates after N steps")


class ModelConfig(BaseModel):
    """Model architecture and loading configuration."""

    base_model: str = Field("firstpixel/F5-TTS-pt-br", description="Base model identifier")
    custom_checkpoint: str | None = Field(
        None, description="Custom checkpoint path (overrides pretrained)"
    )

    auto_download_pretrained: bool = Field(True, description="Auto-download from HuggingFace")
    model_filename: str = Field("pt-br/model_200000.pt", description="Model filename for download")

    model_type: str = Field("DiT", description="Model architecture type", pattern="^(DiT|UNetT)$")
    dim: int = Field(1024, ge=256, description="Model dimension")
    depth: int = Field(22, ge=1, description="Model depth")
    heads: int = Field(16, ge=1, description="Attention heads")
    ff_mult: int = Field(2, ge=1, description="Feed-forward multiplier")
    text_dim: int = Field(512, ge=128, description="Text embedding dimension")
    conv_layers: int = Field(4, ge=0, description="Number of convolutional layers")

    use_ema: bool = Field(True, description="Use EMA (legacy, prefer ema section)")
    ema_decay: float = Field(0.9999, ge=0.0, le=1.0, description="EMA decay (legacy)")
    ema_update_every: int = Field(10, ge=1, description="EMA update frequency (legacy)")
    ema_update_after_step: int = Field(100, ge=0, description="EMA start step (legacy)")


# ========================================
# MEL SPECTROGRAM CONFIGURATION
# ========================================


class MelSpecConfig(BaseModel):
    """Mel spectrogram configuration."""

    target_sample_rate: int = Field(24000, description="Target sample rate (Hz)")
    n_mel_channels: int = Field(100, ge=1, description="Number of mel channels")
    hop_length: int = Field(256, ge=1, description="Hop length for STFT")
    win_length: int = Field(1024, ge=1, description="Window length for STFT")
    n_fft: int = Field(1024, ge=1, description="FFT size")
    mel_spec_type: str = Field("vocos", description="Mel spec type", pattern="^(vocos|bigvgan)$")


# ========================================
# VOCODER CONFIGURATION
# ========================================


class VocoderConfig(BaseModel):
    """Vocoder configuration."""

    name: str = Field("vocos", description="Vocoder name")
    is_local: bool = Field(False, description="Use local vocoder")
    local_path: str | None = Field(None, description="Local vocoder path")


# ========================================
# TRAINING CONFIGURATION
# ========================================


class TrainingConfig(BaseModel):
    """Training hyperparameters."""

    exp_name: str = Field("F5TTS_Base", description="Experiment name")
    dataset_name: str = Field("f5_dataset", description="Dataset name")

    learning_rate: float = Field(1.0e-4, gt=0.0, description="Learning rate")
    batch_size_per_gpu: int = Field(2, ge=1, description="Batch size per GPU")
    batch_size_type: str = Field(
        "sample", description="Batch size type", pattern="^(sample|frame)$"
    )
    max_samples: int = Field(32, ge=1, description="Max samples per batch")
    grad_accumulation_steps: int = Field(8, ge=1, description="Gradient accumulation steps")
    max_grad_norm: float = Field(1.0, gt=0.0, description="Max gradient norm for clipping")

    num_warmup_updates: int = Field(200, ge=0, description="Warmup steps")
    warmup_start_lr: float = Field(1.0e-6, gt=0.0, description="Warmup start LR")
    warmup_end_lr: float = Field(1.0e-4, gt=0.0, description="Warmup end LR")

    epochs: int = Field(1000, ge=1, description="Number of epochs")
    max_steps: int | None = Field(None, description="Max training steps (overrides epochs)")

    early_stop_patience: int = Field(1000, ge=0, description="Early stopping patience (0=disabled)")
    early_stop_min_delta: float = Field(
        0.001, ge=0.0, description="Min improvement for early stopping"
    )

    use_finetune_flag: bool = Field(True, description="Use finetune flag")


# ========================================
# OPTIMIZER CONFIGURATION
# ========================================


class OptimizerConfig(BaseModel):
    """Optimizer configuration."""

    type: str = Field("AdamW", description="Optimizer type", pattern="^(AdamW|Adam8bit)$")
    betas: list[float] = Field([0.9, 0.95], description="Adam betas")
    weight_decay: float = Field(0.0, ge=0.0, description="Weight decay")
    eps: float = Field(1.0e-8, gt=0.0, description="Epsilon")
    use_8bit_adam: bool = Field(False, description="Use 8-bit Adam optimizer")

    @field_validator("betas")
    @classmethod
    def validate_betas(cls, v):
        if len(v) != 2:
            raise ValueError("betas must have exactly 2 values")
        if not all(0.0 < b < 1.0 for b in v):
            raise ValueError("betas must be between 0 and 1")
        return v


# ========================================
# MIXED PRECISION CONFIGURATION
# ========================================


class MixedPrecisionConfig(BaseModel):
    """Mixed precision training configuration."""

    enabled: bool = Field(True, description="Enable mixed precision")
    dtype: str | None = Field("fp16", description="Data type", pattern="^(fp16|bf16|null)$")


# ========================================
# CHECKPOINT CONFIGURATION
# ========================================


class CheckpointsConfig(BaseModel):
    """Checkpoint saving configuration."""

    save_per_updates: int = Field(500, ge=1, description="Save checkpoint every N updates")
    save_per_epochs: int = Field(1, ge=1, description="Save checkpoint every N epochs")
    keep_last_n_checkpoints: int = Field(3, ge=1, description="Keep last N checkpoints")
    last_per_updates: int = Field(100, ge=1, description="Save 'last' checkpoint every N updates")

    resume_from_checkpoint: str | None = Field(None, description="Resume from checkpoint path")

    log_samples: bool = Field(True, description="Log audio samples")
    log_samples_per_updates: int = Field(500, ge=1, description="Log samples every N updates")
    log_samples_per_epochs: int = Field(1, ge=1, description="Log samples every N epochs")


# ========================================
# LOGGING CONFIGURATION
# ========================================


class WandBConfig(BaseModel):
    """Weights & Biases configuration."""

    enabled: bool = Field(False, description="Enable W&B logging")
    project: str = Field("f5tts-ptbr-finetune", description="W&B project name")
    entity: str | None = Field(None, description="W&B entity (username/team)")
    run_name: str | None = Field(None, description="W&B run name")


class LoggingConfig(BaseModel):
    """Logging and monitoring configuration."""

    logger: str = Field(
        "tensorboard", description="Logger type", pattern="^(tensorboard|wandb|null)$"
    )
    log_every_n_steps: int = Field(10, ge=1, description="Log every N steps")

    wandb: WandBConfig = Field(default_factory=WandBConfig, description="W&B config")
    tensorboard_port: int = Field(6006, ge=1024, le=65535, description="TensorBoard port")


# ========================================
# HARDWARE CONFIGURATION
# ========================================


class HardwareConfig(BaseModel):
    """Hardware configuration."""

    device: str = Field("cuda", description="Device", pattern="^(cuda|cpu|auto)$")
    num_gpus: int = Field(1, ge=1, description="Number of GPUs")
    num_workers: int = Field(2, ge=0, description="Number of workers")
    dataloader_workers: int = Field(8, ge=0, description="DataLoader workers")
    pin_memory: bool = Field(True, description="Pin memory for DataLoader")
    persistent_workers: bool = Field(True, description="Persistent workers")


# ========================================
# VALIDATION CONFIGURATION
# ========================================


class ValidationConfig(BaseModel):
    """Validation configuration."""

    enabled: bool = Field(False, description="Enable validation")
    val_dataset_path: str | None = Field(None, description="Validation dataset path")
    val_every_n_updates: int = Field(1000, ge=1, description="Validate every N updates")
    num_val_samples: int = Field(100, ge=1, description="Number of validation samples")


# ========================================
# ADVANCED CONFIGURATION
# ========================================


class AdvancedConfig(BaseModel):
    """Advanced training configuration."""

    gradient_checkpointing: bool = Field(True, description="Enable gradient checkpointing")
    seed: int = Field(666, ge=0, description="Random seed")
    compile_model: bool = Field(False, description="Compile model (PyTorch 2.0+)")

    f5tts_base_dir: str | None = Field(None, description="F5-TTS base directory")
    f5tts_ckpts_dir: str | None = Field(None, description="F5-TTS checkpoints directory")


# ========================================
# AUDIO PROCESSING CONFIGURATION
# ========================================


class AudioConfig(BaseModel):
    """Audio processing configuration."""

    target_sample_rate: int = Field(24000, description="Target sample rate (Hz)")
    format: str = Field("wav", description="Audio format")
    channels: int = Field(1, ge=1, le=2, description="Number of audio channels")
    bit_depth: int = Field(16, description="Bit depth")

    normalize_audio: bool = Field(True, description="Normalize audio")
    target_lufs: float = Field(-23.0, description="Target LUFS for normalization")
    headroom_db: float = Field(-1.0, description="Headroom (dB)")
    fade_ms: float = Field(5.0, ge=0.0, description="Fade in/out duration (ms)")


# ========================================
# SEGMENTATION CONFIGURATION
# ========================================


class SegmentationConfig(BaseModel):
    """Audio segmentation configuration."""

    min_duration: float = Field(3.0, gt=0.0, description="Minimum segment duration (seconds)")
    max_duration: float = Field(10.0, gt=0.0, description="Maximum segment duration (seconds)")
    target_duration: float = Field(7.0, gt=0.0, description="Target segment duration (seconds)")
    segment_overlap: float = Field(0.1, ge=0.0, description="Segment overlap (seconds)")

    use_vad: bool = Field(True, description="Use Voice Activity Detection")
    vad_threshold: float = Field(-40.0, description="VAD threshold (dB)")
    vad_frame_size: int = Field(512, ge=64, description="VAD frame size")
    vad_chunk_duration: float = Field(10.0, gt=0.0, description="VAD chunk duration (seconds)")

    remove_silence: bool = Field(True, description="Remove silence")
    silence_threshold_db: float = Field(-40.0, description="Silence threshold (dB)")
    min_silence_duration: float = Field(0.3, ge=0.0, description="Min silence duration (seconds)")

    @field_validator("target_duration")
    @classmethod
    def validate_target_duration(cls, v, info):
        values = info.data
        if "min_duration" in values and "max_duration" in values:
            if not (values["min_duration"] <= v <= values["max_duration"]):
                raise ValueError("target_duration must be between min_duration and max_duration")
        return v


# ========================================
# TRANSCRIPTION CONFIGURATION
# ========================================


class ASRConfig(BaseModel):
    """ASR (Whisper) configuration."""

    model: str = Field(
        "base", description="Whisper model", pattern="^(tiny|base|small|medium|large|large-v2)$"
    )
    high_precision_model: str = Field("base", description="High precision model")
    device: str = Field("cuda", description="Device", pattern="^(cuda|cpu)$")
    language: str = Field("pt", description="Language code")
    task: str = Field("transcribe", description="Task", pattern="^(transcribe|translate)$")

    beam_size: int = Field(5, ge=1, description="Beam size")
    best_of: int = Field(5, ge=1, description="Best of")
    temperature: float = Field(0.0, ge=0.0, le=1.0, description="Temperature")

    hp_beam_size: int = Field(8, ge=1, description="High precision beam size")
    hp_best_of: int = Field(8, ge=1, description="High precision best of")
    hp_temperature: float = Field(0.0, ge=0.0, le=1.0, description="High precision temperature")

    use_vad_filter: bool = Field(True, description="Use VAD filter")
    vad_filter_min_silence_duration: float = Field(
        0.5, ge=0.0, description="VAD min silence (seconds)"
    )


class TranscriptionConfig(BaseModel):
    """Transcription configuration."""

    prefer_youtube_subtitles: bool = Field(True, description="Prefer YouTube subtitles over ASR")
    asr: ASRConfig = Field(default_factory=ASRConfig, description="ASR configuration")


# ========================================
# TEXT PREPROCESSING CONFIGURATION
# ========================================


class TextPreprocessingConfig(BaseModel):
    """Text preprocessing configuration."""

    lowercase: bool = Field(True, description="Convert to lowercase")
    convert_numbers_to_words: bool = Field(True, description="Convert numbers to words")
    numbers_lang: str = Field("pt_BR", description="Language for number conversion")

    normalize_punctuation: bool = Field(True, description="Normalize punctuation")
    remove_special_chars: bool = Field(True, description="Remove special characters")
    allowed_chars: str = Field(
        "abcdefghijklmnopqrstuvwxyzáàâãéêíóôõúçABCDEFGHIJKLMNOPQRSTUVWXYZÁÀÂÃÉÊÍÓÔÕÚÇ0123456789 .,!?;:-'\"()",
        description="Allowed characters",
    )

    replacements: dict[str, str] = Field(
        default_factory=lambda: {"...": ".", "!!": "!", "??": "?", "  ": " "},
        description="Text replacements",
    )

    min_text_length: int = Field(10, ge=1, description="Min text length (characters)")
    max_text_length: int = Field(500, ge=1, description="Max text length (characters)")
    min_word_count: int = Field(2, ge=1, description="Min word count")

    cleanup_segment_edges: bool = Field(True, description="Cleanup segment edges")

    retranscribe_on_oov: bool = Field(True, description="Retranscribe on high OOV")
    oov_ratio_threshold: float = Field(0.6, ge=0.0, le=1.0, description="OOV ratio threshold")
    oov_min_unknowns: int = Field(4, ge=1, description="Min unknown words for retranscription")
    oov_min_total_words: int = Field(8, ge=1, description="Min total words for OOV check")

    remove_lines_with: list[str] = Field(
        default_factory=lambda: ["[música]", "[aplausos]", "[risos]", "♪", "�"],
        description="Terms to remove lines containing",
    )


# ========================================
# YOUTUBE CONFIGURATION
# ========================================


class SubtitlesConfig(BaseModel):
    """YouTube subtitles configuration."""

    download_auto_subs: bool = Field(True, description="Download auto-generated subtitles")
    subtitle_formats: list[str] = Field(["vtt", "srt"], description="Subtitle formats")
    subtitle_langs: list[str] = Field(["pt", "pt-BR"], description="Subtitle languages")


class YouTubeConfig(BaseModel):
    """YouTube download configuration."""

    audio_format: str = Field("bestaudio", description="Audio format")
    audio_quality: str = Field("best", description="Audio quality")
    rate_limit: str = Field("1M", description="Rate limit")
    max_retries: int = Field(3, ge=0, description="Max retries")
    retry_delay: int = Field(5, ge=1, description="Retry delay (seconds)")
    subtitles: SubtitlesConfig = Field(
        default_factory=SubtitlesConfig, description="Subtitles config"
    )


# ========================================
# DATASET SPLIT CONFIGURATION
# ========================================


class SplitConfig(BaseModel):
    """Dataset split configuration."""

    train_ratio: float = Field(0.95, ge=0.0, le=1.0, description="Train split ratio")
    val_ratio: float = Field(0.05, ge=0.0, le=1.0, description="Validation split ratio")
    shuffle: bool = Field(True, description="Shuffle before split")
    random_seed: int = Field(42, ge=0, description="Random seed for split")

    @model_validator(mode="after")
    def validate_split_ratios(self):
        train = self.train_ratio
        val = self.val_ratio
        if abs(train + val - 1.0) > 1e-6:
            raise ValueError(f"train_ratio + val_ratio must equal 1.0 (got {train + val})")
        return self


# ========================================
# QUALITY FILTERS CONFIGURATION
# ========================================


class QualityFiltersConfig(BaseModel):
    """Quality filters configuration."""

    min_snr_db: float = Field(10.0, description="Min SNR (dB)")
    skip_too_short: bool = Field(True, description="Skip too short segments")
    skip_too_long: bool = Field(True, description="Skip too long segments")
    min_speech_rate: float = Field(5.0, gt=0.0, description="Min speech rate (chars/second)")
    max_speech_rate: float = Field(25.0, gt=0.0, description="Max speech rate (chars/second)")
    skip_music: bool = Field(True, description="Skip segments with music")
    music_detection_threshold: float = Field(
        0.3, ge=0.0, le=1.0, description="Music detection threshold"
    )


# ========================================
# OUTPUT CONFIGURATION
# ========================================


class OutputConfig(BaseModel):
    """Dataset output configuration."""

    format: str = Field("arrow", description="Dataset format", pattern="^(arrow|parquet)$")
    metadata_filename: str = Field("metadata.csv", description="Metadata filename")
    metadata_separator: str = Field("|", description="Metadata separator")
    wavs_subdir: str = Field("wavs", description="Wavs subdirectory")
    generate_vocab: bool = Field(False, description="Generate vocab file")
    save_duration_json: bool = Field(True, description="Save duration JSON")


# ========================================
# DATA PREPARATION CONFIGURATION
# ========================================


class DataPreparationConfig(BaseModel):
    """Data preparation advanced configuration."""

    num_workers: int = Field(4, ge=1, description="Number of workers")
    chunk_size: int = Field(100, ge=1, description="Chunk size for processing")
    cache_downloads: bool = Field(True, description="Cache downloads")
    verbose: bool = Field(True, description="Verbose logging")


# ========================================
# MAIN CONFIG MODEL
# ========================================


class F5TTSConfig(BaseModel):
    """Complete F5-TTS training configuration."""

    paths: PathsConfig = Field(default_factory=PathsConfig)
    model: ModelConfig = Field(default_factory=ModelConfig)
    mel_spec: MelSpecConfig = Field(default_factory=MelSpecConfig)
    vocoder: VocoderConfig = Field(default_factory=VocoderConfig)
    training: TrainingConfig = Field(default_factory=TrainingConfig)
    optimizer: OptimizerConfig = Field(default_factory=OptimizerConfig)
    mixed_precision: MixedPrecisionConfig = Field(default_factory=MixedPrecisionConfig)
    checkpoints: CheckpointsConfig = Field(default_factory=CheckpointsConfig)
    logging: LoggingConfig = Field(default_factory=LoggingConfig)
    hardware: HardwareConfig = Field(default_factory=HardwareConfig)
    validation: ValidationConfig = Field(default_factory=ValidationConfig)
    advanced: AdvancedConfig = Field(default_factory=AdvancedConfig)

    # Dataset preparation
    audio: AudioConfig = Field(default_factory=AudioConfig)
    segmentation: SegmentationConfig = Field(default_factory=SegmentationConfig)
    transcription: TranscriptionConfig = Field(default_factory=TranscriptionConfig)
    text_preprocessing: TextPreprocessingConfig = Field(default_factory=TextPreprocessingConfig)
    youtube: YouTubeConfig = Field(default_factory=YouTubeConfig)
    split: SplitConfig = Field(default_factory=SplitConfig)
    quality_filters: QualityFiltersConfig = Field(default_factory=QualityFiltersConfig)
    output: OutputConfig = Field(default_factory=OutputConfig)
    data_preparation: DataPreparationConfig = Field(default_factory=DataPreparationConfig)

    class Config:
        extra = "forbid"  # Não permite campos extras não definidos
        validate_assignment = True  # Valida quando atribuir valores
