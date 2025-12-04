#!/usr/bin/env python3
"""
Script para analisar métricas do modelo F5-TTS fine-tuned
"""
import torch
import json
from pathlib import Path
import logging
import re
from datetime import datetime

logging.basicConfig(level=logging.INFO, format='%(message)s')
logger = logging.getLogger(__name__)

def parse_training_log(log_path):
    """Extrai métricas do log de treinamento"""
    metrics = {
        'epochs': [],
        'losses': [],
        'updates': []
    }
    
    if not log_path.exists():
        return metrics
    
    with open(log_path, 'r') as f:
        for line in f:
            # Procurar por linhas de epoch com loss
            match = re.search(r'Epoch (\d+)/(\d+).*loss=([\d.]+).*update=(\d+)', line)
            if match:
                epoch = int(match.group(1))
                total_epochs = int(match.group(2))
                loss = float(match.group(3))
                update = int(match.group(4))
                
                if not metrics['epochs'] or metrics['epochs'][-1] != epoch:
                    metrics['epochs'].append(epoch)
                    metrics['losses'].append(loss)
                    metrics['updates'].append(update)
                elif loss < metrics['losses'][-1]:  # Atualizar com loss menor
                    metrics['losses'][-1] = loss
                    metrics['updates'][-1] = update
    
    return metrics

def analyze_checkpoint(checkpoint_path, checkpoint_name="Checkpoint"):
    """Analisa um checkpoint e retorna informações detalhadas"""
    if not checkpoint_path.exists():
        return None
    
    try:
        checkpoint = torch.load(checkpoint_path, map_location='cpu', weights_only=False)
        
        info = {
            'name': checkpoint_name,
            'path': str(checkpoint_path),
            'size_mb': checkpoint_path.stat().st_size / (1024**2),
            'modified': datetime.fromtimestamp(checkpoint_path.stat().st_mtime).strftime('%Y-%m-%d %H:%M:%S')
        }
        
        # Extrair informações do checkpoint
        if isinstance(checkpoint, dict):
            # Estrutura: { 'ema_model_state_dict': {...}, 'steps': X }
            if 'ema_model_state_dict' in checkpoint:
                info['num_parameters'] = len(checkpoint['ema_model_state_dict'])
                info['steps'] = checkpoint.get('steps', 'N/A')
                info['type'] = 'F5-TTS Checkpoint (EMA)'
            elif 'model_state_dict' in checkpoint:
                info['num_parameters'] = len(checkpoint['model_state_dict'])
                info['epoch'] = checkpoint.get('epoch', 'N/A')
                info['updates'] = checkpoint.get('total_updates', 'N/A')
                info['loss'] = checkpoint.get('last_loss', 'N/A')
                info['type'] = 'Training Checkpoint'
            else:
                # Estado direto do modelo
                info['num_parameters'] = len(checkpoint)
                info['type'] = 'Model State Dict'
        else:
            info['type'] = 'Unknown Format'
        
        return info
        
    except Exception as e:
        logger.error(f"Erro ao analisar {checkpoint_name}: {e}")
        return None

