# 🎙️ XTTS-v2 Training Pipeline

Pipeline completo de preparação de dados e treinamento fine-tuning para XTTS-v2 (Coqui TTS).

## 📁 Estrutura

```
train/
├── config/
│   └── dataset_config.yaml      # Configuração de preparação de dados
├── data/
│   ├── videos.csv               # Catálogo de vídeos do YouTube
│   ├── raw/                     # Áudios baixados (22050Hz mono)
│   ├── processed/               # Segmentos processados com VAD
│   └── MyTTSDataset/            # Dataset final (formato LJSpeech)
│       ├── wavs/                # Arquivos de áudio
│       ├── metadata.csv         # Metadata completo
│       ├── metadata_train.csv   # Split de treino (90%)
│       └── metadata_val.csv     # Split de validação (10%)
├── scripts/
│   ├── download_youtube.py      # Download de áudios do YouTube
│   ├── segment_audio.py         # Segmentação com VAD
│   ├── transcribe_audio.py      # Transcrição com Whisper
│   ├── build_ljs_dataset.py     # Construção do dataset LJSpeech
│   └── pipeline.py              # Orquestrador completo
├── output/
│   ├── checkpoints/             # Checkpoints do fine-tuning
│   └── samples/                 # Amostras geradas durante treino
└── logs/                        # Logs de execução
```

## 🚀 Quickstart

### 1. Preparar Dataset

**Opção A: Pipeline completo (recomendado)**
```bash
# Executar todos os steps
python -m train.scripts.pipeline
```

**Opção B: Steps individuais**
```bash
# 1. Download de áudios do YouTube
python -m train.scripts.download_youtube

# 2. Segmentação com VAD (7-12s por segmento)
python -m train.scripts.segment_audio

# 3. Transcrição com Whisper
python -m train.scripts.transcribe_audio

# 4. Construção do dataset LJSpeech
python -m train.scripts.build_ljs_dataset
```

**Opção C: Pular steps já executados**
```bash
# Se já baixou os vídeos
python -m train.scripts.pipeline --skip-download

# Se já segmentou
python -m train.scripts.pipeline --skip-download --skip-segment
```

### 2. Configurar Dataset

Edite `train/config/dataset_config.yaml` para ajustar:
- **Audio**: Sample rate (22050Hz), canais (mono)
- **Segmentação**: Duração min/max (7-12s), threshold VAD
- **Transcrição**: Modelo Whisper (base/small/medium)
- **Qualidade**: Filtros de palavras, duração

### 3. Adicionar Vídeos

Edite `train/data/videos.csv`:
```csv
id,youtube_url,speaker,emotion,language,split,notes
1,https://www.youtube.com/watch?v=xxxxx,narrator1,neutral,pt-br,train,Podcast EP1
2,https://www.youtube.com/watch?v=yyyyy,narrator1,happy,pt-br,train,Podcast EP2
```

## 🎯 Especificações XTTS-v2

**Requisitos do modelo:**
- ✅ Sample rate: **22050Hz** (não 24000!)
- ✅ Formato: **WAV mono 16-bit**
- ✅ Duração ideal: **7-12 segundos** por segmento
- ✅ Idioma: **pt-BR** (Português Brasil)
- ✅ Formato dataset: **LJSpeech** (`wavs/audio_00001.wav|texto aqui`)

**Diferenças vs F5-TTS:**
| Feature | F5-TTS | XTTS-v2 |
|---------|--------|---------|
| Sample rate | 24000Hz | **22050Hz** |
| Duração ideal | 3-30s | **7-12s** |
| Formato metadata | `path|text` | `path|text` (igual) |
| Normalização texto | Case-sensitive | **Lowercase** |

## 📊 Pipeline de Dados

### 1. Download YouTube (`download_youtube.py`)
- Lê `videos.csv`
- Baixa áudio com yt-dlp
- Converte para WAV 22050Hz mono
- Salva em `data/raw/video_XXXXX.wav`

### 2. Segmentação VAD (`segment_audio.py`)
- Voice Activity Detection (energia RMS)
- Streaming (não carrega arquivo inteiro na RAM)
- Segmenta em 7-12s (ideal para XTTS-v2)
- Aplica fade in/out, normalização RMS
- Salva em `data/processed/video_XXXXX_YYYY.wav`

### 3. Transcrição (`transcribe_audio.py`)
- **Prioriza legendas do YouTube** (mais rápido, exato)
- **Fallback para Whisper** se não houver legendas
- Normalização pt-BR:
  - Números expandidos ("123" → "cento e vinte e três")
  - Lowercase (XTTS funciona melhor)
  - Remoção de caracteres especiais
- Salva em `data/processed/transcriptions.json`

### 4. Build Dataset (`build_ljs_dataset.py`)
- Copia WAVs para `MyTTSDataset/wavs/`
- Gera `metadata.csv` (formato LJSpeech)
- Aplica filtros de qualidade:
  - Duração: 7-12s
  - Palavras: 3-50
- Split train/val (90/10)

## 🔧 Troubleshooting

### Erro: "yt-dlp não encontrado"
```bash
pip install yt-dlp
```

### Erro: "ffmpeg not found"
```bash
# Ubuntu/Debian
sudo apt install ffmpeg

# macOS
brew install ffmpeg
```

### Erro: "Whisper model not found"
```bash
pip install openai-whisper
```

### Erro: "Memory error during segmentation"
Reduza `vad_chunk_duration` em `dataset_config.yaml`:
```yaml
segmentation:
  vad_chunk_duration: 5.0  # Reduzir de 10.0 para 5.0
```

### Erro: "Too many segments filtered out"
Ajuste filtros em `dataset_config.yaml`:
```yaml
quality_filters:
  enabled: false  # Desabilitar filtros temporariamente
```

## 📈 Métricas Esperadas

Para um dataset de qualidade:
- ✅ **1-2 horas** de áudio total (mínimo)
- ✅ **500-1000 segmentos** (7-12s cada)
- ✅ **Taxa de filtro < 20%** (poucos segmentos descartados)
- ✅ **Duração média ~10s** (ideal para XTTS-v2)

## 🔜 Próximos Passos

Após preparar o dataset:
1. **Treinar XTTS-v2**: `python -m train.scripts.train_xtts`
2. **Avaliar checkpoints**: `python -m train.scripts.evaluate`
3. **Integrar com API**: Modificar `app/engines/xtts_engine.py`

## 📚 Referências

- [XTTS-v2 Paper](https://arxiv.org/abs/2406.04904)
- [Coqui TTS Docs](https://docs.coqui.ai/)
- [LJSpeech Dataset Format](https://keithito.com/LJ-Speech-Dataset/)
- [Whisper by OpenAI](https://github.com/openai/whisper)
