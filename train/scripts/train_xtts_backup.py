"""
XTTS-v2 Fine-tuning Script com LoRA

Este script implementa fine-tuning do XTTS-v2 usando LoRA (Low-Rank Adaptation)
para adaptar o modelo pré-treinado para vozes específicas em português.

Uso:
    # Training completo
    python -m train.scripts.train_xtts
    
    # Com config customizado
    python -m train.scripts.train_xtts --config train/config/train_config.yaml
    
    # Resume do checkpoint
    python -m train.scripts.train_xtts --resume train/output/checkpoints/step_1000

Dependências:
    - coqui-tts: pip install TTS
    - peft: pip install peft (para LoRA)
    - tensorboard: pip install tensorboard
"""

import logging
import os
from pathlib import Path
import sys
from typing import Dict, List, Optional

import click
import torch
import torch.nn as nn
from torch.utils.data import DataLoader
from torch.utils.tensorboard import SummaryWriter
import yaml
from tqdm import tqdm

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

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


def load_config(config_path: Path) -> dict:
    """Carrega configuração de treinamento"""
    with open(config_path, encoding="utf-8") as f:
        return yaml.safe_load(f)


def setup_device(config: dict) -> torch.device:
    """Setup device (CUDA ou CPU)"""
    if config["hardware"]["device"] == "cuda" and torch.cuda.is_available():
        device_id = config["hardware"]["cuda_device_id"]
        device = torch.device(f"cuda:{device_id}")
        logger.info(f"✅ Using CUDA device: {torch.cuda.get_device_name(device_id)}")
        logger.info(f"   VRAM: {torch.cuda.get_device_properties(device_id).total_memory / 1e9:.2f} GB")
    else:
        device = torch.device("cpu")
        logger.info("⚠️  Using CPU (training will be slow)")
    
    return device


def load_pretrained_model(config: dict, device: torch.device):
    """
    Carrega modelo XTTS-v2 pré-treinado
    
    NOTA: Esta é uma implementação simplificada.
    O código real depende da API do Coqui TTS que pode mudar.
    """
    try:
        from TTS.tts.configs.xtts_config import XttsConfig
        from TTS.tts.models.xtts import Xtts
    except ImportError:
        logger.error("❌ TTS (Coqui) não encontrado. Instale com: pip install TTS")
        sys.exit(1)
        sys.exit(1)
    
    logger.info("📥 Carregando modelo XTTS-v2 pré-treinado...")
    
    # Carregar config do modelo
    model_name = config["model"]["name"]
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


def setup_lora(model: nn.Module, config: dict) -> nn.Module:
    """
    Configura LoRA (Low-Rank Adaptation) no modelo
    
    Usa biblioteca PEFT (Parameter-Efficient Fine-Tuning)
    """
    if not config["model"]["use_lora"]:
        logger.info("⏭️  LoRA desabilitado, usando fine-tuning completo")
        return model
    
    try:
        from peft import LoraConfig, get_peft_model
        
        logger.info("🔧 Configurando LoRA...")
        
        lora_cfg = config["model"]["lora"]
        
        peft_config = LoraConfig(
            r=lora_cfg["rank"],
            lora_alpha=lora_cfg["alpha"],
            lora_dropout=lora_cfg["dropout"],
            target_modules=lora_cfg["target_modules"],
            bias="none",
            task_type="CAUSAL_LM",  # Adaptar se necessário
        )
        
        model = get_peft_model(model, peft_config)
        
        # Log trainable parameters
        trainable_params = sum(p.numel() for p in model.parameters() if p.requires_grad)
        total_params = sum(p.numel() for p in model.parameters())
        
        logger.info(f"   LoRA rank: {lora_cfg['rank']}")
        logger.info(f"   Trainable params: {trainable_params:,} ({trainable_params/total_params*100:.2f}%)")
        logger.info(f"   Total params: {total_params:,}")
        
        return model
        
    except ImportError:
        logger.error("❌ PEFT não encontrado. Instale com: pip install peft")
        sys.exit(1)