def print_metrics_report():
    """Gera relatório completo de métricas do treinamento"""
    
    logger.info("=" * 80)
    logger.info("📊 RELATÓRIO COMPLETO DE MÉTRICAS - F5-TTS FINE-TUNING")
    logger.info("=" * 80)
    logger.info("")
    
    # 1. Analisar logs de treinamento
    log_path = Path("train/logs/training_interactive.log")
    if log_path.exists():
        metrics = parse_training_log(log_path)
        
        if metrics['epochs']:
            logger.info("📈 EVOLUÇÃO DO TREINAMENTO")
            logger.info("-" * 80)
            logger.info(f"{'Epoch':<10} {'Loss':<15} {'Updates':<15} {'Melhora':<15}")
            logger.info("-" * 80)
            
            for i, (epoch, loss, update) in enumerate(zip(metrics['epochs'], metrics['losses'], metrics['updates'])):
                if i == 0:
                    improvement = "-"
                else:
                    prev_loss = metrics['losses'][i-1]
                    improvement = f"{((prev_loss - loss) / prev_loss * 100):+.2f}%"
                
                logger.info(f"{epoch:<10} {loss:<15.4f} {update:<15} {improvement:<15}")
            
            logger.info("-" * 80)
            logger.info(f"📊 Loss inicial: {metrics['losses'][0]:.4f}")
            logger.info(f"📊 Loss final: {metrics['losses'][-1]:.4f}")
            logger.info(f"📊 Redução total: {((metrics['losses'][0] - metrics['losses'][-1]) / metrics['losses'][0] * 100):.2f}%")
            logger.info(f"📊 Total de updates: {metrics['updates'][-1]}")
            logger.info("")
    
    # 2. Analisar checkpoints
    # Usar OUTPUT_DIR do .env
    import sys
    from pathlib import Path as PathLib
    project_root = PathLib(__file__).parent.parent.parent
    sys.path.insert(0, str(project_root))
    from train.utils.env_loader import get_training_config
    config = get_training_config()
    output_dir = project_root / config.get('output_dir', 'train/output/ptbr_finetuned')
    checkpoints = []
    
    if output_dir.exists():
        for ckpt_file in sorted(output_dir.glob("*.pt")):
            info = analyze_checkpoint(ckpt_file, ckpt_file.name)
            if info:
                checkpoints.append(info)
    
    if checkpoints:
        logger.info("💾 CHECKPOINTS SALVOS")
        logger.info("-" * 80)
        for ckpt in checkpoints:
            logger.info(f"📁 {ckpt['name']}")
            logger.info(f"   Caminho: {ckpt['path']}")
            logger.info(f"   Tamanho: {ckpt['size_mb']:.1f} MB")
            logger.info(f"   Modificado: {ckpt['modified']}")
            logger.info(f"   Tipo: {ckpt['type']}")
            logger.info(f"   Parâmetros: {ckpt['num_parameters']} tensores")
            if 'steps' in ckpt:
                logger.info(f"   Steps: {ckpt['steps']}")
            logger.info("")
    
    # 3. Verificar amostras de áudio geradas
    samples_dir = output_dir / "samples"
    if samples_dir.exists():
        audio_files = list(samples_dir.glob("*.wav"))
        if audio_files:
            logger.info("🔊 AMOSTRAS DE ÁUDIO GERADAS")
            logger.info("-" * 80)
            for audio in sorted(audio_files):
                size_kb = audio.stat().st_size / 1024
                logger.info(f"   {audio.name} ({size_kb:.1f} KB)")
            logger.info("")
    
    # 4. Verificar TensorBoard logs
    tensorboard_dirs = []
    runs_dir = Path("runs")
    if runs_dir.exists():
        for run_dir in runs_dir.iterdir():
            if run_dir.is_dir():
                events = list(run_dir.glob("events.out.tfevents.*"))
                if events:
                    tensorboard_dirs.append((run_dir, len(events)))
    
    if tensorboard_dirs:
        logger.info("📊 LOGS DO TENSORBOARD")
        logger.info("-" * 80)
        for run_dir, num_events in tensorboard_dirs:
            logger.info(f"   📂 {run_dir.name}")
            logger.info(f"      {num_events} arquivo(s) de eventos")
        logger.info("")
        logger.info("💡 Para visualizar no TensorBoard:")
        logger.info(f"   export PATH=\"$HOME/.local/bin:$PATH\"")
        logger.info(f"   tensorboard --logdir=runs")
        logger.info(f"   Acesse: http://localhost:6006")
        logger.info("")
    
    # 5. Resumo final
    logger.info("=" * 80)
    logger.info("✅ RESUMO FINAL")
    logger.info("=" * 80)
    if metrics['epochs']:
        logger.info(f"✓ Treinamento: {len(metrics['epochs'])} epochs completadas")
        logger.info(f"✓ Loss: {metrics['losses'][0]:.4f} → {metrics['losses'][-1]:.4f} ({((metrics['losses'][0] - metrics['losses'][-1]) / metrics['losses'][0] * 100):.1f}% redução)")
    logger.info(f"✓ Checkpoints: {len(checkpoints)} modelo(s) salvo(s)")
    if samples_dir.exists():
        logger.info(f"✓ Amostras: {len(list(samples_dir.glob('*.wav')))} arquivo(s) de áudio")
    logger.info("=" * 80)

if __name__ == "__main__":
    print_metrics_report()
