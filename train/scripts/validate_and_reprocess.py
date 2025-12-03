#!/usr/bin/env python3
"""
Valida transcrições e reprocessa áudios problemáticos com modelo mais preciso.

Detecta:
- Palavras repetidas excessivamente (>4x)
- Caracteres inválidos (%, /, \, etc)
- Letras isoladas com pontuação
- Palavras não-portuguesas
- Padrões anormais
"""

import json
import re
import logging
from pathlib import Path
from typing import Dict, List, Set, Tuple
from collections import Counter
import whisper
import torch
import gc

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Vocabulário base português (palavras mais comuns)
PORTUGUESE_COMMON_WORDS = {
    'a', 'o', 'e', 'de', 'da', 'do', 'em', 'um', 'uma', 'os', 'as', 'dos', 'das',
    'para', 'com', 'não', 'que', 'se', 'na', 'no', 'por', 'mais', 'ou', 'mas',
    'eu', 'você', 'ele', 'ela', 'nós', 'eles', 'elas', 'seu', 'sua', 'meu', 'minha',
    'é', 'são', 'foi', 'ser', 'estar', 'ter', 'fazer', 'ir', 'ver', 'dar', 'saber',
    'pode', 'vai', 'tem', 'está', 'esse', 'isso', 'aqui', 'ali', 'onde', 'quando',
    'como', 'porque', 'muito', 'bem', 'só', 'já', 'ainda', 'também', 'sempre',
    'nunca', 'todo', 'tudo', 'nada', 'algo', 'alguém', 'ninguém', 'cada', 'outro',
    'dia', 'vez', 'ano', 'casa', 'tempo', 'pessoa', 'coisa', 'vida', 'mundo',
    'cara', 'gente', 'banco', 'dinheiro', 'real', 'reais', 'brasil', 'brasileiro',
    'empresa', 'negócio', 'mercado', 'sistema', 'forma', 'caso', 'momento', 'hora',
    'pra', 'pro', 'né', 'tá', 'tô', 'tô', 'vou', 'vai', 'vamos', 'tipo', 'legal'
}

# Caracteres permitidos
ALLOWED_CHARS = set('abcdefghijklmnopqrstuvwxyzáàâãéêíóôõúçABCDEFGHIJKLMNOPQRSTUVWXYZÁÀÂÃÉÊÍÓÔÕÚÇ0123456789 .,!?-')

class TranscriptionValidator:
    """Valida qualidade das transcrições."""
    
    def __init__(self, portuguese_words: Set[str] = None):
        self.portuguese_words = portuguese_words or PORTUGUESE_COMMON_WORDS
        self.issues_found = []
    
    def validate(self, text: str, filename: str) -> Tuple[bool, List[str]]:
        """
        Valida um texto transcrito.
        
        Returns:
            (is_valid, list_of_issues)
        """
        issues = []
        
        # 1. Verificar caracteres inválidos
        invalid_chars = set(text) - ALLOWED_CHARS
        if invalid_chars:
            issues.append(f"Caracteres inválidos: {invalid_chars}")
        
        # 2. Verificar repetições excessivas
        words = text.split()
        if len(words) > 3:
            word_counts = Counter(words)
            for word, count in word_counts.items():
                if count >= 5 and len(word) > 3:
                    issues.append(f"Palavra '{word}' repetida {count}x (suspeito)")
        
        # 3. Verificar letras isoladas com pontuação
        isolated_pattern = re.findall(r'\b[a-zA-Z]\s*[.,;:]\s*', text)
        if isolated_pattern:
            issues.append(f"Letras isoladas com pontuação: {isolated_pattern}")
        
        # 4. Verificar palavras muito longas (>20 chars - provavelmente erro)
        long_words = [w for w in words if len(w) > 20]
        if long_words:
            issues.append(f"Palavras muito longas: {long_words}")
        
        # 5. Verificar se texto é muito curto (<3 palavras)
        if len(words) < 3:
            issues.append(f"Texto muito curto: apenas {len(words)} palavras")
        
        # 6. Verificar sequências repetidas (ex: "pra, pra, pra, pra,")
        text_normalized = ' '.join(words)
        # Detectar sequências de 2-3 palavras repetidas 3+ vezes
        for seq_len in [2, 3]:
            for i in range(len(words) - seq_len * 3):
                seq = ' '.join(words[i:i+seq_len])
                pattern = (seq + ' ') * 3
                if pattern in text_normalized:
                    issues.append(f"Sequência repetida 3+x: '{seq}'")
                    break
        
        # 7. Verificar proporção de palavras não-portuguesas
        unknown_words = [w for w in words if len(w) > 3 and w.lower() not in self.portuguese_words and not w.isdigit()]
        if len(words) > 0:
            unknown_ratio = len(unknown_words) / len(words)
            if unknown_ratio > 0.7:  # >70% palavras desconhecidas
                issues.append(f"Muitas palavras desconhecidas: {unknown_ratio:.1%} ({unknown_words[:5]}...)")
        
        is_valid = len(issues) == 0
        
        if issues:
            self.issues_found.append({
                'filename': filename,
                'text': text[:100],
                'issues': issues
            })
        
        return is_valid, issues


