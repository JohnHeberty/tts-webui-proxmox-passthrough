# F5-TTS Training - Setup Guide

## Quick Start

### 1. Preparar Dataset
```bash
# Seus arquivos devem estar em: train/data/f5_dataset/
# Estrutura:
train/data/f5_dataset/
├── audio/          # Arquivos .wav (24kHz, mono)
└── metadata.csv    # Formato: audio_file|text|duration
```

### 2. Configurar Treinamento
```bash
# Editar train/.env com suas configurações
cp train/.env.example train/.env
nano train/.env
```

Principais configurações:
- `EPOCHS=1000` - Número máximo de epochs
- `BATCH_SIZE=4` - Ajustar conforme VRAM disponível
- `EARLY_STOP_PATIENCE=1000` - Parar se não melhorar em N epochs
- `LOG_SAMPLES_PER_UPDATES=250` - Gerar samples a cada 250 updates

### 3. Executar Treinamento
```bash
# Método 1: Script simplificado
./run.sh

# Método 2: Direto via Python
cd train && python3 run_training.py
```

### 4. Monitorar Progresso
- **TensorBoard**: http://192.168.18.134:6006 (iniciado automaticamente)
- **Logs**: Terminal mostra progress bars em tempo real
- **Checkpoints**: `train/output/ptbr_finetuned/model_*.pt`
- **Samples**: `train/output/ptbr_finetuned/samples/`

## Requisitos

- **GPU**: NVIDIA com 16GB+ VRAM (RTX 3090, A100, etc)
- **Python**: 3.11+
- **Dependências**: Instaladas via `requirements_train.txt`
- **Modelo base**: firstpixel/F5-TTS-pt-br (baixado automaticamente)

## Estrutura de Arquivos

```
train/
├── .env                    # Configuração (EDITAR AQUI)
├── .env.example            # Template
├── run_training.py         # Script principal
├── data/                   # Dataset
│   └── f5_dataset/
├── output/                 # Checkpoints e samples
│   └── ptbr_finetuned/
├── runs/                   # Logs do TensorBoard
└── logs/                   # Logs de execução
```

## Funcionalidades

✅ **Auto-resume**: Continua de onde parou se encontrar `model_last.pt`  
✅ **Early stopping**: Para automaticamente se não melhorar  
✅ **TensorBoard**: Visualização de métricas em tempo real  
✅ **Sample generation**: Gera áudios de teste durante treinamento  
✅ **Checkpoints incrementais**: Salva a cada N updates  

## Troubleshooting

**TensorBoard não inicia:**
```bash
# Verificar se porta 6006 está livre
lsof -i :6006
# Iniciar manualmente
tensorboard --logdir=train/runs --host=0.0.0.0 --port=6006
```

**CUDA out of memory:**
```bash
# Reduzir batch size no .env
BATCH_SIZE=2
GRAD_ACCUMULATION_STEPS=8  # Compensar com mais acumulação
```

**Dataset não encontrado:**
```bash
# Verificar paths
ls train/data/f5_dataset/audio/
head train/data/f5_dataset/metadata.csv
```
