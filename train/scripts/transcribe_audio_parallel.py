"""
Transcrição paralela de áudio usando Whisper (XTTS-v2)

Versão otimizada com:
- Processamento paralelo (múltiplos workers GPU)
- Auto-detecção de VRAM disponível
- Salvamento incremental (proteção contra crash)
- Resume automático (continua de onde parou)

Uso:
    # Auto-detect workers (baseado em VRAM)
    python -m train.scripts.transcribe_audio_parallel
    
    # Especificar workers manualmente
    WHISPER_NUM_WORKERS=4 python -m train.scripts.transcribe_audio_parallel
    
    # Single worker (fallback)
    WHISPER_NUM_WORKERS=1 python -m train.scripts.transcribe_audio_parallel

Dependências:
    - torch: pip install torch
    - whisper: pip install openai-whisper
    - num2words: pip install num2words
"""

import json
import logging
import sys
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import List, Dict, Optional
import time

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

# Import original functions from transcribe_audio
from train.scripts.transcribe_audio import (
    preprocess_text,
    _should_retry_with_high_precision,
)

# Import env config
from train.env_config import (
    WHISPER_NUM_WORKERS,
    WHISPER_DEVICE,
    WHISPER_MODEL,
    DATA_DIR,
    LOGS_DIR,
)

try:
    import yaml
    import whisper
    import torch
except ImportError as e:
    print(f"❌ Dependência não encontrada: {e}")
    print("Instale com: pip install openai-whisper pyyaml torch")
    sys.exit(1)

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - [Worker %(worker_id)s] %(message)s",
    handlers=[
        logging.FileHandler(project_root / LOGS_DIR / "transcribe_parallel.log"),
        logging.StreamHandler(),
    ],
)
logger = logging.getLogger(__name__)

# Global model pool (one model per worker)
_MODEL_POOL: List[whisper.Whisper] = []
_MODEL_POOL_LOCK = None


def init_model_pool(num_workers: int, model_name: str, device: str):
    """Initialize pool of Whisper models (one per worker)"""
    global _MODEL_POOL, _MODEL_POOL_LOCK
    
    import threading
    _MODEL_POOL_LOCK = threading.Lock()
    
    logger.info(f"🎤 Inicializando {num_workers} modelos Whisper ({model_name})...")
    
    for i in range(num_workers):
        try:
            # Each worker gets its own model instance
            model = whisper.load_model(model_name, device=device)
            _MODEL_POOL.append(model)
            logger.info(f"   ✅ Worker {i+1}/{num_workers} pronto")
        except Exception as e:
            logger.error(f"   ❌ Erro ao carregar modelo {i+1}: {e}")
            raise
    
    logger.info(f"✅ Pool de {len(_MODEL_POOL)} modelos inicializado\n")


def get_model_from_pool(worker_id: int) -> whisper.Whisper:
    """Get model for specific worker"""
    return _MODEL_POOL[worker_id % len(_MODEL_POOL)]


def transcribe_segment_worker(
    worker_id: int,
    segment: Dict,
    config: Dict,
    high_precision: bool = False
) -> Optional[Dict]:
    """
    Transcreve um segmento (executado por worker)
    
    Args:
        worker_id: ID do worker (0-N)
        segment: Dados do segmento
        config: Configuração do dataset
        high_precision: Usar modelo HP se disponível
    
    Returns:
        Dict com transcrição ou None se erro
    """
    audio_path_rel = segment['audio_path']
    audio_path = project_root / "train" / "data" / audio_path_rel
    
    try:
        # Get model for this worker
        model = get_model_from_pool(worker_id)
        
        # Transcribe
        trans_config = config["transcription"]
        language = trans_config.get("language", "pt")
        temperature = trans_config.get("temperature", 0.0)
        
        result = model.transcribe(
            str(audio_path),
            language=language,
            temperature=temperature,
        )
        
        text_raw = result.get("text", "").strip()
        
        if not text_raw:
            return None
        
        # Preprocess
        text = preprocess_text(text_raw, config)
        
        # Check if need high precision retry
        if not high_precision and _should_retry_with_high_precision(text, config):
            logger.info(f"   [Worker {worker_id}] 🔁 Retranscrevendo com HP...")
            # TODO: Implementar HP model pool se necessário
            pass
        
        # Validate length
        text_config = config["text_processing"]
        min_len = text_config.get("min_text_length", 1)
        
        if len(text) < min_len:
            return None
        
        # Return result
        return {
            **segment,
            "text": text,
            "char_count": len(text),
            "worker_id": worker_id,
        }
        
    except Exception as e:
        logger.error(f"   [Worker {worker_id}] ❌ Erro: {e}")
        return None


