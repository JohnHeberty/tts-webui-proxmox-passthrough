"""
Preparação e segmentação de áudio OTIMIZADA para baixo consumo de memória

Este script processa os áudios baixados usando streaming e processamento em chunks,
evitando carregar arquivos grandes completamente na memória.

Melhorias:
- Processamento em chunks de 30s (baixo uso de RAM)
- VAD baseado em energia (sem modelos ML pesados)
- Streaming de áudio (não carrega tudo na memória)
- Normalização incremental

Uso:
    python -m train.scripts.prepare_segments_optimized
"""
import json
import logging
import sys
import gc
from pathlib import Path
from typing import List, Tuple, Generator
import wave

import yaml

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

try:
    import numpy as np
    import soundfile as sf
except ImportError as e:
    print(f"❌ Dependência não encontrada: {e}")
    print("Instale com: pip install numpy soundfile")
    sys.exit(1)

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('train/logs/prepare_segments.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


def load_config() -> dict:
    """Carrega configuração do dataset"""
    config_path = project_root / "train" / "config" / "dataset_config.yaml"
    with open(config_path, 'r', encoding='utf-8') as f:
        return yaml.safe_load(f)


def read_audio_chunks(
    filepath: Path,
    chunk_duration: float = 30.0,
    target_sr: int = 24000
) -> Generator[Tuple[np.ndarray, int, float], None, None]:
    """
    Lê áudio em chunks para economizar memória
    
    Args:
        filepath: Arquivo de áudio
        chunk_duration: Duração de cada chunk em segundos
        target_sr: Sample rate alvo
    
    Yields:
        (audio_chunk, sample_rate, start_time)
    """
    with sf.SoundFile(str(filepath)) as audio_file:
        sr = audio_file.samplerate
        channels = audio_file.channels
        
        # Se não for o sample rate alvo, avisar mas continuar
        if sr != target_sr:
            logger.warning(f"   ⚠️  Sample rate {sr}Hz será convertido para {target_sr}Hz")
        
        chunk_samples = int(chunk_duration * sr)
        start_time = 0.0
        
        while True:
            # Ler chunk
            chunk = audio_file.read(chunk_samples)
            
            if len(chunk) == 0:
                break
            
            # Converter para mono se necessário
            if channels > 1:
                chunk = chunk.mean(axis=1)
            
            # Resample se necessário (simples: decimação/interpolação)
            if sr != target_sr:
                # Decimação simples se downsampling
                if sr > target_sr:
                    step = int(sr / target_sr)
                    chunk = chunk[::step]
                # Se upsampling, usar repetição simples (não ideal mas funcional)
                else:
                    factor = int(target_sr / sr)
                    chunk = np.repeat(chunk, factor)
            
            yield chunk, target_sr, start_time
            
            start_time += len(chunk) / target_sr
            
            # Limpar memória
            del chunk
            gc.collect()


def detect_voice_in_chunk(
    audio_chunk: np.ndarray,
    sr: int,
    threshold_db: float = -40,
    frame_size: int = 2048
) -> List[Tuple[float, float]]:
    """
    Detecta segmentos com voz em um chunk usando energia RMS
    
    Args:
        audio_chunk: Chunk de áudio
        sr: Sample rate
        threshold_db: Threshold em dB
        frame_size: Tamanho do frame para análise
    
    Returns:
        Lista de (start, end) em segundos relativos ao chunk
    """
    hop_size = frame_size // 2
    
    # Calcular RMS por frame
    num_frames = len(audio_chunk) // hop_size
    segments = []
    in_voice = False
    voice_start = 0.0
    min_silence_frames = 10  # ~100ms de silêncio para separar
    silence_count = 0
    
    for i in range(num_frames):
        start_idx = i * hop_size
        end_idx = start_idx + frame_size
        
        if end_idx > len(audio_chunk):
            break
        
        frame = audio_chunk[start_idx:end_idx]
        
        # Calcular energia RMS
        rms = np.sqrt(np.mean(frame**2))
        db = 20 * np.log10(rms + 1e-10)
        
        has_voice = db > threshold_db
        time = i * hop_size / sr
        
        if has_voice:
            if not in_voice:
                voice_start = time
                in_voice = True
            silence_count = 0
        else:
            if in_voice:
                silence_count += 1
                if silence_count >= min_silence_frames:
                    # Fim de segmento
                    segments.append((voice_start, time))
                    in_voice = False
                    silence_count = 0
    
    # Adicionar último segmento se ainda em voz
    if in_voice:
        segments.append((voice_start, num_frames * hop_size / sr))
    
    return segments


def normalize_audio_simple(audio: np.ndarray, target_db: float = -20.0) -> np.ndarray:
    """
    Normalização simples de áudio para um nível de dB alvo
    
    Args:
        audio: Array de áudio
        target_db: Nível alvo em dB
    
    Returns:
        Áudio normalizado
    """
    # Calcular RMS atual
    rms = np.sqrt(np.mean(audio**2))
    current_db = 20 * np.log10(rms + 1e-10)
    
    # Calcular ganho necessário
    gain_db = target_db - current_db
    gain_linear = 10 ** (gain_db / 20)
    
    # Aplicar ganho
    normalized = audio * gain_linear
    
    # Prevenir clipping
    max_val = np.abs(normalized).max()
    if max_val > 0.99:
        normalized = normalized / max_val * 0.99
    
    return normalized


def process_audio_file_optimized(
    input_path: Path,
    output_dir: Path,
    config: dict
) -> List[dict]:
    """
    Processa arquivo de áudio com baixo consumo de memória
    
    Args:
        input_path: Path do arquivo
        output_dir: Diretório de saída
        config: Configuração
    
    Returns:
        Lista de informações dos segmentos
    """
    logger.info(f"📄 Processando: {input_path.name}")
    
    seg_config = config['segmentation']
    audio_config = config['audio']
    
    target_sr = audio_config['target_sample_rate']
    min_duration = seg_config['min_duration']
    max_duration = seg_config['max_duration']
    
    base_name = input_path.stem
    segment_info_list = []
    segment_counter = 0
    
    # Processar em chunks
    chunk_duration = 30.0  # 30 segundos por chunk
    all_voice_segments = []
    
    logger.info(f"   Processando em chunks de {chunk_duration}s...")
    
    for chunk, sr, chunk_start in read_audio_chunks(input_path, chunk_duration, target_sr):
        # Detectar voz no chunk
        if seg_config['use_vad']:
            voice_segs = detect_voice_in_chunk(
                chunk,
                sr,
                seg_config['vad_threshold']
            )
            
            # Ajustar tempos para o tempo global
            for start, end in voice_segs:
                global_start = chunk_start + start
                global_end = chunk_start + end
                duration = global_end - global_start
                
                # Filtrar muito curtos
                if duration < min_duration:
                    continue
                
                # Dividir se muito longo
                if duration > max_duration:
                    # Dividir em partes de max_duration
                    current = global_start
                    while current < global_end:
                        seg_end = min(current + max_duration, global_end)
                        if seg_end - current >= min_duration:
                            all_voice_segments.append((current, seg_end))
                        current = seg_end
                else:
                    all_voice_segments.append((global_start, global_end))
        
        # Limpar memória
        del chunk
        gc.collect()
    
    logger.info(f"   Segmentos detectados: {len(all_voice_segments)}")
    
    # Agora extrair e salvar os segmentos
    # Fazer isso de forma eficiente, lendo apenas as partes necessárias
    with sf.SoundFile(str(input_path)) as audio_file:
        sr = audio_file.samplerate
        
        for start_time, end_time in all_voice_segments:
            # Calcular posição em samples
            start_sample = int(start_time * sr)
            end_sample = int(end_time * sr)
            
            # Posicionar e ler apenas esse segmento
            audio_file.seek(start_sample)
            segment = audio_file.read(end_sample - start_sample)
            
            # Converter para mono se necessário
            if len(segment.shape) > 1:
                segment = segment.mean(axis=1)
            
            # Resample se necessário (simples)
            if sr != target_sr:
                if sr > target_sr:
                    step = int(sr / target_sr)
                    segment = segment[::step]
                else:
                    factor = int(target_sr / sr)
                    segment = np.repeat(segment, factor)
            
            # Normalizar
            if audio_config['normalize_audio']:
                try:
                    segment = normalize_audio_simple(segment, audio_config['target_lufs'])
                except Exception as e:
                    logger.warning(f"   ⚠️  Erro ao normalizar segmento: {e}")
            
            # Salvar
            output_filename = f"{base_name}_seg{segment_counter:04d}.wav"
            output_path = output_dir / output_filename
            
            sf.write(
                str(output_path),
                segment,
                target_sr,
                subtype='PCM_16'
            )
            
            # Metadata
            duration = len(segment) / target_sr
            segment_info = {
                'audio_path': str(output_path.relative_to(project_root / "train" / "data")),
                'original_file': input_path.name,
                'segment_index': segment_counter,
                'duration': duration,
                'start_time': start_time,
                'end_time': end_time
            }
            segment_info_list.append(segment_info)
            segment_counter += 1
            
            # Limpar
            del segment
            gc.collect()
    
    logger.info(f"   ✅ {len(segment_info_list)} segmentos salvos\n")
    
    return segment_info_list


def main():
    """Main function"""
    logger.info("=" * 80)
    logger.info("PREPARAÇÃO E SEGMENTAÇÃO DE ÁUDIO (OTIMIZADO)")
    logger.info("=" * 80)
    
    # Load config
    config = load_config()
    
    # Paths
    data_dir = project_root / "train" / "data"
    raw_dir = data_dir / "raw"
    processed_dir = data_dir / "processed"
    wavs_dir = processed_dir / "wavs"
    
    # Criar diretórios
    wavs_dir.mkdir(parents=True, exist_ok=True)
    
    # Verificar arquivos
    audio_files = sorted(raw_dir.glob("*.wav"))
    
    if not audio_files:
        logger.error(f"❌ Nenhum arquivo WAV encontrado em {raw_dir}")
        sys.exit(1)
    
    logger.info(f"📁 {len(audio_files)} arquivos encontrados em {raw_dir}\n")
    
    # Processar cada arquivo
    all_segments = []
    
    for i, audio_file in enumerate(audio_files, 1):
        logger.info(f"[{i}/{len(audio_files)}] Processando {audio_file.name}")
        try:
            segments = process_audio_file_optimized(audio_file, wavs_dir, config)
            all_segments.extend(segments)
        except Exception as e:
            logger.error(f"❌ Erro ao processar {audio_file.name}: {e}")
            import traceback
            traceback.print_exc()
            continue
        
        # Force garbage collection entre arquivos
        gc.collect()
    
    # Salvar mapping
    mapping_file = processed_dir / "segments_mapping.json"
    with open(mapping_file, 'w', encoding='utf-8') as f:
        json.dump(all_segments, f, indent=2, ensure_ascii=False)
    
    # Summary
    logger.info("\n" + "=" * 80)
    logger.info("RESUMO DA SEGMENTAÇÃO")
    logger.info("=" * 80)
    logger.info(f"📁 Arquivos processados: {len(audio_files)}")
    logger.info(f"✂️  Segmentos gerados: {len(all_segments)}")
    
    if all_segments:
        durations = [seg['duration'] for seg in all_segments]
        logger.info(f"⏱️  Duração média: {np.mean(durations):.2f}s")
        logger.info(f"⏱️  Duração mínima: {np.min(durations):.2f}s")
        logger.info(f"⏱️  Duração máxima: {np.max(durations):.2f}s")
        logger.info(f"⏱️  Duração total: {sum(durations) / 3600:.2f}h")
    
    logger.info(f"📁 Segmentos salvos em: {wavs_dir}")
    logger.info(f"📄 Mapping salvo em: {mapping_file}")
    logger.info("=" * 80)


if __name__ == "__main__":
    main()
