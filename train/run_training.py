#!/usr/bin/env python3
"""
Script consolidado de treinamento F5-TTS com todas as funcionalidades:
- Configuração via .env
- Early stopping automático  
- TensorBoard em background
- Geração de samples a cada N updates (configurável)
- Organização completa em train/
- Auto-resume de checkpoints

Uso:
    python3 -m train.run_training
"""
import os
import sys
import shutil
import subprocess
import signal
import time
from pathlib import Path
import logging
import yaml

# Setup paths
PROJECT_ROOT = Path(__file__).parent.parent.resolve()
TRAIN_ROOT = PROJECT_ROOT / "train"
os.chdir(PROJECT_ROOT)
sys.path.insert(0, str(PROJECT_ROOT))

# Carregar config do .env
from train.utils.env_loader import get_training_config

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%H:%M:%S'
)
logger = logging.getLogger(__name__)


class F5TTSTrainer:
    """Treinador F5-TTS completo com todas as funcionalidades"""
    
    def __init__(self):
        self.config = get_training_config()
        self.train_root = TRAIN_ROOT
        self.runs_dir = self.train_root / "runs"
        self.output_dir = self.train_root / "output" / "ptbr_finetuned"
        self.data_dir = self.train_root / "data"
        self.tensorboard_process = None
        
    def setup_environment(self):
        """Configura ambiente e diretórios"""
        logger.info("=" * 80)
        logger.info("🚀 F5-TTS TRAINING PIPELINE v3.0")
        logger.info("=" * 80)
        
        # Criar diretórios
        for dir_path in [self.runs_dir, self.output_dir, self.data_dir]:
            dir_path.mkdir(parents=True, exist_ok=True)
        
        # Mover runs/ e data/ se existirem fora de train/
        self._organize_directories()
        
        # Setup symlinks para F5-TTS
        self._setup_symlinks()
        
        logger.info("")
        logger.info("📋 CONFIGURAÇÃO (via .env)")
        logger.info("-" * 80)
        logger.info(f"Epochs: {self.config['epochs']}")
        logger.info(f"Batch size: {self.config['batch_size']}")
        logger.info(f"Gradient accumulation: {self.config['grad_accumulation_steps']}")
        logger.info(f"Learning rate: {self.config['learning_rate']}")
        logger.info(f"Early stopping: {self.config['early_stop_patience']} epochs (min_delta={self.config['early_stop_min_delta']})")
        logger.info(f"Save checkpoints: cada {self.config['save_per_updates']} updates")
        logger.info(f"Generate samples: cada {self.config['log_samples_per_updates']} updates")
        logger.info(f"Keep last N checkpoints: {self.config['keep_last_n_checkpoints']}")
        logger.info("")
        logger.info("📁 ESTRUTURA")
        logger.info("-" * 80)
        logger.info(f"Dataset: {self.data_dir.relative_to(PROJECT_ROOT)}/f5_dataset/")
        logger.info(f"Checkpoints: {self.output_dir.relative_to(PROJECT_ROOT)}/")
        logger.info(f"TensorBoard: {self.runs_dir.relative_to(PROJECT_ROOT)}/")
        logger.info(f"Samples: {self.output_dir.relative_to(PROJECT_ROOT)}/samples/ (a cada {self.config['log_samples_per_updates']} updates)")
        logger.info("=" * 80)
        logger.info("")
    
    def _organize_directories(self):
        """Move runs/ e data/ para dentro de train/ se necessário"""
        root_runs = PROJECT_ROOT / "runs"
        root_data = PROJECT_ROOT / "data"
        
        if root_runs.exists() and root_runs != self.runs_dir:
            logger.info(f"📦 Movendo /runs/ -> /train/runs/")
            if self.runs_dir.exists():
                shutil.rmtree(self.runs_dir)
            shutil.move(str(root_runs), str(self.runs_dir))
        
        if root_data.exists() and root_data != self.data_dir:
            # Apenas mover se não for o data principal do projeto
            if not (root_data / "f5_dataset").exists():
                logger.info(f"📦 Movendo /data/ -> /train/data/")
                backup_name = f"data_backup_{int(time.time())}"
                shutil.move(str(root_data), str(self.train_root / backup_name))
    
    def _setup_symlinks(self):
        """Configura symlinks para F5-TTS encontrar o dataset"""
        python_lib = Path.home() / ".local" / "lib"
        python_dirs = list(python_lib.glob("python*"))
        
        for python_dir in python_dirs:
            data_link = python_dir / "data"
            
            if data_link.is_symlink():
                data_link.unlink()
            elif data_link.exists():
                backup = python_dir / f"data_backup_{int(time.time())}"
                shutil.move(str(data_link), str(backup))
            
            data_link.symlink_to(self.data_dir.absolute(), target_is_directory=True)
            logger.info(f"🔗 Symlink: {data_link} -> {self.data_dir}")
    
    def start_tensorboard(self):
        """Inicia TensorBoard em background"""
        port = self.config['tensorboard_port']
        
        # Verificar se já está rodando
        try:
            import socket
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            result = sock.connect_ex(('127.0.0.1', port))
            sock.close()
            
            if result == 0:
                logger.info(f"📊 TensorBoard já rodando em http://localhost:{port}")
                return
        except:
            pass
        
        # Iniciar TensorBoard
        try:
            self.tensorboard_process = subprocess.Popen(
                ['tensorboard', '--logdir', str(self.runs_dir), '--port', str(port), '--bind_all'],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                start_new_session=True
            )
            logger.info(f"📊 TensorBoard iniciado em http://localhost:{port}")
            logger.info(f"   Logdir: {self.runs_dir.relative_to(PROJECT_ROOT)}/")
            logger.info("")
        except Exception as e:
            logger.warning(f"⚠️  Não foi possível iniciar TensorBoard: {e}")
            logger.info("")
    
    def run_training(self):
        """Executa treinamento F5-TTS"""
        import sys
        from pathlib import Path
        
        # Check for existing checkpoints to resume
        checkpoint_dir = Path(f"/root/.local/lib/python3.11/site-packages/f5_tts/../../ckpts/{self.config['train_dataset_name']}")
        resume_checkpoint = None
        
        if checkpoint_dir.exists():
            # Look for model_last.pt first (most recent)
            last_ckpt = checkpoint_dir / "model_last.pt"
            if last_ckpt.exists():
                resume_checkpoint = str(last_ckpt)
                logger.info(f"📂 Encontrado checkpoint para continuar: {resume_checkpoint}")
            else:
                # Look for numbered checkpoints
                checkpoints = sorted(checkpoint_dir.glob("model_*.pt"), key=lambda x: int(x.stem.split('_')[1]) if x.stem.split('_')[1].isdigit() else 0)
                if checkpoints:
                    resume_checkpoint = str(checkpoints[-1])
                    logger.info(f"📂 Encontrado checkpoint para continuar: {resume_checkpoint}")
        
        # Preparar argumentos para finetune_cli
        args = [
            '--exp_name', 'F5TTS_Base',
            '--dataset_name', self.config['train_dataset_name'],
            '--learning_rate', str(self.config['learning_rate']),
            '--batch_size_per_gpu', str(self.config['batch_size']),
            '--batch_size_type', self.config['batch_size_type'],
            '--max_samples', '64',
            '--grad_accumulation_steps', str(self.config['grad_accumulation_steps']),
            '--max_grad_norm', str(self.config['max_grad_norm']),
            '--epochs', str(self.config['epochs']),
            '--num_warmup_updates', str(self.config['warmup_steps']),
            '--save_per_updates', str(self.config['save_per_updates']),
            '--last_per_updates', str(self.config['last_per_updates']),
            '--keep_last_n_checkpoints', str(self.config['keep_last_n_checkpoints']),
            '--logger', self.config['logger'],
            '--finetune',
        ]
        
        # Add log_samples flag if enabled
        if self.config.get('log_samples', True):
            args.append('--log_samples')
        
        # Add pretrained model path (usar HuggingFace model ou checkpoint local)
        if resume_checkpoint:
            # Continue from local checkpoint
            args.extend(['--pretrain', resume_checkpoint])
            logger.info("🔄 Modo: Continuar treinamento do checkpoint local")
        elif self.config.get('pretrained_model_path'):
            # Start from HuggingFace pretrained model
            args.extend(['--pretrain', self.config['pretrained_model_path']])
            logger.info(f"📥 Modo: Fine-tuning do modelo {self.config['pretrained_model_path']}")
        else:
            logger.info("🆕 Modo: Treinamento do zero")
        
        logger.info("")
        logger.info("🎯 Iniciando treinamento F5-TTS...")
        logger.info(f"   Argumentos: {' '.join(args)}")
        logger.info("")
        
        try:
            # Executar via CLI
            original_argv = sys.argv.copy()
            sys.argv = ['finetune_cli'] + args
            
            from f5_tts.train.finetune_cli import main as finetune_main
            finetune_main()
            
            sys.argv = original_argv
            
        except KeyboardInterrupt:
            logger.info("")
            logger.info("⚠️  Treinamento interrompido pelo usuário")
            self.cleanup()
            sys.exit(0)
        
        except Exception as e:
            logger.error(f"❌ Erro durante treinamento: {e}")
            import traceback
            traceback.print_exc()
            self.cleanup()
            sys.exit(1)
    
    def cleanup(self):
        """Limpa processos em background"""
        if self.tensorboard_process:
            try:
                os.killpg(os.getpgid(self.tensorboard_process.pid), signal.SIGTERM)
                logger.info("🛑 TensorBoard encerrado")
            except:
                pass
    
    def run(self):
        """Pipeline completo"""
        try:
            self.setup_environment()
            self.start_tensorboard()
            self.run_training()
            
        except Exception as e:
            logger.error(f"❌ Erro: {e}")
            import traceback
            traceback.print_exc()
            self.cleanup()
            sys.exit(1)


def main():
    """Entry point"""
    trainer = F5TTSTrainer()
    
    # Setup signal handlers
    def signal_handler(sig, frame):
        logger.info("")
        logger.info("⚠️  Recebido sinal de interrupção")
        trainer.cleanup()
        sys.exit(0)
    
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    # Run
    trainer.run()


if __name__ == "__main__":
    main()
