#!/usr/bin/env python3
"""
Treinamento com Early Stopping - Wrapper para F5-TTS
Monitora o loss durante treinamento e para automaticamente se não melhorar
"""
import subprocess
import re
import sys
import time
import signal
from pathlib import Path
import logging
import yaml

logging.basicConfig(level=logging.INFO, format='%(message)s')
logger = logging.getLogger(__name__)

class TrainingMonitor:
    """Monitora treinamento e implementa early stopping"""
    
    def __init__(self, patience=3, min_delta=0.001):
        self.patience = patience
        self.min_delta = min_delta
        self.epoch_losses = {}
        self.best_loss = None
        self.best_epoch = 0
        self.counter = 0
        self.process = None
        
    def extract_epoch_loss(self, line):
        """Extrai epoch e loss de uma linha do log"""
        # Epoch 1/10: 100%|██████| 75/75 [03:03<00:00,  2.45s/update, loss=0.676, update=75]
        match = re.search(r'Epoch (\d+)/\d+.*loss=([\d.]+)', line)
        if match:
            epoch = int(match.group(1))
            loss = float(match.group(2))
            return epoch, loss
        return None, None
    
    def should_stop(self, epoch, loss):
        """Verifica se deve parar o treinamento"""
        if self.patience <= 0:
            return False
        
        # Atualizar loss da epoch
        if epoch in self.epoch_losses:
            # Pegar menor loss da epoch
            if loss < self.epoch_losses[epoch]:
                self.epoch_losses[epoch] = loss
        else:
            self.epoch_losses[epoch] = loss
        
        # Primeira epoch
        if self.best_loss is None:
            self.best_loss = loss
            self.best_epoch = epoch
            logger.info(f"🎯 Baseline loss: {loss:.4f}")
            return False
        
        # Checar melhora no final da epoch (quando epoch muda)
        current_epoch_loss = self.epoch_losses.get(epoch)
        if current_epoch_loss is None:
            return False
        
        # Se epoch mudou, avaliar epoch anterior
        if epoch > self.best_epoch + 1:
            prev_epoch = epoch - 1
            prev_loss = self.epoch_losses.get(prev_epoch)
            
            if prev_loss and (self.best_loss - prev_loss) > self.min_delta:
                # Melhorou!
                improvement = self.best_loss - prev_loss
                logger.info(f"")
                logger.info(f"✅ EPOCH {prev_epoch} - Loss melhorou: {self.best_loss:.4f} → {prev_loss:.4f} (+{improvement:.4f})")
                self.best_loss = prev_loss
                self.best_epoch = prev_epoch
                self.counter = 0
            else:
                # Não melhorou
                self.counter += 1
                logger.info(f"")
                logger.info(f"⚠️  EPOCH {prev_epoch} - Loss não melhorou: {prev_loss:.4f} (melhor: {self.best_loss:.4f} @ epoch {self.best_epoch})")
                logger.info(f"   🛑 Early Stopping: {self.counter}/{self.patience} epochs sem melhora")
                
                if self.counter >= self.patience:
                    logger.info(f"")
                    logger.info("=" * 80)
                    logger.info("🛑 EARLY STOPPING ATIVADO!")
                    logger.info("=" * 80)
                    logger.info(f"✅ Melhor loss: {self.best_loss:.4f} @ epoch {self.best_epoch}")
                    logger.info(f"⚠️  {self.patience} epochs consecutivas sem melhora (min_delta={self.min_delta})")
                    logger.info(f"💾 Checkpoint salvo em: train/output/ptbr_finetuned/model_last.pt")
                    logger.info("=" * 80)
                    return True
        
        return False
    
    def run_training(self, config_path='train/config/train_config.yaml'):
        """Executa treinamento com monitoramento"""
        # Carregar config
        with open(config_path, 'r') as f:
            config = yaml.safe_load(f)
        
        patience = config['training'].get('early_stop_patience', 0)
        min_delta = config['training'].get('early_stop_min_delta', 0.001)
        
        if patience <= 0:
            logger.info("⚠️  Early Stopping desabilitado (patience=0)")
            logger.info("   Executando treinamento normal...")
            # Executar sem monitoramento
            subprocess.run([sys.executable, '-m', 'train.run_training'])
            return
        
        self.patience = patience
        self.min_delta = min_delta
        
        logger.info("=" * 80)
        logger.info("🚀 TREINAMENTO COM EARLY STOPPING")
        logger.info("=" * 80)
        logger.info(f"📊 Patience: {patience} epochs")
        logger.info(f"📊 Min delta: {min_delta}")
        logger.info(f"📊 Epochs: {config['training']['epochs']}")
        logger.info("=" * 80)
        logger.info("")
        
        # Iniciar processo de treinamento
        self.process = subprocess.Popen(
            [sys.executable, '-m', 'train.run_training'],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            universal_newlines=True,
            bufsize=1
        )
        
        try:
            # Monitorar output
            for line in self.process.stdout:
                print(line, end='')  # Imprimir linha
                
                # Extrair epoch e loss
                epoch, loss = self.extract_epoch_loss(line)
                if epoch and loss:
                    # Checar early stopping
                    if self.should_stop(epoch, loss):
                        logger.info("⏹️  Parando treinamento...")
                        self.process.send_signal(signal.SIGINT)
                        time.sleep(2)
                        self.process.terminate()
                        break
            
            # Esperar processo finalizar
            self.process.wait()
            
            if self.process.returncode == 0 or self.process.returncode == -2:  # SIGINT
                logger.info("")
                logger.info("✅ Treinamento finalizado com sucesso")
            else:
                logger.error(f"❌ Treinamento terminou com código {self.process.returncode}")
                
        except KeyboardInterrupt:
            logger.info("\n⚠️  Interrompido pelo usuário")
            self.process.send_signal(signal.SIGINT)
            time.sleep(2)
            self.process.terminate()
        except Exception as e:
            logger.error(f"❌ Erro durante treinamento: {e}")
            if self.process:
                self.process.terminate()
            raise


if __name__ == "__main__":
    monitor = TrainingMonitor()
    monitor.run_training()
