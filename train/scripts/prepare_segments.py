"""
Preparação e segmentação de áudio

Este script processa os áudios baixados, aplicando:
- Voice Activity Detection (VAD)
- Segmentação em trechos de 3-12 segundos
- Normalização de volume
- Conversão para mono 24kHz

Uso:
    python -m train.scripts.prepare_segments

Dependências:
    - librosa: pip install librosa
    - soundfile: pip install soundfile
    - pydub: pip install pydub
    - pyloudnorm: pip install pyloudnorm
"""
import json
import logging
import sys
from pathlib import Path
from typing import List, Tuple

import yaml

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

try:
    import librosa
    import numpy as np
    import soundfile as sf
    import pyloudnorm as pyln
except ImportError as e:
    print(f"❌ Dependência não encontrada: {e}")
    print("Instale com: pip install librosa soundfile pyloudnorm")
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


def detect_voice_segments(
    audio: np.ndarray,
    sr: int,
    config: dict
) -> List[Tuple[float, float]]:
    """
    Detecta segmentos com voz usando VAD simples baseado em energia
    
    Args:
        audio: Audio array
        sr: Sample rate
        config: Configuração
    
    Returns:
        Lista de tuplas (start_time, end_time) em segundos
    """
    seg_config = config['segmentation']
    
    # Parâmetros
    frame_length = seg_config['vad_frame_size']
    hop_length = frame_length // 2
    threshold_db = seg_config['vad_threshold']
    min_silence_duration = seg_config['min_silence_duration']
    
    # Calcular energia por frame (em dB)
    energy = librosa.feature.rms(
        y=audio,
        frame_length=frame_length,
        hop_length=hop_length
    )[0]
    
    energy_db = librosa.amplitude_to_db(energy, ref=np.max)
    
    # Detectar frames com voz (acima do threshold)
    is_voice = energy_db > threshold_db
    
    # Converter frames para tempo
    times = librosa.frames_to_time(
        np.arange(len(is_voice)),
        sr=sr,
        hop_length=hop_length
    )
    
    # Encontrar segmentos contínuos de voz
    segments = []
    in_segment = False
    start_time = 0.0
    
    min_silence_frames = int(min_silence_duration * sr / hop_length)
    silence_counter = 0
    
    for i, (time, voice) in enumerate(zip(times, is_voice)):
        if voice:
            if not in_segment:
                # Início de novo segmento
                start_time = time
                in_segment = True
            silence_counter = 0
        else:
            if in_segment:
                silence_counter += 1
                if silence_counter >= min_silence_frames:
                    # Fim do segmento (silêncio suficientemente longo)
                    end_time = time - min_silence_duration
                    segments.append((start_time, end_time))
                    in_segment = False
                    silence_counter = 0
    
    # Adicionar último segmento se ainda ativo
    if in_segment:
        segments.append((start_time, times[-1]))
    
    return segments


def split_segment_by_duration(
    start: float,
    end: float,
    config: dict
) -> List[Tuple[float, float]]:
    """
    Divide um segmento longo em partes menores respeitando duração máxima
    
    Args:
        start: Início do segmento (segundos)
        end: Fim do segmento (segundos)
        config: Configuração
    
    Returns:
        Lista de tuplas (start, end) dos subsegmentos
    """
    seg_config = config['segmentation']
    max_dur = seg_config['max_duration']
    overlap = seg_config['segment_overlap']
    
    duration = end - start
    
    if duration <= max_dur:
        return [(start, end)]
    
    # Dividir em múltiplos segmentos com overlap
    segments = []
    current_start = start
    
    while current_start < end:
        current_end = min(current_start + max_dur, end)
        segments.append((current_start, current_end))
        current_start = current_end - overlap
    
    return segments


def normalize_loudness(
    audio: np.ndarray,
    sr: int,
    target_lufs: float
) -> np.ndarray:
    """
    Normaliza loudness do áudio para target LUFS
    
    Args:
        audio: Audio array
        sr: Sample rate
        target_lufs: Target loudness em LUFS
    
    Returns:
        Audio normalizado
    """
    # Meter
    meter = pyln.Meter(sr)
    
    # Medir loudness
    loudness = meter.integrated_loudness(audio)
    
    # Normalizar
    normalized_audio = pyln.normalize.loudness(audio, loudness, target_lufs)
    
    return normalized_audio