def create_dataset(config: dict):
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
    
    dataset_dir = project_root / config["data"]["dataset_dir"]
    train_metadata = dataset_dir / config["data"]["train_metadata"]
    val_metadata = dataset_dir / config["data"]["val_metadata"]
    
    logger.info(f"   Dataset: {dataset_dir}")
    logger.info(f"   Train: {train_metadata}")
    logger.info(f"   Val: {val_metadata}")
    
    train_dataset = XTTSDataset(train_metadata, sample_rate=config["data"]["sample_rate"])
    val_dataset = XTTSDataset(val_metadata, sample_rate=config["data"]["sample_rate"])
    
    return train_dataset, val_dataset


def create_optimizer(model: nn.Module, config: dict):
    """Cria otimizador AdamW"""
    optimizer = torch.optim.AdamW(
        model.parameters(),
        lr=config["training"]["learning_rate"],
        betas=(config["training"]["adam_beta1"], config["training"]["adam_beta2"]),
        eps=config["training"]["adam_epsilon"],
        weight_decay=config["training"]["weight_decay"],
    )
    
    logger.info(f"🎯 Optimizer: AdamW (lr={config['training']['learning_rate']})")
    
    return optimizer


def create_scheduler(optimizer, config: dict):
    """Cria learning rate scheduler"""
    from torch.optim.lr_scheduler import LambdaLR
    import math
    
    scheduler_type = config["training"]["lr_scheduler"]
    
    if scheduler_type == "cosine_with_warmup":
        warmup_steps = 500
        total_steps = config["training"]["max_steps"]
        
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