def transcribe_parallel(
    segments: List[Dict],
    config: Dict,
    num_workers: int,
    checkpoint_file: Path,
    checkpoint_interval: int = 10
) -> List[Dict]:
    """
    Transcreve segmentos em paralelo
    
    Args:
        segments: Lista de segmentos
        config: Configuração do dataset
        num_workers: Número de workers paralelos
        checkpoint_file: Arquivo de checkpoint
        checkpoint_interval: Salvar a cada N transcrições
    
    Returns:
        Lista de transcrições
    """
    # Load existing checkpoint
    transcriptions = []
    processed_paths = set()
    
    if checkpoint_file.exists():
        logger.info(f"📂 Checkpoint encontrado: {checkpoint_file}")
        try:
            with open(checkpoint_file, "r", encoding="utf-8") as f:
                transcriptions = json.load(f)
            processed_paths = {t["audio_path"] for t in transcriptions}
            logger.info(f"✅ Carregadas {len(transcriptions)} transcrições anteriores")
            logger.info(f"🔄 Continuando de onde parou...\n")
        except Exception as e:
            logger.warning(f"⚠️ Erro ao carregar checkpoint: {e}")
    
    # Filter segments to process
    segments_to_process = [
        s for s in segments
        if s["audio_path"] not in processed_paths
    ]
    
    if not segments_to_process:
        logger.info("✅ Todos os segmentos já foram processados!")
        return transcriptions
    
    logger.info(f"📋 Segmentos a processar: {len(segments_to_process)}/{len(segments)}")
    logger.info(f"👷 Workers paralelos: {num_workers}")
    logger.info(f"💾 Checkpoint a cada: {checkpoint_interval} segmentos\n")
    
    # Initialize model pool
    model_name = config["transcription"].get("whisper_model", "base")
    device = WHISPER_DEVICE
    init_model_pool(num_workers, model_name, device)
    
    # Process in parallel
    start_time = time.time()
    completed = 0
    
    with ThreadPoolExecutor(max_workers=num_workers) as executor:
        # Submit all tasks
        future_to_segment = {}
        for i, segment in enumerate(segments_to_process):
            worker_id = i % num_workers
            future = executor.submit(
                transcribe_segment_worker,
                worker_id,
                segment,
                config,
                False
            )
            future_to_segment[future] = (i, segment)
        
        # Process results as they complete
        for future in as_completed(future_to_segment):
            i, segment = future_to_segment[future]
            completed += 1
            
            try:
                result = future.result()
                
                if result:
                    transcriptions.append(result)
                    
                    # Progress log
                    total = len(segments_to_process)
                    percent = (completed / total) * 100
                    elapsed = time.time() - start_time
                    rate = completed / elapsed
                    eta = (total - completed) / rate if rate > 0 else 0
                    
                    logger.info(
                        f"[{completed}/{total}] {percent:.1f}% | "
                        f"{rate:.1f} seg/s | ETA: {eta/60:.1f}min | "
                        f"{result['char_count']} chars"
                    )
                    
                    # Checkpoint
                    if len(transcriptions) % checkpoint_interval == 0:
                        with open(checkpoint_file, "w", encoding="utf-8") as f:
                            json.dump(transcriptions, f, indent=2, ensure_ascii=False)
                        logger.info(f"   💾 Checkpoint salvo: {len(transcriptions)} transcrições\n")
                
            except Exception as e:
                logger.error(f"❌ Erro no segmento {i}: {e}")
    
    # Final save
    with open(checkpoint_file, "w", encoding="utf-8") as f:
        json.dump(transcriptions, f, indent=2, ensure_ascii=False)
    
    # Summary
    elapsed = time.time() - start_time
    logger.info("\n" + "=" * 80)
    logger.info("📊 RESUMO DA TRANSCRIÇÃO PARALELA")
    logger.info("=" * 80)
    logger.info(f"✅ Segmentos transcritos: {len(transcriptions)}")
    logger.info(f"⏱️  Tempo total: {elapsed/60:.1f} min")
    logger.info(f"⚡ Velocidade média: {len(segments_to_process)/elapsed:.2f} seg/s")
    logger.info(f"👷 Workers usados: {num_workers}")
    logger.info(f"💾 Salvo em: {checkpoint_file}")
    logger.info("=" * 80)
    
    return transcriptions


def main():
    """Main function"""
    logger.info("=" * 80)
    logger.info("TRANSCRIÇÃO PARALELA COM WHISPER (XTTS-v2)")
    logger.info("=" * 80)
    
    # Load config
    config_path = project_root / "train" / "config" / "dataset_config.yaml"
    with open(config_path, "r", encoding="utf-8") as f:
        config = yaml.safe_load(f)
    
    logger.info(f"📝 Config: {config['audio']['target_sample_rate']}Hz, "
                f"{config['segmentation']['min_duration']}-{config['segmentation']['max_duration']}s, "
                f"Whisper: {config['transcription']['whisper_model']}")
    logger.info(f"🎮 VRAM: {torch.cuda.mem_get_info()[0]/1024/1024:.0f}MB livre")
    logger.info(f"👷 Workers: {WHISPER_NUM_WORKERS} (auto-detectado)\n")
    
    # Load segments
    processed_dir = project_root / "train" / "data" / "processed"
    segments_file = processed_dir / "segments_mapping.json"
    
    with open(segments_file, "r", encoding="utf-8") as f:
        segments = json.load(f)
    
    logger.info(f"📋 {len(segments)} segmentos carregados\n")
    
    # Transcribe in parallel
    checkpoint_file = processed_dir / "transcriptions.json"
    transcriptions = transcribe_parallel(
        segments,
        config,
        WHISPER_NUM_WORKERS,
        checkpoint_file,
        checkpoint_interval=10
    )
    
    logger.info("\n🎉 Transcrição paralela completada!")


if __name__ == "__main__":
    main()
