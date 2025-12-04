"""
Preparação e segmentação de áudio OTIMIZADA para baixo consumo de memória,
com correção de artefatos de recorte (click/zumbido no fim dos segmentos).

- Processamento em chunks (streaming, não carrega o arquivo inteiro)
- VAD baseado em energia RMS (sem modelos pesados)
- Merge de segmentos entre chunks
- Segmentação com overlap configurável
- Normalização com pyloudnorm (se disponível) ou RMS simples
- Resample com resample_poly (quando disponível)
- Fade-in / fade-out curto em cada segmento para evitar clicks/zumbido

Uso:
    python -m train.scripts.prepare_segments
"""

import gc
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
    import numpy as np
    import soundfile as sf
except ImportError as e:
    print(f"❌ Dependência não encontrada: {e}")
    print("Instale com: pip install numpy soundfile")
    sys.exit(1)

# Dependências opcionais (melhor qualidade se existirem)
try:
    import pyloudnorm as pyln
except ImportError:
    pyln = None

try:
    from scipy import signal
except ImportError:
    signal = None

import math

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("train/logs/prepare_segments.log"),
        logging.StreamHandler(),
    ],
)
logger = logging.getLogger(__name__)


# ======================
# CONFIG
# ======================


def load_config() -> dict:
    """Carrega configuração do dataset"""
    config_path = project_root / "train" / "config" / "dataset_config.yaml"
    with open(config_path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


# ======================
# SEGMENTAÇÃO
# ======================


def split_segment_by_duration(
    start: float, end: float, config: dict
) -> List[Tuple[float, float]]:
    """
    Divide um segmento longo em partes menores respeitando duração máxima
    e overlap configurado.
    """
    seg_config = config["segmentation"]
    max_dur = float(seg_config["max_duration"])
    overlap = float(seg_config.get("segment_overlap", 0.0))

    duration = end - start
    if duration <= max_dur:
        return [(start, end)]

    segments: List[Tuple[float, float]] = []
    current_start = start

    while current_start < end:
        current_end = min(current_start + max_dur, end)
        segments.append((current_start, current_end))
        current_start = current_end - overlap

    return segments


def detect_voice_in_chunk(
    audio_chunk: np.ndarray,
    sr: int,
    seg_config: dict,
) -> List[Tuple[float, float]]:
    """
    Detecta segmentos com voz em um chunk usando energia RMS.

    Retorna tempos RELATIVOS ao chunk (em segundos).
    """
    frame_size = int(seg_config["vad_frame_size"])
    hop_size = frame_size // 2
    threshold_db = float(seg_config["vad_threshold"])
    min_silence_duration = float(seg_config["min_silence_duration"])

    if frame_size <= 0 or hop_size <= 0:
        raise ValueError("vad_frame_size deve ser > 0")

    num_frames = max(0, (len(audio_chunk) - frame_size) // hop_size + 1)

    segments: List[Tuple[float, float]] = []
    in_voice = False
    voice_start = 0.0

    min_silence_frames = max(1, int(min_silence_duration * sr / hop_size))
    silence_count = 0

    for i in range(num_frames):
        start_idx = i * hop_size
        end_idx = start_idx + frame_size
        frame = audio_chunk[start_idx:end_idx]

        # RMS -> dB (com epsilon pra evitar log(0))
        rms = float(np.sqrt(np.mean(frame**2) + 1e-10))
        db = 20.0 * np.log10(rms + 1e-10)

        has_voice = db > threshold_db
        time = start_idx / sr  # tempo relativo ao chunk

        if has_voice:
            if not in_voice:
                voice_start = time
                in_voice = True
            silence_count = 0
        else:
            if in_voice:
                silence_count += 1
                if silence_count >= min_silence_frames:
                    voice_end = time
                    if voice_end > voice_start:
                        segments.append((voice_start, voice_end))
                    in_voice = False
                    silence_count = 0

    if in_voice:
        voice_end = (num_frames * hop_size) / sr
        if voice_end > voice_start:
            segments.append((voice_start, voice_end))

    return segments


def merge_segments(
    segments: List[Tuple[float, float]], seg_config: dict
) -> List[Tuple[float, float]]:
    """
    Mescla segmentos adjacentes se o silêncio entre eles for menor que
    min_silence_duration.
    """
    if not segments:
        return []

    segments = sorted(segments, key=lambda x: x[0])
    merged: List[Tuple[float, float]] = []

    min_silence = float(seg_config["min_silence_duration"])
    current_start, current_end = segments[0]

    for start, end in segments[1:]:
        if start - current_end < min_silence:
            current_end = max(current_end, end)
        else:
            merged.append((current_start, current_end))
            current_start, current_end = start, end

    merged.append((current_start, current_end))
    return merged


# ======================
# NORMALIZAÇÃO
# ======================


def normalize_audio_simple(audio: np.ndarray, target_db: float = -20.0) -> np.ndarray:
    """
    Normalização simples de áudio para um nível de dB alvo (RMS).
    """
    rms = float(np.sqrt(np.mean(audio**2) + 1e-10))
    current_db = 20.0 * np.log10(rms + 1e-10)
    gain_db = target_db - current_db
    gain_linear = 10.0 ** (gain_db / 20.0)
    normalized = audio * gain_linear

    # Prevenir clipping
    max_val = float(np.abs(normalized).max())
    if max_val > 0.99:
        normalized = normalized / max_val * 0.99

    return normalized.astype(np.float32, copy=False)


def normalize_segment(
    audio: np.ndarray,
    sr: int,
    audio_config: dict,
) -> np.ndarray:
    """
    Normaliza um segmento de áudio usando pyloudnorm se disponível,
    senão cai para normalização RMS simples.
    """
    if not audio_config.get("normalize_audio", False):
        return audio

    target_lufs = float(audio_config.get("target_lufs", -23.0))

    if pyln is not None:
        try:
            meter = pyln.Meter(sr)
            loudness = meter.integrated_loudness(audio)
            normalized = pyln.normalize.loudness(audio, loudness, target_lufs)
            # Prevenir clipping
            max_val = float(np.abs(normalized).max())
            if max_val > 0.99:
                normalized = normalized / max_val * 0.99
            return normalized.astype(np.float32, copy=False)
        except Exception as e:
            logger.warning(f"   ⚠️  Falha ao normalizar com pyloudnorm: {e}")

    # Fallback: usa target_lufs como alvo em dB RMS
    return normalize_audio_simple(audio, target_db=target_lufs)


# ======================
# RESAMPLE + FADE
# ======================


def resample_segment(
    audio: np.ndarray,
    orig_sr: int,
    target_sr: int,
) -> Tuple[np.ndarray, int]:
    """
    Faz resample do segmento. Se scipy.signal estiver disponível, usa
    resample_poly (qualidade melhor e menos artefatos). Senão, faz
    decimação/repetição simples.
    """
    if orig_sr == target_sr:
        return audio, orig_sr

    if signal is not None:
        try:
            # Usa razão em termos reduzidos para resample_poly
            g = math.gcd(orig_sr, target_sr)
            up = target_sr // g
            down = orig_sr // g
            audio_rs = signal.resample_poly(audio, up, down).astype(
                np.float32, copy=False
            )
            return audio_rs, target_sr
        except Exception as e:
            logger.warning(f"   ⚠️  Falha ao fazer resample com resample_poly: {e}")

    # Fallback simples (menos ideal, porém estável)
    if orig_sr > target_sr:
        step = max(1, int(round(orig_sr / target_sr)))
        audio_rs = audio[::step]
    else:
        factor = max(1, int(round(target_sr / orig_sr)))
        audio_rs = np.repeat(audio, factor)

    return audio_rs.astype(np.float32, copy=False), target_sr


def apply_fade(
    audio: np.ndarray,
    sr: int,
    fade_ms: float = 5.0,
) -> np.ndarray:
    """
    Aplica fade-in e fade-out curto para evitar clicks/zumbidos no começo/fim.

    fade_ms: duração do fade em milissegundos.
    """
    if fade_ms <= 0.0:
        return audio

    n_fade = int(sr * fade_ms / 1000.0)
    if n_fade <= 0 or len(audio) < 2 * n_fade:
        return audio

    fade_in = np.linspace(0.0, 1.0, n_fade, dtype=audio.dtype)
    fade_out = np.linspace(1.0, 0.0, n_fade, dtype=audio.dtype)

    audio[:n_fade] *= fade_in
    audio[-n_fade:] *= fade_out
    return audio


# ======================
# PIPELINE PRINCIPAL
# ======================


def process_audio_file(
    input_path: Path,
    output_dir: Path,
    config: dict,
) -> List[dict]:
    """
    Processa um arquivo de áudio com baixo consumo de memória:
    - VAD em chunks
    - merge de segmentos
    - split de segmentos longos com overlap
    - extração + normalização + resample de cada segmento
    - fade-in / fade-out curto em cada segmento (para evitar zumbido/click)
    """
    logger.info(f"📄 Processando: {input_path.name}")

    seg_config = config["segmentation"]
    audio_config = config["audio"]

    target_sr = int(audio_config["target_sample_rate"])
    min_duration = float(seg_config["min_duration"])
    max_duration = float(seg_config["max_duration"])
    fade_ms = float(audio_config.get("fade_ms", 5.0))  # ms de fade-in/out

    # Info do arquivo
    info = sf.info(str(input_path))
    total_duration = float(info.duration)
    orig_sr = int(info.samplerate)

    logger.info(f"   Duração total: {total_duration:.2f}s")
    logger.info(f"   Sample rate original: {orig_sr}Hz")

    # VAD em chunks
    use_vad = seg_config.get("use_vad", True)
    vad_chunk_duration = float(seg_config.get("vad_chunk_duration", 60.0))
    vad_chunk_duration = max(5.0, min(vad_chunk_duration, total_duration))

    all_voice_segments: List[Tuple[float, float]] = []

    if use_vad:
        logger.info(f"   VAD em chunks de {vad_chunk_duration:.1f}s...")
        chunk_samples = int(vad_chunk_duration * orig_sr)

        with sf.SoundFile(str(input_path)) as audio_file:
            chunk_start_time = 0.0
            while True:
                # Lê chunk como float32
                chunk = audio_file.read(frames=chunk_samples, dtype="float32")
                if chunk.size == 0:
                    break

                # Mono
                if chunk.ndim > 1:
                    chunk = chunk.mean(axis=1)

                # Detecta voz nesse chunk (tempos relativos)
                voice_rel = detect_voice_in_chunk(chunk, orig_sr, seg_config)

                # Ajusta para tempo absoluto
                for s_rel, e_rel in voice_rel:
                    s_abs = chunk_start_time + s_rel
                    e_abs = chunk_start_time + e_rel
                    if e_abs > s_abs:
                        all_voice_segments.append((s_abs, e_abs))

                # Atualiza tempo global
                chunk_start_time += len(chunk) / orig_sr

                # Liberar memória
                del chunk
                gc.collect()

        logger.info(
            f"   Segmentos com voz detectados (antes do merge): {len(all_voice_segments)}"
        )

        # Mesclar segmentos adjacentes
        all_voice_segments = merge_segments(all_voice_segments, seg_config)
        logger.info(f"   Segmentos após merge: {len(all_voice_segments)}")
    else:
        # Sem VAD: usa áudio inteiro
        all_voice_segments = [(0.0, total_duration)]

    # Filtra curtos e divide longos, com overlap
    final_segments: List[Tuple[float, float]] = []
    for start, end in all_voice_segments:
        dur = end - start
        if dur < min_duration:
            continue

        if dur > max_duration:
            subsegments = split_segment_by_duration(start, end, config)
            for s_sub, e_sub in subsegments:
                if e_sub - s_sub >= min_duration:
                    final_segments.append((s_sub, e_sub))
        else:
            final_segments.append((start, end))

    logger.info(f"   Segmentos finais: {len(final_segments)}")

    # Extração de segmentos + normalização + resample + fade
    segment_info_list: List[dict] = []
    base_name = input_path.stem

    with sf.SoundFile(str(input_path)) as audio_file:
        total_frames = len(audio_file)

        for idx, (start_time, end_time) in enumerate(final_segments):
            start_sample = int(round(start_time * orig_sr))
            end_sample = int(round(end_time * orig_sr))
            # Garante que não passa do tamanho do arquivo
            start_sample = max(0, min(start_sample, total_frames))
            end_sample = max(0, min(end_sample, total_frames))

            frames = max(0, end_sample - start_sample)
            if frames <= 0:
                continue

            audio_file.seek(start_sample)
            segment = audio_file.read(frames=frames, dtype="float32")

            if segment.ndim > 1:
                segment = segment.mean(axis=1)

            # Resample para target_sr
            segment, current_sr = resample_segment(segment, orig_sr, target_sr)

            # Normalização
            segment = normalize_segment(segment, current_sr, audio_config)

            # Sanitizar valores (evita NaN/Inf que podem virar zumbido)
            segment = np.nan_to_num(segment, nan=0.0, posinf=0.0, neginf=0.0)

            # Fade-in / Fade-out curto para evitar click/zumbido no recorte
            segment = apply_fade(segment, current_sr, fade_ms=fade_ms)

            # Prevenir clipping extra
            max_val = float(np.abs(segment).max())
            if max_val > 0.99:
                segment = segment / max_val * 0.99

            # Salvar
            output_filename = f"{base_name}_seg{idx:04d}.wav"
            output_path = output_dir / output_filename

            sf.write(
                str(output_path),
                segment.astype(np.float32, copy=False),
                current_sr,
                subtype="PCM_16",
            )

            duration = len(segment) / current_sr
            segment_info = {
                "audio_path": str(
                    output_path.relative_to(project_root / "train" / "data")
                ),
                "original_file": input_path.name,
                "segment_index": idx,
                "duration": duration,
                "start_time": start_time,
                "end_time": end_time,
            }
            segment_info_list.append(segment_info)

            del segment
            gc.collect()

            # Log a cada 100 segmentos
            if (idx + 1) % 100 == 0:
                logger.info(
                    f"   Progresso: {idx + 1}/{len(final_segments)} segmentos salvos..."
                )

    logger.info(f"   ✅ {len(segment_info_list)} segmentos salvos\n")
    return segment_info_list


def main():
    """Main function"""
    logger.info("=" * 80)
    logger.info("PREPARAÇÃO E SEGMENTAÇÃO DE ÁUDIO (OTIMIZADA + HÍBRIDA)")
    logger.info("=" * 80)

    config = load_config()

    data_dir = project_root / "train" / "data"
    raw_dir = data_dir / "raw"
    processed_dir = data_dir / "processed"
    wavs_dir = processed_dir / "wavs"

    wavs_dir.mkdir(parents=True, exist_ok=True)

    audio_files = sorted(raw_dir.glob("*.wav"))
    if not audio_files:
        logger.error(f"❌ Nenhum arquivo WAV encontrado em {raw_dir}")
        sys.exit(1)

    logger.info(f"📁 {len(audio_files)} arquivos encontrados em {raw_dir}\n")

    all_segments: List[dict] = []

    for i, audio_file in enumerate(audio_files, 1):
        logger.info(f"[{i}/{len(audio_files)}] Processando {audio_file.name}")
        try:
            segs = process_audio_file(audio_file, wavs_dir, config)
            all_segments.extend(segs)
        except Exception as e:
            logger.error(f"❌ Erro ao processar {audio_file.name}: {e}")
            import traceback

            traceback.print_exc()
        gc.collect()

    mapping_file = processed_dir / "segments_mapping.json"
    with open(mapping_file, "w", encoding="utf-8") as f:
        json.dump(all_segments, f, indent=2, ensure_ascii=False)

    logger.info("\n" + "=" * 80)
    logger.info("RESUMO DA SEGMENTAÇÃO")
    logger.info("=" * 80)
    logger.info(f"📁 Arquivos processados: {len(audio_files)}")
    logger.info(f"✂️  Segmentos gerados: {len(all_segments)}")

    if all_segments:
        durations = np.array(
            [seg["duration"] for seg in all_segments], dtype=np.float32
        )
        logger.info(f"⏱️  Duração média: {float(durations.mean()):.2f}s")
        logger.info(f"⏱️  Duração mínima: {float(durations.min()):.2f}s")
        logger.info(f"⏱️  Duração máxima: {float(durations.max()):.2f}s")
        logger.info(f"⏱️  Duração total: {float(durations.sum()) / 3600:.2f}h")

    logger.info(f"📁 Segmentos salvos em: {wavs_dir}")
    logger.info(f"📄 Mapping salvo em: {mapping_file}")
    logger.info("=" * 80)


if __name__ == "__main__":
    main()
