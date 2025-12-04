#!/usr/bin/env python3
"""
Converte checkpoint PyTorch (.pt) para SafeTensors (.safetensors)

Este script:
1. Carrega checkpoint .pt do F5-TTS
2. Extrai model_state_dict e ema_model_state_dict
3. Salva em formato SafeTensors (mais seguro e eficiente)
4. Preserva metadados importantes (epoch, step, etc)

Uso:
    python -m train.scripts.convert_to_safetensors
    
    # Ou especificar checkpoint:
    python -m train.scripts.convert_to_safetensors --checkpoint /path/to/model_last.pt

SafeTensors vs PyTorch:
    ✅ Mais rápido para carregar
    ✅ Mais seguro (não executa código arbitrário)
    ✅ Interoperável (Rust, Python, JS)
    ✅ Menor tamanho em disco
    ✅ Suporte nativo em HuggingFace
"""

import torch
import argparse
import logging
import sys
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, Optional

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from train.utils.env_loader import get_training_config

try:
    from safetensors.torch import save_file, load_file
except ImportError:
    print("❌ safetensors não instalado!")
    print("Instale com: pip install safetensors")
    sys.exit(1)

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def load_checkpoint(checkpoint_path: Path) -> Dict[str, Any]:
    """
    Carrega checkpoint PyTorch
    
    Args:
        checkpoint_path: Caminho para o arquivo .pt
        
    Returns:
        Dict com checkpoint completo
    """
    logger.info(f"📥 Carregando checkpoint: {checkpoint_path}")
    
    try:
        checkpoint = torch.load(
            checkpoint_path, 
            map_location='cpu',
            weights_only=False  # Necessário para F5-TTS
        )
        
        logger.info(f"✅ Checkpoint carregado com sucesso")
        logger.info(f"   Keys: {list(checkpoint.keys())}")
        
        return checkpoint
        
    except Exception as e:
        logger.error(f"❌ Erro ao carregar checkpoint: {e}")
        raise


def extract_state_dicts(checkpoint: Dict[str, Any]) -> Dict[str, torch.Tensor]:
    """
    Extrai state_dicts do checkpoint F5-TTS
    
    Args:
        checkpoint: Checkpoint completo
        
    Returns:
        Dict unificado com todos os tensores
    """
    state_dicts = {}
    
    # 1. Model principal
    if 'model_state_dict' in checkpoint:
        logger.info("📦 Extraindo model_state_dict...")
        model_dict = checkpoint['model_state_dict']
        
        for key, tensor in model_dict.items():
            if isinstance(tensor, torch.Tensor):
                state_dicts[f"model.{key}"] = tensor
        
        logger.info(f"   ✅ {len(model_dict)} parâmetros extraídos")
    
    # 2. EMA model (mais importante para inferência)
    if 'ema_model_state_dict' in checkpoint:
        logger.info("📦 Extraindo ema_model_state_dict...")
        ema_dict = checkpoint['ema_model_state_dict']
        
        for key, tensor in ema_dict.items():
            if isinstance(tensor, torch.Tensor):
                # Remover prefixo 'ema_model.' se existir
                clean_key = key.replace('ema_model.', '')
                state_dicts[f"ema.{clean_key}"] = tensor
        
        logger.info(f"   ✅ {len(ema_dict)} parâmetros extraídos")
    
    # 3. Optimizer (opcional, geralmente muito grande)
    # Não incluímos por padrão para reduzir tamanho
    
    if not state_dicts:
        logger.warning("⚠️  Nenhum state_dict encontrado!")
        logger.info("Estrutura do checkpoint:")
        for key in checkpoint.keys():
            logger.info(f"  - {key}: {type(checkpoint[key])}")
    
    return state_dicts


def create_metadata(checkpoint: Dict[str, Any]) -> Dict[str, str]:
    """
    Cria metadados para SafeTensors
    
    Args:
        checkpoint: Checkpoint completo
        
    Returns:
        Dict com metadados (apenas strings)
    """
    metadata = {
        "format": "f5-tts-safetensors",
        "converted_at": datetime.now().isoformat(),
        "original_format": "pytorch",
    }
    
    # Adicionar informações do checkpoint
    if 'update' in checkpoint:
        metadata['training_step'] = str(checkpoint['update'])
    
    if 'epoch' in checkpoint:
        metadata['epoch'] = str(checkpoint['epoch'])
    
    # Contar parâmetros
    if 'ema_model_state_dict' in checkpoint:
        ema_dict = checkpoint['ema_model_state_dict']
        total_params = sum(
            p.numel() for p in ema_dict.values() 
            if isinstance(p, torch.Tensor)
        )
        metadata['total_parameters'] = str(total_params)
        metadata['total_parameters_millions'] = f"{total_params / 1e6:.1f}M"
    
    logger.info("📋 Metadados criados:")
    for key, value in metadata.items():
        logger.info(f"   {key}: {value}")
    
    return metadata


