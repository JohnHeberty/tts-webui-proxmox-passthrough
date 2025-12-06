"""
Preparação e segmentação de áudio para XTTS-v2 (PT-BR)
-------------------------------------------------------

Objetivos:
- Funcionar com áudios MUITO longos sem estourar RAM
- Usar VAD simples (energia RMS em dB) para pegar só trechos com fala
- Dividir as regiões de fala em segmentos de duração controlada XTTS-v2 (7-12s)
- Aplicar fade-in / fade-out curto para evitar clicks/zumbidos
- Normalizar (RMS ou pyloudnorm, se disponível)
- Resample para 22050Hz (XTTS-v2 requirement, não 24000Hz!)

Uso:
    python -m train.scripts.segment_audio
"""

from collections.abc import Iterable
import gc
import json
import logging
import math
from pathlib import Path
import sys
import warnings

import yaml


# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

# Dependências básicas
try:
    import numpy as np
    import soundfile as sf
except ImportError as e:
    print(f"❌ Dependência não encontrada: {e}")
    print("Instale com: pip install numpy soundfile")
    sys.exit(1)

# Dependências opcionais
try:
    import pyloudnorm as pyln
except ImportError:
    pyln = None

try:
    from scipy import signal
except ImportError:
    signal = None

# Logging
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
    """Carrega configuração do dataset (dataset_config.yaml)."""
    config_path = project_root / "train" / "config" / "dataset_config.yaml"
    with open(config_path, encoding="utf-8") as f:
        return yaml.safe_load(f)


# ======================
# VAD SIMPLES (ENERGIA)
# ======================


