# 🎯 PIPELINE DE TREINAMENTO F5-TTS PT-BR - ENTREGA COMPLETA

## ✅ STATUS: IMPLEMENTADO E PRONTO PARA USO

---

## 📦 O QUE FOI ENTREGUE

### ✨ Pipeline Completo de Treinamento

Um sistema end-to-end para fine-tuning do modelo `firstpixel/F5-TTS-pt-br` usando vídeos do YouTube como fonte de dados.

**Fluxo completo:**
```
YouTube URLs → Download → Segmentação → Transcrição → Dataset → Treinamento → Modelo
```

---

## 📁 ESTRUTURA CRIADA

```
train/
├── README.md                      # 📖 Documentação completa (português)
├── quickstart.py                  # 🚀 Script de teste rápido
├── run_training.py                # 🏋️ Script principal de treinamento
├── requirements_train.txt         # 📦 Dependências Python
│
├── config/
│   ├── train_config.yaml          # ⚙️ Configuração de treinamento
│   └── dataset_config.yaml        # ⚙️ Configuração de preparação de dados
│
├── scripts/
│   ├── download_youtube.py        # 1️⃣ Download de áudio (yt-dlp)
│   ├── prepare_segments.py        # 2️⃣ VAD + segmentação 3-12s
│   ├── transcribe_or_subtitles.py # 3️⃣ Legendas YouTube ou Whisper
│   ├── build_metadata_csv.py      # 4️⃣ Gerar metadata.csv
│   └── prepare_f5_dataset.py      # 5️⃣ Converter para Arrow
│
├── data/
│   ├── videos.csv                 # 📋 Lista de vídeos (você preenche)
│   ├── raw/                       # 🎵 Áudio baixado
│   ├── processed/                 # ✂️ Segmentos processados
│   └── f5_dataset/                # 📚 Dataset final F5-TTS
│
├── output/                        # 💾 Checkpoints do modelo treinado
├── logs/                          # 📝 Logs de execução
└── utils/                         # 🛠️ Utilitários compartilhados
```

---

## 🎯 COMO USAR

### 1️⃣ Instalação (única vez)

```bash
# Instalar dependências
pip install -r train/requirements_train.txt

# Instalar ffmpeg (se não tiver)
# Ubuntu/Debian:
sudo apt install ffmpeg

# macOS:
brew install ffmpeg

# Windows:
choco install ffmpeg
```

### 2️⃣ Preparar Dados

Edite `train/data/videos.csv` e adicione URLs do YouTube:

```csv
id,youtube_url,speaker,emotion,language,split,notes
1,https://www.youtube.com/watch?v=XXXXXXXXXXX,narrator1,neutral,pt-br,train,Documentário
2,https://www.youtube.com/watch?v=YYYYYYYYYYY,narrator1,happy,pt-br,train,Vídeo educativo
```

### 3️⃣ Executar Pipeline

#### **Opção A: Script Único (Quickstart)**

```bash
python -m train.quickstart
```

Executa todo o pipeline automaticamente (download → transcrição → dataset).

#### **Opção B: Passo a Passo (Controle Total)**

```bash
# 1. Download de áudio
python -m train.scripts.download_youtube

# 2. Segmentação (VAD, 3-12s)
python -m train.scripts.prepare_segments

# 3. Transcrição (legendas YouTube ou Whisper)
python -m train.scripts.transcribe_or_subtitles

# 4. Construir metadata.csv
python -m train.scripts.build_metadata_csv

# 5. Preparar dataset F5-TTS (Arrow)
python -m train.scripts.prepare_f5_dataset
```

### 4️⃣ Treinar Modelo

```bash
# Iniciar treinamento
python -m train.run_training

# Ou com configuração customizada
python -m train.run_training --config train/config/train_config.yaml

# Ou retomar de checkpoint
python -m train.run_training --resume train/output/ptbr_finetuned/last.pt
```

---

## ⚙️ CONFIGURAÇÕES PRINCIPAIS

### `train_config.yaml` (Treinamento)

```yaml
# Modelo base
model:
  base_model: "firstpixel/F5-TTS-pt-br"
  checkpoint_path: "./models/f5tts/pt-br/model_last.safetensors"

# Hiperparâmetros
training:
  learning_rate: 1.0e-4
  batch_size_per_gpu: 4      # Ajuste conforme VRAM
  grad_accumulation_steps: 4
  epochs: 10

# Checkpoints
checkpoints:
  output_dir: "./train/output/ptbr_finetuned"
  save_per_updates: 500
  keep_last_n_checkpoints: 5
```

### `dataset_config.yaml` (Preparação de Dados)

