#!/usr/bin/env python3
"""
Download do modelo F5-TTS pt-br do HuggingFace

Baixa o modelo pré-treinado firstpixel/F5-TTS-pt-br para usar como ponto de partida
no fine-tuning.
"""

import logging
from pathlib import Path
from huggingface_hub import hf_hub_download
import shutil

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def download_model():
    """Baixa modelo F5-TTS pt-br do HuggingFace"""
    
    model_id = "firstpixel/F5-TTS-pt-br"
    output_dir = Path("/home/tts-webui-proxmox-passthrough/models/f5tts/pt-br")
    output_dir.mkdir(parents=True, exist_ok=True)
    
    logger.info("=" * 80)
    logger.info("DOWNLOAD MODELO F5-TTS PT-BR")
    logger.info("=" * 80)
    logger.info(f"Modelo: {model_id}")
    logger.info(f"Destino: {output_dir}")
    
    # Arquivos necessários
    files = [
        "pt-br/model_last.safetensors",
        "pt-br/model_last.pt",
    ]
    
    for filename in files:
        logger.info(f"\n📥 Baixando: {filename}")
        
        try:
            # Download do HuggingFace Hub
            downloaded_path = hf_hub_download(
                repo_id=model_id,
                filename=filename,
                cache_dir=None,  # Usa cache padrão
                force_download=False  # Usa cache se disponível
            )
            
            # Copiar para diretório de modelos
            dest_path = output_dir / Path(filename).name  # Usar apenas o nome do arquivo
            shutil.copy2(downloaded_path, dest_path)
            
            logger.info(f"   ✅ Salvo em: {dest_path}")
            
        except Exception as e:
            logger.warning(f"   ⚠️  Erro ao baixar {filename}: {e}")
            logger.warning(f"   Continuando...")
    
    logger.info("\n" + "=" * 80)
    logger.info("✅ DOWNLOAD CONCLUÍDO")
    logger.info("=" * 80)
    logger.info(f"Modelo disponível em: {output_dir}")
    logger.info("\nArquivos:")
    for f in output_dir.glob("*"):
        size = f.stat().st_size / (1024**2)  # MB
        logger.info(f"  - {f.name} ({size:.1f} MB)")

if __name__ == "__main__":
    download_model()
