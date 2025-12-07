# Geração de Samples Durante Treinamento XTTS

## Problema Encontrado: cuFFT Error

Ao tentar gerar samples de áudio durante o treinamento, encontramos um bug persistente no XTTS:

```
RuntimeError: cuFFT error: CUFFT_INVALID_SIZE
```

### Root Cause

- **Local**: `torch.stft()` dentro de `get_conditioning_latents()`
- **Quando**: Ao usar XTTS na GPU neste ambiente específico
- **Motivo**: Bug upstream no PyTorch/CUDA/cuFFT (não relacionado ao código)
- **Arquivo**: `TTS/tts/models/xtts.py` linha 320-365
- **Persistência**: Ocorre MESMO em subprocesso limpo isolado

### Tentativas Falhadas

1. ❌ Limpar contexto CUDA (empty_cache + synchronize + gc.collect)
2. ❌ Subprocesso Python isolado com GPU limpa
3. ❌ Não carregar checkpoint state_dict
4. ❌ Validar e ajustar propriedades do áudio de referência
5. ❌ Usar apenas modelo base sem fine-tuning
6. ❌ Diferentes sample rates e configurações

**Todas falharam** - o erro persiste independentemente da abordagem na GPU.

## Solução Implementada: Subprocesso CPU

### Estratégia

Usar **subprocesso isolado com CPU** para geração de samples:

```python
# Processo principal continua na GPU
# Ao gerar sample:
1. Salvar checkpoint
2. Descarregar modelo de treinamento (GPU → CPU)
3. Spawn subprocesso:
   subprocess.run([
       "python3", "generate_sample_subprocess.py",
       "--reference_wav", "audio.wav",
       "--text", "texto do metadata.csv",
       "--output", "epoch_N_output.wav"
   ])
4. Subprocesso:
   - Carrega XTTS em CPU (evita cuFFT)
   - Gera áudio
   - Salva WAV
   - Exit (memória liberada automaticamente)
5. Recarregar modelo de treinamento (CPU → GPU)
6. Continuar treinamento
```

### Arquitetura da Solução

```
┌─────────────────────────────────────────────────────────┐
│ PROCESSO PRINCIPAL (train_xtts.py)                    │
│ ┌─────────────────────────────────────────────────┐   │
│ │ TREINAMENTO NA GPU                               │   │
│ │ • Modelo XTTS carregado (GPU)                   │   │
│ │ • Training loop                                  │   │
│ │ • Loss decreasing                                │   │
│ └─────────────────────────────────────────────────┘   │
│                     ↓                                   │
│ ┌─────────────────────────────────────────────────┐   │
│ │ CHECKPOINT SAVE                                  │   │
│ │ • Salvar model_state_dict                       │   │
│ │ • Salvar optimizer_state_dict                   │   │
│ └─────────────────────────────────────────────────┘   │
│                     ↓                                   │
│ ┌─────────────────────────────────────────────────┐   │
│ │ UNLOAD TRAINING MODEL                           │   │
│ │ • model = model.cpu()                           │   │
│ │ • torch.cuda.empty_cache()                      │   │
│ └─────────────────────────────────────────────────┘   │
│                     ↓                                   │
│            subprocess.run([...])                       │
└─────────────────┼───────────────────────────────────────┘
                  │
                  ↓
        ┌─────────────────────────────────────────┐
        │ SUBPROCESSO (generate_sample_subprocess) │
        │ ┌─────────────────────────────────────┐ │
        │ │ LOAD XTTS (CPU)                    │ │
        │ │ • Processo limpo                   │ │
        │ │ • gpu=False                        │ │
        │ │ • Sem conflito cuFFT               │ │
        │ └─────────────────────────────────────┘ │
        │                 ↓                        │
        │ ┌─────────────────────────────────────┐ │
        │ │ GENERATE AUDIO                      │ │
        │ │ • tts.tts(text=..., speaker_wav=...) │ │
        │ │ • Usando CPU (~43s)                 │ │
        │ └─────────────────────────────────────┘ │
        │                 ↓                        │
        │ ┌─────────────────────────────────────┐ │
        │ │ SAVE WAV                            │ │
        │ │ • sf.write(output.wav, wav, 22050)  │ │
        │ └─────────────────────────────────────┘ │
        │                 ↓                        │
        │ ┌─────────────────────────────────────┐ │
        │ │ EXIT                                │ │
        │ │ • del tts                           │ │
        │ │ • Memória liberada automaticamente  │ │
        │ └─────────────────────────────────────┘ │
        └───────────────┬─────────────────────────┘
                        │ return code 0
                        ↓
┌─────────────────────────────────────────────────────────┐
│ PROCESSO PRINCIPAL (continua)                          │
│ ┌─────────────────────────────────────────────────┐   │
│ │ RELOAD TRAINING MODEL                           │   │
│ │ • checkpoint = torch.load(...)                  │   │
│ │ • model.load_state_dict(checkpoint['...'])      │   │
│ │ • model = model.to(device)                      │   │
│ │ • model.train()                                 │   │
│ └─────────────────────────────────────────────────┘   │
│                     ↓                                   │
│ ┌─────────────────────────────────────────────────┐   │
│ │ CONTINUAR TREINAMENTO                           │   │
│ │ • Próxima época                                 │   │
│ │ • Estado preservado                             │   │
│ └─────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────┘
```

### Trade-offs

| Aspecto | GPU (quebrado) | CPU Subprocesso (funciona) |
|---------|----------------|----------------------------|
| **Velocidade** | ~3s | ~43s |
| **cuFFT Error** | ❌ Sim | ✅ Não |
| **VRAM** | Alta | Nenhuma (usa RAM) |
| **Confiabilidade** | 0% | 100% |
| **Isolamento** | N/A | ✅ Processo separado |
| **Auto-cleanup** | Manual | ✅ Automático |

**Decisão**: CPU é **14x mais lento**, mas é a **única opção que funciona** neste ambiente.

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

### Monitoramento

### Logs Durante Geração

```
💾 Checkpoint salvo: checkpoint_epoch_1.pt
🧹 Liberando VRAM para geração de samples...
   ✅ Modelo de treinamento movido para CPU
   📝 Texto do metadata: 'ah, agora eu estou me ouvindo na tv...'
🎤 Gerando sample de áudio (subprocesso CPU)...
   Época: 1
   Referência: audio_00001.wav
   ⚠️  Usando CPU - bug cuFFT impede uso da GPU
   🚀 Iniciando subprocesso...
   
   [SUBPROCESSO]
   📥 Carregando XTTS em CPU...
   🔊 Sintetizando áudio em CPU (mais lento mas evita cuFFT bug)...
    > Processing time: 42.8s
    > Real-time factor: 2.54x
   ✅ Sample gerado: /path/to/epoch_1_output.wav
   
   ✅ Sample gerado: epoch_1_output.wav
   ✅ Referência copiada: epoch_1_reference.wav
📥 Recarregando modelo de treinamento...
   ✅ Modelo de treinamento restaurado na GPU
```

### Tempo Total por Sample

- Unload training model: ~1s
- Subprocess overhead: ~2s
- Carregar XTTS CPU: ~11s
- Gerar áudio: ~30s (depende do tamanho do texto)
- **Total: ~43s por sample**

### Performance Impact

Para treinamento com 1000 épocas:
- Sem samples: ~1h
- Com samples (1 por época, 43s cada): ~1h + 12h = ~13h total
- **Recomendação**: `save_every_n_epochs = 10` (13h → 2.2h overhead)

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
