#!/usr/bin/env python3
"""
Benchmark e validação dos scripts de segmentação

Compara V2 vs V3 em termos de:
- Memória pico
- Tempo de execução
- Qualidade dos segmentos
- I/O disco

Uso:
    python3 train/scripts/benchmark_segmentation.py
"""

import gc
import sys
import time
import psutil
import tempfile
import numpy as np
import soundfile as sf
from pathlib import Path
from typing import Dict, List
from dataclasses import dataclass

# Add project root
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))


@dataclass
class BenchmarkResult:
    """Resultado de benchmark"""
    version: str
    peak_memory_mb: float
    execution_time_s: float
    num_segments: int
    disk_writes_mb: float
    avg_segment_duration: float


class MemoryMonitor:
    """Monitor de uso de memória"""
    
    def __init__(self):
        self.process = psutil.Process()
        self.peak_mb = 0
        self.start_mb = 0
    
    def start(self):
        """Inicia monitoramento"""
        gc.collect()
        self.start_mb = self.process.memory_info().rss / 1024 / 1024
        self.peak_mb = self.start_mb
    
    def update(self):
        """Atualiza pico"""
        current_mb = self.process.memory_info().rss / 1024 / 1024
        self.peak_mb = max(self.peak_mb, current_mb)
    
    def get_peak_increase(self) -> float:
        """Retorna incremento de pico em MB"""
        return self.peak_mb - self.start_mb


def create_test_audio(duration: float, sr: int = 24000) -> Path:
    """Cria arquivo de áudio de teste"""
    temp_dir = Path(tempfile.gettempdir())
    output_path = temp_dir / f"test_audio_{duration}s.wav"
    
    if output_path.exists():
        return output_path
    
    print(f"Criando áudio de teste: {duration}s @ {sr}Hz...")
    
    # Gera áudio com variações (simula fala)
    samples = int(duration * sr)
    t = np.linspace(0, duration, samples)
    
    # Mix de frequências para simular voz
    audio = np.zeros(samples, dtype=np.float32)
    
    # Segmentos de "voz" alternados com silêncio
    segment_duration = 5.0  # 5s de voz
    silence_duration = 1.0  # 1s de silêncio
    
    current_time = 0
    is_voice = True
    
    while current_time < duration:
        if is_voice:
            # Gera "voz" (mix de frequências)
            end_time = min(current_time + segment_duration, duration)
            start_idx = int(current_time * sr)
            end_idx = int(end_time * sr)
            
            seg_t = t[start_idx:end_idx]
            voice = (
                0.3 * np.sin(2 * np.pi * 200 * seg_t) +
                0.2 * np.sin(2 * np.pi * 400 * seg_t) +
                0.1 * np.sin(2 * np.pi * 800 * seg_t) +
                0.05 * np.random.randn(len(seg_t))  # Ruído
            )
            audio[start_idx:end_idx] = voice.astype(np.float32)
            current_time = end_time
        else:
            # Silêncio
            current_time += silence_duration
        
        is_voice = not is_voice
    
    # Normalizar
    max_val = np.abs(audio).max()
    if max_val > 0:
        audio = audio / max_val * 0.8
    
    # Salvar
    sf.write(str(output_path), audio, sr, subtype='PCM_16')
    
    file_size_mb = output_path.stat().st_size / 1024 / 1024
    print(f"✓ Criado: {output_path.name} ({file_size_mb:.1f} MB)")
    
    return output_path


def benchmark_v2(audio_path: Path, output_dir: Path) -> BenchmarkResult:
    """Benchmark do script V2 (optimized)"""
    print("\n" + "="*60)
    print("BENCHMARK V2 (prepare_segments_optimized.py)")
    print("="*60)
    
    from train.scripts.prepare_segments_optimized import (
        process_audio_file,
        load_config
    )
    
    config = load_config()
    
    mem_monitor = MemoryMonitor()
    mem_monitor.start()
    
    start_time = time.time()
    
    # Processar
    segments = process_audio_file(audio_path, output_dir, config)
    
    end_time = time.time()
    mem_monitor.update()
    
    # Calcular estatísticas
    execution_time = end_time - start_time
    peak_memory = mem_monitor.get_peak_increase()
    
    durations = [s['duration'] for s in segments]
    avg_duration = sum(durations) / len(durations) if durations else 0
    
    # Calcular tamanho dos arquivos escritos
    disk_writes = 0
    for seg in segments:
        seg_path = project_root / "train" / "data" / seg['audio_path']
        if seg_path.exists():
            disk_writes += seg_path.stat().st_size
    
    disk_writes_mb = disk_writes / 1024 / 1024
    
    return BenchmarkResult(
        version="V2 Optimized",
        peak_memory_mb=peak_memory,
        execution_time_s=execution_time,
        num_segments=len(segments),
        disk_writes_mb=disk_writes_mb,
        avg_segment_duration=avg_duration
    )


