#!/usr/bin/env python3
"""
Monitor de espaço em disco durante treinamento

Monitora continuamente o espaço em disco e limpa checkpoints
antigos automaticamente quando necessário.

Uso:
    python3 train/utils/disk_monitor.py --threshold 20 --keep 3
"""

import argparse
import logging
import time
import shutil
from pathlib import Path

# Setup
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%H:%M:%S'
)
logger = logging.getLogger(__name__)

PROJECT_ROOT = Path(__file__).parent.parent.parent
OUTPUT_DIR = PROJECT_ROOT / "train" / "output" / "ptbr_finetuned2"


def get_disk_space_gb(path: Path) -> tuple:
    """Retorna (total, usado, disponível) em GB"""
    stat = shutil.disk_usage(str(path))
    return (
        stat.total / (1024**3),
        stat.used / (1024**3),
        stat.free / (1024**3)
    )


def cleanup_old_checkpoints(output_dir: Path, keep_last_n: int = 3):
    """Remove checkpoints antigos mantendo apenas os últimos N"""
    
    # Listar checkpoints numerados (model_*.pt, exceto model_last.pt)
    checkpoints = sorted(
        [f for f in output_dir.glob("model_*.pt") if f.name != "model_last.pt"],
        key=lambda x: int(x.stem.split('_')[1]) if x.stem.split('_')[1].isdigit() else 0
    )
    
    if len(checkpoints) <= keep_last_n:
        logger.info(f"✓ {len(checkpoints)} checkpoints (ok, limite: {keep_last_n})")
        return 0
    
    # Remover os mais antigos
    to_remove = checkpoints[:-keep_last_n]
    freed_space_gb = 0
    
    for ckpt in to_remove:
        size_gb = ckpt.stat().st_size / (1024**3)
        ckpt.unlink()
        freed_space_gb += size_gb
        logger.info(f"🗑️  Removido: {ckpt.name} ({size_gb:.1f}GB)")
    
    logger.info(f"✅ Liberado: {freed_space_gb:.1f}GB")
    return freed_space_gb


def monitor_disk(
    output_dir: Path,
    threshold_gb: float = 20.0,
    keep_checkpoints: int = 3,
    interval_seconds: int = 60
):
    """
    Monitora espaço em disco continuamente
    
    Args:
        output_dir: Diretório de checkpoints
        threshold_gb: Limiar para limpeza automática
        keep_checkpoints: Número de checkpoints a manter
        interval_seconds: Intervalo de verificação
    """
    logger.info("=" * 60)
    logger.info("💾 MONITOR DE DISCO")
    logger.info("=" * 60)
    logger.info(f"Diretório: {output_dir}")
    logger.info(f"Limiar: {threshold_gb}GB")
    logger.info(f"Manter: {keep_checkpoints} checkpoints")
    logger.info(f"Intervalo: {interval_seconds}s")
    logger.info("=" * 60)
    
    try:
        while True:
            total_gb, used_gb, available_gb = get_disk_space_gb(output_dir)
            usage_pct = (used_gb / total_gb) * 100
            
            logger.info(
                f"💾 Disco: {available_gb:.1f}GB livres "
                f"({used_gb:.1f}/{total_gb:.1f}GB, {usage_pct:.1f}%)"
            )
            
            # Limpar se abaixo do threshold
            if available_gb < threshold_gb:
                logger.warning(f"⚠️  Espaço baixo! ({available_gb:.1f}GB < {threshold_gb}GB)")
                freed = cleanup_old_checkpoints(output_dir, keep_checkpoints)
                
                if freed > 0:
                    # Re-verificar
                    _, _, available_gb = get_disk_space_gb(output_dir)
                    logger.info(f"✅ Espaço após limpeza: {available_gb:.1f}GB")
                else:
                    logger.warning("⚠️  Nenhum checkpoint para remover!")
            
            # Verificar espaço crítico
            if available_gb < 10.0:
                logger.error(f"❌ CRÍTICO: Apenas {available_gb:.1f}GB disponível!")
                logger.error("   Considere:")
                logger.error("   1. Parar treinamento temporariamente")
                logger.error("   2. Liberar espaço manualmente")
                logger.error("   3. Reduzir keep_last_n_checkpoints")
            
            time.sleep(interval_seconds)
            
    except KeyboardInterrupt:
        logger.info("\n⚠️  Monitor interrompido")
    except Exception as e:
        logger.error(f"❌ Erro: {e}")
        import traceback
        traceback.print_exc()


def main():
    parser = argparse.ArgumentParser(description="Monitor de espaço em disco")
    parser.add_argument(
        '--threshold',
        type=float,
        default=20.0,
        help='Limiar em GB para limpeza automática (padrão: 20)'
    )
    parser.add_argument(
        '--keep',
        type=int,
        default=3,
        help='Número de checkpoints a manter (padrão: 3)'
    )
    parser.add_argument(
        '--interval',
        type=int,
        default=60,
        help='Intervalo de verificação em segundos (padrão: 60)'
    )
    parser.add_argument(
        '--output-dir',
        type=str,
        default=None,
        help='Diretório de output (padrão: train/output/ptbr_finetuned2)'
    )
    
    args = parser.parse_args()
    
    # Output directory
    if args.output_dir:
        output_dir = Path(args.output_dir)
    else:
        output_dir = OUTPUT_DIR
    
    if not output_dir.exists():
        logger.error(f"❌ Diretório não encontrado: {output_dir}")
        return
    
    # Iniciar monitor
    monitor_disk(
        output_dir=output_dir,
        threshold_gb=args.threshold,
        keep_checkpoints=args.keep,
        interval_seconds=args.interval
    )


if __name__ == "__main__":
    main()
