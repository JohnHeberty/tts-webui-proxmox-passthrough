#!/usr/bin/env python3
"""
Script de migração e comparação entre versões de segmentação

Funcionalidades:
1. Compara resultados entre V2 e V3
2. Valida consistência dos segmentos
3. Migra metadata se necessário
4. Gera relatório de diferenças

Uso:
    python3 train/scripts/migrate_segmentation.py --compare
    python3 train/scripts/migrate_segmentation.py --validate
"""

import argparse
import json
import logging
from pathlib import Path
from typing import Dict, List, Tuple
from collections import defaultdict

# Setup
project_root = Path(__file__).parent.parent.parent
logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)


def load_segments_mapping(mapping_file: Path) -> List[Dict]:
    """Carrega mapeamento de segmentos"""
    if not mapping_file.exists():
        logger.error(f"Arquivo não encontrado: {mapping_file}")
        return []
    
    with open(mapping_file, 'r', encoding='utf-8') as f:
        return json.load(f)


def compare_segments(
    segments_a: List[Dict],
    segments_b: List[Dict],
    name_a: str = "V2",
    name_b: str = "V3"
) -> Dict:
    """
    Compara dois conjuntos de segmentos
    
    Returns:
        Dict com estatísticas de comparação
    """
    logger.info(f"\n{'='*60}")
    logger.info(f"COMPARAÇÃO: {name_a} vs {name_b}")
    logger.info(f"{'='*60}")
    
    # Agrupar por arquivo original
    files_a = defaultdict(list)
    files_b = defaultdict(list)
    
    for seg in segments_a:
        files_a[seg['original_file']].append(seg)
    
    for seg in segments_b:
        files_b[seg['original_file']].append(seg)
    
    # Estatísticas gerais
    total_a = len(segments_a)
    total_b = len(segments_b)
    
    durations_a = [s['duration'] for s in segments_a]
    durations_b = [s['duration'] for s in segments_b]
    
    avg_duration_a = sum(durations_a) / len(durations_a) if durations_a else 0
    avg_duration_b = sum(durations_b) / len(durations_b) if durations_b else 0
    
    logger.info(f"\n📊 ESTATÍSTICAS GERAIS:")
    logger.info(f"  {name_a}: {total_a} segmentos, duração média {avg_duration_a:.2f}s")
    logger.info(f"  {name_b}: {total_b} segmentos, duração média {avg_duration_b:.2f}s")
    logger.info(f"  Diferença: {total_b - total_a:+d} segmentos ({((total_b/total_a - 1)*100):+.1f}%)")
    
    # Comparação por arquivo
    logger.info(f"\n📁 COMPARAÇÃO POR ARQUIVO:")
    
    all_files = sorted(set(files_a.keys()) | set(files_b.keys()))
    
    significant_diffs = []
    
    for filename in all_files:
        segs_a = files_a.get(filename, [])
        segs_b = files_b.get(filename, [])
        
        count_a = len(segs_a)
        count_b = len(segs_b)
        
        if count_a == 0 or count_b == 0:
            logger.warning(f"  ⚠️  {filename}: {name_a}={count_a}, {name_b}={count_b}")
            continue
        
        diff_pct = ((count_b / count_a) - 1) * 100
        
        if abs(diff_pct) > 10:  # Diferença significativa > 10%
            significant_diffs.append((filename, count_a, count_b, diff_pct))
            logger.warning(f"  ⚠️  {filename}: {count_a} → {count_b} ({diff_pct:+.1f}%)")
        else:
            logger.info(f"  ✓ {filename}: {count_a} → {count_b} ({diff_pct:+.1f}%)")
    
    # Resumo de diferenças
    if significant_diffs:
        logger.warning(f"\n⚠️  {len(significant_diffs)} arquivos com diferença > 10%:")
        for filename, ca, cb, pct in significant_diffs[:5]:  # Top 5
            logger.warning(f"    {filename}: {ca} → {cb} ({pct:+.1f}%)")
    else:
        logger.info(f"\n✅ Todas as diferenças < 10%")
    
    # Análise de duração
    logger.info(f"\n⏱️  ANÁLISE DE DURAÇÃO:")
    
    min_a, max_a = min(durations_a), max(durations_a)
    min_b, max_b = min(durations_b), max(durations_b)
    
    logger.info(f"  {name_a}: min={min_a:.2f}s, max={max_a:.2f}s, avg={avg_duration_a:.2f}s")
    logger.info(f"  {name_b}: min={min_b:.2f}s, max={max_b:.2f}s, avg={avg_duration_b:.2f}s")
    
    return {
        'total_a': total_a,
        'total_b': total_b,
        'diff_count': total_b - total_a,
        'diff_pct': ((total_b / total_a) - 1) * 100 if total_a > 0 else 0,
        'avg_duration_a': avg_duration_a,
        'avg_duration_b': avg_duration_b,
        'significant_diffs': len(significant_diffs)
    }