def detect_voice_in_chunk(
    audio_chunk: np.ndarray,
    sr: int,
    seg_config: dict,
) -> list[tuple[float, float]]:
    """
    Detecta regiões com voz em um chunk usando energia RMS em dB.

    Retorna tempos RELATIVOS ao chunk (segundos):
        [(start_sec_rel, end_sec_rel), ...]
    """
    frame_size = int(seg_config.get("vad_frame_size", 512))
    hop_size = frame_size // 2
    threshold_db = float(seg_config.get("vad_threshold", -40.0))
    min_silence_duration = float(seg_config.get("min_silence_duration", 0.3))

    if frame_size <= 0 or hop_size <= 0:
        raise ValueError("vad_frame_size deve ser > 0")

    num_frames = max(0, (len(audio_chunk) - frame_size) // hop_size + 1)

    segments: list[tuple[float, float]] = []
    in_voice = False
    voice_start = 0.0

    min_silence_frames = max(1, int(min_silence_duration * sr / hop_size))
    silence_count = 0
    eps = 1e-10

    for i in range(num_frames):
        start_idx = i * hop_size
        end_idx = start_idx + frame_size
        frame = audio_chunk[start_idx:end_idx]

        # RMS -> dB (energia)
        rms = float(np.sqrt(np.mean(frame * frame) + eps))
        db = 20.0 * math.log10(rms + eps)

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

    # Se terminou o chunk ainda em voz
    if in_voice:
        voice_end = (num_frames * hop_size) / sr
        if voice_end > voice_start:
            segments.append((voice_start, voice_end))

    return segments


def iter_voice_regions(
    input_path: Path,
    seg_config: dict,
    orig_sr: int,
    total_frames: int,
) -> Iterable[tuple[float, float]]:
    """
    Lê o arquivo em chunks pequenos, aplica VAD e devolve
    REGIÕES DE FALA (start_sec, end_sec) já mescladas.

    Tudo em streaming; só mantém na memória:
      - o chunk atual
      - a região atual em construção
    """
    use_vad = seg_config.get("use_vad", True)
    if not use_vad:
        # Sem VAD: o arquivo inteiro é "voz"
        total_duration = total_frames / orig_sr
        yield (0.0, total_duration)
        return

    vad_chunk_duration = float(seg_config.get("vad_chunk_duration", 10.0))
    vad_chunk_duration = max(2.0, vad_chunk_duration)  # não deixar ridiculamente pequeno
    chunk_samples = int(vad_chunk_duration * orig_sr)
    min_silence_to_merge = float(seg_config.get("min_silence_duration", 0.3))

    logger.info(f"   VAD streaming em chunks de {vad_chunk_duration:.1f}s")

    current_region_start = None  # tipo: float | None
    current_region_end = None

    with sf.SoundFile(str(input_path)) as audio_file:
        chunk_start_time = 0.0

        while True:
            chunk = audio_file.read(frames=chunk_samples, dtype="float32")
            if chunk.size == 0:
                break

            # Mono
            if chunk.ndim > 1:
                chunk = chunk.mean(axis=1)

            # VAD no chunk (tempos relativos)
            local_segments = detect_voice_in_chunk(chunk, orig_sr, seg_config)

            # Converter para tempos absolutos e mesclar em uma linha contínua
            for s_rel, e_rel in local_segments:
                s_abs = chunk_start_time + s_rel
                e_abs = chunk_start_time + e_rel

                if current_region_start is None:
                    current_region_start = s_abs
                    current_region_end = e_abs
                else:
                    # Se a nova região começa logo depois da atual, mescla
                    if s_abs - current_region_end <= min_silence_to_merge:
                        current_region_end = max(current_region_end, e_abs)
                    else:
                        # Fecha a região anterior e começa outra
                        yield (current_region_start, current_region_end)
                        current_region_start = s_abs
                        current_region_end = e_abs

            chunk_start_time += len(chunk) / orig_sr
            del chunk
            gc.collect()

    # Última região
    if current_region_start is not None and current_region_end is not None:
        yield (current_region_start, current_region_end)


# ======================
# SEGMENTOS FINAIS
# ======================


def iter_final_segments_from_regions(
    regions: Iterable[tuple[float, float]],
    seg_config: dict,
) -> Iterable[tuple[float, float]]:
    """
    A partir de regiões de fala (start, end) gera segmentos finais respeitando:
    - min_duration
    - max_duration
    - segment_overlap
    """
    min_duration = float(seg_config.get("min_duration", 3.0))
    max_duration = float(seg_config.get("max_duration", 7.0))
    target_duration = float(seg_config.get("target_duration", max_duration))
    overlap = float(seg_config.get("segment_overlap", 0.0))

    # Por segurança: target_duration não pode passar de max_duration
    target_duration = min(target_duration, max_duration)
    step = max(0.1, target_duration - overlap)

    logger.info(
        f"   target_duration={target_duration:.1f}s, max_duration={max_duration:.1f}s, "
        f"overlap={overlap:.1f}s, step={step:.2f}s"
    )

    for region_start, region_end in regions:
        region_dur = region_end - region_start
        if region_dur < min_duration:
            continue

        cur_start = region_start

        while True:
            # Se não cabe pelo menos min_duration, para
            if cur_start + min_duration > region_end:
                break

            seg_end = min(cur_start + max_duration, region_end)
            seg_dur = seg_end - cur_start

            if seg_dur < min_duration:
                break

            yield (cur_start, seg_end)

            if seg_end >= region_end:
                break

            cur_start = seg_end - overlap


# ======================
# NORMALIZAÇÃO / RESAMPLE / FADE
# ======================


def normalize_audio_simple(audio: np.ndarray, target_db: float = -20.0) -> np.ndarray:
    """Normalização RMS simples para target_db."""
    eps = 1e-10
    rms = float(np.sqrt(np.mean(audio * audio) + eps))
    current_db = 20.0 * math.log10(rms + eps)
    gain_db = target_db - current_db
    gain_linear = 10.0 ** (gain_db / 20.0)
    audio = audio * gain_linear

    max_val = float(np.max(np.abs(audio)))
    if max_val > 0.99:
        audio = audio * (0.99 / max_val)

    return audio.astype(np.float32, copy=False)


def normalize_segment(
    audio: np.ndarray,
    sr: int,
    audio_config: dict,
    meter=None,
) -> np.ndarray:
    """Normaliza um segmento usando pyloudnorm (se disponível) ou RMS simples."""
    if not audio_config.get("normalize_audio", False):
        return audio

    target_lufs = float(audio_config.get("target_lufs", -20.0))

    if pyln is not None and meter is not None:
        try:
            loudness = meter.integrated_loudness(audio)
            with warnings.catch_warnings():
                warnings.simplefilter("ignore", UserWarning)
                audio = pyln.normalize.loudness(audio, loudness, target_lufs)
            max_val = float(np.max(np.abs(audio)))
            if max_val > 0.99:
                audio = audio * (0.99 / max_val)
            return audio.astype(np.float32, copy=False)
        except Exception as e:
            logger.warning(f"   ⚠️  Falha ao normalizar com pyloudnorm: {e}")

    # Fallback RMS
    return normalize_audio_simple(audio, target_db=target_lufs)


def resample_segment(
    audio: np.ndarray,
    orig_sr: int,
    target_sr: int,
) -> tuple[np.ndarray, int]:
    """
    Resample do segmento:
    - resample_poly (scipy) se disponível
    - senão, decimação/repetição simples
    """
    if orig_sr == target_sr:
        return audio, orig_sr

    if signal is not None:
        try:
            g = math.gcd(orig_sr, target_sr)
            up = target_sr // g
            down = orig_sr // g
            audio_rs = signal.resample_poly(audio, up, down).astype(np.float32, copy=False)
            return audio_rs, target_sr
        except Exception as e:
            logger.warning(f"   ⚠️  Falha ao fazer resample com resample_poly: {e}")

    # Fallback simples
    if orig_sr > target_sr:
        step = max(1, int(round(orig_sr / target_sr)))
        audio_rs = audio[::step]
    else:
        factor = max(1, int(round(target_sr / orig_sr)))
        audio_rs = np.repeat(audio, factor)

    return audio_rs.astype(np.float32, copy=False), target_sr


def apply_fade(audio: np.ndarray, sr: int, fade_ms: float = 5.0) -> np.ndarray:
    """Fade-in e fade-out curtos para evitar clicks/zumbidos."""
    if fade_ms <= 0.0:
        return audio

    n_fade = int(sr * fade_ms / 1000.0)
    if n_fade <= 0 or len(audio) < 2 * n_fade:
        return audio

    fade_in = np.linspace(0.0, 1.0, n_fade, dtype=np.float32)
    fade_out = np.linspace(1.0, 0.0, n_fade, dtype=np.float32)

    audio[:n_fade] *= fade_in
    audio[-n_fade:] *= fade_out
    return audio


# ======================
# PROCESSAMENTO POR ARQUIVO
# ======================


def process_audio_file(
    input_path: Path,
    output_dir: Path,
    config: dict,
) -> list[dict]:
    """
    Pipeline completo para um arquivo:
    - Descobre regiões de fala via VAD streaming
    - Gera segmentos finais (start/end em segundos)
    - Extrai o áudio de cada segmento, normaliza, aplica fade e salva
    """
    seg_config = config["segmentation"]
    audio_config = config["audio"]

    # Descobrir SR e total de frames pela API unificada
    with sf.SoundFile(str(input_path)) as f:
        orig_sr = int(f.samplerate)
        total_frames = len(f)

    total_duration = total_frames / orig_sr

    target_sr = int(audio_config["target_sample_rate"])
    fade_ms = float(audio_config.get("fade_ms", 5.0))

    logger.info(f"📄 Processando: {input_path.name}")
    logger.info(f"   Duração total: {total_duration:.2f}s | SR: {orig_sr}Hz")

    # Passo 1: VAD streaming -> regiões de fala
    regions = list(iter_voice_regions(input_path, seg_config, orig_sr, total_frames))
    logger.info(f"   Regiões de fala detectadas (após merge): {len(regions)}")

    if not regions:
        logger.warning("   ⚠️ Nenhuma região de fala detectada, pulando arquivo.")
        return []

    # Passo 2: Geração dos segmentos finais (somente tempos)
    final_segments = list(iter_final_segments_from_regions(regions, seg_config))
    logger.info(f"   Segmentos finais a extrair: {len(final_segments)}")

    if not final_segments:
        logger.warning("   ⚠️ Nenhum segmento final gerado (talvez min_duration muito alta).")
        return []

    # Meter para normalização por loudness (por SR alvo)
    meter = None
    if pyln is not None and audio_config.get("normalize_audio", False):
        try:
            meter = pyln.Meter(target_sr)
        except Exception:
            meter = None

    segment_info_list: list[dict] = []
    base_name = input_path.stem

    # Passo 3: Extração dos segmentos do arquivo original
    with sf.SoundFile(str(input_path)) as audio_file:
        for idx, (start_time, end_time) in enumerate(final_segments):
            start_sample = int(round(start_time * orig_sr))
            end_sample = int(round(end_time * orig_sr))

            # Garantias de bounds
            start_sample = max(0, min(start_sample, total_frames))
            end_sample = max(0, min(end_sample, total_frames))
            frames = max(0, end_sample - start_sample)
            if frames <= 0:
                continue

            audio_file.seek(start_sample)
            segment = audio_file.read(frames=frames, dtype="float32")

            if segment.ndim > 1:
                segment = segment.mean(axis=1)

            # Resample para SR alvo
            segment, current_sr = resample_segment(segment, orig_sr, target_sr)

            # Normalização
            segment = normalize_segment(segment, current_sr, audio_config, meter)

            # Sanitizar valores (NaN/Inf)
            np.nan_to_num(segment, copy=False, nan=0.0, posinf=0.0, neginf=0.0)

            # Fade in/out
            segment = apply_fade(segment, current_sr, fade_ms=fade_ms)

            # Anti-clipping extra
            max_val = float(np.max(np.abs(segment)))
            if max_val > 0.99:
                segment *= 0.99 / max_val

            # Salvar
            output_filename = f"{base_name}_seg{idx:04d}.wav"
            output_path = output_dir / output_filename

            sf.write(
                str(output_path),
                segment.astype(np.float32, copy=False),
                current_sr,
                subtype="PCM_16",
            )

            seg_duration = len(segment) / current_sr
            segment_info = {
                "audio_path": str(output_path.relative_to(project_root / "train" / "data")),
                "original_file": input_path.name,
                "segment_index": idx,
                "duration": seg_duration,
                "start_time": float(start_time),
                "end_time": float(end_time),
            }
            segment_info_list.append(segment_info)

            # GC ocasional (para longos loops)
            if (idx + 1) % 100 == 0:
                gc.collect()
                logger.info(f"   Progresso: {idx + 1}/{len(final_segments)} segmentos extraídos...")

    logger.info(f"   ✅ {len(segment_info_list)} segmentos salvos para {input_path.name}\n")
    return segment_info_list


# ======================
# MAIN
# ======================


def main():
    logger.info("=" * 80)
    logger.info("PREPARAÇÃO E SEGMENTAÇÃO DE ÁUDIO (VAD + STREAMING)")
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

    all_segments: list[dict] = []

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

    processed_dir.mkdir(parents=True, exist_ok=True)
    mapping_file = processed_dir / "segments_mapping.json"
    with open(mapping_file, "w", encoding="utf-8") as f:
        json.dump(all_segments, f, indent=2, ensure_ascii=False)

    logger.info("\n" + "=" * 80)
    logger.info("RESUMO DA SEGMENTAÇÃO")
    logger.info("=" * 80)
    logger.info(f"📁 Arquivos processados: {len(audio_files)}")
    logger.info(f"✂️  Segmentos gerados: {len(all_segments)}")

    if all_segments:
        durations = [seg["duration"] for seg in all_segments]
        total_duration = sum(durations)
        min_duration = min(durations)
        max_duration = max(durations)
        avg_duration = total_duration / len(durations)

        logger.info(f"⏱️  Duração média: {avg_duration:.2f}s")
        logger.info(f"⏱️  Duração mínima: {min_duration:.2f}s")
        logger.info(f"⏱️  Duração máxima: {max_duration:.2f}s")
        logger.info(f"⏱️  Duração total: {total_duration / 3600:.2f}h")

    logger.info(f"📁 Segmentos salvos em: {wavs_dir}")
    logger.info(f"📄 Mapping salvo em: {mapping_file}")
    logger.info("=" * 80)


if __name__ == "__main__":
    main()
