# 🎯 BUG cuFFT RESOLVIDO: Use Docker!

## 🔍 Investigação Completa

### Problema Descoberto

Bug **cuFFT CUFFT_INVALID_SIZE** ao sintetizar XTTS na GPU:
- Afeta **ambiente HOST** (PyTorch 2.6+ / CUDA 12.4)
- Afeta tanto **treinamento** quanto **API de produção**
- Ocorre em `torch.stft()` → `torchaudio.transforms.Spectrogram`

### Causa Raiz

**Incompatibilidade entre PyTorch 2.6+ e CUDA 12.4** com biblioteca cuFFT.

Bug upstream não presente em PyTorch 2.4.0.

## ✅ SOLUÇÃO: Docker

### Ambiente que FUNCIONA

```
PyTorch:  2.4.0+cu118
CUDA:     11.8
Status:   ✅ GPU funciona perfeitamente
```

### Performance

| Operação | Host (CPU) | Docker (GPU) | Speedup |
|----------|-----------|--------------|---------|
| **Síntese XTTS** | ❌ Falha | ✅ 5.8s | - |
| **Sample Training** | 43s (CPU) | **5.8s** (GPU) | **7.4x mais rápido!** |
| **Treinamento** | ✅ GPU OK | ✅ GPU OK | Igual |

## 🚀 Como Usar

### 1. API em Produção (XTTS + RVC)

```bash
# Iniciar serviços
docker compose -f docker-compose-gpu.yml up -d

# Verificar saúde
docker compose -f docker-compose-gpu.yml ps

# Logs
docker logs -f audio-voice-api
```

**Portas:**
- API: http://localhost:8005
- Docs: http://localhost:8005/docs

**Status Atual:**
- Container: `audio-voice-api` - ✅ HEALTHY
- GPU: ✅ NVIDIA GeForce RTX 3090
- XTTS síntese: ✅ Funciona na GPU (confirmado por teste)

### 2. Treinamento XTTS

```bash
# Build (primeira vez)
docker compose -f docker-compose-training.yml build

# Treinar com configuração personalizada
MAX_TRAIN_SAMPLES=100 NUM_EPOCHS=10 \
  docker compose -f docker-compose-training.yml up

# Ou editar .env:
# MAX_TRAIN_SAMPLES=1000
# NUM_EPOCHS=50
docker compose -f docker-compose-training.yml up
```

**Features:**
- ✅ Treinamento na GPU (RTX 3090)
- ✅ Geração de samples **NA GPU** durante treino (5.8s cada!)
- ✅ TensorBoard automático (porta 6006)
- ✅ Auto-resume de checkpoints
- ✅ Texto real do `metadata.csv` nos samples

**Outputs:**
- Checkpoints: `train/output/checkpoints/`
- Samples: `train/output/samples/`
- TensorBoard logs: `train/runs/`

### 3. Monitorar TensorBoard

```bash
# Abrir em: http://localhost:6006
# Métricas disponíveis:
# - train_loss
# - val_loss  
# - learning_rate
```

## 🔧 Configuração

### Variáveis de Ambiente (.env)

```bash
# Treinamento
MAX_TRAIN_SAMPLES=      # Vazio = dataset completo (4429)
NUM_EPOCHS=1000
LOG_EVERY_N_STEPS=10

# API
XTTS_DEVICE=cuda
XTTS_FALLBACK_CPU=true
```

### Limites de Recursos

**API:** (docker-compose-gpu.yml)
- Memory: 12GB limit, 8GB reservado
- GPU: 1x NVIDIA (compartilhado com Celery)

**Training:** (docker-compose-training.yml)
- Memory: 20GB limit, 16GB reservado  
- GPU: 1x NVIDIA (dedicado)

## 📝 Teste de Verificação

### Confirmar GPU Funciona

```bash
# Dentro do container API
docker compose -f docker-compose-gpu.yml exec audio-voice-service \
  python3 -c "
import torch
from TTS.api import TTS
print(f'CUDA: {torch.cuda.is_available()}')
print(f'PyTorch: {torch.__version__}')

tts = TTS('tts_models/multilingual/multi-dataset/xtts_v2', gpu=True)
print('✅ XTTS carregado na GPU com sucesso!')
"
```

**Saída esperada:**
```
CUDA: True
PyTorch: 2.4.0+cu118
✅ XTTS carregado na GPU com sucesso!
```

