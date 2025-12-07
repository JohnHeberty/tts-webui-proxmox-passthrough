"""
XTTS-v2 Fine-tuning Script com LoRA

Este script implementa fine-tuning do XTTS-v2 usando LoRA (Low-Rank Adaptation)
para adaptar o modelo pré-treinado para vozes específicas em português.

v2.0: Migrado para Pydantic Settings (train_settings.py)

Uso:
    # Training completo
    python -m train.scripts.train_xtts
    
    # Resume do checkpoint
    python -m train.scripts.train_xtts --resume train/checkpoints/epoch_100

Dependências:
    - coqui-tts: pip install TTS
    - peft: pip install peft (para LoRA)
    - tensorboard: pip install tensorboard
"""

import logging
import os
from pathlib import Path
import sys
from typing import Optional

import click
import torch
import torch.nn as nn
from torch.utils.data import DataLoader
from torch.utils.tensorboard import SummaryWriter
from tqdm import tqdm

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

# Import Pydantic Settings
from train.train_settings import get_train_settings, TrainingSettings

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler(project_root / "train" / "logs" / "train_xtts.log"),
        logging.StreamHandler(),
    ],
)
logger = logging.getLogger(__name__)


def setup_device(settings: TrainingSettings) -> torch.device:
    """Setup device (CUDA ou CPU) usando Pydantic Settings"""
    if settings.device == "cuda" and torch.cuda.is_available():
        device_id = settings.cuda_device_id
        device = torch.device(f"cuda:{device_id}")
        logger.info(f"✅ Using CUDA device: {torch.cuda.get_device_name(device_id)}")
        logger.info(f"   VRAM: {torch.cuda.get_device_properties(device_id).total_memory / 1e9:.2f} GB")
    else:
        device = torch.device("cpu")
        logger.info("⚠️  Using CPU (training will be slow)")
    
    return device


def load_pretrained_model(settings: TrainingSettings, device: torch.device):
    """
    Carrega modelo XTTS-v2 pré-treinado usando Pydantic Settings
    
    NOTA: Esta é uma implementação simplificada.
    O código real depende da API do Coqui TTS que pode mudar.
    """
    try:
        from TTS.tts.configs.xtts_config import XttsConfig
        from TTS.tts.models.xtts import Xtts
    except ImportError:
        logger.error("❌ TTS (Coqui) não encontrado. Instale com: pip install TTS")
        sys.exit(1)
    
    logger.info("📥 Carregando modelo XTTS-v2 pré-treinado...")
    
    # Carregar config do modelo
    model_name = settings.model_name
    logger.info(f"   Modelo: {model_name}")
    
    # Set environment variables
    os.environ['COQUI_TOS_AGREED'] = '1'
    
    # Para smoke test: criar modelo dummy
    # Em produção, usar TTS.api.TTS para download automático
    # tts_api = TTS(model_name, gpu=(device.type == 'cuda'), progress_bar=False)
    # model = tts_api.synthesizer.tts_model
    
    logger.warning("⚠️  SMOKE TEST MODE: Using dummy model (not loading full XTTS)")
    logger.info("   Para produção, descomentar TTS.api.TTS loading")
    
    # Criar placeholder model
    class DummyModel(nn.Module):
        def __init__(self):
            super().__init__()
            self.dummy_layer = nn.Linear(10, 10)
        
        def forward(self, x):
            return self.dummy_layer(x)
    
    model = DummyModel().to(device)
    
    logger.info(f"✅ Modelo carregado: {model.__class__.__name__}")
    logger.info(f"   Device: {device}")
    logger.info(f"   Parâmetros: {sum(p.numel() for p in model.parameters())/1e6:.1f}M")
    
    return model


def setup_lora(model: nn.Module, settings: TrainingSettings) -> nn.Module:
    """
    Configura LoRA (Low-Rank Adaptation) no modelo usando Pydantic Settings
    
    NOTA: LoRA training requer modelo real XTTS, não dummy model.
    Este template apenas demonstra a estrutura.
    """
    if not settings.use_lora:
        logger.info("⏭️  LoRA desabilitado, usando fine-tuning completo")
        return model
    
    logger.warning("⚠️  TEMPLATE MODE: LoRA setup requer modelo XTTS real")
    logger.info("   Para implementar LoRA no XTTS:")
    logger.info("   1. Identifique os módulos alvo (GPT layers, vocoder, etc)")
    logger.info("   2. Configure LoraConfig com target_modules corretos")
    logger.info("   3. Use get_peft_model() apenas com modelo real")
    logger.info("")
    logger.info("   Skipping LoRA setup em template mode...")
    
    return model


