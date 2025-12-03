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
        from f5_tts.train.finetune import train
        
        # Carregar config YAML base
        yaml_config_path = self.train_root / "config" / "train_config.yaml"
        with open(yaml_config_path, 'r') as f:
            yaml_config = yaml.safe_load(f)
        
        # Override com valores do .env
        yaml_config['training']['epochs'] = self.config['epochs']
        yaml_config['training']['batch_size'] = self.config['batch_size']
        yaml_config['training']['batch_size_type'] = self.config['batch_size_type']
        yaml_config['training']['grad_accumulation_steps'] = self.config['grad_accumulation_steps']
        yaml_config['training']['max_grad_norm'] = self.config['max_grad_norm']
        yaml_config['training']['learning_rate'] = self.config['learning_rate']
        yaml_config['training']['warmup_steps'] = self.config['warmup_steps']
        yaml_config['training']['save_per_updates'] = self.config['save_per_updates']
        yaml_config['training']['last_per_updates'] = self.config['last_per_updates']
        yaml_config['training']['keep_last_n_checkpoints'] = self.config['keep_last_n_checkpoints']
        yaml_config['training']['log_samples_per_updates'] = self.config['log_samples_per_updates']
        yaml_config['training']['early_stop_patience'] = self.config['early_stop_patience']
        yaml_config['training']['early_stop_min_delta'] = self.config['early_stop_min_delta']
        
        # Paths
        yaml_config['data']['train_dataset_name'] = self.config['train_dataset_name']
        yaml_config['training']['checkpoint_path'] = str(self.output_dir)
        yaml_config['training']['tensorboard_path'] = str(self.runs_dir)
        
        # Usar pré-treinado
        yaml_config['training']['finetune'] = True
        yaml_config['model']['pretrained_path'] = self.config['pretrained_model_path']
        
        # Salvar config temporário
        temp_config_path = self.train_root / "config" / "train_config_runtime.yaml"
        with open(temp_config_path, 'w') as f:
            yaml.dump(yaml_config, f, default_flow_style=False, allow_unicode=True)
        
        logger.info("🎯 Iniciando treinamento...")
        logger.info("")
        
        try:
            # Executar treinamento
            train(temp_config_path)
            
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
        
        finally:
            # Limpar config temporário
            if temp_config_path.exists():
                temp_config_path.unlink()
    
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
