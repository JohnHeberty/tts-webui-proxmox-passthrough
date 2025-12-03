#!/usr/bin/env python3
"""
Normaliza todas as transcrições convertendo números e símbolos para forma falada.

Este script:
1. Carrega transcrições existentes
2. Aplica normalização de texto (números, %, moeda, etc)
3. Salva versão normalizada
4. Cria backup do original

Uso:
    python -m train.scripts.normalize_transcriptions
"""

import json
import logging
import shutil
from pathlib import Path
from datetime import datetime
import sys

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from train.utils.text_normalizer import TextNormalizer

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def main():
    """Função principal."""
    base_path = Path("/home/tts-webui-proxmox-passthrough/train")
    transcriptions_path = base_path / "data/processed/transcriptions.json"
    
    if not transcriptions_path.exists():
        logger.error(f"❌ Arquivo não encontrado: {transcriptions_path}")
        return
    
    logger.info("=" * 80)
    logger.info("📝 NORMALIZAÇÃO DE TRANSCRIÇÕES")
    logger.info("=" * 80)
    
    # Criar backup
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_path = transcriptions_path.parent / f"transcriptions_backup_{timestamp}.json"
    
    logger.info(f"\n💾 Criando backup: {backup_path.name}")
    shutil.copy2(transcriptions_path, backup_path)
    
    # Carregar transcrições
    logger.info(f"\n📂 Carregando transcrições...")
    with open(transcriptions_path, 'r', encoding='utf-8') as f:
        transcriptions = json.load(f)
    
    logger.info(f"   Total: {len(transcriptions)} transcrições")
    
    # Inicializar normalizador
    normalizer = TextNormalizer(lang='pt_BR')
    
    # Estatísticas
    stats = {
        'total': len(transcriptions),
        'normalized': 0,
        'unchanged': 0,
        'with_numbers': 0,
        'with_percentage': 0,
        'with_currency': 0,
        'with_symbols': 0,
    }
    
    # Normalizar cada transcrição
    logger.info(f"\n🔄 Normalizando transcrições...")
    
    for i, item in enumerate(transcriptions, 1):
        original_text = item['text']
        normalized_text = normalizer.normalize(original_text)
        
        # Detectar tipos de normalização aplicados
        if original_text != normalized_text:
            stats['normalized'] += 1
            
            # Analisar o que foi normalizado
            import re
            if re.search(r'\d+', original_text):
                stats['with_numbers'] += 1
            if '%' in original_text:
                stats['with_percentage'] += 1
            if 'R$' in original_text or '$' in original_text:
                stats['with_currency'] += 1
            if any(s in original_text for s in ['&', '@', '#', '/', '\\']):
                stats['with_symbols'] += 1
            
            # Mostrar alguns exemplos
            if stats['normalized'] <= 5:
                logger.info(f"\n   Exemplo {stats['normalized']}:")
                logger.info(f"   Original:    {original_text[:80]}...")
                logger.info(f"   Normalizado: {normalized_text[:80]}...")
        else:
            stats['unchanged'] += 1
        
        # Atualizar item
        item['text'] = normalized_text
        item['text_original'] = original_text  # Preservar original
        item['normalized'] = True
        
        # Progresso
        if i % 100 == 0:
            logger.info(f"   Progresso: {i}/{len(transcriptions)} ({i/len(transcriptions)*100:.1f}%)")
    
    # Salvar transcrições normalizadas
    logger.info(f"\n💾 Salvando transcrições normalizadas...")
    with open(transcriptions_path, 'w', encoding='utf-8') as f:
        json.dump(transcriptions, f, ensure_ascii=False, indent=2)
    
    # Relatório final
    logger.info(f"\n" + "=" * 80)
    logger.info("✅ NORMALIZAÇÃO CONCLUÍDA")
    logger.info("=" * 80)
    logger.info(f"\n📊 Estatísticas:")
    logger.info(f"   Total de transcrições: {stats['total']}")
    logger.info(f"   Normalizadas: {stats['normalized']} ({stats['normalized']/stats['total']*100:.1f}%)")
    logger.info(f"   Sem alteração: {stats['unchanged']} ({stats['unchanged']/stats['total']*100:.1f}%)")
    logger.info(f"\n📈 Tipos de normalização:")
    logger.info(f"   Com números: {stats['with_numbers']}")
    logger.info(f"   Com percentuais: {stats['with_percentage']}")
    logger.info(f"   Com moeda: {stats['with_currency']}")
    logger.info(f"   Com símbolos: {stats['with_symbols']}")
    logger.info(f"\n📁 Arquivos:")
    logger.info(f"   Transcrições: {transcriptions_path}")
    logger.info(f"   Backup: {backup_path}")
    logger.info("=" * 80)


if __name__ == "__main__":
    main()