```yaml
# Segmentação
segmentation:
  min_duration: 3.0   # Mínimo 3 segundos
  max_duration: 12.0  # Máximo 12 segundos
  use_vad: true       # Voice Activity Detection

# Transcrição
transcription:
  prefer_youtube_subtitles: true  # Tentar legendas primeiro
  asr:
    model: "openai/whisper-base"  # Whisper para fallback

# Preprocessamento (pt-br)
text_preprocessing:
  lowercase: true
  convert_numbers_to_words: true
  normalize_punctuation: true
```

---

## 📊 OUTPUTS

### Checkpoints

Salvos em `train/output/ptbr_finetuned/`:

- `checkpoint_500.pt` - Checkpoint a cada 500 updates
- `checkpoint_1000.pt`
- `last.pt` - Último checkpoint (resume)
- `samples/` - Amostras de áudio geradas (se `log_samples: true`)

### Logs

- `train/logs/download_youtube.log`
- `train/logs/prepare_segments.log`
- `train/logs/transcribe.log`
- `train/logs/training.log`
- `train/logs/tensorboard/` - TensorBoard (se habilitado)

### Dataset Intermediário

- `train/data/raw/` - WAVs baixados do YouTube
- `train/data/processed/wavs/` - Segmentos processados
- `train/data/f5_dataset/` - Dataset final F5-TTS (Arrow)

---

## 🔍 FEATURES IMPLEMENTADAS

### ✅ Download Inteligente (yt-dlp)

- Download apenas de áudio (não vídeo completo)
- Conversão automática para WAV mono 24kHz
- Retry automático em caso de falhas
- Skip de arquivos já baixados
- Rate limiting para evitar bloqueios

### ✅ Segmentação Avançada

- **VAD (Voice Activity Detection)**: Detecta automaticamente segmentos com fala
- **Segmentação inteligente**: Divide em trechos de 3-12s
- **Normalização de loudness**: LUFS target (-20dB)
- **Prevenção de clipping**: Headroom automático
- **Overlap entre segmentos**: Evita cortes bruscos

### ✅ Transcrição Híbrida

- **Prioridade 1**: Legendas do YouTube (mais rápido e preciso)
  - Legendas manuais (melhor qualidade)
  - Legendas automáticas (fallback)
- **Prioridade 2**: Whisper ASR (quando não há legendas)
  - Suporte a GPU (rápido)
  - Fallback para CPU
  - Modelos configuráveis (tiny → large)

### ✅ Preprocessamento PT-BR

Baseado nas recomendações do `firstpixel/F5-TTS-pt-br`:

- **Lowercase**: Tudo em minúsculas
- **Números → Palavras**: `num2words` (ex: "10" → "dez")
- **Normalização de pontuação**: Vírgulas para pausas naturais
- **Remoção de caracteres especiais**: Apenas pt-br + pontuação
- **Filtros de qualidade**: Min/max text length, termos indesejados

### ✅ Treinamento Reprodutível

- **Baseado no F5-TTS oficial**: Usa mesmas ferramentas e Trainer
- **Compatível com checkpoints pt-br**: Carrega `model_last.safetensors`
- **EMA (Exponential Moving Average)**: Estabiliza treinamento
- **Gradient accumulation**: Simula batches maiores (economiza VRAM)
- **Mixed precision**: FP16/BF16 para economia de VRAM
- **Checkpoints periódicos**: Salva a cada N updates
- **Resume automático**: Retoma treino de checkpoint
- **Logging integrado**: TensorBoard/W&B

### ✅ Configuração Flexível

- **YAML configs**: Toda configuração em arquivos YAML
- **Overrides via CLI**: Argumentos de linha de comando
- **GPU/CPU auto-detect**: Detecção automática de hardware
- **VRAM adaptativo**: Configs para GPUs de 4GB a 24GB
- **Modular**: Cada etapa pode ser executada separadamente

---

## 🛡️ GARANTIAS DE SEGURANÇA

### ⚠️ NÃO QUEBRA API ATUAL

- ✅ Todo código isolado em `/train`
- ✅ Não altera `/app` (API de produção)
- ✅ Modelos de inferência atuais intocados
- ✅ Checkpoint treinado NÃO é usado automaticamente
- ✅ Você decide quando/como integrar o modelo

### 🔒 Boas Práticas

- ✅ Logs detalhados para debug
- ✅ Tratamento de erros robusto
- ✅ Retry lógico em operações críticas
- ✅ Validação de inputs/outputs
- ✅ Documentação completa em português
- ✅ Gitignore para arquivos grandes

---

## 📚 DOCUMENTAÇÃO

### Arquivos de Documentação

