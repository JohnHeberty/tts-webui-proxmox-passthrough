# 🎙️ Pipeline de Treinamento F5-TTS Português Brasileiro

**Pipeline completo e reprodutível para fine-tuning do modelo `firstpixel/F5-TTS-pt-br` usando vídeos do YouTube**

Este diretório contém toda a infraestrutura necessária para treinar modelos customizados de TTS em português brasileiro, desde o download de vídeos do YouTube até o modelo final pronto para uso.

---

## 📋 Índice

- [Visão Geral](#-visão-geral)
- [Pré-requisitos](#-pré-requisitos)
- [Instalação](#-instalação)
- [Fluxo Completo](#-fluxo-completo)
  - [1. Preparar Lista de Vídeos](#1-preparar-lista-de-vídeos)
  - [2. Download de Áudio](#2-download-de-áudio)
  - [3. Segmentação](#3-segmentação)
  - [4. Transcrição](#4-transcrição)
  - [5. Construir Metadata](#5-construir-metadata)
  - [6. Preparar Dataset](#6-preparar-dataset)
  - [7. Treinar Modelo](#7-treinar-modelo)
- [Configuração](#-configuração)
- [Estrutura de Diretórios](#-estrutura-de-diretórios)
- [Solução de Problemas](#-solução-de-problemas)
- [Próximos Passos](#-próximos-passos)

---

## 🎯 Visão Geral

Este pipeline automatiza todo o processo de fine-tuning do F5-TTS:

```mermaid
graph LR
    A[Vídeos YouTube] --> B[Download Áudio]
    B --> C[Segmentação 3-12s]
    C --> D[Transcrição/Legendas]
    D --> E[Dataset F5-TTS]
    E --> F[Fine-tuning]
    F --> G[Modelo Treinado]
```

**Principais características:**

- ✅ **Zero configuração manual**: Lista de vídeos → Modelo treinado
- ✅ **Suporta legendas do YouTube**: Preferência por legendas oficiais (melhor qualidade)
- ✅ **Fallback para Whisper**: Transcrição automática quando não há legendas
- ✅ **Processamento otimizado**: VAD, normalização de loudness, segmentação inteligente
- ✅ **Preprocessamento pt-br**: Lowercase, num2words, normalização de pontuação
- ✅ **Compatível com F5-TTS oficial**: Usa mesmas ferramentas e formato de dataset
- ✅ **Checkpoints periódicos**: Não perde progresso em caso de falha
- ✅ **TensorBoard/W&B**: Monitoramento em tempo real

---

## 🔧 Pré-requisitos

### Sistema

- **Python**: 3.8 ou superior
- **CUDA**: Recomendado para GPU (opcional para CPU)
- **ffmpeg**: Para processamento de áudio
  ```bash
  # Ubuntu/Debian
  sudo apt install ffmpeg
  
  # macOS
  brew install ffmpeg
  
  # Windows
  choco install ffmpeg
  ```

### GPU (Recomendado)

- **VRAM mínima**: 6GB (para batch_size=4)
- **VRAM recomendada**: 8-12GB
- **Para GPUs menores**: Ajustar `batch_size_per_gpu` e `grad_accumulation_steps` em `train_config.yaml`

---

## 📦 Instalação

### 1. Instalar Dependências Python

```bash
# Navegar até o diretório do projeto
cd /path/to/tts-webui-proxmox-passthrough

# Criar ambiente virtual (recomendado)
python -m venv venv
source venv/bin/activate  # Linux/Mac
# ou
.\venv\Scripts\activate  # Windows

# Instalar dependências
pip install -r train/requirements_train.txt
```

### 2. Verificar Instalação

```bash
# Verificar ffmpeg
ffmpeg -version

# Verificar CUDA (se disponível)
python -c "import torch; print(f'CUDA disponível: {torch.cuda.is_available()}')"

# Verificar F5-TTS
python -c "from f5_tts.model import CFM; print('F5-TTS OK!')"
```

---

## 🚀 Fluxo Completo

### 1. Preparar Lista de Vídeos

Edite o arquivo `train/data/videos.csv` com os links dos vídeos do YouTube:

```csv
id,youtube_url,speaker,emotion,language,split,notes
1,https://www.youtube.com/watch?v=XXXXXXXXXXX,narrator1,neutral,pt-br,train,Documentário sobre história
2,https://www.youtube.com/watch?v=YYYYYYYYYYY,narrator1,happy,pt-br,train,Vídeo educativo
3,https://www.youtube.com/watch?v=ZZZZZZZZZZZ,speaker_male,neutral,pt-br,val,Podcast
```

**Dicas para selecionar vídeos:**

- ✅ Áudio limpo, sem música de fundo
- ✅ Fala clara e pausada
- ✅ Legendas disponíveis (preferencialmente manuais)
- ✅ Variedade de tópicos para generalização
- ⚠️ Evitar: vídeos com múltiplos falantes, música alta, ruído excessivo

**Quanto áudio você precisa?**

- **Mínimo**: 30 minutos (~10 vídeos curtos)
- **Recomendado**: 2-5 horas (~20-50 vídeos)
- **Ideal**: 10+ horas (100+ vídeos)

---

### 2. Download de Áudio

Baixa áudio dos vídeos e converte para WAV mono 24kHz:

```bash
python -m train.scripts.download_youtube
```

**O que acontece:**

- Baixa apenas áudio (não vídeo completo)
- Converte para WAV mono 24kHz
- Aplica retry automático em caso de falhas
- Skip de arquivos já baixados
- Salva em `train/data/raw/`

**Saída esperada:**

```
📥 Iniciando download de 10 vídeos...

[1/10] Processando vídeo 1...
⬇️  Baixando [1]: https://www.youtube.com/watch?v=... (tentativa 1/3)
✅ video_00001.wav baixado com sucesso!
   Título: Como funciona a IA
   Duração: 625.3s

...

✅ Sucessos: 10
⏭️  Pulados: 0
❌ Falhas: 0
📁 Arquivos salvos em: train/data/raw
```

---

### 3. Segmentação

Processa áudios, aplicando VAD e segmentando em trechos de 3-12 segundos:

```bash
python -m train.scripts.prepare_segments
```

**O que acontece:**

- Voice Activity Detection (VAD) para encontrar segmentos com fala
- Segmentação em trechos de 3-12s
- Normalização de loudness (LUFS)
- Conversão para mono 24kHz 16-bit
- Salva em `train/data/processed/wavs/`

**Saída esperada:**

```
📄 Processando: video_00001.wav
   Duração total: 625.32s
   Segmentos com voz detectados: 45
   Segmentos finais: 52
   ✅ 52 segmentos salvos

...

📁 Arquivos originais processados: 10
✂️  Segmentos gerados: 487
⏱️  Duração média: 7.32s
⏱️  Duração total: 0.99h
📁 Segmentos salvos em: train/data/processed/wavs
```

---

### 4. Transcrição

Transcreve áudio usando legendas do YouTube (preferencial) ou Whisper:

```bash
python -m train.scripts.transcribe_or_subtitles
```

**O que acontece:**

1. **Tenta baixar legendas do YouTube** (mais rápido e preciso)
   - Legendas manuais (melhor)
   - Legendas automáticas (fallback)
2. **Se não houver legendas, usa Whisper** (mais lento)
   - Transcrição automática de alta qualidade
3. **Preprocessamento de texto**:
   - Lowercase
   - Números → palavras (`num2words`)
   - Normalização de pontuação
   - Remoção de caracteres especiais
4. **Salva em** `train/data/processed/transcriptions.json`

**Saída esperada:**

```
ETAPA 1: DOWNLOAD DE LEGENDAS DO YOUTUBE
==========================================

🔍 Buscando legendas para video_1...
   ✅ Legendas encontradas: video_00001.pt.vtt
   ✅ 12543 caracteres extraídos

...

ETAPA 2: TRANSCRIÇÃO DE SEGMENTOS
==========================================

[1/487] processed/wavs/video_00001_seg0000.wav
   📝 Usando legendas do YouTube
   ✅ 89 caracteres: a inteligência artificial está revolucionando o mundo moderno...

[50/487] processed/wavs/video_00003_seg0012.wav
   🎤 Transcrevendo com Whisper (openai/whisper-base)...
   ✅ 76 caracteres: neste vídeo vamos explorar como a tecnologia mudou...

...

📝 Segmentos transcritos: 487
📊 Legendas do YouTube: 8 vídeos
📄 Transcrições salvas em: train/data/processed/transcriptions.json
```

---

### 5. Construir Metadata

Gera `metadata.csv` no formato F5-TTS:

```bash
python -m train.scripts.build_metadata_csv
```

**O que acontece:**

- Lê transcrições de `transcriptions.json`
- Copia/organiza WAVs para `f5_dataset/wavs/`
- Gera `metadata.csv` no formato: `wavs/audio_00001.wav|texto aqui`
- Salva `duration.json` com durações

**Saída esperada:**

```
📁 Organizando arquivos WAV...
   Processados 100/487...
   Processados 200/487...
   ...
   ✅ 487 arquivos organizados

✅ metadata.csv salvo: train/data/f5_dataset/metadata.csv
   487 linhas

✅ duration.json salvo: train/data/f5_dataset/duration.json

📊 Total de amostras: 487
⏱️  Duração total: 0.99h
⏱️  Duração média: 7.32s
📁 Dataset em: train/data/f5_dataset
```

---

### 6. Preparar Dataset

Converte para formato Arrow (usado pelo F5-TTS):

```bash
python -m train.scripts.prepare_f5_dataset
```

**O que acontece:**

- Lê `metadata.csv`
- Valida arquivos e durações
- Gera `raw.arrow` (formato Arrow)
- Copia `vocab.txt` do modelo base pt-br
- Atualiza `duration.json`

**Saída esperada:**

```
📄 Lendo metadata.csv...
   487 linhas encontradas

✅ 487 amostras válidas (0 ignoradas)

💾 Salvando dataset em formato Arrow...
✅ raw.arrow salvo: train/data/f5_dataset/raw.arrow

💾 Atualizando duration.json...
✅ duration.json atualizado

📝 Configurando vocab.txt...
✅ vocab.txt copiado de: models/f5tts/pt-br/vocab.txt

==========================================
DATASET F5-TTS PRONTO!
==========================================
📊 Total de amostras: 487
⏱️  Duração total: 0.99h
⏱️  Duração média: 7.32s
📝 Vocab size: 245 caracteres
📁 Dataset salvo em: train/data/f5_dataset
   - raw.arrow
   - duration.json
   - vocab.txt
   - wavs/
==========================================
```

---

### 7. Treinar Modelo

Inicia o fine-tuning do F5-TTS pt-br:

```bash
python -m train.run_training
```

**Opções:**

```bash
# Usar config customizada
python -m train.run_training --config train/config/my_config.yaml

# Retomar treino de checkpoint
python -m train.run_training --resume train/output/ptbr_finetuned/last.pt

# Override dataset path
python -m train.run_training --dataset-path /caminho/custom/dataset
```

**O que acontece:**

1. Carrega configuração de `train_config.yaml`
2. Inicializa modelo F5-TTS (DiT ou UNetT)
3. Carrega checkpoint base `firstpixel/F5-TTS-pt-br`
4. Configura Trainer (optimizer, scheduler, EMA, etc.)
5. Carrega dataset do Arrow
6. Inicia treinamento:
   - Salva checkpoints a cada N updates
   - Loga métricas (TensorBoard/W&B)
   - Gera samples de áudio (se `log_samples: true`)

**Saída esperada:**

```
==========================================
F5-TTS FINE-TUNING - PORTUGUÊS BRASILEIRO
==========================================
Modelo base: firstpixel/F5-TTS-pt-br
Config: train/config/train_config.yaml

📁 Dataset: train/data/f5_dataset

==========================================
INICIALIZAÇÃO DO MODELO
==========================================
📝 Usando tokenizer: pinyin
🏗️  Inicializando modelo DiT...
✅ Modelo criado: 450.2M parâmetros
📥 Carregando checkpoint base: ./models/f5tts/pt-br/model_last.safetensors
✅ Checkpoint EMA carregado

==========================================
CONFIGURAÇÃO DO TREINAMENTO
==========================================
💻 Device: cuda
🏋️  Configurando Trainer...
✅ Trainer configurado

==========================================
CARREGAMENTO DO DATASET
==========================================
📚 Carregando dataset: ptbr_youtube_custom
✅ Dataset carregado: 487 amostras

==========================================
INICIANDO TREINAMENTO
==========================================
Epochs: 10
Batch size: 4
Grad accumulation: 4
Learning rate: 0.0001
Output dir: train/output/ptbr_finetuned
==========================================

Epoch 1/10: 100%|████████████| 30/30 [03:42<00:00, 7.41s/update]
loss: 0.4532, lr: 0.000100

Checkpoint saved: train/output/ptbr_finetuned/checkpoint_500.pt
Audio samples saved: train/output/ptbr_finetuned/samples/sample_500_*.wav

...

==========================================
✅ TREINAMENTO CONCLUÍDO!
==========================================
Checkpoints salvos em: train/output/ptbr_finetuned

Para usar o modelo treinado:
  1. Encontre o checkpoint em train/output/ptbr_finetuned/
  2. Teste com o script de inferência
  3. Integre na API (próxima tarefa)
==========================================
```

---

## ⚙️ Configuração

### `train_config.yaml` (Treinamento)

Principais parâmetros:

```yaml
# Modelo base
model:
  base_model: "firstpixel/F5-TTS-pt-br"
  checkpoint_path: "./models/f5tts/pt-br/model_last.safetensors"

# Hiperparâmetros
training:
  learning_rate: 1.0e-4
  batch_size_per_gpu: 4  # Ajuste conforme sua VRAM
  grad_accumulation_steps: 4
  epochs: 10

# Checkpoints
checkpoints:
  output_dir: "./train/output/ptbr_finetuned"
  save_per_updates: 500
  keep_last_n_checkpoints: 5
```

**Para GPUs com pouca VRAM (4-6GB):**

```yaml
training:
  batch_size_per_gpu: 2  # Reduzir batch size
  grad_accumulation_steps: 8  # Aumentar accumulation
  
advanced:
  gradient_checkpointing: true  # Economiza VRAM
```

### `dataset_config.yaml` (Preparação de Dados)

Principais parâmetros:

```yaml
# Segmentação
segmentation:
  min_duration: 3.0  # Mínimo 3s
  max_duration: 12.0  # Máximo 12s
  use_vad: true  # Voice Activity Detection

# Transcrição
transcription:
  prefer_youtube_subtitles: true  # Tentar legendas primeiro
  asr:
    model: "openai/whisper-base"  # tiny, base, small, medium, large

# Preprocessamento
text_preprocessing:
  lowercase: true
  convert_numbers_to_words: true
```

---

## 📁 Estrutura de Diretórios

```
train/
├── README.md                      # Esta documentação
├── __init__.py
├── run_training.py                # Script principal de treinamento
│
├── config/
│   ├── train_config.yaml          # Configuração de treinamento
│   └── dataset_config.yaml        # Configuração de preparação
│
├── scripts/
│   ├── __init__.py
│   ├── download_youtube.py        # 1. Download de áudio
│   ├── prepare_segments.py        # 2. Segmentação
│   ├── transcribe_or_subtitles.py # 3. Transcrição
│   ├── build_metadata_csv.py      # 4. Construir metadata
│   └── prepare_f5_dataset.py      # 5. Preparar dataset Arrow
│
├── data/
│   ├── videos.csv                 # Lista de vídeos do YouTube
│   ├── raw/                       # Áudio baixado (WAV 24kHz)
│   ├── subtitles/                 # Legendas do YouTube
│   ├── processed/
│   │   ├── wavs/                  # Segmentos processados
│   │   ├── segments_mapping.json  # Mapping segmentos → vídeos
│   │   └── transcriptions.json    # Transcrições
│   └── f5_dataset/                # Dataset final F5-TTS
│       ├── raw.arrow              # Dataset Arrow
│       ├── duration.json          # Durações
│       ├── vocab.txt              # Vocabulário
│       ├── metadata.csv           # Metadata (path|text)
│       └── wavs/                  # WAVs organizados
│
├── output/
│   └── ptbr_finetuned/            # Checkpoints do modelo treinado
│       ├── checkpoint_500.pt
│       ├── checkpoint_1000.pt
│       ├── last.pt
│       └── samples/               # Samples de áudio (se log_samples=true)
│
└── logs/
    ├── download_youtube.log
    ├── prepare_segments.log
    ├── transcribe.log
    ├── build_metadata.log
    ├── prepare_f5_dataset.log
    ├── training.log
    └── tensorboard/               # TensorBoard logs
```

---

## 🔍 Solução de Problemas

### Erro: `ffmpeg não encontrado`

```bash
# Ubuntu/Debian
sudo apt install ffmpeg

# macOS
brew install ffmpeg

# Windows
choco install ffmpeg
```

### Erro: `CUDA out of memory`

Reduza batch size em `train_config.yaml`:

```yaml
training:
  batch_size_per_gpu: 2  # Era 4
  grad_accumulation_steps: 8  # Era 4

advanced:
  gradient_checkpointing: true
```

### Erro: `yt-dlp não consegue baixar vídeo`

Alguns vídeos têm restrições de download. Tente:

1. Verificar se o vídeo é público
2. Atualizar yt-dlp: `pip install --upgrade yt-dlp`
3. Usar outro vídeo

### Dataset muito pequeno (< 30 minutos)

O modelo pode overfittar. Soluções:

1. Adicionar mais vídeos ao `videos.csv`
2. Reduzir número de epochs
3. Usar data augmentation (TODO: implementar)

### Transcrição com Whisper muito lenta

Whisper é lento em CPU. Opções:

1. Usar GPU: `device: cuda` em `dataset_config.yaml`
2. Usar modelo menor: `model: openai/whisper-tiny`
3. Preferir vídeos com legendas: `prefer_youtube_subtitles: true`

### Checkpoints ocupando muito espaço

Configure em `train_config.yaml`:

```yaml
checkpoints:
  keep_last_n_checkpoints: 3  # Manter apenas 3
  save_per_updates: 1000  # Salvar menos frequentemente
```

---

## 🎯 Próximos Passos

Após concluir o treinamento:

### 1. Testar o Modelo

```bash
# TODO: Criar script de inferência
python -m train.scripts.test_inference \
    --checkpoint train/output/ptbr_finetuned/checkpoint_1000.pt \
    --text "olá, como você está?" \
    --ref-audio samples/ref.wav \
    --output test_output.wav
```

### 2. Avaliar Qualidade

- Escutar samples gerados em `train/output/ptbr_finetuned/samples/`
- Comparar com modelo base `firstpixel/F5-TTS-pt-br`
- Avaliar naturalidade, pronúncia, prosódia

### 3. Integrar na API

**Opção A: Substituir modelo padrão**

```bash
# Copiar checkpoint para models/
cp train/output/ptbr_finetuned/checkpoint_1000.pt \
   models/f5tts/pt-br/model_finetuned.safetensors
```

Atualizar `.env`:

```bash
F5TTS_MODEL=models/f5tts/pt-br/model_finetuned.safetensors
```

**Opção B: Criar novo engine/preset** (Próxima tarefa)

- Adicionar engine `f5tts-custom` em `engines/factory.py`
- Criar quality profile `f5tts_custom_high_quality`
- Expor via API `/quality-profiles`

### 4. Continuar Treinamento (Opcional)

Se quiser mais epochs:

```bash
python -m train.run_training \
    --resume train/output/ptbr_finetuned/last.pt
```

Ajustar `epochs` em `train_config.yaml` antes.

---

## 📚 Referências

- **F5-TTS Original**: https://github.com/SWivid/F5-TTS
- **firstpixel/F5-TTS-pt-br**: https://huggingface.co/firstpixel/F5-TTS-pt-br
- **Whisper (OpenAI)**: https://github.com/openai/whisper
- **yt-dlp**: https://github.com/yt-dlp/yt-dlp

---

## 📝 Notas

### ⚠️ IMPORTANTE: Não Quebra API Atual

- ✅ Todo código de treinamento está isolado em `/train`
- ✅ API de produção (`/app`) não é alterada
- ✅ Modelos de inferência atuais continuam funcionando
- ✅ Checkpoint treinado NÃO é usado automaticamente

Para usar o modelo treinado, você deve **manualmente** integrá-lo na API (Tarefa futura).

### 🔒 Licença

O modelo base `firstpixel/F5-TTS-pt-br` é licenciado sob **CC-BY-NC-4.0** (não comercial).

Certifique-se de respeitar os termos de licença ao usar modelos derivados.

---

**✨ Boa sorte com o treinamento! ✨**

Para dúvidas ou problemas, consulte os logs em `train/logs/` ou abra uma issue.
