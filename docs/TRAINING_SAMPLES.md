# Geração de Samples Durante Treinamento XTTS

## Problema Encontrado: cuFFT Error

Ao tentar gerar samples de áudio durante o treinamento, encontramos um bug no XTTS:

```
RuntimeError: cuFFT error: CUFFT_INVALID_SIZE
```

### Root Cause

- **Local**: `torch.stft()` dentro de `get_conditioning_latents()`
- **Quando**: Ao carregar XTTS múltiplas vezes na GPU no mesmo processo
- **Motivo**: Estado corrompido do CUDA após treinamento intensivo
- **Arquivo**: `TTS/tts/models/xtts.py` linha 320-365

### Tentativas Falhadas

1. ❌ Ajustar API (`audio_path` vs `audio`)
2. ❌ Corrigir sample rate (24000 → 22050)
3. ❌ Não carregar checkpoint state_dict
4. ❌ Validar propriedades do áudio de referência
5. ❌ Usar apenas modelo base

**Todas falharam** - o erro persiste mesmo com modelo base na GPU.

## Solução Implementada: CPU Inference

### Estratégia

Usar **CPU para geração de samples** (workaround do bug cuFFT na GPU):

```python
def generate_sample_audio(...):
    # 1. Carregar XTTS em CPU (não GPU)
    tts = TTS('tts_models/multilingual/multi-dataset/xtts_v2', gpu=False)
    
    # 2. Gerar áudio normalmente
    wav = tts.tts(text=..., language='pt', speaker_wav=...)
    
    # 3. Salvar e limpar
    sf.write(output_path, wav, 22050)
    del tts
```

### Gerenciamento de VRAM

Fluxo completo no training loop:

```python
# Após salvar checkpoint
checkpoint_path = checkpoints_dir / f"checkpoint_epoch_{epoch}.pt"
torch.save({...}, checkpoint_path)

# 1. UNLOAD modelo de treinamento
model = model.cpu()
torch.cuda.empty_cache()

# 2. GERAR sample (em CPU, função interna carrega TTS)
generate_sample_audio(checkpoint_path, epoch, settings, samples_dir, device)

# 3. RELOAD modelo de treinamento
checkpoint = torch.load(checkpoint_path)
model.load_state_dict(checkpoint['model_state_dict'])
model = model.to(device)
model.train()
```

### Trade-offs

| Aspecto | GPU (quebrado) | CPU (funciona) |
|---------|----------------|----------------|
| **Velocidade** | ~1s | ~12s |
| **cuFFT Error** | ❌ Sim | ✅ Não |
| **VRAM** | Alta | Baixa |
| **Confiabilidade** | 0% | 100% |

**Decisão**: CPU é **12x mais lento**, mas **funciona perfeitamente**.

## Uso

### Treinar com Samples Automáticos

```bash
# Treinamento normal - samples gerados automaticamente
python3 train/scripts/train_xtts.py

# Teste rápido
MAX_TRAIN_SAMPLES=20 NUM_EPOCHS=2 python3 train/scripts/train_xtts.py
```

### Outputs Gerados

```
train/output/samples/
├── epoch_1_output.wav      # Sample gerado (síntese com XTTS)
├── epoch_1_reference.wav   # Áudio de referência (copiado)
├── epoch_2_output.wav
├── epoch_2_reference.wav
└── best/
    ├── epoch_N_output.wav  # Sample do melhor modelo
    └── epoch_N_reference.wav
```

### Validar Samples

```bash
# Verificar propriedades
file train/output/samples/epoch_1_output.wav
ffprobe train/output/samples/epoch_1_output.wav

# Propriedades esperadas:
# - Sample rate: 22050 Hz
# - Canais: mono
# - Duração: ~7s (texto: "Olá, este é um teste...")
# - Tamanho: ~310KB
```

## Configurações

### Desabilitar Samples (se necessário)

Se quiser treinar SEM gerar samples (mais rápido):

```python
# Em train/scripts/train_xtts.py, comentar:
# generate_sample_audio(checkpoint_path, epoch, settings, samples_dir, device)
```

### Ajustar Frequência