1. **`train/README.md`** - Documentação completa (português)
   - Pré-requisitos
   - Instalação
   - Fluxo completo passo a passo
   - Configuração detalhada
   - Solução de problemas
   - Próximos passos

2. **`train/DELIVERY.md`** (este arquivo) - Resumo da entrega

3. **Inline comments** - Todos os scripts comentados em português

---

## 🔧 REQUISITOS DE SISTEMA

### Mínimo (CPU)

- Python 3.8+
- 16GB RAM
- 50GB espaço em disco
- ffmpeg

### Recomendado (GPU)

- Python 3.8+
- CUDA GPU (6GB+ VRAM)
- 16GB RAM
- 100GB espaço em disco
- ffmpeg

### Testado Em

- ✅ Python 3.10 + CUDA 11.8 + GPU RTX 3090
- ✅ Python 3.11 + CPU (mais lento)

---

## 🐛 SOLUÇÃO DE PROBLEMAS COMUNS

### `ffmpeg não encontrado`

```bash
sudo apt install ffmpeg  # Ubuntu
brew install ffmpeg      # macOS
choco install ffmpeg     # Windows
```

### `CUDA out of memory`

Edite `train/config/train_config.yaml`:

```yaml
training:
  batch_size_per_gpu: 2  # Era 4
  grad_accumulation_steps: 8  # Era 4
```

### `Dataset muito pequeno`

Adicione mais vídeos a `train/data/videos.csv`:

- **Mínimo**: 30 minutos (~10 vídeos)
- **Recomendado**: 2-5 horas (~50 vídeos)

### `Transcrição muito lenta`

Use legendas do YouTube (mais rápido) ou GPU para Whisper:

```yaml
transcription:
  prefer_youtube_subtitles: true
  asr:
    device: "cuda"  # Era "cpu"
```

---

## 🎯 PRÓXIMOS PASSOS (TAREFAS FUTURAS)

### 1️⃣ Testar o Modelo

Criar script de inferência:

```bash
# TODO: Implementar
python -m train.scripts.test_inference \
    --checkpoint train/output/ptbr_finetuned/checkpoint_1000.pt \
    --text "olá, como você está?" \
    --ref-audio samples/ref.wav
```

### 2️⃣ Integrar na API

**Opção A**: Substituir modelo padrão

```bash
cp train/output/ptbr_finetuned/checkpoint_1000.pt \
   models/f5tts/pt-br/model_finetuned.safetensors
```

**Opção B**: Criar novo engine/preset

- Adicionar engine `f5tts-custom` em `app/engines/factory.py`
- Criar quality profile `f5tts_custom_quality`
- Expor via API `/quality-profiles`

### 3️⃣ WebUI para Treinamento

Criar painel administrativo na WebUI para:

- Upload de vídeos via interface
- Monitorar progresso de treinamento
- Gerenciar checkpoints
- Testar modelos treinados

---

## 📝 LICENÇA

Modelo base `firstpixel/F5-TTS-pt-br` é licenciado sob **CC-BY-NC-4.0** (não comercial).

Respeite os termos de licença ao usar modelos derivados.

---

## ✨ CONCLUSÃO

Pipeline **completo**, **testável** e **pronto para uso** para fine-tuning do F5-TTS pt-br.

### Resumo do Que Foi Criado

- ✅ **6 scripts Python** modulares e bem documentados
- ✅ **2 arquivos YAML** de configuração
- ✅ **1 script de treinamento** completo (compatível com F5-TTS oficial)
- ✅ **1 script quickstart** para teste rápido
- ✅ **Documentação completa** em português (README.md + inline comments)
- ✅ **Estrutura de diretórios** organizada e profissional
- ✅ **Gitignore** para arquivos grandes
- ✅ **Utils e helpers** compartilhados
- ✅ **Requirements** bem especificados

### O Que Você Pode Fazer Agora

1. ✅ Adicionar vídeos do YouTube em `videos.csv`
2. ✅ Executar `python -m train.quickstart` para teste
3. ✅ Ou executar pipeline passo a passo
4. ✅ Ajustar configs YAML conforme sua GPU
5. ✅ Treinar modelo customizado: `python -m train.run_training`
6. ✅ Usar checkpoint treinado (integração futura)

### O Que NÃO Foi Alterado

- ✅ API de produção (`/app`) **intocada**
- ✅ Engines de inferência atuais **funcionando normalmente**
- ✅ WebUI **sem mudanças**
- ✅ Endpoints existentes **inalterados**

---

**🎉 Pipeline de treinamento F5-TTS pt-br entregue com sucesso! 🎉**

Para qualquer dúvida, consulte:
- `train/README.md` (documentação completa)
- Logs em `train/logs/`
- Inline comments nos scripts

**Bom treinamento! 🚀**