def validate_segments(segments: List[Dict], data_dir: Path) -> Tuple[int, int]:
    """
    Valida integridade dos segmentos
    
    Returns:
        (num_valid, num_invalid)
    """
    logger.info(f"\n{'='*60}")
    logger.info(f"VALIDAÇÃO DE SEGMENTOS")
    logger.info(f"{'='*60}")
    
    valid = 0
    invalid = 0
    missing_files = []
    invalid_durations = []
    
    for seg in segments:
        audio_path = data_dir / seg['audio_path']
        
        # Verificar existência
        if not audio_path.exists():
            invalid += 1
            missing_files.append(seg['audio_path'])
            continue
        
        # Verificar duração
        duration = seg.get('duration', 0)
        if duration < 1.0 or duration > 30.0:
            invalid += 1
            invalid_durations.append((seg['audio_path'], duration))
            continue
        
        valid += 1
    
    logger.info(f"\n📊 RESULTADOS:")
    logger.info(f"  ✓ Válidos: {valid}")
    logger.info(f"  ✗ Inválidos: {invalid}")
    
    if missing_files:
        logger.error(f"\n❌ {len(missing_files)} arquivos não encontrados:")
        for path in missing_files[:5]:
            logger.error(f"    {path}")
        if len(missing_files) > 5:
            logger.error(f"    ... e mais {len(missing_files) - 5}")
    
    if invalid_durations:
        logger.warning(f"\n⚠️  {len(invalid_durations)} durações inválidas:")
        for path, dur in invalid_durations[:5]:
            logger.warning(f"    {path}: {dur:.2f}s")
        if len(invalid_durations) > 5:
            logger.warning(f"    ... e mais {len(invalid_durations) - 5}")
    
    return valid, invalid


def generate_report(
    comparison: Dict,
    validation_v2: Tuple[int, int],
    validation_v3: Tuple[int, int],
    output_file: Path
):
    """Gera relatório de migração"""
    
    report = f"""# Relatório de Migração de Segmentação

## Resumo Executivo

### Comparação V2 vs V3

- **Total de Segmentos:**
  - V2: {comparison['total_a']:,}
  - V3: {comparison['total_b']:,}
  - Diferença: {comparison['diff_count']:+,} ({comparison['diff_pct']:+.1f}%)

- **Duração Média:**
  - V2: {comparison['avg_duration_a']:.2f}s
  - V3: {comparison['avg_duration_b']:.2f}s

- **Arquivos com Diferença Significativa (>10%):** {comparison['significant_diffs']}

### Validação de Integridade

#### V2
- Válidos: {validation_v2[0]:,}
- Inválidos: {validation_v2[1]:,}
- Taxa de sucesso: {(validation_v2[0]/(validation_v2[0]+validation_v2[1])*100):.1f}%

#### V3
- Válidos: {validation_v3[0]:,}
- Inválidos: {validation_v3[1]:,}
- Taxa de sucesso: {(validation_v3[0]/(validation_v3[0]+validation_v3[1])*100):.1f}%

## Recomendações

"""
    
    if comparison['diff_pct'] > 5:
        report += "⚠️  **ATENÇÃO:** Diferença significativa no número de segmentos (>5%)\n"
        report += "   - Revisar configurações de VAD\n"
        report += "   - Comparar qualidade de áudio dos segmentos\n\n"
    elif comparison['diff_pct'] < -5:
        report += "⚠️  **ATENÇÃO:** V3 gerou menos segmentos que V2 (-5%)\n"
        report += "   - Verificar se VAD está muito restritivo\n"
        report += "   - Ajustar vad_threshold no config\n\n"
    else:
        report += "✅ **OK:** Diferença no número de segmentos está dentro do esperado (<5%)\n\n"
    
    if validation_v3[1] > validation_v2[1]:
        report += "⚠️  **ATENÇÃO:** V3 tem mais segmentos inválidos que V2\n"
        report += "   - Revisar processo de geração\n\n"
    else:
        report += "✅ **OK:** V3 mantém ou melhora qualidade de validação\n\n"
    
    report += """## Próximos Passos

1. Revisar arquivos com diferenças significativas
2. Validar qualidade de áudio manualmente (ouvir samples)
3. Se tudo OK, migrar completamente para V3
4. Documentar configurações usadas

---
*Relatório gerado automaticamente*
"""
    
    output_file.write_text(report, encoding='utf-8')
    logger.info(f"\n📄 Relatório salvo em: {output_file}")


def main():
    parser = argparse.ArgumentParser(description="Migração e comparação de segmentação")
    parser.add_argument('--compare', action='store_true', help='Comparar V2 vs V3')
    parser.add_argument('--validate', action='store_true', help='Validar integridade')
    parser.add_argument('--report', type=str, help='Gerar relatório (path)')
    args = parser.parse_args()
    
    data_dir = project_root / "train" / "data"
    processed_dir = data_dir / "processed"
    
    # Arquivos de mapping
    mapping_v2 = processed_dir / "segments_mapping_v2.json"
    mapping_v3 = processed_dir / "segments_mapping.json"
    
    # Se não existir v2, tentar o padrão
    if not mapping_v2.exists():
        mapping_v2 = processed_dir / "segments_mapping.json"
    
    if args.compare:
        if not mapping_v2.exists():
            logger.error(f"Mapping V2 não encontrado: {mapping_v2}")
            return
        
        if not mapping_v3.exists():
            logger.error(f"Mapping V3 não encontrado: {mapping_v3}")
            return
        
        segments_v2 = load_segments_mapping(mapping_v2)
        segments_v3 = load_segments_mapping(mapping_v3)
        
        comparison = compare_segments(segments_v2, segments_v3)
        
        # Validação
        validation_v2 = (0, 0)
        validation_v3 = (0, 0)
        
        if args.validate:
            validation_v2 = validate_segments(segments_v2, data_dir)
            validation_v3 = validate_segments(segments_v3, data_dir)
        
        # Relatório
        if args.report:
            report_path = Path(args.report)
            generate_report(comparison, validation_v2, validation_v3, report_path)
    
    elif args.validate:
        # Validar apenas V3 (padrão)
        if not mapping_v3.exists():
            logger.error(f"Mapping não encontrado: {mapping_v3}")
            return
        
        segments = load_segments_mapping(mapping_v3)
        validate_segments(segments, data_dir)
    
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