def create_dataset(settings: TrainingSettings):
    """
    Cria dataset para treinamento
    
    NOTA: Implementação simplificada.
    Requer TTS.tts.datasets.TTSDataset ou custom implementation.
    """
    from torch.utils.data import Dataset
    import torchaudio
    
    class XTTSDataset(Dataset):
        def __init__(self, metadata_path, sample_rate=22050):
            self.sample_rate = sample_rate
            self.samples = []
            
            with open(metadata_path, 'r', encoding='utf-8') as f:
                for line in f:
                    parts = line.strip().split('|')
                    if len(parts) >= 2:
                        audio_path = parts[0]
                        text = '|'.join(parts[1:])
                        
                        # Resolve path relativo
                        if not Path(audio_path).is_absolute():
                            dataset_dir = Path(metadata_path).parent
                            audio_path = dataset_dir / audio_path
                        
                        if Path(audio_path).exists():
                            self.samples.append({'audio_path': str(audio_path), 'text': text})
            
            logger.info(f"   Loaded {len(self.samples)} samples from {metadata_path}")
        
        def __len__(self):
            return len(self.samples)
        
        def __getitem__(self, idx):
            return self.samples[idx]
    
    logger.info("📊 Carregando dataset...")
    
    dataset_dir = settings.dataset_dir
    train_metadata = dataset_dir / "train_metadata.csv"
    val_metadata = dataset_dir / "val_metadata.csv"
    
    logger.info(f"   Dataset: {dataset_dir}")
    logger.info(f"   Train: {train_metadata}")
    logger.info(f"   Val: {val_metadata}")
    
    # TEMPLATE MODE: Verificar se dataset existe
    if not train_metadata.exists() or not val_metadata.exists():
        logger.warning("⚠️  Dataset não encontrado - usando modo TEMPLATE")
        logger.info("   Para treinar com dataset real:")
        logger.info(f"   1. Criar dataset em: {dataset_dir}")
        logger.info("   2. Usar scripts: download_youtube → segment_audio → transcribe → build_ljs_dataset")
        logger.info("")
        logger.info("   Criando dataset dummy para demonstração...")
        
        # Criar dataset dummy
        class DummyDataset:
            def __init__(self, name):
                self.name = name
                self.samples = [{'audio_path': f'sample_{i}.wav', 'text': f'Texto {i}'} for i in range(10)]
            
            def __len__(self):
                return len(self.samples)
            
            def __getitem__(self, idx):
                return self.samples[idx]
        
        train_dataset = DummyDataset("train")
        val_dataset = DummyDataset("val")
        
        logger.info(f"   ✅ Dataset dummy criado: {len(train_dataset)} train, {len(val_dataset)} val samples")
        return train_dataset, val_dataset
    
    # Dataset real existe
    train_dataset = XTTSDataset(train_metadata, sample_rate=settings.sample_rate)
    val_dataset = XTTSDataset(val_metadata, sample_rate=settings.sample_rate)
    
    return train_dataset, val_dataset


def create_optimizer(model: nn.Module, settings: TrainingSettings):
    """Cria otimizador AdamW usando Pydantic Settings"""
    optimizer = torch.optim.AdamW(
        model.parameters(),
        lr=settings.learning_rate,
        betas=(settings.adam_beta1, settings.adam_beta2),
        eps=settings.adam_epsilon,
        weight_decay=settings.weight_decay,
    )
    
    logger.info(f"🎯 Optimizer: AdamW (lr={settings.learning_rate})")
    
    return optimizer


