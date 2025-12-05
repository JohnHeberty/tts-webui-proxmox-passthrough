# 🎙️ Pipeline de Treinamento F5-TTS Português Brasileiro

**Pipeline completo e otimizado para fine-tuning do modelo `firstpixel/F5-TTS-pt-br` usando vídeos do YouTube**

---

## 📋 Índice

- [Visão Geral](#-visão-geral)
- [Pré-requisitos](#-pré-requisitos)
- [Instalação Rápida](#-instalação-rápida)
- [Pipeline Completo](#-pipeline-completo)
- [Scripts Disponíveis](#-scripts-disponíveis)
- [Estrutura de Diretórios](#-estrutura-de-diretórios)
- [Otimizações e Melhorias](#-otimizações-e-melhorias)
- [Solução de Problemas](#-solução-de-problemas)

---

## 🎯 Visão Geral

Pipeline automatizado para treinar modelos F5-TTS em português brasileiro a partir de vídeos do YouTube.

**Fluxo do Pipeline:**

```
Vídeos YouTube → Download Áudio → Segmentação → Transcrição → Normalização → 
Validação QA → Dataset F5-TTS → Treinamento → Modelo Treinado
```

**Características:**

- ✅ **Otimizado para Baixa Memória**: Processamento em streaming (<500MB RAM)
- ✅ **Transcrição Multi-Modelo**: Whisper Base (rápido) + Medium (qualidade)
- ✅ **Normalização Inteligente**: Números, %, moedas → forma falada
- ✅ **Validação Automática**: Detecta e re-processa transcrições problemáticas
- ✅ **Retomada de Progresso**: Suporta interrupção e continuação
- ✅ **Formato F5-TTS Nativo**: Dataset em Arrow format compatível

---

## 🔧 Pré-requisitos

### Sistema

```bash
# Ubuntu/Debian
sudo apt install ffmpeg python3.11 python3-pip

# Verificar instalação
ffmpeg -version
python3 --version  # >= 3.8
```

### Hardware

- **CPU**: Qualquer (GPU recomendada para treinamento)
- **RAM**: 8GB+ (segmentação otimizada usa <500MB)
- **GPU**: NVIDIA com 8GB+ VRAM (opcional, mas recomendado)
- **Disco**: ~10GB para 2-3h de áudio

---

## 📦 Instalação Rápida

```bash
# 1. Clonar repositório (se ainda não tiver)
cd /home/tts-webui-proxmox-passthrough

# 2. Instalar dependências
pip3 install -r train/requirements_train.txt

# 3. Verificar instalação
python3 -c "import whisper, torch; print('✅ Tudo instalado!')"
```

---

## 🚀 Pipeline Completo

### Etapa 1: Preparar Lista de Vídeos

Edite `train/data/videos.csv` com URLs do YouTube:

```csv
# Comentários começam com #
# Formato: id,youtube_url,speaker,emotion,language,split,notes

1,https://www.youtube.com/watch?v=XXXXXXXXXXX,narrator1,neutral,pt-br,train,Finanças
2,https://www.youtube.com/watch?v=YYYYYYYYYYY,narrator1,neutral,pt-br,train,Empreendedorismo
3,https://www.youtube.com/watch?v=ZZZZZZZZZZZ,narrator2,neutral,pt-br,val,Marketing
```

**Dicas:**
- ✅ Áudio limpo, sem música de fundo forte
- ✅ Um falante principal por vídeo
- ✅ Fala clara e natural
- ⚠️ Evite: múltiplos falantes, música alta, ruído

**Quantidade recomendada:**
- Mínimo: 30 min (~10 vídeos)
- Ideal: 2-5 horas (~20-50 vídeos)

---

### Etapa 2: Download de Áudio

```bash
python3 -m train.scripts.simple_download
```

**O que faz:**
- Baixa apenas áudio (economia de banda)
- Converte para WAV mono 24kHz 16-bit
- Ignora comentários (#) no CSV
- Retry automático em falhas
- Salva em `train/data/raw/`

**Saída esperada:**
```
📥 Iniciando download de 11 vídeos...
[1/11] video_00001.wav - ✅ Sucesso (625s)
[2/11] video_00002.wav - ✅ Sucesso (842s)
...
✅ 11/11 vídeos baixados com sucesso
```

---

### Etapa 3: Segmentação Otimizada

```bash
python3 -m train.scripts.prepare_segments_optimized
```

**O que faz:**
- **Processamento em streaming**: Carrega áudio em chunks de 30s
- **VAD simples**: Detecção de voz por RMS threshold
- **Segmentação 3-12s**: Trechos ideais para F5-TTS
- **Baixíssimo uso de RAM**: <500MB (vs 27GB do script antigo!)
- **Garbage collection agressivo**: Libera memória continuamente

**Saída esperada:**
```
🎧 Processando: video_00001.wav
   ✂️  1197 segmentos criados
   💾 Salvos em: train/data/processed/wavs/
   🧠 RAM: ~450MB
```

**Arquivos gerados:**
- `train/data/processed/wavs/video_XXXXX_segXXXX.wav` (áudio)
- `train/data/processed/segments_mapping.json` (metadados)

---

### Etapa 4: Transcrição com Whisper

```bash
python3 -m train.scripts.transcribe_segments
```

**O que faz:**
- **Modelo Base**: Transcrição rápida em lote
- **Batch processing**: 10 segmentos por vez
- **Gestão de memória**: Libera GPU entre batches
- **Retomada automática**: Continua de onde parou
- **Pós-processamento**: Lowercase, limpeza de espaços

**Configuração** (`train/config/dataset_config.yaml`):
```yaml
asr:
  model: "openai/whisper-base"  # Rápido
  language: "pt"
  batch_size: 10
```

**Saída esperada:**
```
🎤 Transcrevendo 1197 segmentos...
[1/1197] video_00001_seg0000.wav
   ✅ "novecentos reais por semana de dentro da sua casa..."
[2/1197] video_00001_seg0001.wav
   ✅ "usando o mercado livre sem trânsito sem..."
...
✅ 1197/1197 transcritos
💾 Salvo em: train/data/processed/transcriptions.json
```

**Tempo estimado:**
- Base model: ~2-4 horas para 1200 segmentos (RTX 3090)
- Medium model: ~5-8 horas

---

### Etapa 5: Normalização de Texto

```bash
python3 -m train.scripts.normalize_transcriptions
```

**O que faz:**
- **Números → Palavras**: `2025` → `"dois mil e vinte e cinco"`
- **Percentuais**: `3%` → `"três porcento"`
- **Moeda**: `R$ 100` → `"cem reais"`
- **Símbolos**: `&` → `"e"`, `/` → `"barra"`
- **Ordinais**: `1º` → `"primeiro"`
- **Preserva original**: Cria backup antes de modificar

**Biblioteca utilizada**: `num2words` com suporte pt_BR

**Saída esperada:**
```
📝 Normalizando 1196 transcrições...

Exemplo 1:
   Original:    "Em 2025 tivemos 3% de crescimento"
   Normalizado: "em dois mil e vinte e cinco tivemos três porcento de crescimento"

Exemplo 2:
   Original:    "Custa R$ 1.500,00"
   Normalizado: "custa mil e quinhentos reais"

✅ 79/1196 normalizadas (6.6%)
💾 Backup salvo: transcriptions_backup_XXXXXXXX.json
```

---

### Etapa 6: Validação e Re-processamento

```bash
python3 -m train.scripts.validate_and_reprocess
```

**O que detecta:**
- ❌ Caracteres inválidos (%, /, \, etc)
- ❌ Palavras repetidas excessivamente (>5x)
- ❌ Letras isoladas com pontuação
- ❌ Textos muito curtos (<3 palavras)
- ❌ Muitas palavras não-portuguesas (>70%)
- ❌ Sequências repetidas suspeitas

**O que faz:**
- Re-transcreve áudios problemáticos com **Whisper Medium** (mais preciso)
- Valida novo texto
- Atualiza JSON se aprovado
- Gera relatório de problemas

**Saída esperada:**
```
🔍 Validando 1196 transcrições...

📈 Resultados:
   ✅ Válidas: 1092 (91.3%)
   ❌ Inválidas: 104 (8.7%)

⚠️  Problemas encontrados:
   - Caracteres inválidos: 17
   - Palavras repetidas: 6
   - Letras isoladas: 12

❓ Re-processar 104 áudios com modelo 'medium'? [s/N]: s

🔄 Re-processando...
[1/104] video_00001_seg0000.wav
   ✅ Novo texto válido!
...
✅ 98/104 re-processados com sucesso
```

---

### Etapa 7: Construir Metadata

```bash
python3 -m train.scripts.build_metadata_csv
```

**O que faz:**
- Combina transcrições + metadados de áudio
- Cria `metadata.csv` no formato F5-TTS
- Filtra segmentos inválidos
- Valida duração, texto, caminhos

**Formato do metadata.csv:**
```csv
audio_path|text|duration|speaker
wavs/video_00001_seg0000.wav|novecentos reais por semana...|12.0|narrator1
wavs/video_00001_seg0001.wav|usando o mercado livre sem...|8.5|narrator1
```

**Saída esperada:**
```
📊 Construindo metadata...
   Transcrições: 1196
   Áudios válidos: 1196
   Metadata gerado: 1196 linhas

💾 Salvo em: train/data/processed/metadata.csv
```

---

### Etapa 8: Preparar Dataset F5-TTS

```bash
python3 -m train.scripts.prepare_f5_dataset
```

**O que faz:**
- Converte `metadata.csv` → formato Arrow
- Cria splits train/val
- Calcula estatísticas do dataset
- Prepara para F5-TTS trainer

**Saída esperada:**
```
🎯 Preparando dataset F5-TTS...

📊 Estatísticas:
   Total de amostras: 1196
   Duração total: 2.8h
   Train: 1076 (90%)
   Val: 120 (10%)

💾 Dataset salvo em: train/output/dataset/
   ├── train.arrow
   ├── val.arrow
   └── metadata.json
```

---

### Etapa 9: Treinar Modelo

```bash
python3 -m train.run_training
```

**Configuração** (`train/config/train_config.yaml`):
```yaml
model:
  base_model: "firstpixel/F5-TTS-pt-br"
  
training:
  epochs: 10
  batch_size_per_gpu: 4
  learning_rate: 1e-5
  gradient_accumulation_steps: 4
  
hardware:
  mixed_precision: "fp16"  # RTX 3090
  num_gpus: 1
```

**Saída esperada:**
```
🚀 Iniciando treinamento F5-TTS...
   Base: firstpixel/F5-TTS-pt-br
   GPU: NVIDIA RTX 3090 (24GB)
   Samples: 1076 train, 120 val

Epoch 1/10
[████████████████████████] 269/269 - loss: 0.245
Validação: loss=0.198

...

✅ Treinamento concluído!
💾 Modelo salvo em: train/output/checkpoints/final/
```

**Tempo estimado:**
- RTX 3090: ~2-4 horas (10 epochs, 1200 samples)
- RTX 3060: ~4-8 horas

---

## 📜 Scripts Disponíveis

### Scripts de Processamento

| Script | Função | Uso |
|--------|--------|-----|
| `simple_download.py` | Download de áudio do YouTube | `python -m train.scripts.simple_download` |
| `prepare_segments_optimized.py` | Segmentação otimizada (streaming) | `python -m train.scripts.prepare_segments_optimized` |
| `transcribe_segments.py` | Transcrição com Whisper Base | `python -m train.scripts.transcribe_segments` |
| `normalize_transcriptions.py` | Normalização de texto (números, %, etc) | `python -m train.scripts.normalize_transcriptions` |
| `validate_and_reprocess.py` | Validação QA + re-processamento | `python -m train.scripts.validate_and_reprocess` |
| `build_metadata_csv.py` | Gerar metadata.csv | `python -m train.scripts.build_metadata_csv` |
| `prepare_f5_dataset.py` | Converter para formato F5-TTS | `python -m train.scripts.prepare_f5_dataset` |
| `run_training.py` | Treinar modelo F5-TTS | `python -m train.run_training` |

### Scripts Legados (não usar)

| Script | Status | Motivo |
|--------|--------|--------|
| `prepare_segments.py` | ⚠️ Obsoleto | Consumia 27GB RAM, use `prepare_segments_optimized.py` |
| `transcribe_or_subtitles.py` | ⚠️ Obsoleto | Legendas do YouTube não funcionaram bem |
| `download_youtube.py` | ⚠️ Obsoleto | Problemas com CSV, use `simple_download.py` |

### Utilitários

| Módulo | Função |
|--------|--------|
| `train/utils/text_normalizer.py` | Normalização de texto (classe `TextNormalizer`) |

---

## 📁 Estrutura de Diretórios

```
train/
├── config/
│   ├── dataset_config.yaml      # Config de processamento
│   └── train_config.yaml         # Config de treinamento
├── data/
│   ├── videos.csv                # Lista de vídeos (INPUT)
│   ├── raw/                      # Áudios baixados
│   │   ├── video_00001.wav
│   │   └── ...
│   └── processed/
│       ├── wavs/                 # Segmentos (3-12s)
│       │   ├── video_00001_seg0000.wav
│       │   └── ...
│       ├── segments_mapping.json # Metadados dos segmentos
│       ├── transcriptions.json   # Transcrições normalizadas
│       └── metadata.csv          # Dataset final
├── scripts/
│   ├── simple_download.py
│   ├── prepare_segments_optimized.py
│   ├── transcribe_segments.py
│   ├── normalize_transcriptions.py
│   ├── validate_and_reprocess.py
│   ├── build_metadata_csv.py
│   ├── prepare_f5_dataset.py
│   └── ...
├── utils/
│   ├── text_normalizer.py        # Normalização de texto
│   └── ...
├── logs/                          # Logs de execução
├── output/
│   ├── dataset/                   # Dataset Arrow
│   └── checkpoints/               # Modelos treinados
├── requirements_train.txt
└── README.md
```

---

## ⚡ Otimizações e Melhorias

### 1. Segmentação Ultra Otimizada ⭐

**Evolução das Versões:**

| Versão | RAM Pico | Velocidade | Features |
|--------|----------|------------|----------|
| V1 Original | 27 GB | Lento | Carrega tudo na RAM |
| V2 Optimized | 400 MB | Médio | Chunks + GC estratégico |
| **V3 Ultra** | **185 MB** | **Rápido** | Streaming nativo + paralelo |

**V3 Ultra (`prepare_segments_v2.py`)** - ⭐ **RECOMENDADO**

**Técnicas Avançadas:**
- ✅ `soundfile.blocks` para streaming zero-copy
- ✅ Object pooling (reutiliza meter, buffers)
- ✅ Processamento paralelo opcional
- ✅ VAD stateful com contexto entre blocos
- ✅ Batch I/O otimizado
- ✅ Suporta arquivos maiores que RAM disponível

**Uso:**
```bash
# Processamento sequencial (RAM limitada)
python3 -m train.scripts.prepare_segments_v2

# Processamento paralelo (máxima velocidade)
python3 -m train.scripts.prepare_segments_v2 --parallel --workers 4
```

**Benchmark (arquivo 2h @ 48kHz):**
- Memória: 185 MB (vs 27 GB original = **99.3% redução**)
- Tempo: 3 min com 4 cores (vs 18 min = **83% mais rápido**)
- Qualidade: Mesma precisão de segmentação

📖 **Guia completo:** `train/scripts/OPTIMIZATION_GUIDE.md`

### 2. Transcrição Multi-Modelo

**Estratégia:**
- **Whisper Base**: Transcrição inicial rápida (bulk processing)
- **Whisper Medium**: Re-processamento de áudios com problemas
- Validação automática detecta erros e aciona modelo melhor

### 3. Normalização de Texto

**Biblioteca:** `num2words` (pt_BR nativo)

**Conversões:**
```python
"2025" → "dois mil e vinte e cinco"
"3%" → "três porcento"
"R$ 100" → "cem reais"
"1º" → "primeiro"
"&" → "e"
```

**Benefícios:**
- Modelo aprende números falados naturalmente
- Elimina caracteres problemáticos (%, /, \)
- Melhora consistência do treinamento

### 4. Sistema de Validação QA

**Checks automáticos:**
- Caracteres inválidos
- Palavras repetidas >5x
- Letras isoladas com pontuação
- Textos muito curtos
- Palavras não-portuguesas >70%

**Ação:**
- Re-processamento com Whisper Medium
- Relatório de problemas
- Backup automático

---

## 🐛 Solução de Problemas

### Erro: "KeyError: 'youtube_url'"

**Causa:** Linhas de comentário (#) no `videos.csv`

**Solução:** Scripts atualizados ignoram linhas com `#`. Se usar script antigo:
```python
# Adicionar antes de processar CSV
lines = [l for l in lines if not l.startswith('#')]
```

### Erro: "RuntimeError: Model whisper-base not found"

**Causa:** Nome do modelo incorreto

**Solução:** Usar apenas `base`, `medium`, `large` (sem prefixo `whisper-`)

```yaml
# dataset_config.yaml
asr:
  model: "openai/whisper-base"  # Correto
```

### Consumo Alto de RAM (>10GB)

**Causa:** Usando `prepare_segments.py` antigo

**Solução:** Usar `prepare_segments_optimized.py`
```bash
python3 -m train.scripts.prepare_segments_optimized
```

### Transcrições com Caracteres Estranhos (%, /, \)

**Solução:** Executar normalização
```bash
python3 -m train.scripts.normalize_transcriptions
```

### CUDA Out of Memory

**Solução 1:** Reduzir batch size
```yaml
# train_config.yaml
training:
  batch_size_per_gpu: 2  # era 4
  gradient_accumulation_steps: 8  # era 4
```

**Solução 2:** Usar FP16
```yaml
hardware:
  mixed_precision: "fp16"
```

---

## 📊 Estatísticas de Exemplo

**Projeto Atual (11 vídeos):**
- ✅ Áudios baixados: 11 (2h 45min)
- ✅ Segmentos gerados: 1197
- ✅ Transcrições válidas: 1092 (91.3%)
- ✅ Re-processadas: 104 (8.7%)
- ✅ Normalizadas: 79 (6.6%)
- ✅ Dataset final: ~2.8h de áudio limpo

**Tempo Total:**
- Download: ~15 min
- Segmentação: ~8 min
- Transcrição Base: ~2.5h
- Validação + Re-processamento: ~30 min
- Normalização: <1 min
- **Total: ~3.5 horas**

---

## 🎓 Próximos Passos

Após treinar seu modelo:

1. **Testar o modelo**
   ```bash
   python -c "from f5_tts import F5TTS; model = F5TTS.from_pretrained('train/output/checkpoints/final'); model.infer('Olá mundo')"
   ```

2. **Integrar na aplicação principal**
   - Copiar checkpoint para `models/f5tts/custom/`
   - Atualizar `app/engines/f5tts_engine.py`

3. **Iterar e melhorar**
   - Adicionar mais vídeos
   - Ajustar hyperparameters
   - Experimentar com diferentes vozes

---

## 📚 Referências

- [F5-TTS Original](https://github.com/SWivid/F5-TTS)
- [F5-TTS Portuguese](https://huggingface.co/firstpixel/F5-TTS-pt-br)
- [OpenAI Whisper](https://github.com/openai/whisper)
- [num2words](https://github.com/savoirfairelinux/num2words)

---

## 📝 Changelog

### 2025-12-02 - Melhorias Majors

- ✅ **Segmentação otimizada**: Redução de RAM de 27GB → <500MB
- ✅ **Sistema de validação QA**: Detecta e re-processa problemas
- ✅ **Normalização de texto**: Números, %, moeda → forma falada
- ✅ **Multi-modelo**: Base (rápido) + Medium (qualidade)
- ✅ **Documentação completa**: README atualizado com todos os detalhes

---

**Desenvolvido com ❤️ para a comunidade de TTS em português brasileiro**
