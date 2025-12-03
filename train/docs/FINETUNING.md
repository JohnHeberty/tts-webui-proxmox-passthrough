# Fine-tuning do F5-TTS com Modelo Pré-treinado PT-BR

## Visão Geral

Este guia explica como fazer fine-tuning do F5-TTS usando o modelo pré-treinado em português brasileiro (pt-br) como ponto de partida.

## Arquitetura do Modelo

O F5-TTS usa um modelo DiT (Diffusion Transformer) com EMA (Exponential Moving Average) para melhorar a estabilidade do treinamento.

### Componentes Principais

1. **Modelo Principal**: Pesos do transformer (DiT)
2. **EMA**: Média móvel exponencial dos pesos (melhora qualidade)
3. **Vocabulário**: Tokenizer customizado para pt-br

## Configuração do Fine-tuning

### 1. Dataset

O dataset deve estar em `train/data/f5_dataset/` com a seguinte estrutura:

```
f5_dataset/
├── metadata.csv       # audio_path|text
├── duration.json      # {"duration": [1.5, 2.3, ...]}
├── vocab.txt          # Vocabulário (um token por linha)
└── wavs/              # Arquivos de áudio
    ├── audio_001.wav
    ├── audio_002.wav
    └── ...
```

### 2. Modelo Pré-treinado

O modelo pt-br está em formato `.pt` (PyTorch nativo) e contém:

- `model`: Pesos do modelo principal
- `ema_model_state_dict`: Pesos do modelo EMA (opcional mas recomendado)
- `optimizer`: Estado do otimizador (opcional)
- `scheduler`: Estado do scheduler (opcional)

**Caminho**: `train/pretrained/F5-TTS-pt-br/pt-br/model_200000.pt`

### 3. Configuração (.env)

```bash
# Ativar fine-tuning
BASE_MODEL=firstpixel/F5-TTS-pt-br
PRETRAIN_MODEL_PATH=train/pretrained/F5-TTS-pt-br/pt-br/model_200000.pt
AUTO_DOWNLOAD_PRETRAINED=true

# Dataset
DATASET_NAME=f5_dataset
DATASET_PATH=train/data/f5_dataset

# Hiperparâmetros (ajustar conforme VRAM)
BATCH_SIZE=4
BATCH_SIZE_TYPE=sample
LEARNING_RATE=0.0001  # ou 1e-5 para fine-tuning mais conservador
GRAD_ACCUMULATION_STEPS=4
EPOCHS=1000
```

## Problemas Comuns e Soluções

### Erro de EMA

**Problema**: "KeyError: 'ema_model_state_dict'" ou modelo não carrega EMA

**Causa**: O modelo .pt pode não ter sido salvo com EMA, ou o código de loading está esperando um formato diferente.

**Solução 1 - Desabilitar EMA no início**:
```python
# Em finetune_cli.py, adicionar flag:
--no-ema  # Desabilita EMA nas primeiras epochs
```

**Solução 2 - Carregar apenas modelo principal**:
```python
# O código já trata isso:
checkpoint = torch.load(pretrain_path, map_location='cpu')
if 'model' in checkpoint:
    model.load_state_dict(checkpoint['model'])
else:
    model.load_state_dict(checkpoint)  # Arquivo contém apenas pesos
```

**Solução 3 - Converter modelo para SafeTensors** (recomendado para produção):
```bash
python scripts/convert_pt_to_safetensors.py \
    --input train/pretrained/F5-TTS-pt-br/pt-br/model_200000.pt \
    --output train/pretrained/F5-TTS-pt-br/pt-br/model_200000.safetensors
```

### Erro de Vocabulário

**Problema**: "Token não encontrado no vocabulário"

**Solução**: Usar o mesmo `vocab.txt` do modelo pré-treinado:
```bash
cp train/pretrained/F5-TTS-pt-br/pt-br/vocab.txt train/data/f5_dataset/
```

### Out of Memory (OOM)

**Problema**: GPU fica sem memória