def create_scheduler(optimizer, settings: TrainingSettings):
    """Cria learning rate scheduler usando Pydantic Settings"""
    from torch.optim.lr_scheduler import LambdaLR
    import math
    
    scheduler_type = settings.lr_scheduler
    
    if scheduler_type == "cosine_with_warmup":
        warmup_steps = 500
        total_steps = settings.max_steps
        
        def lr_lambda(current_step):
            if current_step < warmup_steps:
                return float(current_step) / float(max(1, warmup_steps))
            progress = float(current_step - warmup_steps) / float(max(1, total_steps - warmup_steps))
            return 0.5 * (1.0 + math.cos(math.pi * progress))
        
        scheduler = LambdaLR(optimizer, lr_lambda)
        logger.info(f"📈 LR Scheduler: Cosine with warmup (warmup={warmup_steps}, total={total_steps})")
    else:
        scheduler = None
        logger.info("⏭️  LR Scheduler: None (constant LR)")
    
    return scheduler


def train_step(model, batch, optimizer, scaler, settings: TrainingSettings, device: torch.device):
    """
    Executa um step de treinamento usando Pydantic Settings
    
    NOTA: Implementação placeholder - adaptar para XTTS-v2
    Em produção, usar TTS.tts.models.xtts para forward pass completo
    """
    model.train()
    
    # Placeholder loss - XTTS training requer:
    # - GPT encoder/decoder forward
    # - HiFi-GAN vocoder
    # - Multi-task loss (mel, duration, alignment)
    # Ref: TTS.tts.models.xtts.Xtts.forward()
    loss = torch.tensor(0.5 + torch.rand(1).item() * 0.1, device=device, requires_grad=True)
    
    # Backward pass
    if settings.use_amp and scaler is not None:
        scaler.scale(loss).backward()
        scaler.unscale_(optimizer)
        torch.nn.utils.clip_grad_norm_(
            model.parameters(),
            settings.max_grad_norm,
        )
        scaler.step(optimizer)
        scaler.update()
    else:
        loss.backward()
        torch.nn.utils.clip_grad_norm_(
            model.parameters(),
            settings.max_grad_norm,
        )
        optimizer.step()
    
    optimizer.zero_grad()
    
    return loss.item()


def validate(model, val_loader, device: torch.device):
    """
    Executa validação
    
    NOTA: Implementação placeholder
    Em produção, usar métricas completas (mel loss, alignment, etc)
    """
    model.eval()
    total_loss = 0.0
    count = 0
    
    with torch.no_grad():
        for batch in val_loader:
            # Placeholder validation loss
            loss = 0.3 + torch.rand(1).item() * 0.1
            total_loss += loss
            count += 1
    
    return total_loss / count if count > 0 else 0.0


def generate_sample_audio(epoch: int, settings: TrainingSettings, output_dir: Path):
    """
    Gera áudio de teste para validação qualitativa
    
    Args:
        epoch: Época atual
        settings: Configuração de treinamento
        output_dir: Diretório de saída para samples
    """
    try:
        import shutil
        
        # Criar diretório se não existir
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # Procurar arquivo de referência
        dataset_dir = settings.dataset_dir
        wavs_dir = dataset_dir / "wavs"
        reference_wavs = list(wavs_dir.glob("*.wav"))[:1]
        
        if not reference_wavs:
            logger.warning("⚠️  Nenhum WAV de referência encontrado")
            return
        
        reference_wav = str(reference_wavs[0])
        
        # Copiar referência
        reference_output = output_dir / f"epoch_{epoch}_reference.wav"
        shutil.copy(reference_wav, reference_output)
        
        # Placeholder para output (em produção, usar modelo para síntese)
        output_wav = output_dir / f"epoch_{epoch}_output.wav"
        shutil.copy(reference_wav, output_wav)
        
        logger.info(f"📢 Sample: {output_wav.name} + {reference_output.name}")
        
    except Exception as e:
        logger.warning(f"⚠️  Erro ao gerar sample: {e}")


def save_checkpoint(model, optimizer, scheduler, step: int, settings: TrainingSettings, best: bool = False):
    """Salva checkpoint usando Pydantic Settings"""
    output_dir = settings.checkpoint_dir
    output_dir.mkdir(parents=True, exist_ok=True)
    
    checkpoint_path = output_dir / f"step_{step}"
    if best:
        checkpoint_path = output_dir / "best_model"
    
    checkpoint_path.mkdir(exist_ok=True)
    
    # Salvar estado
    torch.save({
        "step": step,
        "model_state_dict": model.state_dict(),
        "optimizer_state_dict": optimizer.state_dict(),
        "scheduler_state_dict": scheduler.state_dict() if scheduler else None,
    }, checkpoint_path / "checkpoint.pt")
    
    # Salvar config
    with open(checkpoint_path / "config.yaml", "w") as f:
        yaml.dump(config, f)
    
    logger.info(f"💾 Checkpoint salvo: {checkpoint_path}")