def train_step(model, batch, optimizer, scaler, config: dict, device: torch.device):
    """
    Executa um step de treinamento
    
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
    if config["training"]["use_amp"] and scaler is not None:
        scaler.scale(loss).backward()
        scaler.unscale_(optimizer)
        torch.nn.utils.clip_grad_norm_(
            model.parameters(),
            config["training"]["max_grad_norm"],
        )
        scaler.step(optimizer)
        scaler.update()
    else:
        loss.backward()
        torch.nn.utils.clip_grad_norm_(
            model.parameters(),
            config["training"]["max_grad_norm"],
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


def save_checkpoint(model, optimizer, scheduler, step: int, config: dict, best: bool = False):
    """Salva checkpoint"""
    output_dir = project_root / config["checkpointing"]["output_dir"]
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
    "--config",
    type=click.Path(exists=True),
    default="train/config/train_config.yaml",
    help="Path para arquivo de configuração",
)
@click.option(
    "--resume",
    type=click.Path(exists=True),
    default=None,
    help="Path para checkpoint para resumir treinamento",
)
def main(config, resume):
    """
    Script principal de treinamento XTTS-v2
    """
    logger.info("=" * 80)
    logger.info("XTTS-v2 FINE-TUNING com LoRA")
    logger.info("=" * 80)
    
    # Carregar config
    config_path = project_root / config
    cfg = load_config(config_path)
    logger.info(f"📝 Config carregada: {config_path}\n")
    
    # Setup device
    device = setup_device(cfg)
    
    # Load model
    model = load_pretrained_model(cfg, device)
    if model is None:
        logger.error("❌ Modelo não carregado (implementação parcial)")
        logger.info("\n" + "=" * 80)
        logger.info("⚠️  ATENÇÃO: Script de treinamento é um TEMPLATE")
        logger.info("=" * 80)
        logger.info("Este script demonstra a estrutura completa de treinamento,")
        logger.info("mas requer implementação específica do XTTS-v2.")
        logger.info("\nPróximos passos:")
        logger.info("  1. Instalar TTS: pip install TTS")
        logger.info("  2. Implementar load_pretrained_model() com TTS API")
        logger.info("  3. Implementar create_dataset() com TTS.tts.datasets")
        logger.info("  4. Implementar train_step() com XTTS-v2 forward pass")
        logger.info("=" * 80)
        return
    
    # Setup LoRA
    model = setup_lora(model, cfg)
    model = model.to(device)
    
    # Create datasets
    train_dataset, val_dataset = create_dataset(cfg)
    
    # Create optimizer & scheduler
    optimizer = create_optimizer(model, cfg)
    scheduler = create_scheduler(optimizer, cfg)
    
    # Mixed precision training
    scaler = torch.amp.GradScaler() if cfg["training"]["use_amp"] else None
    
    # Checkpoints directory
    checkpoints_dir = project_root / cfg["output"]["checkpoint_dir"]
    checkpoints_dir.mkdir(parents=True, exist_ok=True)
    logger.info(f"📁 Checkpoints: {checkpoints_dir}")
    
    # TensorBoard
    writer = None
    if cfg["logging"]["use_tensorboard"]:
        log_dir = project_root / cfg["logging"]["log_dir"]
        writer = SummaryWriter(log_dir)
        logger.info(f"📊 TensorBoard: {log_dir}")
    
    # Training loop
    logger.info("\n🚀 Iniciando treinamento...")
    logger.info(f"   Max steps: {cfg['training']['max_steps']}")
    logger.info(f"   Batch size: {cfg['data']['batch_size']}")
    logger.info(f"   Learning rate: {cfg['training']['learning_rate']}\n")
    
    global_step = 0
    best_val_loss = float('inf')
    
    # Create datasets
    train_dataset, val_dataset = create_dataset(cfg)
    
    # Create dataloaders
    from torch.utils.data import DataLoader
    train_loader = DataLoader(
        train_dataset,
        batch_size=cfg["data"]["batch_size"],
        shuffle=True,
        num_workers=cfg["data"]["num_workers"],
    )
    val_loader = DataLoader(
        val_dataset,
        batch_size=cfg["data"]["batch_size"],
        shuffle=False,
        num_workers=cfg["data"]["num_workers"],
    )
    
    logger.info(f"\n📊 Datasets carregados:")
    logger.info(f"   Train: {len(train_dataset)} samples")
    logger.info(f"   Val: {len(val_dataset)} samples\n")
    
    # Training loop
    while global_step < cfg["training"]["max_steps"]:
        for batch in train_loader:
            if global_step >= cfg["training"]["max_steps"]:
                break
            
            # Train step
            loss = train_step(model, batch, optimizer, scaler, cfg, device)
            
            # Update scheduler
            if scheduler is not None:
                scheduler.step()
            
            global_step += 1
            
            # Logging
            if global_step % cfg["logging"]["log_every_n_steps"] == 0:
                lr = optimizer.param_groups[0]['lr']
                logger.info(
                    f"Step {global_step}/{cfg['training']['max_steps']} | "
                    f"Loss: {loss:.4f} | LR: {lr:.2e}"
                )
                
                if writer is not None:
                    writer.add_scalar('train/loss', loss, global_step)
                    writer.add_scalar('train/lr', lr, global_step)
            
            # Validation
            if global_step % cfg["logging"]["save_every_n_steps"] == 0:
                val_loss = validate(model, val_loader, device)
                logger.info(f"\n📊 Step {global_step} | Val Loss: {val_loss:.4f}\n")
                
                if writer is not None:
                    writer.add_scalar('val/loss', val_loss, global_step)
                
                # Save checkpoint
                checkpoint_path = checkpoints_dir / f"checkpoint_step_{global_step}.pt"
                torch.save({
                    'global_step': global_step,
                    'model_state_dict': model.state_dict(),
                    'optimizer_state_dict': optimizer.state_dict(),
                    'scheduler_state_dict': scheduler.state_dict() if scheduler else None,
                    'val_loss': val_loss,
                    'config': cfg,
                }, checkpoint_path)
                logger.info(f"💾 Checkpoint salvo: {checkpoint_path}")
                
                # Best model
                if val_loss < best_val_loss:
                    best_val_loss = val_loss
                    best_model_path = checkpoints_dir / "best_model.pt"
                    torch.save(model.state_dict(), best_model_path)
                    logger.info(f"🏆 Novo melhor modelo! Val Loss: {val_loss:.4f}\n")
    
    # Cleanup
    if writer is not None:
        writer.close()
    
    logger.info("\n" + "="*80)
    logger.info("✅ TREINAMENTO COMPLETO!")
    logger.info("="*80)
    logger.info(f"Best Val Loss: {best_val_loss:.4f}")
    logger.info(f"Total Steps: {global_step}")
    logger.info(f"Checkpoints: {checkpoints_dir}")


if __name__ == "__main__":
    main()
