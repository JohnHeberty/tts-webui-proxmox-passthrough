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
        self.pretrained_dir = self.train_root / "pretrained"
        self.tensorboard_process = None
        
    def download_pretrained_model(self):
        """Baixa modelo pré-treinado do HuggingFace se necessário"""
        if not self.config.get('pretrained_model_path'):
            return None
            
        pretrained_path = Path(self.config['pretrained_model_path'])
        
        # Se caminho relativo, converter para absoluto
        if not pretrained_path.is_absolute():
            pretrained_path = PROJECT_ROOT / pretrained_path
        
        # Se o arquivo já existe, retorna o caminho
        if pretrained_path.exists():
            logger.info(f"✅ Modelo pré-treinado encontrado: {pretrained_path}")
            return str(pretrained_path.absolute())
        
        # Verificar se deve baixar automaticamente
        if not self.config.get('auto_download_pretrained', False):
            logger.warning(f"⚠️  Modelo não encontrado: {pretrained_path}")
            logger.warning("   Configure AUTO_DOWNLOAD_PRETRAINED=true no .env para baixar automaticamente")
            return None
        
        # Baixar modelo do HuggingFace
        base_model = self.config.get('base_model', 'firstpixel/F5-TTS-pt-br')
        logger.info(f"📥 Baixando modelo pré-treinado: {base_model}")
        
        try:
            from huggingface_hub import hf_hub_download
            
            # Criar diretório
            self.pretrained_dir.mkdir(parents=True, exist_ok=True)
            model_dir = self.pretrained_dir / base_model.split('/')[-1]
            model_dir.mkdir(parents=True, exist_ok=True)
            
            # Baixar arquivo pt-br/model_200000.pt (formato .pt com EMA completo)
            logger.info("   Baixando pt-br/model_200000.pt...")
            downloaded_file = hf_hub_download(
                repo_id=base_model,
                filename="pt-br/model_200000.pt",
                local_dir=str(model_dir),
                local_dir_use_symlinks=False
            )
            
            logger.info(f"✅ Modelo baixado: {downloaded_file}")
            return downloaded_file
            
        except Exception as e:
            logger.error(f"❌ Erro ao baixar modelo: {e}")
            logger.info("   Você pode baixar manualmente de:")
            logger.info(f"   https://huggingface.co/{base_model}")
            return None
    
    def setup_checkpoints_symlink(self):
        """
        Cria symlinks automáticos para F5-TTS:
        1. ckpts/f5_dataset -> train/output/F5TTS_Base (checkpoints)
        2. data -> train/data (dataset)
        3. runs -> train/runs (TensorBoard logs)
        """
        # 1. Symlink de checkpoints
        f5_ckpt_dir = Path("/root/.local/lib/python3.11/ckpts") / self.config['train_dataset_name']
        target_dir = self.output_dir
        
        # Garantir que target existe
        target_dir.mkdir(parents=True, exist_ok=True)
        
        if f5_ckpt_dir.exists() and f5_ckpt_dir.is_symlink():
            # Já é symlink - verificar se aponta para lugar certo
            current_target = f5_ckpt_dir.resolve()
            if current_target != target_dir:
                logger.warning(f"⚠️  Symlink aponta para: {current_target}")
                logger.warning(f"   Redirecionando para: {target_dir}")
                f5_ckpt_dir.unlink()
                f5_ckpt_dir.symlink_to(target_dir)
            else:
                logger.info(f"✅ Symlink de checkpoints OK: ckpts/{self.config['train_dataset_name']} -> {target_dir.relative_to(PROJECT_ROOT)}")
        elif f5_ckpt_dir.exists():
            # Diretório real existe - mover conteúdo
            logger.info(f"📦 Movendo checkpoints existentes para {target_dir.relative_to(PROJECT_ROOT)}/")
            import shutil
            for item in f5_ckpt_dir.iterdir():
                dest = target_dir / item.name
                if not dest.exists():
                    shutil.move(str(item), str(dest))
                    logger.info(f"   ✅ {item.name}")
            
            # Remover diretório vazio e criar symlink
            try:
                f5_ckpt_dir.rmdir()
            except:
                import shutil
                shutil.rmtree(f5_ckpt_dir)
            
            f5_ckpt_dir.symlink_to(target_dir)
            logger.info(f"✅ Symlink criado: ckpts/{self.config['train_dataset_name']} -> {target_dir.relative_to(PROJECT_ROOT)}")
        else:
            # Não existe - criar symlink
            f5_ckpt_dir.parent.mkdir(parents=True, exist_ok=True)
            f5_ckpt_dir.symlink_to(target_dir)
            logger.info(f"✅ Symlink criado: ckpts/{self.config['train_dataset_name']} -> {target_dir.relative_to(PROJECT_ROOT)}")
        
        # 2. Symlink de data (automático)
        data_link = Path("/root/.local/lib/python3.11/data")
        if not data_link.exists():
            data_link.symlink_to(self.data_dir.absolute(), target_is_directory=True)
            logger.info(f"✅ Symlink criado: data -> {self.data_dir.relative_to(PROJECT_ROOT)}")
        elif data_link.is_symlink() and data_link.resolve() == self.data_dir:
            logger.info(f"✅ Symlink de data OK")
        
        # 3. Symlink f5_dataset_pinyin -> f5_dataset (automático)
        dataset_dir = self.data_dir / self.config['train_dataset_name']
        pinyin_link = self.data_dir / f"{self.config['train_dataset_name']}_pinyin"
        if not pinyin_link.exists() and dataset_dir.exists():
            pinyin_link.symlink_to(dataset_dir, target_is_directory=True)
            logger.info(f"✅ Symlink criado: {pinyin_link.name} -> {dataset_dir.name}")
        
        # 4. Symlink runs/ -> train/runs/ (para TensorBoard logs)
        # F5-TTS cria runs/ na raiz do workspace automaticamente
        # Precisamos redirecionar ANTES do treinamento começar
        root_runs = PROJECT_ROOT / "runs"
        if not root_runs.exists():
            # Ainda não foi criado - criar symlink preventivamente
            root_runs.symlink_to(self.runs_dir.absolute(), target_is_directory=True)
            logger.info(f"✅ Symlink criado: /runs -> {self.runs_dir.relative_to(PROJECT_ROOT)}")
        elif root_runs.is_symlink():
            # Já é symlink - verificar se aponta para o lugar certo
            if root_runs.resolve() != self.runs_dir.absolute():
                logger.warning(f"⚠️  Symlink /runs aponta para {root_runs.resolve()}")
                logger.warning(f"   Redirecionando para {self.runs_dir.absolute()}")
                root_runs.unlink()
                root_runs.symlink_to(self.runs_dir.absolute(), target_is_directory=True)
            else:
                logger.info(f"✅ Symlink /runs OK")
    
    def setup_environment(self):
        """Configura ambiente e diretórios"""
        logger.info("=" * 80)
        logger.info("🚀 F5-TTS TRAINING PIPELINE v3.0")
        logger.info("=" * 80)
        
        # Criar diretórios
        for dir_path in [self.runs_dir, self.output_dir, self.data_dir, self.pretrained_dir]:
            dir_path.mkdir(parents=True, exist_ok=True)
        
        # Setup symlinks automáticos (checkpoints, data, pinyin)
        self.setup_checkpoints_symlink()
        
        # Baixar modelo pré-treinado se necessário
        pretrained_path = self.download_pretrained_model()
        if pretrained_path:
            self.config['pretrained_model_path'] = pretrained_path
        
        # Mover runs/ e data/ se existirem fora de train/
        # NÃO PRECISA MAIS - O symlink já redireciona tudo
        # self._organize_directories()
        
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
        
        # Iniciar TensorBoard automaticamente
        self.start_tensorboard()
    
    def _organize_directories(self):
        """Move runs/ da raiz para train/runs se necessário"""
        root_runs = PROJECT_ROOT / "runs"
        
        if root_runs.exists() and root_runs != self.runs_dir:
            logger.info(f"📦 Movendo /runs/ -> /train/runs/")
            if self.runs_dir.exists():
                import shutil
                shutil.rmtree(self.runs_dir)
            import shutil
            shutil.move(str(root_runs), str(self.runs_dir))
            logger.info(f"   ✅ Movido")
    
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
            # Tentar encontrar tensorboard no PATH ou em locais comuns
            tensorboard_cmd = None
            for cmd in ['/root/.local/bin/tensorboard', 'tensorboard']:
                try:
                    result = subprocess.run([cmd, '--version'], capture_output=True, timeout=2)
                    tensorboard_cmd = cmd
                    break
                except:
                    continue
            
            if not tensorboard_cmd:
                raise FileNotFoundError("tensorboard não encontrado")
            
            self.tensorboard_process = subprocess.Popen(
                [tensorboard_cmd, '--logdir', str(self.runs_dir), '--port', str(port), '--bind_all'],
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
        
        # Priority 1: Check training output directory for existing checkpoints
        local_output_dir = self.output_dir
        resume_checkpoint = None
        
        if local_output_dir.exists():
            # Look for model_last.pt first (most recent)
            last_ckpt = local_output_dir / "model_last.pt"
            if last_ckpt.exists():
                resume_checkpoint = str(last_ckpt.absolute())
                logger.info(f"📂 Checkpoint encontrado em train/output/: {last_ckpt.name}")
            else:
                # Look for numbered checkpoints
                checkpoints = sorted(local_output_dir.glob("model_*.pt"), 
                                   key=lambda x: int(x.stem.split('_')[1]) if x.stem.split('_')[1].isdigit() else 0)
                if checkpoints:
                    resume_checkpoint = str(checkpoints[-1].absolute())
                    logger.info(f"📂 Checkpoint encontrado em train/output/: {checkpoints[-1].name}")
        
        # Priority 2: Check F5-TTS ckpts directory
        if not resume_checkpoint:
            checkpoint_dir = Path(f"/root/.local/lib/python3.11/site-packages/f5_tts/../../ckpts/{self.config['train_dataset_name']}")
            if checkpoint_dir.exists():
                last_ckpt = checkpoint_dir / "model_last.pt"
                if last_ckpt.exists():
                    resume_checkpoint = str(last_ckpt.absolute())
                    logger.info(f"📂 Checkpoint encontrado em ckpts/: {last_ckpt.name}")
        
        # Priority 3: Use local pretrained model from models/f5tts/pt-br/
        pretrained_model = None
        if not resume_checkpoint:
            local_pretrained = PROJECT_ROOT / "models" / "f5tts" / "pt-br" / "model_last.pt"
            if local_pretrained.exists():
                pretrained_model = str(local_pretrained.absolute())
                logger.info(f"📥 Modelo pré-treinado encontrado: {local_pretrained.relative_to(PROJECT_ROOT)}")
        
        # Priority 4: Use pretrained model from .env configuration
        if not resume_checkpoint and not pretrained_model:
            pretrained_path_env = self.config.get('pretrained_model_path')
            if pretrained_path_env and pretrained_path_env.strip():  # Só se não estiver vazio
                # Caminhos podem ser:
                # 1. Absolutos: /root/.local/lib/python3.11/ckpts/f5_dataset/model_last.pt
                # 2. Relativos ao F5-TTS: ckpts/f5_dataset/model_last.pt
                # 3. Relativos ao workspace: train/pretrained/model.pt
                
                pretrained_path = Path(pretrained_path_env)
                
                if pretrained_path.is_absolute() and pretrained_path.exists():
                    # Caminho absoluto
                    pretrained_model = str(pretrained_path.absolute())
                    logger.info(f"📥 Usando modelo pré-treinado (absoluto): {pretrained_path.name}")
                elif pretrained_path_env.startswith('ckpts/'):
                    # Caminho relativo ao F5-TTS (ckpts/f5_dataset/model_last.pt)
                    f5tts_base = Path("/root/.local/lib/python3.11")
                    pretrained_full = f5tts_base / pretrained_path_env
                    if pretrained_full.exists():
                        pretrained_model = str(pretrained_full.absolute())
                        logger.info(f"📥 Usando modelo pré-treinado (F5-TTS): {pretrained_full.name}")
                    else:
                        logger.warning(f"⚠️  Modelo não encontrado: {pretrained_full}")
                else:
                    # Caminho relativo ao workspace
                    pretrained_full = self.train_root / pretrained_path_env.replace('train/', '')
                    if pretrained_full.exists():
                        pretrained_model = str(pretrained_full.absolute())
                        logger.info(f"📥 Usando modelo pré-treinado (workspace): {pretrained_full.name}")
                    else:
                        logger.warning(f"⚠️  Modelo não encontrado: {pretrained_full}")
        
        # Preparar argumentos para finetune_cli
        args = [
            '--exp_name', 'F5TTS_Base',
            '--dataset_name', self.config['train_dataset_name'],
            '--learning_rate', str(self.config['learning_rate']),
            '--batch_size_per_gpu', str(self.config['batch_size']),
            '--batch_size_type', self.config['batch_size_type'],
            '--max_samples', str(self.config.get('max_samples', 32)),
            '--grad_accumulation_steps', str(self.config['grad_accumulation_steps']),
            '--max_grad_norm', str(self.config['max_grad_norm']),
            '--epochs', str(self.config['epochs']),
            '--num_warmup_updates', str(self.config['warmup_steps']),
            '--save_per_updates', str(self.config['save_per_updates']),
            '--last_per_updates', str(self.config['last_per_updates']),
            '--keep_last_n_checkpoints', str(self.config['keep_last_n_checkpoints']),
            '--logger', self.config['logger'],
        ]
        
        # Add finetune flag only if we have a pretrained model
        # (finetune mode requires a checkpoint to continue from)
        has_pretrained = resume_checkpoint or pretrained_model
        if has_pretrained:
            args.append('--finetune')
        
        # Add log_samples flag if enabled
        if self.config.get('log_samples', True):
            args.append('--log_samples')
        
        # Add pretrained model path
        if resume_checkpoint:
            # Continue from existing checkpoint
            args.extend(['--pretrain', resume_checkpoint])
            logger.info("🔄 Modo: Continuar treinamento do checkpoint")
        elif pretrained_model:
            # Start from local pretrained model
            args.extend(['--pretrain', pretrained_model])
            logger.info("🎯 Modo: Fine-tuning do modelo pré-treinado local")
        else:
            logger.info("🆕 Modo: Treinamento do zero (sem modelo pré-treinado)")
        
        logger.info("")
        logger.info("🚀 Iniciando treinamento F5-TTS...")
        logger.info(f"   Argumentos completos: {args}")
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
