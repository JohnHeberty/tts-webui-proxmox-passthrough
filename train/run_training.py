"""
Script principal de treinamento/fine-tuning do F5-TTS pt-br

Este script treina/finetune o modelo firstpixel/F5-TTS-pt-br usando o dataset preparado.
Baseado no código oficial do F5-TTS (https://github.com/SWivid/F5-TTS).

Uso:
    python -m train.run_training
    python -m train.run_training --config train/config/train_config.yaml
    python -m train.run_training --resume train/output/ptbr_finetuned/last.pt

Dependências:
    - torch: pip install torch
    - f5-tts: pip install f5-tts (ou git+https://github.com/SWivid/F5-TTS.git)
    - accelerate: pip install accelerate
    - tensorboard: pip install tensorboard (opcional)
    - wandb: pip install wandb (opcional)
"""
import argparse
import logging
import os
import sys
from pathlib import Path

import yaml
import torch

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

try:
    from f5_tts.model import CFM, DiT, UNetT, Trainer
    from f5_tts.model.dataset import load_dataset
    from f5_tts.model.utils import get_tokenizer
except ImportError:
    print("❌ F5-TTS não encontrado. Instale com:")
    print("   pip install f5-tts")
    print("   ou: pip install git+https://github.com/SWivid/F5-TTS.git")
    sys.exit(1)

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('train/logs/training.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


def load_config(config_path: Path) -> dict:
    """Carrega configuração do treinamento"""
    with open(config_path, 'r', encoding='utf-8') as f:
        return yaml.safe_load(f)


def setup_model(config: dict):
    """
    Inicializa o modelo F5-TTS
    
    Args:
        config: Configuração completa
    
    Returns:
        Modelo CFM
    """
    model_config = config['model']
    mel_config = config['mel_spec']
    
    # Determinar tipo de modelo
    model_cls = DiT if model_config['model_type'] == 'DiT' else UNetT
    
    # Tokenizer
    vocab_file = model_config.get('vocab_file')
    if vocab_file and Path(vocab_file).exists():
        tokenizer = "custom"
        logger.info(f"📝 Usando tokenizer customizado: {vocab_file}")
    else:
        tokenizer = "pinyin"  # Padrão do pt-br
        logger.info(f"📝 Usando tokenizer: {tokenizer}")
    
    vocab_char_map, vocab_size = get_tokenizer(vocab_file if vocab_file and Path(vocab_file).exists() else None, tokenizer)
    
    # Criar modelo
    logger.info(f"🏗️  Inicializando modelo {model_config['model_type']}...")
    
    model = CFM(
        transformer=model_cls(
            dim=model_config['dim'],
            depth=model_config['depth'],
            heads=model_config['heads'],
            ff_mult=model_config['ff_mult'],
            text_dim=model_config['text_dim'],
            conv_layers=model_config['conv_layers'],
            vocab_char_map=vocab_char_map,
        ),
        mel_spec_kwargs=dict(
            target_sample_rate=mel_config['target_sample_rate'],
            n_mel_channels=mel_config['n_mel_channels'],
            hop_length=mel_config['hop_length'],
            win_length=mel_config['win_length'],
            n_fft=mel_config['n_fft'],
            mel_spec_type=mel_config['mel_spec_type'],
        ),
        vocab_char_map=vocab_char_map,
    )
    
    logger.info(f"✅ Modelo criado: {sum(p.numel() for p in model.parameters()) / 1e6:.1f}M parâmetros")
    
    return model


def setup_trainer(model, config: dict):
    """
    Configura o Trainer do F5-TTS
    
    Args:
        model: Modelo CFM
        config: Configuração completa
    
    Returns:
        Trainer
    """
    train_config = config['training']
    ckpt_config = config['checkpoints']
    opt_config = config['optimizer']
    log_config = config['logging']
    hw_config = config['hardware']
    ema_config = train_config['ema']
    
    # Determinar device
    if hw_config['device'] == 'auto':
        device = 'cuda' if torch.cuda.is_available() else 'cpu'
    else:
        device = hw_config['device']
    
    logger.info(f"💻 Device: {device}")
    
    # Criar Trainer
    logger.info("🏋️  Configurando Trainer...")
    
    trainer = Trainer(
        model=model,
        epochs=train_config['epochs'],
        learning_rate=train_config['learning_rate'],
        num_warmup_updates=train_config['num_warmup_updates'],
        save_per_updates=ckpt_config['save_per_updates'],
        checkpoint_path=ckpt_config['output_dir'],
        batch_size_per_gpu=train_config['batch_size_per_gpu'],
        batch_size_type=train_config['batch_size_type'],
        max_samples=train_config['max_samples'],
        grad_accumulation_steps=train_config['grad_accumulation_steps'],
        max_grad_norm=train_config['max_grad_norm'],
        logger=log_config['logger'],
        wandb_project=log_config.get('wandb', {}).get('project'),
        wandb_run_name=log_config.get('wandb', {}).get('run_name'),
        last_per_updates=ckpt_config.get('last_per_updates', 100),
        log_samples=ckpt_config.get('log_samples', False),
        keep_last_n_checkpoints=ckpt_config.get('keep_last_n_checkpoints', 5),
        bnb_optimizer=opt_config.get('use_8bit_adam', False),
        mel_spec_type=config['mel_spec']['mel_spec_type'],
        # EMA config
        ema_kwargs=dict(
            beta=ema_config['ema_decay'],
            update_every=ema_config['update_every'],
            update_after_step=ema_config['update_after_step'],
        ) if ema_config['use_ema'] else dict(),
    )
    
    logger.info("✅ Trainer configurado")
    
    return trainer


def main():
    """Main function"""
    parser = argparse.ArgumentParser(description="F5-TTS Fine-tuning")
    parser.add_argument(
        '--config',
        type=str,
        default='train/config/train_config.yaml',
        help='Path to config file'
    )
    parser.add_argument(
        '--resume',
        type=str,
        default=None,
        help='Path to checkpoint to resume from'
    )
    parser.add_argument(
        '--dataset-path',
        type=str,
        default=None,
        help='Override dataset path'
    )
    
    args = parser.parse_args()
    
    logger.info("=" * 80)
    logger.info("F5-TTS FINE-TUNING - PORTUGUÊS BRASILEIRO")
    logger.info("=" * 80)
    logger.info(f"Modelo base: firstpixel/F5-TTS-pt-br")
    logger.info(f"Config: {args.config}")
    
    # Load config
    config_path = project_root / args.config
    if not config_path.exists():
        logger.error(f"❌ Config não encontrado: {config_path}")
        sys.exit(1)
    
    config = load_config(config_path)
    
    # Override dataset path if provided
    if args.dataset_path:
        config['training']['dataset_path'] = args.dataset_path
    
    # Override resume checkpoint if provided
    if args.resume:
        config['checkpoints']['resume_from_checkpoint'] = args.resume
    
    # Verificar dataset
    dataset_path = Path(config['training']['dataset_path'])
    raw_arrow = dataset_path / "raw.arrow"
    
    if not raw_arrow.exists():
        logger.error(f"❌ Dataset não encontrado: {raw_arrow}")
        logger.error("   Execute primeiro:")
        logger.error("   1. python -m train.scripts.download_youtube")
        logger.error("   2. python -m train.scripts.prepare_segments")
        logger.error("   3. python -m train.scripts.transcribe_or_subtitles")
        logger.error("   4. python -m train.scripts.build_metadata_csv")
        logger.error("   5. python -m train.scripts.prepare_f5_dataset")
        sys.exit(1)
    
    logger.info(f"📁 Dataset: {dataset_path}")
    
    # Criar diretórios de output
    output_dir = Path(config['checkpoints']['output_dir'])
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Criar diretórios de logs
    if config['logging']['logger'] == 'tensorboard':
        tb_dir = Path(config['logging']['tensorboard_dir'])
        tb_dir.mkdir(parents=True, exist_ok=True)
        logger.info(f"📊 TensorBoard logs: {tb_dir}")
    
    # Setup model
    logger.info("\n" + "=" * 80)
    logger.info("INICIALIZAÇÃO DO MODELO")
    logger.info("=" * 80)
    
    model = setup_model(config)
    
    # Carregar checkpoint base (se especificado)
    checkpoint_path = config['model'].get('checkpoint_path')
    if checkpoint_path and Path(checkpoint_path).exists():
        logger.info(f"📥 Carregando checkpoint base: {checkpoint_path}")
        try:
            # Load checkpoint
            from safetensors.torch import load_file
            ckpt = load_file(checkpoint_path, device='cpu')
            
            # Carregar state dict (pode ser que precise de unwrap)
            if 'ema_model_state_dict' in ckpt:
                model.load_state_dict(ckpt['ema_model_state_dict'])
                logger.info("✅ Checkpoint EMA carregado")
            elif 'model_state_dict' in ckpt:
                model.load_state_dict(ckpt['model_state_dict'])
                logger.info("✅ Checkpoint carregado")
            else:
                model.load_state_dict(ckpt)
                logger.info("✅ Checkpoint carregado")
        except Exception as e:
            logger.warning(f"⚠️  Erro ao carregar checkpoint: {e}")
            logger.warning("   Iniciando treino do zero...")
    
    # Setup trainer
    logger.info("\n" + "=" * 80)
    logger.info("CONFIGURAÇÃO DO TREINAMENTO")
    logger.info("=" * 80)
    
    trainer = setup_trainer(model, config)
    
    # Carregar dataset
    logger.info("\n" + "=" * 80)
    logger.info("CARREGAMENTO DO DATASET")
    logger.info("=" * 80)
    
    dataset_name = config['training']['dataset_name']
    
    logger.info(f"📚 Carregando dataset: {dataset_name}")
    
    try:
        train_dataset = load_dataset(
            dataset_name=str(dataset_path),
            tokenizer="custom" if config['model'].get('vocab_file') else "pinyin",
            dataset_type="CustomDataset",
            mel_spec_kwargs=config['mel_spec']
        )
        logger.info(f"✅ Dataset carregado: {len(train_dataset)} amostras")
    except Exception as e:
        logger.error(f"❌ Erro ao carregar dataset: {e}")
        sys.exit(1)
    
    # Iniciar treinamento
    logger.info("\n" + "=" * 80)
    logger.info("INICIANDO TREINAMENTO")
    logger.info("=" * 80)
    logger.info(f"Epochs: {config['training']['epochs']}")
    logger.info(f"Batch size: {config['training']['batch_size_per_gpu']}")
    logger.info(f"Grad accumulation: {config['training']['grad_accumulation_steps']}")
    logger.info(f"Learning rate: {config['training']['learning_rate']}")
    logger.info(f"Output dir: {output_dir}")
    logger.info("=" * 80 + "\n")
    
    try:
        trainer.train(
            train_dataset=train_dataset,
            num_workers=config['hardware'].get('num_workers', 4),
            resumable_with_seed=config.get('advanced', {}).get('resumable_with_seed', 666)
        )
    except KeyboardInterrupt:
        logger.info("\n⚠️  Treinamento interrompido pelo usuário")
        logger.info("   Salvando checkpoint...")
        # Trainer já salva automaticamente via last_per_updates
    except Exception as e:
        logger.error(f"\n❌ Erro durante treinamento: {e}")
        raise
    
    logger.info("\n" + "=" * 80)
    logger.info("✅ TREINAMENTO CONCLUÍDO!")
    logger.info("=" * 80)
    logger.info(f"Checkpoints salvos em: {output_dir}")
    logger.info("\nPara usar o modelo treinado:")
    logger.info("  1. Encontre o checkpoint em train/output/ptbr_finetuned/")
    logger.info("  2. Teste com o script de inferência (a criar)")
    logger.info("  3. Integre na API (próxima tarefa)")
    logger.info("=" * 80)


if __name__ == "__main__":
    main()
