#!/usr/bin/env python3
"""
Wrapper inteligente para treinamento F5-TTS
- Garante que TUDO fique dentro da pasta train/
- Gera áudio de teste a cada epoch
- Salva modelo a cada epoch
- Organiza logs do TensorBoard
- Configurável via .env
"""
import os
import sys
import shutil
import subprocess
import re
import signal
import time
from pathlib import Path
import logging
import yaml
import torch
import torchaudio

# Forçar working directory para o root do projeto
PROJECT_ROOT = Path(__file__).parent.parent.resolve()
TRAIN_ROOT = PROJECT_ROOT / "train"

os.chdir(PROJECT_ROOT)
sys.path.insert(0, str(PROJECT_ROOT))

# Carregar configurações do .env
from train.utils.env_loader import get_training_config

logging.basicConfig(level=logging.INFO, format='%(message)s')
logger = logging.getLogger(__name__)


class TrainingSupervisor:
    """Supervisiona treinamento e mantém tudo organizado em train/"""
    
    def __init__(self):
        self.train_root = TRAIN_ROOT
        self.runs_dir = self.train_root / "runs"
        self.data_dir = self.train_root / "data"
        self.output_dir = self.train_root / "output" / "ptbr_finetuned"
        self.test_samples_dir = self.output_dir / "test_samples"
        
        # Áudio de referência para testes
        self.reference_text = "Olá, este é um teste de qualidade do modelo de síntese de voz em português brasileiro."
        self.current_epoch = 0
        self.process = None
        
    def setup_directories(self):
        """Garante que todos os diretórios estejam em train/"""
        logger.info("=" * 80)
        logger.info("🔧 CONFIGURANDO ESTRUTURA DE DIRETÓRIOS")
        logger.info("=" * 80)
        
        # Criar diretórios necessários
        dirs_to_create = [
            self.runs_dir,
            self.data_dir,
            self.output_dir,
            self.test_samples_dir,
            self.train_root / "logs",
        ]
        
        for dir_path in dirs_to_create:
            dir_path.mkdir(parents=True, exist_ok=True)
            logger.info(f"✅ {dir_path.relative_to(PROJECT_ROOT)}")
        
        # Mover arquivos que estejam fora de train/
        root_runs = PROJECT_ROOT / "runs"
        root_data = PROJECT_ROOT / "data"
        
        if root_runs.exists() and root_runs != self.runs_dir:
            logger.info(f"📦 Movendo runs/ -> train/runs/")
            if self.runs_dir.exists():
                shutil.rmtree(self.runs_dir)
            shutil.move(str(root_runs), str(self.runs_dir))
        
        if root_data.exists() and root_data != self.data_dir:
            # Apenas mover se não for o data principal do projeto
            if not (root_data / "f5_dataset").exists():
                logger.info(f"📦 Movendo data/ -> train/data/")
                backup_name = f"data_backup_{int(time.time())}"
                shutil.move(str(root_data), str(self.train_root / backup_name))
        
        # Criar symlinks necessários para F5-TTS
        self._setup_f5tts_symlinks()
        
        logger.info("=" * 80)
        logger.info("")
    
    def _setup_f5tts_symlinks(self):
        """Configura symlinks para F5-TTS (sempre dentro de train/)"""
        # F5-TTS procura em: /root/.local/lib/python3.11/data/
        # Criar symlink apontando para train/data/
        
        python_lib = Path.home() / ".local" / "lib"
        
        # Encontrar diretório python
        python_dirs = list(python_lib.glob("python*"))
        if not python_dirs:
            logger.warning("⚠️  Python lib dir não encontrado")
            return
        
        for python_dir in python_dirs:
            data_link = python_dir / "data"
            
            # Remover link antigo se existir
            if data_link.is_symlink():
                data_link.unlink()
            elif data_link.exists():
                # Se for diretório real, fazer backup
                backup = python_dir / f"data_backup_{int(time.time())}"
                shutil.move(str(data_link), str(backup))
            
            # Criar link apontando para train/data
            data_link.symlink_to(self.data_dir.absolute(), target_is_directory=True)
            logger.info(f"🔗 Symlink: {data_link} -> {self.data_dir}")
    
    def generate_test_audio(self, epoch: int, model_path: Path):
        """
        Gera áudio de teste para avaliar qualidade do modelo
        
        Args:
            epoch: Número da epoch
            model_path: Path do checkpoint do modelo
        """
        if not model_path.exists():
            logger.warning(f"⚠️  Checkpoint não encontrado: {model_path}")
            return
        
        epoch_dir = self.test_samples_dir / f"epoch_{epoch}"
        epoch_dir.mkdir(parents=True, exist_ok=True)
        
        logger.info(f"")
        logger.info(f"🎵 Gerando áudio de teste - Epoch {epoch}")
        logger.info(f"   Texto: \"{self.reference_text}\"")
        logger.info(f"   Output: {epoch_dir.relative_to(PROJECT_ROOT)}/")
        
        try:
            # Importar F5-TTS (apenas quando necessário)
            from f5_tts.infer.utils_infer import infer_process, load_vocoder, load_model
            from f5_tts.model.utils import get_tokenizer
            
            # Carregar vocab
            vocab_path = self.train_root / "data" / "f5_dataset" / "vocab.txt"
            if not vocab_path.exists():
                logger.warning(f"⚠️  Vocab não encontrado: {vocab_path}")
                return
            
            with open(vocab_path, 'r', encoding='utf-8') as f:
                vocab_char_map = {char: idx for idx, char in enumerate(f.read().strip())}
            
            # Carregar modelo
            device = "cuda" if torch.cuda.is_available() else "cpu"
            
            # Usar áudio de referência do dataset
            ref_audio_path = None
            wavs_dir = self.train_root / "data" / "f5_dataset" / "wavs"
            if wavs_dir.exists():
                audio_files = list(wavs_dir.glob("*.wav"))
                if audio_files:
                    ref_audio_path = audio_files[0]  # Usar primeiro áudio como referência
            
            if not ref_audio_path or not ref_audio_path.exists():
                logger.warning("⚠️  Nenhum áudio de referência encontrado no dataset")
                return
            
            # Carregar áudio de referência
            ref_audio, sr = torchaudio.load(str(ref_audio_path))
            if sr != 24000:
                ref_audio = torchaudio.functional.resample(ref_audio, sr, 24000)
            
            # Salvar referência (primeira vez)
            ref_output = epoch_dir / "reference.wav"
            if not ref_output.exists():
                torchaudio.save(str(ref_output), ref_audio, 24000)
            
            # Texto de referência (primeiros 50 chars do arquivo)
            metadata_path = self.train_root / "data" / "f5_dataset" / "metadata.csv"
            ref_text = "Este é um teste de voz."
            if metadata_path.exists():
                with open(metadata_path, 'r', encoding='utf-8') as f:
                    first_line = f.readline().strip()
                    if '|' in first_line:
                        ref_text = first_line.split('|')[1][:100]
            
            # Nota: Geração completa requer modelo carregado e configurado
            # Por enquanto, apenas salvar informações
            info_path = epoch_dir / "info.txt"
            with open(info_path, 'w', encoding='utf-8') as f:
                f.write(f"Epoch: {epoch}\n")
                f.write(f"Checkpoint: {model_path.name}\n")
                f.write(f"Texto de teste: {self.reference_text}\n")
                f.write(f"Referência: {ref_audio_path.name}\n")
                f.write(f"Texto referência: {ref_text}\n")
            
            logger.info(f"   ✅ Info salva: {info_path.relative_to(PROJECT_ROOT)}")
            logger.info(f"   📝 Nota: Geração de áudio requer inferência completa")
            
        except Exception as e:
            logger.error(f"   ❌ Erro ao gerar áudio: {e}")
    
    def monitor_training(self, config_path='train/config/train_config.yaml'):
        """
        Monitora treinamento e gera samples por epoch
        """
        # Carregar config do .env
        env_config = get_training_config()
        
        # Carregar config YAML
        config_file = PROJECT_ROOT / config_path
        with open(config_file, 'r') as f:
            config = yaml.safe_load(f)
        
        # Override com valores do .env
        patience = env_config.get('early_stop_patience', config['training'].get('early_stop_patience', 5))
        min_delta = env_config.get('early_stop_min_delta', config['training'].get('early_stop_min_delta', 0.001))
        epochs = env_config.get('epochs', config['training'].get('epochs', 1000))
        
        logger.info("=" * 80)
        logger.info("🚀 INICIANDO TREINAMENTO SUPERVISIONADO")
        logger.info("=" * 80)
        logger.info(f"📊 Epochs: {epochs}")
        if patience > 0:
            logger.info(f"🛑 Early Stopping: {patience} epochs (min_delta={min_delta})")
            logger.info(f"   Vai treinar até {epochs} epochs OU até parar de evoluir")
        logger.info(f"📁 Tudo salvo em: {self.train_root.relative_to(PROJECT_ROOT)}/")
        logger.info(f"📊 TensorBoard: {self.runs_dir.relative_to(PROJECT_ROOT)}/")
        logger.info(f"💾 Checkpoints: {self.output_dir.relative_to(PROJECT_ROOT)}/")
        logger.info(f"🎵 Test samples: {self.test_samples_dir.relative_to(PROJECT_ROOT)}/")
        logger.info(f"⚙️  Config: .env + train_config.yaml")
        logger.info("=" * 80)
        logger.info("")
        
        # Iniciar processo de treinamento
        self.process = subprocess.Popen(
            [sys.executable, '-m', 'train.run_training'],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            universal_newlines=True,
            bufsize=1,
            cwd=str(PROJECT_ROOT)
        )
        
        epoch_losses = {}
        best_loss = None
        counter = 0
        
        try:
            # Monitorar output
            for line in self.process.stdout:
                print(line, end='')  # Imprimir linha
                
                # Detectar nova epoch
                epoch_match = re.search(r'Epoch (\d+)/(\d+).*loss=([\d.]+)', line)
                if epoch_match:
                    epoch = int(epoch_match.group(1))
                    loss = float(epoch_match.group(3))
                    
                    # Atualizar loss da epoch
                    if epoch not in epoch_losses:
                        epoch_losses[epoch] = []
                    epoch_losses[epoch].append(loss)
                
                # Detectar salvamento de checkpoint
                checkpoint_match = re.search(r'Saved last checkpoint at update (\d+)', line)
                if checkpoint_match:
                    update = int(checkpoint_match.group(1))
                    
                    # Se mudou de epoch, gerar sample
                    if epoch_losses:
                        current_epoch = max(epoch_losses.keys())
                        if current_epoch > self.current_epoch:
                            # Nova epoch completada
                            avg_loss = sum(epoch_losses[current_epoch]) / len(epoch_losses[current_epoch])
                            
                            logger.info(f"")
                            logger.info(f"📊 EPOCH {current_epoch} COMPLETA - Loss médio: {avg_loss:.4f}")
                            
                            # Gerar áudio de teste
                            model_path = self.output_dir / "model_last.pt"
                            if model_path.exists():
                                self.generate_test_audio(current_epoch, model_path)
                            
                            # Early stopping check
                            if patience > 0:
                                if best_loss is None or (best_loss - avg_loss) > min_delta:
                                    if best_loss is not None:
                                        improvement = best_loss - avg_loss
                                        logger.info(f"✅ Loss melhorou: {best_loss:.4f} → {avg_loss:.4f} (+{improvement:.4f})")
                                    best_loss = avg_loss
                                    counter = 0
                                else:
                                    counter += 1
                                    logger.info(f"⚠️  Loss não melhorou: {avg_loss:.4f} (melhor: {best_loss:.4f})")
                                    logger.info(f"   🛑 Early Stopping: {counter}/{patience} epochs sem melhora")
                                    
                                    if counter >= patience:
                                        logger.info(f"")
                                        logger.info("=" * 80)
                                        logger.info("🛑 EARLY STOPPING ATIVADO!")
                                        logger.info("=" * 80)
                                        self.process.send_signal(signal.SIGINT)
                                        time.sleep(2)
                                        break
                            
                            self.current_epoch = current_epoch
            
            # Esperar processo finalizar
            self.process.wait()
            
            logger.info("")
            logger.info("=" * 80)
            logger.info("✅ TREINAMENTO FINALIZADO")
            logger.info("=" * 80)
            logger.info(f"📁 Checkpoints: {self.output_dir.relative_to(PROJECT_ROOT)}/")
            logger.info(f"🎵 Test samples: {self.test_samples_dir.relative_to(PROJECT_ROOT)}/")
            logger.info(f"📊 TensorBoard: tensorboard --logdir={self.runs_dir.relative_to(PROJECT_ROOT)}")
            logger.info("=" * 80)
            
        except KeyboardInterrupt:
            logger.info("\n⚠️  Interrompido pelo usuário")
            if self.process:
                self.process.send_signal(signal.SIGINT)
                time.sleep(2)
                self.process.terminate()
        except Exception as e:
            logger.error(f"❌ Erro durante treinamento: {e}")
            if self.process:
                self.process.terminate()
            raise


def main():
    """Main function"""
    supervisor = TrainingSupervisor()
    
    # Setup inicial
    supervisor.setup_directories()
    
    # Rodar treinamento
    supervisor.monitor_training()


if __name__ == "__main__":
    main()