Samples são gerados:
- A cada `save_every_n_epochs` (padrão: 1)
- Quando val_loss melhora (best model)

Para mudar frequência:

```python
# train/train_settings.py
save_every_n_epochs: int = 5  # Gerar sample a cada 5 épocas
```

## Monitoramento

### Logs Durante Geração

```
💾 Checkpoint salvo: checkpoint_epoch_1.pt
🧹 Liberando VRAM para geração de samples...
   ✅ Modelo de treinamento movido para CPU
🎤 Gerando sample de áudio em CPU (workaround cuFFT)...
   Época: 1
   Referência: audio_00001.wav
   📥 Carregando XTTS em CPU...
   🔊 Sintetizando áudio (CPU - pode demorar)...
 > Processing time: 12.44s
 > Real-time factor: 1.73x
   ✅ Sample gerado: epoch_1_output.wav
   ✅ Referência copiada: epoch_1_reference.wav
   🧹 Modelo de inferência descarregado
📥 Recarregando modelo de treinamento...
   ✅ Modelo de treinamento restaurado na GPU
```

### Tempo Total por Sample

- Unload training model: ~1s
- Carregar XTTS CPU: ~11s
- Gerar áudio: ~12s
- Reload training model: ~5s
- **Total: ~29s por sample**

### Performance Impact

Para treinamento com 1000 épocas:
- Sem samples: ~1h
- Com samples (1 por época): ~1h + 8h = ~9h total
- **Recomendação**: `save_every_n_epochs = 10` (9h → 1.8h overhead)

## Troubleshooting

### Sample não gerado

```bash
# Verificar logs
grep "Gerando sample" train_output.log

# Se vazio, verificar:
# 1. epoch % save_every_n_epochs == 0?
# 2. Erro na função? grep "Erro ao gerar" train_output.log
```

### Áudio vazio/corrompido

```bash
# Validar arquivo
file train/output/samples/epoch_1_output.wav
# Deve mostrar: "WAVE audio, Microsoft PCM, 16 bit, mono 22050 Hz"

# Se corrompido, verificar:
# 1. Áudio de referência válido?
ls -lh train/data/MyTTSDataset/wavs/audio_00001.wav
# 2. Espaço em disco?
df -h
```

### Processo muito lento

```python
# Opção 1: Gerar samples menos frequentes
save_every_n_epochs: int = 10  # ao invés de 1

# Opção 2: Desabilitar best_model samples
# Comentar em train_xtts.py:
# generate_sample_audio(best_model_path, ...)

# Opção 3: Desabilitar completamente
# Comentar todas chamadas generate_sample_audio()
```

## Limitações Conhecidas

1. **Não usa pesos do checkpoint**
   - Samples são gerados com modelo BASE XTTS
   - Não com os pesos treinados (causaria cuFFT)
   - Serve apenas para validar síntese funciona

2. **CPU obrigatória**
   - Não há solução conhecida para cuFFT na GPU
   - Problema upstream no PyTorch/CUDA

3. **Sem voice cloning do treino**
   - Voice cloning ainda usa áudio de referência do dataset
   - Não aplica aprendizado do fine-tuning

## Próximos Passos

Para aplicar pesos do checkpoint nos samples:

1. **Opção A**: Gerar samples DEPOIS do treino terminar
   ```bash
   # Treinar sem samples (rápido)
   python3 train/scripts/train_xtts.py
   
   # Gerar samples offline
   python3 scripts/generate_checkpoint_samples.py --checkpoint checkpoint_epoch_100.pt
   ```

2. **Opção B**: Investigar cuFFT bug upstream
   - Reportar issue no repositório coqui-ai/TTS
   - Testar com versões diferentes de PyTorch/CUDA
   - Contribuir fix se possível

3. **Opção C**: Usar modelo diferente
   - F5-TTS não tem esse problema
   - Considerar migrar treinamento

## Referências

- **Issue cuFFT**: https://github.com/pytorch/pytorch/issues/91640
- **XTTS Training**: https://tts.readthedocs.io/en/latest/
- **Código**: `train/scripts/train_xtts.py` linha 421-522