**Soluções**:
1. Reduzir `BATCH_SIZE` (ex: 2 ou 1)
2. Aumentar `GRAD_ACCUMULATION_STEPS` (simula batch maior)
3. Usar `MIXED_PRECISION=fp16` ou `bf16`
4. Ativar gradient checkpointing: `gradient_checkpointing: true`

### Perda não diminui

**Problema**: Loss fica estável ou aumenta

**Causas possíveis**:
1. Learning rate muito alto → Reduzir para `1e-5` ou `5e-6`
2. Dataset muito pequeno → Precisa de pelo menos 1 hora de áudio
3. Transcrições incorretas → Verificar `metadata.csv`
4. Batch size muito pequeno → Aumentar ou usar gradient accumulation

## Melhores Práticas

### 1. Preparação do Dataset

- **Duração dos áudios**: 3-30 segundos (ideal: 5-15s)
- **Qualidade**: Taxa de amostragem 24kHz, mono
- **Transcrições**: 100% precisas, sem erros
- **Quantidade**: Mínimo 1 hora, ideal 10+ horas
- **Variedade**: Múltiplos speakers para melhor generalização

### 2. Hiperparâmetros Recomendados

#### Para datasets pequenos (1-5 horas):
```bash
BATCH_SIZE=2
LEARNING_RATE=5e-5
GRAD_ACCUMULATION_STEPS=8
EPOCHS=500
NUM_WARMUP_UPDATES=100
```

#### Para datasets médios (5-50 horas):
```bash
BATCH_SIZE=4
LEARNING_RATE=1e-4
GRAD_ACCUMULATION_STEPS=4
EPOCHS=200
NUM_WARMUP_UPDATES=200
```

#### Para datasets grandes (50+ horas):
```bash
BATCH_SIZE=8
LEARNING_RATE=7.5e-5
GRAD_ACCUMULATION_STEPS=2
EPOCHS=100
NUM_WARMUP_UPDATES=500
```

### 3. Monitoramento

Use TensorBoard para acompanhar:
```bash
tensorboard --logdir train/runs --port 6006
```

Métricas importantes:
- **Loss**: Deve diminuir consistentemente
- **Learning Rate**: Deve seguir warmup schedule
- **Samples**: Verificar qualidade do áudio gerado

### 4. Early Stopping

Configure para evitar overfitting:
```bash
EARLY_STOP_PATIENCE=5  # Para após 5 epochs sem melhora
EARLY_STOP_MIN_DELTA=0.001  # Melhora mínima significativa
```

## Troubleshooting Avançado

### Verificar se modelo carregou corretamente

```python
import torch

# Carregar checkpoint
ckpt = torch.load('train/pretrained/F5-TTS-pt-br/pt-br/model_200000.pt')

# Ver chaves
print("Chaves:", ckpt.keys())

# Verificar se tem EMA
if 'ema_model_state_dict' in ckpt:
    print("✅ Modelo tem EMA")
else:
    print("❌ Modelo não tem EMA")

# Verificar tamanho do modelo
if 'model' in ckpt:
    print(f"Parâmetros: {sum(p.numel() for p in ckpt['model'].values()) / 1e6:.1f}M")
```

### Converter checkpoint se necessário

Se o modelo não tem a estrutura esperada:

```python
import torch

# Carregar
old = torch.load('model_200000.pt')

# Criar nova estrutura
new = {
    'model': old if isinstance(old, dict) and 'model' not in old else old.get('model'),
    'iteration': 200000,
}

# Salvar
torch.save(new, 'model_200000_fixed.pt')
```

## Referências

- [F5-TTS Official Training Guide](https://github.com/SWivid/F5-TTS/tree/main/src/f5_tts/train)
- [Finetune Discussion #57](https://github.com/SWivid/F5-TTS/discussions/57)
- [Modelo PT-BR HuggingFace](https://huggingface.co/firstpixel/F5-TTS-pt-br)

## Próximos Passos

1. ✅ Configurar .env com modelo pré-treinado
2. ✅ Preparar dataset em train/data/f5_dataset
3. ✅ Iniciar treinamento: `python -m train.run_training`
4. ⏳ Monitorar via TensorBoard
5. 🎯 Avaliar checkpoints gerados
6. 🚀 Usar modelo fine-tuned em produção