def load_transcriptions(json_path: Path) -> Dict:
    """Carrega transcrições existentes."""
    if json_path.exists():
        with open(json_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    return []


def save_transcriptions(json_path: Path, data: List[Dict]):
    """Salva transcrições atualizadas."""
    with open(json_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def retranscribe_with_better_model(audio_path: Path, model_name: str = "medium") -> str:
    """
    Re-transcreve áudio com modelo mais preciso.
    
    Args:
        audio_path: Caminho do arquivo de áudio
        model_name: Nome do modelo Whisper (medium ou large)
    
    Returns:
        Texto transcrito
    """
    logger.info(f"   🔄 Re-transcrevendo com modelo '{model_name}': {audio_path.name}")
    
    device = "cuda" if torch.cuda.is_available() else "cpu"
    model = whisper.load_model(model_name, device=device)
    
    try:
        result = model.transcribe(
            str(audio_path),
            language="pt",
            task="transcribe",
            fp16=(device == "cuda"),
            temperature=0.0,  # Mais determinístico
            compression_ratio_threshold=2.4,
            logprob_threshold=-1.0,
            no_speech_threshold=0.6,
            condition_on_previous_text=False  # Evita repetições
        )
        
        text = result["text"].strip()
        
        # Pós-processamento
        text = text.lower()
        text = re.sub(r'\s+', ' ', text)  # Múltiplos espaços
        text = re.sub(r'\s+([.,!?])', r'\1', text)  # Espaço antes pontuação
        
        return text
        
    finally:
        # Limpar memória
        del model
        gc.collect()
        if device == "cuda":
            torch.cuda.empty_cache()


def main():
    """Função principal."""
    base_path = Path("/home/tts-webui-proxmox-passthrough/train")
    transcriptions_path = base_path / "data/processed/transcriptions.json"
    wavs_dir = base_path / "data/processed/wavs"
    
    logger.info("=" * 80)
    logger.info("🔍 VALIDAÇÃO E RE-PROCESSAMENTO DE TRANSCRIÇÕES")
    logger.info("=" * 80)
    
    # Carregar transcrições
    transcriptions = load_transcriptions(transcriptions_path)
    logger.info(f"📊 Total de transcrições: {len(transcriptions)}")
    
    # Validar todas as transcrições
    validator = TranscriptionValidator()
    invalid_items = []
    
    logger.info("\n🔍 Validando transcrições...")
    for item in transcriptions:
        # Extrair nome do arquivo do caminho
        audio_path = item.get('audio_path', '')
        filename = Path(audio_path).name if audio_path else f"segment_{item.get('segment_index', 0)}"
        text = item['text']
        
        is_valid, issues = validator.validate(text, filename)
        
        if not is_valid:
            invalid_items.append({
                'item': item,
                'issues': issues
            })
    
    logger.info(f"\n📈 Resultados da validação:")
    logger.info(f"   ✅ Válidas: {len(transcriptions) - len(invalid_items)}")
    logger.info(f"   ❌ Inválidas: {len(invalid_items)}")
    
    if len(invalid_items) == 0:
        logger.info("\n🎉 Todas as transcrições estão válidas!")
        return
    
    # Mostrar alguns exemplos de problemas
    logger.info(f"\n⚠️  Exemplos de problemas encontrados:")
    for i, invalid in enumerate(invalid_items[:5]):
        item = invalid['item']
        audio_path = item.get('audio_path', '')
        filename = Path(audio_path).name if audio_path else f"segment_{item.get('segment_index', 0)}"
        
        logger.info(f"\n{i+1}. {filename}")
        logger.info(f"   Texto: {item['text'][:100]}...")
        for issue in invalid['issues']:
            logger.info(f"   - {issue}")
    
    # Perguntar se deve re-processar
    logger.info(f"\n" + "=" * 80)
    logger.info(f"🔄 Re-processamento com modelo 'medium'")
    logger.info(f"=" * 80)
    logger.info(f"Total de áudios a re-processar: {len(invalid_items)}")
    logger.info(f"Modelo: whisper-medium (mais preciso que base)")
    logger.info(f"Tempo estimado: ~{len(invalid_items) * 3} segundos")
    
    response = input("\n❓ Deseja re-processar os áudios inválidos? [s/N]: ").strip().lower()
    
    if response != 's':
        logger.info("❌ Re-processamento cancelado pelo usuário.")
        
        # Salvar relatório de problemas
        report_path = base_path / "logs/validation_report.json"
        report_path.parent.mkdir(exist_ok=True)
        with open(report_path, 'w', encoding='utf-8') as f:
            json.dump(validator.issues_found, f, ensure_ascii=False, indent=2)
        logger.info(f"📄 Relatório salvo em: {report_path}")
        return
    
    # Re-processar áudios inválidos
    logger.info(f"\n🚀 Iniciando re-processamento...")
    reprocessed_count = 0
    
    for i, invalid in enumerate(invalid_items, 1):
        item = invalid['item']
        audio_path = item.get('audio_path', '')
        filename = Path(audio_path).name if audio_path else f"segment_{item.get('segment_index', 0)}"
        full_audio_path = wavs_dir / filename
        
        if not full_audio_path.exists():
            logger.warning(f"   ⚠️  Áudio não encontrado: {filename}")
            continue
        
        logger.info(f"\n[{i}/{len(invalid_items)}] Processando: {filename}")
        logger.info(f"   Problemas: {', '.join(invalid['issues'])}")
        logger.info(f"   Texto original: {item['text'][:80]}...")
        
        try:
            # Re-transcrever com modelo melhor
            new_text = retranscribe_with_better_model(full_audio_path, model_name="medium")
            
            # Validar novo texto
            is_valid, new_issues = validator.validate(new_text, filename)
            
            if is_valid:
                logger.info(f"   ✅ Novo texto válido: {new_text[:80]}...")
                
                # Atualizar na lista
                for orig_item in transcriptions:
                    orig_audio_path = orig_item.get('audio_path', '')
                    orig_filename = Path(orig_audio_path).name if orig_audio_path else ''
                    if orig_filename == filename:
                        orig_item['text'] = new_text
                        orig_item['reprocessed'] = True
                        orig_item['model'] = 'medium'
                        break
                
                reprocessed_count += 1
            else:
                logger.warning(f"   ⚠️  Novo texto ainda tem problemas: {new_issues}")
                logger.warning(f"   Texto: {new_text[:80]}...")
        
        except Exception as e:
            logger.error(f"   ❌ Erro ao re-processar: {e}")
    
    # Salvar transcrições atualizadas
    logger.info(f"\n💾 Salvando transcrições atualizadas...")
    save_transcriptions(transcriptions_path, transcriptions)
    
    logger.info(f"\n" + "=" * 80)
    logger.info(f"✅ RE-PROCESSAMENTO CONCLUÍDO")
    logger.info(f"=" * 80)
    logger.info(f"   Re-processados com sucesso: {reprocessed_count}/{len(invalid_items)}")
    logger.info(f"   Transcrições salvas em: {transcriptions_path}")


if __name__ == "__main__":
    main()