def process_audio_file(
    input_path: Path,
    output_dir: Path,
    config: dict
) -> List[dict]:
    """
    Processa um arquivo de áudio, gerando segmentos
    
    Args:
        input_path: Path do arquivo de entrada
        output_dir: Diretório de saída para segmentos
        config: Configuração
    
    Returns:
        Lista de dicts com informações dos segmentos gerados
    """
    logger.info(f"📄 Processando: {input_path.name}")
    
    seg_config = config['segmentation']
    audio_config = config['audio']
    
    # Carregar áudio
    audio, sr = librosa.load(
        input_path,
        sr=audio_config['target_sample_rate'],
        mono=True
    )
    
    total_duration = len(audio) / sr
    logger.info(f"   Duração total: {total_duration:.2f}s")
    
    # Voice Activity Detection
    if seg_config['use_vad']:
        voice_segments = detect_voice_segments(audio, sr, config)
        logger.info(f"   Segmentos com voz detectados: {len(voice_segments)}")
    else:
        # Usar áudio completo
        voice_segments = [(0.0, total_duration)]
    
    # Dividir segmentos longos
    all_segments = []
    for start, end in voice_segments:
        duration = end - start
        
        # Filtrar segmentos muito curtos
        if duration < seg_config['min_duration']:
            continue
        
        # Dividir se muito longo
        if duration > seg_config['max_duration']:
            subsegments = split_segment_by_duration(start, end, config)
            all_segments.extend(subsegments)
        else:
            all_segments.append((start, end))
    
    logger.info(f"   Segmentos finais: {len(all_segments)}")
    
    # Salvar cada segmento
    segment_info_list = []
    base_name = input_path.stem
    
    for i, (start, end) in enumerate(all_segments):
        # Extrair segmento
        start_sample = int(start * sr)
        end_sample = int(end * sr)
        segment_audio = audio[start_sample:end_sample]
        
        duration = len(segment_audio) / sr
        
        # Normalizar loudness
        if audio_config['normalize_audio']:
            try:
                segment_audio = normalize_loudness(
                    segment_audio,
                    sr,
                    audio_config['target_lufs']
                )
            except Exception as e:
                logger.warning(f"   ⚠️  Falha ao normalizar segmento {i}: {e}")
        
        # Prevenir clipping
        max_val = np.abs(segment_audio).max()
        if max_val > 0.99:
            segment_audio = segment_audio / max_val * 0.99
        
        # Nome do arquivo de saída
        output_filename = f"{base_name}_seg{i:04d}.wav"
        output_path = output_dir / output_filename
        
        # Salvar
        sf.write(
            output_path,
            segment_audio,
            sr,
            subtype='PCM_16'
        )
        
        # Metadata
        segment_info = {
            'audio_path': str(output_path.relative_to(project_root / "train" / "data")),
            'original_file': input_path.name,
            'segment_index': i,
            'duration': duration,
            'start_time': start,
            'end_time': end
        }
        segment_info_list.append(segment_info)
    
    logger.info(f"   ✅ {len(segment_info_list)} segmentos salvos\n")
    
    return segment_info_list


def main():
    """Main function"""
    logger.info("=" * 80)
    logger.info("PREPARAÇÃO E SEGMENTAÇÃO DE ÁUDIO")
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
    
    # Verificar se existem áudios em raw/
    audio_files = list(raw_dir.glob("*.wav"))
    
    if not audio_files:
        logger.error(f"❌ Nenhum arquivo WAV encontrado em {raw_dir}")
        logger.error("   Execute primeiro: python -m train.scripts.download_youtube")
        sys.exit(1)
    
    logger.info(f"📁 {len(audio_files)} arquivos encontrados em {raw_dir}\n")
    
    # Processar cada arquivo
    all_segments = []
    
    for audio_file in audio_files:
        try:
            segments = process_audio_file(audio_file, wavs_dir, config)
            all_segments.extend(segments)
        except Exception as e:
            logger.error(f"❌ Erro ao processar {audio_file.name}: {e}")
            continue
    
    # Salvar mapping de segmentos
    mapping_file = processed_dir / "segments_mapping.json"
    with open(mapping_file, 'w', encoding='utf-8') as f:
        json.dump(all_segments, f, indent=2, ensure_ascii=False)
    
    # Summary
    logger.info("\n" + "=" * 80)
    logger.info("RESUMO DA SEGMENTAÇÃO")
    logger.info("=" * 80)
    logger.info(f"📁 Arquivos originais processados: {len(audio_files)}")
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