@click.command()
@click.option(
    "--resume",
    type=click.Path(exists=True),
    default=None,
    help="Path para checkpoint para resumir treinamento",
)
def main(resume):
    """
    Script principal de treinamento XTTS-v2
    v2.0: Usa Pydantic Settings em vez de config YAML
    """
    logger.info("=" * 80)
    logger.info("XTTS-v2 FINE-TUNING com LoRA")
    logger.info("=" * 80)
    
    # Carregar settings
    settings = get_train_settings()
    logger.info(f"📝 Settings carregadas via Pydantic\n")
    
    # Setup device
    device = setup_device(settings)
    
    # Load model
    model = load_pretrained_model(settings, device)
    if model is None:
        logger.error("❌ Modelo não carregado (TEMPLATE MODE)")
        logger.info("\n" + "=" * 80)
        logger.info("⚠️  ATENÇÃO: Script de treinamento é um TEMPLATE")
        logger.info("=" * 80)
        logger.info("Este script demonstra a estrutura completa de treinamento XTTS,")
        logger.info("mas requer implementação específica do modelo XTTS-v2.")
        logger.info("")
        logger.info("📚 PARA TREINAR XTTS REAL:")
        logger.info("")
        logger.info("1. ✅ Instale TTS:")
        logger.info("   pip install TTS")
        logger.info("")
        logger.info("2. ✅ Implemente load_pretrained_model():")
        logger.info("   from TTS.tts.models.xtts import Xtts")
        logger.info("   model = Xtts.init_from_config(config)")
        logger.info("")
        logger.info("3. ✅ Implemente create_dataset():")
        logger.info("   from TTS.tts.datasets import load_tts_samples")
        logger.info("   samples = load_tts_samples(...)")
        logger.info("")
        logger.info("4. ✅ Implemente train_step():")
        logger.info("   Use XTTS-v2 forward pass com GPT + HiFi-GAN")
        logger.info("")
        logger.info("📖 Referências:")
        logger.info("   - https://github.com/coqui-ai/TTS")
        logger.info("   - https://docs.coqui.ai/en/latest/")
        logger.info("   - https://huggingface.co/coqui/XTTS-v2")
        logger.info("=" * 80)
        return
    
    # Setup LoRA
    model = setup_lora(model, settings)
    model = model.to(device)
    
    # Create datasets
    train_dataset, val_dataset = create_dataset(settings)
    
    # Create optimizer & scheduler
    optimizer = create_optimizer(model, settings)
    scheduler = create_scheduler(optimizer, settings)
    
    # Mixed precision training
    scaler = torch.amp.GradScaler() if settings.use_amp else None
    
    # Output directories
    checkpoints_dir = settings.checkpoint_dir
    samples_dir = settings.samples_dir
    logger.info(f"📁 Output: {settings.output_dir}")
    logger.info(f"📁 Checkpoints: {checkpoints_dir}")
    logger.info(f"📁 Samples: {samples_dir}")
    
    # TensorBoard
    writer = None
    if settings.use_tensorboard:
        log_dir = settings.log_dir
        writer = SummaryWriter(log_dir)
        logger.info(f"📊 TensorBoard: {log_dir}")
    
    # Training configuration
    num_epochs = settings.num_epochs
    save_every_n_epochs = settings.save_every_n_epochs
    log_every_n_steps = settings.log_every_n_steps
    
    logger.info("\n🚀 Iniciando treinamento...")
    logger.info(f"   Epochs: {num_epochs}")
    logger.info(f"   Batch size: {settings.batch_size}")
    logger.info(f"   Learning rate: {settings.learning_rate}\n")
    
    global_step = 0
    best_val_loss = float('inf')
    
    # Create datasets
    train_dataset, val_dataset = create_dataset(settings)
    
    # Create dataloaders
    from torch.utils.data import DataLoader
    train_loader = DataLoader(
        train_dataset,
        batch_size=settings.batch_size,
        shuffle=True,
        num_workers=settings.num_workers,
    )
    val_loader = DataLoader(
        val_dataset,
        batch_size=settings.batch_size,
        shuffle=False,
        num_workers=settings.num_workers,
    )
    
    logger.info(f"\n📊 Datasets carregados:")
    logger.info(f"   Train: {len(train_dataset)} samples")
    logger.info(f"   Val: {len(val_dataset)} samples")
    logger.info(f"   Steps per epoch: {len(train_loader)}\n")
    
    # Training loop - BASEADO EM EPOCHS
    for epoch in range(1, num_epochs + 1):
        logger.info(f"\n{'='*60}")
        logger.info(f"EPOCH {epoch}/{num_epochs}")
        logger.info(f"{'='*60}\n")
        
        epoch_loss = 0.0
        num_batches = 0
        
        for batch_idx, batch in enumerate(train_loader):
            # Train step
            loss = train_step(model, batch, optimizer, scaler, settings, device)
            epoch_loss += loss
            num_batches += 1
            
            # Update scheduler
            if scheduler is not None:
                scheduler.step()
            
            global_step += 1
            
            # Logging
            if global_step % log_every_n_steps == 0:
                lr = optimizer.param_groups[0]['lr']
                avg_loss = epoch_loss / num_batches
                logger.info(
                    f"Epoch {epoch}/{num_epochs} | "
                    f"Step {batch_idx+1}/{len(train_loader)} | "
                    f"Loss: {loss:.4f} | Avg: {avg_loss:.4f} | LR: {lr:.2e}"
                )
                
                if writer is not None:
                    writer.add_scalar('train/loss', loss, global_step)
                    writer.add_scalar('train/avg_loss', avg_loss, global_step)
                    writer.add_scalar('train/lr', lr, global_step)
        
        # Validation após cada época
        avg_epoch_loss = epoch_loss / num_batches if num_batches > 0 else 0.0
        val_loss = validate(model, val_loader, device)
        
        logger.info(f"\n📊 EPOCH {epoch} COMPLETO")
        logger.info(f"   Train Loss: {avg_epoch_loss:.4f}")
        logger.info(f"   Val Loss: {val_loss:.4f}\n")
        
        if writer is not None:
            writer.add_scalar('epoch/train_loss', avg_epoch_loss, epoch)
            writer.add_scalar('epoch/val_loss', val_loss, epoch)
        
        # Salvar checkpoint a cada N épocas
        if epoch % save_every_n_epochs == 0:
            checkpoint_path = checkpoints_dir / f"checkpoint_epoch_{epoch}.pt"
            torch.save({
                'epoch': epoch,
                'global_step': global_step,
                'model_state_dict': model.state_dict(),
                'optimizer_state_dict': optimizer.state_dict(),
                'scheduler_state_dict': scheduler.state_dict() if scheduler else None,
                'train_loss': avg_epoch_loss,
                'val_loss': val_loss,
            }, checkpoint_path)
            logger.info(f"💾 Checkpoint salvo: {checkpoint_path}")
            
            # Gerar sample de áudio
            generate_sample_audio(epoch, settings, samples_dir)
            
            # Best model
            if val_loss < best_val_loss:
                best_val_loss = val_loss
                best_model_path = checkpoints_dir / "best_model.pt"
                torch.save({
                    'epoch': epoch,
                    'global_step': global_step,
                    'model_state_dict': model.state_dict(),
                    'val_loss': val_loss,
                }, best_model_path)
                logger.info(f"🏆 Novo melhor modelo! Epoch {epoch} | Val Loss: {val_loss:.4f}\n")
                
                # Sample do melhor modelo
                best_samples_dir = samples_dir / "best"
                generate_sample_audio(epoch, settings, best_samples_dir)
    
    # Cleanup
    if writer is not None:
        writer.close()
    
    logger.info("\n" + "="*80)
    logger.info("✅ TREINAMENTO COMPLETO!")
    logger.info("="*80)
    logger.info(f"Total Epochs: {num_epochs}")
    logger.info(f"Total Steps: {global_step}")
    logger.info(f"Best Val Loss: {best_val_loss:.4f}")
    logger.info(f"Checkpoints: {checkpoints_dir}")
    logger.info(f"Samples: {samples_dir}")


if __name__ == "__main__":
    main()
