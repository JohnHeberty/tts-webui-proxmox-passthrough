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
import glob

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


def find_latest_checkpoint(output_dir: Path) -> Path:
    """
    Encontra o último checkpoint salvo no diretório de output
    
    Args:
        output_dir: Diretório de checkpoints
    
    Returns:
        Path do último checkpoint ou None
    """
    if not output_dir.exists():
        return None
    
    # Procurar por model_last.pt primeiro
    last_ckpt = output_dir / "model_last.pt"
    if last_ckpt.exists():
        return last_ckpt
    
    # Procurar por model_XXXX.pt
    checkpoints = list(output_dir.glob("model_*.pt"))
    if not checkpoints:
        return None
    
    # Ordenar por número (model_500.pt, model_1000.pt, etc)
    def get_step(path):
        try:
            return int(path.stem.split('_')[1])
        except:
            return 0
    
    checkpoints.sort(key=get_step, reverse=True)
    return checkpoints[0]


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
    
    # Tokenizer - usar vocab.txt do dataset
    dataset_path = Path(config['training']['dataset_path'])
    vocab_file_dataset = dataset_path / "vocab.txt"
    vocab_file_config = model_config.get('vocab_file')
    
    # Prioridade: 1. vocab do dataset, 2. vocab do config, 3. padrão pt-br
    if vocab_file_dataset.exists():
        vocab_file = str(vocab_file_dataset)
        tokenizer = "custom"
        logger.info(f"📝 Usando vocab do dataset: {vocab_file}")
    elif vocab_file_config and Path(vocab_file_config).exists():
        vocab_file = vocab_file_config
        tokenizer = "custom"
        logger.info(f"📝 Usando vocab do config: {vocab_file}")
    else:
        # Usar vocab padrão do modelo pt-br
        vocab_file = None
        tokenizer = "custom"  # pt-br usa custom, não pinyin
        logger.warning("⚠️  Nenhum vocab.txt encontrado, usando caracteres do dataset")
    
    vocab_char_map, vocab_size = get_tokenizer(vocab_file, tokenizer)
    
    logger.info(f"📊 Vocab size: {vocab_size} caracteres")
    
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
            text_num_embeds=vocab_size,  # Tamanho do vocabulário
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
        '--fresh-start',
        action='store_true',
        help='Ignore existing checkpoints and start fresh training'
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
    
    # Detectar automaticamente se há checkpoint anterior
    output_dir = Path(config['checkpoints']['output_dir'])
    existing_checkpoint = find_latest_checkpoint(output_dir)
    
    # Override resume checkpoint if provided
    if args.resume:
        config['checkpoints']['resume_from_checkpoint'] = args.resume
        logger.info(f"🔄 Checkpoint manual especificado: {args.resume}")
    elif existing_checkpoint and not args.fresh_start:
        # Auto-retomar do último checkpoint
        config['checkpoints']['resume_from_checkpoint'] = str(existing_checkpoint)
        logger.info(f"🔄 Checkpoint detectado - continuando treinamento: {existing_checkpoint}")
        logger.info(f"   (use --fresh-start para treinar do zero)")
    else:
        if args.fresh_start:
            logger.info("🆕 Iniciando treinamento do zero (--fresh-start)")
        else:
            logger.info("🆕 Nenhum checkpoint encontrado - iniciando do zero")
    
    # Verificar dataset - usar caminho absoluto
    dataset_path = Path(config['training']['dataset_path'])
    if not dataset_path.is_absolute():
        dataset_path = (project_root / dataset_path).resolve()
    
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
        if not tb_dir.is_absolute():
            tb_dir = (project_root / tb_dir).resolve()
        tb_dir.mkdir(parents=True, exist_ok=True)
        logger.info(f"📊 TensorBoard logs: {tb_dir}")
        logger.info(f"   Para visualizar: tensorboard --logdir={tb_dir}")
        logger.info(f"   Acesse: http://localhost:6006")
    
    # Setup model
    logger.info("\n" + "=" * 80)
    logger.info("INICIALIZAÇÃO DO MODELO")
    logger.info("=" * 80)
    
    model = setup_model(config)
    
    # Carregar checkpoint base (FINE-TUNING do modelo pré-treinado)
    checkpoint_path = config['model'].get('checkpoint_path')
    if checkpoint_path:
        checkpoint_path = Path(checkpoint_path)
        if not checkpoint_path.is_absolute():
            checkpoint_path = (project_root / checkpoint_path).resolve()
        
        if checkpoint_path.exists():
            logger.info(f"📥 Carregando modelo pré-treinado: {checkpoint_path}")
            try:
                # Tentar carregar safetensors primeiro (mais rápido)
                if checkpoint_path.suffix == '.safetensors':
                    from safetensors.torch import load_file
                    ckpt = load_file(str(checkpoint_path), device='cpu')
                else:
                    # Carregar .pt/.pth
                    ckpt = torch.load(str(checkpoint_path), map_location='cpu')
                
                # Carregar state dict (pode ter wrapping diferente)
                # IMPORTANTE: strict=False porque vocab size é diferente (pt-br vs original)
                if 'ema_model_state_dict' in ckpt:
                    incompatible = model.load_state_dict(ckpt['ema_model_state_dict'], strict=False)
                    logger.info("✅ Checkpoint EMA carregado (fine-tuning)")
                elif 'model_state_dict' in ckpt:
                    incompatible = model.load_state_dict(ckpt['model_state_dict'], strict=False)
                    logger.info("✅ Checkpoint carregado (fine-tuning)")
                else:
                    incompatible = model.load_state_dict(ckpt, strict=False)
                    logger.info("✅ Checkpoint carregado (fine-tuning)")
                
                # Mostrar layers não carregados (esperado devido a vocab size diferente)
                if incompatible.missing_keys:
                    logger.info(f"   ⚠️  {len(incompatible.missing_keys)} layers não carregados (serão treinados do zero)")
                    logger.debug(f"      Missing: {incompatible.missing_keys[:3]}...")
                if incompatible.unexpected_keys:
                    logger.info(f"   ℹ️  {len(incompatible.unexpected_keys)} layers ignorados (não compatíveis)")
                
                logger.info("🎯 Modo: FINE-TUNING (partindo de modelo pré-treinado pt-br)")
            except RuntimeError as e:
                # Erro de compatibilidade - tentar carregar parcialmente
                if "size mismatch" in str(e):
                    logger.warning(f"⚠️  Incompatibilidade de tamanho detectada (vocab diferente)")
                    logger.warning("   Carregando apenas layers compatíveis...")
                    
                    # Carregar apenas layers compatíveis
                    model_dict = model.state_dict()
                    if 'ema_model_state_dict' in ckpt:
                        pretrained_dict = ckpt['ema_model_state_dict']
                    elif 'model_state_dict' in ckpt:
                        pretrained_dict = ckpt['model_state_dict']
                    else:
                        pretrained_dict = ckpt
                    
                    # Filtrar layers incompatíveis
                    pretrained_dict = {k: v for k, v in pretrained_dict.items() 
                                      if k in model_dict and v.shape == model_dict[k].shape}
                    
                    logger.info(f"   ✅ {len(pretrained_dict)}/{len(model_dict)} layers carregados")
                    logger.info(f"   ⚠️  {len(model_dict) - len(pretrained_dict)} layers serão treinados do zero")
                    
                    model_dict.update(pretrained_dict)
                    model.load_state_dict(model_dict)
                    
                    logger.info("🎯 Modo: FINE-TUNING PARCIAL (vocab pt-br customizado)")
                else:
                    raise
            except Exception as e:
                logger.error(f"❌ Erro ao carregar checkpoint: {e}")
                logger.error("   Não é possível continuar sem modelo pré-treinado!")
                import traceback
                traceback.print_exc()
                sys.exit(1)
        else:
            logger.error(f"❌ Checkpoint não encontrado: {checkpoint_path}")
            logger.error("   Execute primeiro: python -m train.scripts.download_pretrained_model")
            sys.exit(1)
    else:
        logger.warning("⚠️  Nenhum checkpoint especificado, iniciando do zero...")
    
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
    logger.info(f"📁 Caminho: {dataset_path}")
    
    try:
        # IMPORTANTE: F5-TTS procura dataset em data/{dataset_name}_{tokenizer}/
        # SEMPRE usar train/data/ (dentro da pasta train)
        train_root = Path(__file__).parent  # train/
        f5_tts_data_dir = train_root / "data"
        f5_tts_data_dir.mkdir(parents=True, exist_ok=True)
        
        expected_dataset_dir = f5_tts_data_dir / f"{dataset_name}_custom"
        
        if not expected_dataset_dir.exists():
            logger.info(f"🔗 Criando symlink: {expected_dataset_dir} -> {dataset_path}")
            expected_dataset_dir.symlink_to(dataset_path.absolute(), target_is_directory=True)
        
        # Criar symlink no local onde F5-TTS procura (/root/.local/lib/pythonX.X/data/)
        python_lib = Path.home() / ".local" / "lib"
        for python_dir in python_lib.glob("python*"):
            lib_data_link = python_dir / "data"
            if lib_data_link.is_symlink():
                lib_data_link.unlink()
            elif lib_data_link.exists() and lib_data_link.is_dir():
                # Backup se for diretório real
                import shutil
                backup = python_dir / f"data_backup_{int(__import__('time').time())}"
                shutil.move(str(lib_data_link), str(backup))
            
            # Criar link apontando para train/data
            if not lib_data_link.exists():
                lib_data_link.symlink_to(f5_tts_data_dir.absolute(), target_is_directory=True)
                logger.info(f"🔗 Symlink F5-TTS: {lib_data_link} -> {f5_tts_data_dir}")
        
        # Carregar dataset usando o loader padrão do F5-TTS
        train_dataset = load_dataset(
            dataset_name=dataset_name,
            tokenizer="custom",
            dataset_type="CustomDataset",
            audio_type="raw",
            mel_spec_kwargs=config['mel_spec']
        )
        logger.info(f"✅ Dataset carregado: {len(train_dataset)} amostras")
    except Exception as e:
        logger.error(f"❌ Erro ao carregar dataset: {e}")
        logger.error(f"   Dataset path: {dataset_path}")
        logger.error(f"   Expected path: {expected_dataset_dir}")
        logger.error(f"   Arquivos no dataset:")
        for f in dataset_path.glob("*"):
            logger.error(f"     - {f.name}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
    
    # Iniciar treinamento
    logger.info("\n" + "=" * 80)
    logger.info("INICIANDO TREINAMENTO")
    logger.info("=" * 80)
    logger.info(f"Epochs: {config['training']['epochs']}")
    logger.info(f"Batch size: {config['training']['batch_size_per_gpu']}")
    logger.info(f"Grad accumulation: {config['training']['grad_accumulation_steps']}")
    logger.info(f"Learning rate: {config['training']['learning_rate']}")
    
    # Early Stopping info
    early_stop_patience = config['training'].get('early_stop_patience', 0)
    if early_stop_patience > 0:
        logger.info(f"🛑 Early Stopping: habilitado ({early_stop_patience} epochs sem melhora)")
        logger.info(f"   Min delta: {config['training'].get('early_stop_min_delta', 0.001)}")
        logger.info(f"   ⚠️  NOTA: F5-TTS não suporta early stopping nativamente")
        logger.info(f"   Monitore o loss e pare manualmente (Ctrl+C) se necessário")
    
    logger.info(f"Output dir: {output_dir}")
    
    # TensorBoard info
    if config['logging']['logger'] == 'tensorboard':
        logger.info(f"\n📊 TensorBoard:")
        logger.info(f"   Logs: ./runs/")
        logger.info(f"   Para visualizar:")
        logger.info(f"     export PATH=\"$HOME/.local/bin:$PATH\"")
        logger.info(f"     tensorboard --logdir=runs")
        logger.info(f"     Abra: http://localhost:6006")
    
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