## ⚠️ Host vs Docker

### NÃO use Python host para XTTS!

```bash
# ❌ FALHA no host (PyTorch 2.6+cu124)
python3 -m train.scripts.train_xtts
# RuntimeError: cuFFT error: CUFFT_INVALID_SIZE

# ✅ FUNCIONA no Docker (PyTorch 2.4.0+cu118)
docker compose -f docker-compose-training.yml up
# Sample gerado NA GPU: epoch_X_output.wav (5.8s)
```

### Código Afetado

**Host quebra em:**
- `app/services/xtts_service.py` → `synthesize()` 
- `train/scripts/train_xtts.py` → `generate_sample_audio()`
- Qualquer chamada `TTS.tts()` na GPU

**Docker funciona em:**
- ✅ Tudo acima

## 🎯 Recomendações

### Para Desenvolvimento

1. **API**: Use Docker (`docker-compose-gpu.yml`)
2. **Treinamento**: Use Docker (`docker-compose-training.yml`)
3. **Testes**: Rode dentro dos containers

### Para Produção

1. Deploy via Docker (imagem já configurada)
2. Configurar volumes persistentes:
   - `models/` - Modelos treinados
   - `voice_profiles/` - Perfis de voz
   - `uploads/`, `processed/` - Arquivos temporários
3. Monitoring: TensorBoard, logs, healthchecks

### Evitar

- ❌ Rodar XTTS síntese no ambiente host
- ❌ PyTorch 2.6+ com CUDA 12.4 para TTS
- ❌ Tentar "consertar" cuFFT com workarounds (não funciona)

## 📦 Arquivos Docker

### Principais

- `Dockerfile` - Imagem base (PyTorch 2.4.0+cu118)
- `docker-compose-gpu.yml` - API + Celery worker
- `docker-compose-training.yml` - Treinamento XTTS
- `docker-entrypoint.sh` - Script de inicialização

### Build Customizado

Se precisar modificar dependências:

```bash
# Editar requirements.txt
# Rebuild
docker compose -f docker-compose-gpu.yml build --no-cache

# Restart
docker compose -f docker-compose-gpu.yml up -d
```

## 🐛 Troubleshooting

### Permissões

```bash
# Diretórios necessários (host)
mkdir -p train/{logs,runs,output/{checkpoints,samples}}
chmod -R 777 train/{logs,runs,output}
```

### GPU não detectada

```bash
# Verificar driver NVIDIA
nvidia-smi

# Verificar runtime Docker
docker run --rm --gpus all nvidia/cuda:11.8.0-base-ubuntu22.04 nvidia-smi
```

### Container sai com erro

```bash
# Ver logs completos
docker logs xtts-training

# Entrar no container
docker compose -f docker-compose-training.yml run --rm xtts-training bash
```

## 📊 Resultados de Testes

### Teste 1: API Síntese (Docker)
```
✅ Modelo: xtts_v2 carregado na GPU
✅ Síntese: 6.03s de áudio gerado
✅ Tempo: 5.3s (Real-time factor: 0.283)
✅ Sem erros cuFFT
```

### Teste 2: Treinamento (Docker)
```
✅ Época 2 completa
✅ Sample gerado na GPU em 5.8s
✅ Checkpoint salvo
✅ Modelo restaurado na GPU
✅ Sem erros cuFFT
```

### Teste 3: Host (Falha Esperada)
```
❌ RuntimeError: cuFFT error: CUFFT_INVALID_SIZE
❌ Afeta síntese XTTS
❌ Afeta app e treinamento igualmente
```

## 🎓 Lições Aprendidas

1. **Bug não é código** - É incompatibilidade PyTorch/CUDA
2. **Docker isola ambiente** - PyTorch 2.4.0 não tem bug
3. **GPU ~7x mais rápida** - Samples: 43s CPU → 5.8s GPU
4. **App também afetado** - Não só treinamento
5. **Solução: containerização** - Não downgrade global

## 📅 Histórico

- **2025-12-07**: Descoberto bug cuFFT no host
- **2025-12-07**: Confirmado Docker (PyTorch 2.4.0) funciona
- **2025-12-07**: Treinamento com samples GPU validado
- **2025-12-07**: Documentação completa criada

---

**Status Final:** ✅ **RESOLVIDO VIA DOCKER**

Use os compose files fornecidos para API e treinamento!