def benchmark_v3(audio_path: Path, output_dir: Path, parallel: bool = False) -> BenchmarkResult:
    """Benchmark do script V3 (ultra optimized)"""
    version_name = "V3 Ultra" + (" (Parallel)" if parallel else "")
    
    print("\n" + "="*60)
    print(f"BENCHMARK {version_name}")
    print("="*60)
    
    from train.scripts.prepare_segments_v2 import (
        process_audio_file,
        ProcessingConfig,
        load_config
    )
    
    config_dict = load_config()
    config = ProcessingConfig.from_yaml(config_dict)
    
    mem_monitor = MemoryMonitor()
    mem_monitor.start()
    
    start_time = time.time()
    
    # Processar
    segments = process_audio_file(audio_path, output_dir, config, 0, 1)
    
    end_time = time.time()
    mem_monitor.update()
    
    # Calcular estatísticas
    execution_time = end_time - start_time
    peak_memory = mem_monitor.get_peak_increase()
    
    durations = [s['duration'] for s in segments]
    avg_duration = sum(durations) / len(durations) if durations else 0
    
    # Calcular tamanho dos arquivos escritos
    disk_writes = 0
    for seg in segments:
        seg_path = project_root / "train" / "data" / seg['audio_path']
        if seg_path.exists():
            disk_writes += seg_path.stat().st_size
    
    disk_writes_mb = disk_writes / 1024 / 1024
    
    return BenchmarkResult(
        version=version_name,
        peak_memory_mb=peak_memory,
        execution_time_s=execution_time,
        num_segments=len(segments),
        disk_writes_mb=disk_writes_mb,
        avg_segment_duration=avg_duration
    )


def print_results(results: List[BenchmarkResult]):
    """Imprime resultados formatados"""
    print("\n" + "="*80)
    print("RESULTADOS DO BENCHMARK")
    print("="*80)
    
    # Header
    print(f"{'Versão':<20} {'RAM (MB)':<12} {'Tempo (s)':<12} {'Segmentos':<12} {'I/O (MB)':<12}")
    print("-" * 80)
    
    # Dados
    for r in results:
        print(f"{r.version:<20} {r.peak_memory_mb:<12.1f} {r.execution_time_s:<12.2f} "
              f"{r.num_segments:<12} {r.disk_writes_mb:<12.1f}")
    
    print("-" * 80)
    
    # Comparação
    if len(results) >= 2:
        v2 = results[0]
        v3 = results[1]
        
        mem_improvement = ((v2.peak_memory_mb - v3.peak_memory_mb) / v2.peak_memory_mb) * 100
        time_improvement = ((v2.execution_time_s - v3.execution_time_s) / v2.execution_time_s) * 100
        
        print("\nMELHORIAS V3 vs V2:")
        print(f"  Memória: {mem_improvement:+.1f}% ({v3.peak_memory_mb:.1f} MB vs {v2.peak_memory_mb:.1f} MB)")
        print(f"  Tempo: {time_improvement:+.1f}% ({v3.execution_time_s:.2f}s vs {v2.execution_time_s:.2f}s)")
        print(f"  Segmentos: {v3.num_segments} vs {v2.num_segments} (diferença: {v3.num_segments - v2.num_segments})")
    
    print("="*80)


def main():
    """Main function"""
    print("🔬 BENCHMARK DE SEGMENTAÇÃO DE ÁUDIO")
    print("="*80)
    
    # Criar áudio de teste
    # Teste 1: 5 minutos (arquivo médio)
    test_duration = 300.0  # 5 minutos
    audio_path = create_test_audio(test_duration)
    
    # Setup output
    output_dir = project_root / "train" / "data" / "processed" / "wavs"
    output_dir.mkdir(parents=True, exist_ok=True)
    
    results = []
    
    # Benchmark V2
    try:
        print("\n🔧 Limpando cache...")
        gc.collect()
        result_v2 = benchmark_v2(audio_path, output_dir)
        results.append(result_v2)
    except Exception as e:
        print(f"❌ Erro no V2: {e}")
        import traceback
        traceback.print_exc()
    
    # Benchmark V3
    try:
        print("\n🔧 Limpando cache...")
        gc.collect()
        result_v3 = benchmark_v3(audio_path, output_dir)
        results.append(result_v3)
    except Exception as e:
        print(f"❌ Erro no V3: {e}")
        import traceback
        traceback.print_exc()
    
    # Resultados
    if results:
        print_results(results)
    
    # Cleanup
    print(f"\n🧹 Arquivo de teste: {audio_path}")
    print(f"🧹 Segmentos em: {output_dir}")


if __name__ == "__main__":
    main()
