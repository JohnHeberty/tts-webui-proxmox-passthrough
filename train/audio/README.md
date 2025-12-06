# F5-TTS Audio Processing Modules

Módulos de processamento de áudio para o pipeline de treinamento F5-TTS.

## Módulos Disponíveis

### 🎵 `io.py` - Audio I/O
Funções para carregar e salvar arquivos de áudio.

**Principais funções:**
- `load_audio(path, sample_rate)` - Carrega áudio com resampling automático
- `save_audio(audio, path, sample_rate)` - Salva áudio em WAV
- Suporta múltiplos formatos (WAV, MP3, FLAC, etc.)

**Exemplo:**
```python
from train.audio import load_audio, save_audio

# Carregar áudio
audio, sr = load_audio("input.mp3", sample_rate=24000)

# Salvar processado
save_audio(audio, "output.wav", sample_rate=24000)
```

---

### 🔇 `vad.py` - Voice Activity Detection
Detecção de atividade vocal para remover silêncios.

**Principais funções:**
- `detect_voice_activity(audio, sample_rate)` - Detecta regiões com fala
- `remove_silence(audio, sample_rate)` - Remove silêncios leading/trailing
- Usa algoritmo energy-based VAD

**Exemplo:**
```python
from train.audio.vad import detect_voice_activity, remove_silence

# Detectar regiões com voz
voice_regions = detect_voice_activity(audio, sr)

# Remover silêncios
audio_clean = remove_silence(audio, sr, threshold_db=-40)
```

---

### ✂️ `segmentation.py` - Audio Segmentation
Segmentação inteligente de áudio em chunks menores.

**Principais funções:**
- `segment_audio(audio, config)` - Segmenta áudio respeitando min/max duration
- `smart_segment_on_silence(audio, sr)` - Corta em pausas naturais
- Evita cortar no meio de palavras

**Exemplo:**
```python
from train.audio.segmentation import segment_audio

segments = segment_audio(
    audio,
    sample_rate=24000,
    min_duration=3.0,
    max_duration=10.0,
    target_duration=7.0
)

for i, segment in enumerate(segments):
    save_audio(segment, f"segment_{i}.wav", 24000)
```

---

### 🎚️ `normalization.py` - Audio Normalization
Normalização de volume (LUFS, peak, RMS).

**Principais funções:**
- `normalize_lufs(audio, target_lufs)` - Normaliza para LUFS target
- `normalize_peak(audio, target_db)` - Normaliza por peak
- `normalize_rms(audio, target_rms)` - Normaliza por RMS

**Exemplo:**
```python
from train.audio.normalization import normalize_lufs

# Normalizar para -23 LUFS (padrão broadcast)
audio_normalized = normalize_lufs(audio, sr, target_lufs=-23.0)
```

---

### 🎛️ `effects.py` - Audio Effects
Efeitos de áudio (EQ, compressão, noise reduction).

**Principais funções:**
- `apply_eq(audio, sr, low_shelf, high_shelf)` - Aplica equalizador
- `compress_audio(audio, threshold, ratio)` - Compressão dinâmica
- `reduce_noise(audio, sr)` - Redução de ruído (spectral subtraction)

**Exemplo:**
```python
from train.audio.effects import reduce_noise, apply_eq

# Reduzir ruído
audio_clean = reduce_noise(audio, sr)

# Aplicar EQ (realçar voz)
audio_eq = apply_eq(audio, sr, low_shelf=-3.0, high_shelf=2.0)
```

---

## Pipeline Completo

Exemplo de pipeline completo de processamento:

```python
from train.audio import load_audio, save_audio
from train.audio.vad import remove_silence
from train.audio.normalization import normalize_lufs
from train.audio.segmentation import segment_audio
from train.audio.effects import reduce_noise

# 1. Carregar áudio
audio, sr = load_audio("raw_audio.mp3", sample_rate=24000)

# 2. Remover silêncios
audio = remove_silence(audio, sr, threshold_db=-40)

# 3. Reduzir ruído
audio = reduce_noise(audio, sr)

# 4. Normalizar volume
audio = normalize_lufs(audio, sr, target_lufs=-23.0)

# 5. Segmentar
segments = segment_audio(
    audio, sr,
    min_duration=3.0,
    max_duration=10.0
)

# 6. Salvar segmentos
for i, segment in enumerate(segments):
    save_audio(segment, f"processed/segment_{i:04d}.wav", sr)
```

---

## Parâmetros Recomendados

### Para Dataset de Treinamento
```python
config = {
    "sample_rate": 24000,         # F5-TTS usa 24kHz
    "target_lufs": -23.0,          # LUFS padrão broadcast
    "vad_threshold_db": -40.0,     # Threshold VAD
    "min_duration": 3.0,           # Mínimo 3s
    "max_duration": 10.0,          # Máximo 10s
    "target_duration": 7.0,        # Ideal 7s
}
```

### Para Inferência
```python
config = {
    "sample_rate": 24000,
    "normalize": True,
    "remove_silence": True,
}
```

---

## Dependências

```bash
pip install librosa soundfile pydub pyloudnorm
```

Ou use o arquivo de requirements:
```bash
pip install -r train/requirements-train-lock.txt
```

---

## Testes

Para testar os módulos de áudio:

```bash
pytest tests/train/audio/ -v
```

---

## Referências

- **LUFS**: [EBU R128](https://tech.ebu.ch/loudness)
- **VAD**: Energy-based voice activity detection
- **Segmentation**: Smart silence-based segmentation

---

**Autor:** F5-TTS Training Pipeline  
**Versão:** 1.0  
**Data:** 2025-12-06