def convert_checkpoint_to_safetensors(
    checkpoint_path: Path,
    output_path: Optional[Path] = None
) -> Path:
    """
    Converte checkpoint .pt para .safetensors
    
    Args:
        checkpoint_path: Caminho para o arquivo .pt
        output_path: Caminho de saída (opcional)
        
    Returns:
        Path do arquivo .safetensors criado
    """
    logger.info("=" * 80)
    logger.info("🔄 CONVERSÃO PT → SAFETENSORS")
    logger.info("=" * 80)
    
    # 1. Definir output path
    if output_path is None:
        output_path = checkpoint_path.with_suffix('.safetensors')
    
    logger.info(f"\n📁 Arquivos:")
    logger.info(f"   Input:  {checkpoint_path}")
    logger.info(f"   Output: {output_path}")
    
    # 2. Verificar se input existe
    if not checkpoint_path.exists():
        raise FileNotFoundError(f"Checkpoint não encontrado: {checkpoint_path}")
    
    # 3. Verificar tamanho do arquivo
    size_mb = checkpoint_path.stat().st_size / (1024 * 1024)
    logger.info(f"\n📊 Tamanho do checkpoint: {size_mb:.1f} MB")
    
    # 4. Carregar checkpoint
    checkpoint = load_checkpoint(checkpoint_path)
    
    # 5. Extrair state dicts
    logger.info("\n🔧 Extraindo state dicts...")
    state_dicts = extract_state_dicts(checkpoint)
    
    if not state_dicts:
        raise ValueError("Nenhum tensor encontrado no checkpoint!")
    
    logger.info(f"\n📊 Total de tensores: {len(state_dicts)}")
    
    # Calcular tamanho total
    total_params = sum(t.numel() for t in state_dicts.values())
    logger.info(f"📊 Total de parâmetros: {total_params / 1e6:.1f}M")
    
    # 6. Criar metadados
    logger.info("\n📋 Criando metadados...")
    metadata = create_metadata(checkpoint)
    
    # 7. Salvar em SafeTensors
    logger.info(f"\n💾 Salvando SafeTensors...")
    try:
        save_file(
            state_dicts,
            output_path,
            metadata=metadata
        )
        logger.info(f"✅ Arquivo salvo com sucesso!")
        
    except Exception as e:
        logger.error(f"❌ Erro ao salvar: {e}")
        raise
    
    # 8. Verificar arquivo de saída
    if output_path.exists():
        output_size_mb = output_path.stat().st_size / (1024 * 1024)
        logger.info(f"\n📊 Tamanho do SafeTensors: {output_size_mb:.1f} MB")
        
        # Comparar tamanhos
        reduction = ((size_mb - output_size_mb) / size_mb) * 100
        if reduction > 0:
            logger.info(f"💾 Redução de tamanho: {reduction:.1f}%")
        else:
            logger.info(f"📈 Aumento de tamanho: {abs(reduction):.1f}%")
    
    # 9. Validar arquivo salvo
    logger.info("\n🔍 Validando arquivo salvo...")
    try:
        loaded = load_file(output_path)
        logger.info(f"✅ Validação OK: {len(loaded)} tensores carregados")
        
        # Verificar alguns tensores aleatoriamente
        import random
        sample_keys = random.sample(list(loaded.keys()), min(3, len(loaded)))
        logger.info(f"📋 Amostra de tensores:")
        for key in sample_keys:
            tensor = loaded[key]
            logger.info(f"   {key}: {tuple(tensor.shape)}")
        
    except Exception as e:
        logger.error(f"❌ Erro na validação: {e}")
        raise
    
    logger.info("\n" + "=" * 80)
    logger.info("✅ CONVERSÃO CONCLUÍDA COM SUCESSO!")
    logger.info("=" * 80)
    
    return output_path


def main():
    """Função principal"""
    parser = argparse.ArgumentParser(
        description='Converte checkpoint F5-TTS (.pt) para SafeTensors (.safetensors)',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Exemplos:
    # Converter checkpoint padrão (model_last.pt)
    python -m train.scripts.convert_to_safetensors
    
    # Converter checkpoint específico
    python -m train.scripts.convert_to_safetensors --checkpoint train/output/ptbr_finetuned/model_50000.pt
    
    # Especificar saída
    python -m train.scripts.convert_to_safetensors --checkpoint model_last.pt --output modelo_ptbr.safetensors
        """
    )
    
    parser.add_argument(
        '--checkpoint',
        type=Path,
        help='Caminho para o checkpoint .pt (default: usa F5TTS_CKPTS_DIR/TRAIN_DATASET_NAME/model_last.pt)'
    )
    
    parser.add_argument(
        '--output',
        type=Path,
        help='Caminho de saída .safetensors (default: mesmo nome com extensão .safetensors)'
    )
    
    args = parser.parse_args()
    
    # Carregar configuração
    config = get_training_config()
    
    # Determinar checkpoint path
    if args.checkpoint:
        checkpoint_path = args.checkpoint
    else:
        # Usar configuração padrão
        ckpts_dir = config.get('f5tts_ckpts_dir', '/root/.local/lib/python3.11/ckpts')
        dataset_name = config.get('train_dataset_name', 'f5_dataset')
        checkpoint_path = Path(f"{ckpts_dir}/{dataset_name}/model_last.pt")
    
    # Converter para Path absoluto
    checkpoint_path = checkpoint_path.resolve()
    
    # Determinar output path
    output_path = args.output.resolve() if args.output else None
    
    try:
        # Executar conversão
        output_file = convert_checkpoint_to_safetensors(
            checkpoint_path,
            output_path
        )
        
        logger.info(f"\n🎉 Arquivo SafeTensors criado:")
        logger.info(f"   {output_file}")
        
        logger.info(f"\n💡 Para usar este modelo:")
        logger.info(f"   from safetensors.torch import load_file")
        logger.info(f"   tensors = load_file('{output_file}')")
        
    except Exception as e:
        logger.error(f"\n❌ Erro na conversão: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
