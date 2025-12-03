# F5-TTS Training Pipeline - Documentation

## Quick Links

📚 **[Setup Guide](SETUP.md)** - Installation and first run  
⚙️ **[Configuration](CONFIGURATION.md)** - All `.env` parameters explained  
🚀 **[Usage Guide](USAGE.md)** - Training, monitoring, and troubleshooting  

## Overview

Pipeline completo para fine-tuning do modelo F5-TTS em português brasileiro.

**Features:**
- ✅ Configuração via `.env` (sem editar código)
- ✅ Auto-resume de checkpoints
- ✅ Early stopping inteligente
- ✅ TensorBoard integrado
- ✅ Geração de samples durante treinamento
- ✅ Progress bars em tempo real

## Quick Start

```bash
# 1. Configure
cp train/.env.example train/.env
nano train/.env

# 2. Run
./run.sh

# 3. Monitor
# TensorBoard: http://192.168.18.134:6006
# Terminal: Live progress bars
```

## File Structure

```
train/
├── docs/              # This documentation
│   ├── README.md
│   ├── SETUP.md
│   ├── CONFIGURATION.md
│   └── USAGE.md
├── .env               # Configuration (EDIT HERE)
├── .env.example       # Template
├── run_training.py    # Main script
├── data/              # Dataset
├── output/            # Checkpoints + samples
├── runs/              # TensorBoard logs
└── logs/              # Execution logs
```

## Getting Help

1. **Setup issues**: Check [SETUP.md](SETUP.md)
2. **Configuration questions**: See [CONFIGURATION.md](CONFIGURATION.md)
3. **Runtime problems**: Refer to [USAGE.md](USAGE.md)

## Model Info

- **Architecture**: F5-TTS (DiT-based, 335.8M parameters)
- **Base Model**: firstpixel/F5-TTS-pt-br
- **Vocabulary**: 44 caracteres (português brasileiro)
- **Audio**: 24kHz mono WAV
- **Training**: Mixed precision FP16

## System Requirements

- **GPU**: NVIDIA 16GB+ VRAM (RTX 3090, A100, etc)
- **Python**: 3.11+
- **CUDA**: 12.1+
- **Storage**: ~50GB (model + checkpoints)
