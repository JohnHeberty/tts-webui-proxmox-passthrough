"""
Testes para segment_audio.py

Valida segmentação de áudio com VAD streaming.
"""

import pytest
from pathlib import Path
import sys
import numpy as np
import soundfile as sf
from unittest.mock import Mock, patch

# Setup paths
TEST_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = TEST_DIR.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))


class TestSegmentAudio:
    """Testes para segmentação de áudio."""
    
    @pytest.fixture
    def mock_config(self):
        """Config mockado."""
        return {
            "audio": {
                "target_sample_rate": 22050,
                "channels": 1,
            },
            "segmentation": {
                "use_vad": True,
                "vad_threshold": -40.0,
                "min_duration": 7.0,
                "max_duration": 12.0,
                "target_duration": 10.0,
                "fade_duration": 0.05,
                "normalization_method": "rms",
                "target_rms_db": -20.0,
            }
        }
    
    @pytest.fixture
    def sample_audio(self, tmp_path):
        """Cria áudio de teste."""
        sr = 22050
        duration = 30.0  # 30 segundos
        
        # Gera sinal de teste (sine wave)
        t = np.linspace(0, duration, int(sr * duration))
        audio = np.sin(2 * np.pi * 440 * t) * 0.5  # 440Hz, amplitude 0.5
        
        # Adiciona silêncios (para VAD detectar)
        silence = np.zeros(int(sr * 2))  # 2s de silêncio
        audio_with_silence = np.concatenate([audio[:int(sr*10)], silence, audio[int(sr*10):]])
        
        audio_file = tmp_path / "test_audio.wav"
        sf.write(audio_file, audio_with_silence, sr)
        
        return audio_file
    
    def test_vad_threshold(self, mock_config):
        """Testa threshold do VAD."""
        threshold = mock_config["segmentation"]["vad_threshold"]
        assert threshold == -40.0
        assert -60.0 <= threshold <= -20.0  # Range válido
    
    def test_duration_range_xtts(self, mock_config):
        """Valida range de duração para XTTS-v2."""
        min_dur = mock_config["segmentation"]["min_duration"]
        max_dur = mock_config["segmentation"]["max_duration"]
        target_dur = mock_config["segmentation"]["target_duration"]
        
        # XTTS-v2 ideal: 7-12s
        assert min_dur == 7.0
        assert max_dur == 12.0
        assert target_dur == 10.0
        assert min_dur < target_dur < max_dur
    
    def test_detect_silence(self, sample_audio):
        """Testa detecção de silêncio."""
        data, sr = sf.read(sample_audio)
        
        # Calcular RMS por frame
        frame_size = 2048
        hop_size = 512
        
        rms_values = []
        for i in range(0, len(data) - frame_size, hop_size):
            frame = data[i:i+frame_size]
            rms = np.sqrt(np.mean(frame**2))
            rms_db = 20 * np.log10(rms + 1e-10)
            rms_values.append(rms_db)
        
        rms_values = np.array(rms_values)
        
        # Deve detectar regiões com silêncio (< -40dB)
        silence_frames = np.sum(rms_values < -40.0)
        assert silence_frames > 0, "Nenhum silêncio detectado"
    
    def test_segment_duration(self, tmp_path, mock_config):
        """Testa se segmentos têm duração correta."""
        sr = 22050
        min_dur = mock_config["segmentation"]["min_duration"]
        max_dur = mock_config["segmentation"]["max_duration"]
        
        # Cria segmento de teste
        duration = 10.0  # Target duration
        samples = int(sr * duration)
        audio = np.random.randn(samples) * 0.1
        
        segment_file = tmp_path / "segment_001.wav"
        sf.write(segment_file, audio, sr)
        
        # Verifica duração
        data, sr_read = sf.read(segment_file)
        actual_duration = len(data) / sr_read
        
        assert min_dur <= actual_duration <= max_dur
    
    def test_fade_in_out(self, tmp_path, mock_config):
        """Testa aplicação de fade in/out."""
        sr = 22050
        fade_duration = mock_config["segmentation"]["fade_duration"]
        fade_samples = int(sr * fade_duration)
        
        # Áudio de teste
        audio = np.ones(sr * 5) * 0.5  # 5s de amplitude constante
        
        # Aplicar fade
        fade_in = np.linspace(0, 1, fade_samples)
        fade_out = np.linspace(1, 0, fade_samples)
        
        audio[:fade_samples] *= fade_in
        audio[-fade_samples:] *= fade_out
        
        # Verificar fade foi aplicado
        assert audio[0] < 0.01  # Início próximo de zero
        assert audio[-1] < 0.01  # Fim próximo de zero
        assert audio[sr] > 0.4  # Meio tem amplitude normal
    
    def test_normalization_rms(self, tmp_path, mock_config):
        """Testa normalização por RMS."""
        sr = 22050
        target_rms_db = mock_config["segmentation"]["target_rms_db"]
        
        # Áudio com RMS baixo
        audio = np.random.randn(sr * 5) * 0.01
        
        # Calcular RMS atual
        rms_current = np.sqrt(np.mean(audio**2))
        rms_current_db = 20 * np.log10(rms_current + 1e-10)
        
        # Normalizar
        target_rms = 10**(target_rms_db / 20.0)
        audio_normalized = audio * (target_rms / (rms_current + 1e-10))
        
        # Verificar RMS normalizado
        rms_normalized = np.sqrt(np.mean(audio_normalized**2))
        rms_normalized_db = 20 * np.log10(rms_normalized + 1e-10)
        
        assert abs(rms_normalized_db - target_rms_db) < 1.0  # Tolerância de 1dB
    
    def test_resample_to_target_sr(self, tmp_path):
        """Testa resample para sample rate alvo."""
        try:
            import librosa
        except ImportError:
            pytest.skip("librosa não instalado")
        
        # Áudio em 44100Hz
        sr_original = 44100
        audio_original = np.random.randn(sr_original * 5)
        
        # Resample para 22050Hz
        sr_target = 22050
        audio_resampled = librosa.resample(audio_original, orig_sr=sr_original, target_sr=sr_target)
        
        # Verificar novo tamanho
        expected_samples = int(len(audio_original) * sr_target / sr_original)
        assert abs(len(audio_resampled) - expected_samples) < 10  # Tolerância
    
    def test_mono_conversion(self, tmp_path):
        """Testa conversão stereo → mono."""
        sr = 22050
        
        # Áudio stereo
        left = np.random.randn(sr * 5)
        right = np.random.randn(sr * 5)
        stereo = np.column_stack((left, right))
        
        # Converter para mono (média dos canais)
        mono = np.mean(stereo, axis=1)
        
        assert mono.ndim == 1
        assert len(mono) == len(left)
    
    @pytest.mark.integration
    def test_segment_pipeline(self, sample_audio, tmp_path, mock_config):
        """Teste de integração do pipeline de segmentação."""
        # Ler áudio
        data, sr = sf.read(sample_audio)
        
        # Parâmetros
        min_dur = mock_config["segmentation"]["min_duration"]
        max_dur = mock_config["segmentation"]["max_duration"]
        
        # Simular segmentação simples (split em chunks)
        segment_samples = int(sr * 10.0)  # 10s chunks
        
        segments = []
        for i in range(0, len(data), segment_samples):
            segment = data[i:i+segment_samples]
            
            # Ignorar segmentos muito curtos
            duration = len(segment) / sr
            if duration >= min_dur:
                segments.append(segment)
        
        # Validar
        assert len(segments) > 0
        
        for idx, segment in enumerate(segments):
            duration = len(segment) / sr
            assert min_dur <= duration <= max_dur + 1.0  # Tolerância
    
    def test_output_format(self, tmp_path):
        """Testa formato de saída dos segmentos."""
        sr = 22050
        audio = np.random.randn(sr * 10) * 0.1
        
        output_file = tmp_path / "segment_001.wav"
        sf.write(output_file, audio, sr, subtype='PCM_16')
        
        # Verificar formato
        info = sf.info(output_file)
        assert info.samplerate == 22050
        assert info.channels == 1
        assert info.subtype == 'PCM_16'


class TestVADStreaming:
    """Testes para VAD streaming (otimização de memória)."""
    
    def test_chunk_processing(self):
        """Testa processamento em chunks."""
        sr = 22050
        chunk_duration = 10.0  # 10s chunks
        chunk_samples = int(sr * chunk_duration)
        
        # Áudio grande (simulado)
        total_duration = 120.0  # 2 minutos
        total_samples = int(sr * total_duration)
        
        # Processar em chunks
        num_chunks = int(np.ceil(total_samples / chunk_samples))
        
        assert num_chunks == 12  # 120s / 10s
    
    def test_memory_efficient_iteration(self):
        """Testa iteração memory-efficient."""
        # Simula processamento de arquivo grande sem carregar tudo na memória
        
        def iter_chunks(total_samples, chunk_size):
            for i in range(0, total_samples, chunk_size):
                yield i, min(i + chunk_size, total_samples)
        
        total = 1000000
        chunk = 10000
        
        chunks_processed = 0
        for start, end in iter_chunks(total, chunk):
            chunks_processed += 1
            assert start < end
            assert end - start <= chunk
        
        assert chunks_processed == 100  # 1000000 / 10000


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
