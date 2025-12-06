# 📊 STATUS DO PROJETO - TTS XTTS-v2 Pipeline

**Última atualização**: 2025-12-06 16:58  
**Tech Lead**: Claude Sonnet 4.5  
**Fase atual**: Sprint 1 completando transcrição paralela (50%)

---

## 🎯 RESUMO EXECUTIVO

**Progresso Global**: 49% (2.5/5 sprints)

| Sprint | Status | % | Tempo | Próximo |
|--------|--------|---|-------|---------|
| Sprint 0 | ✅ COMPLETO | 100% | 1h | - |
| Sprint 1 | 🔄 85% | Dataset quase pronto | 5h | Aguardar transcrição (13min) |
| Sprint 2 | ⏸️ 60% | Template criado | - | Implementar TODOs TTS |
| Sprint 3 | ⏳ 0% | Não iniciado | - | Após Sprint 2 |
| Sprint 4-5 | ⏳ 0% | Não iniciado | - | Após Sprint 3 |

**Transcrição em andamento**: 4583/9173 (50%) - ETA: 13min - Speed: 5.9 seg/s 🚀

---

## ✅ COMPLETO

### Sprint 0: Segurança (100%)
- ✅ `.env` no gitignore
- ✅ Docs F5-TTS deprecated
- ✅ Estrutura analisada

### Sprint 1: Dataset Pipeline (85%)
- ✅ Estrutura `train/` completa
- ✅ 15 vídeos baixados (~30-40h)
- ✅ 9173 segmentos gerados (22050Hz, 7-12s)
- 🔄 **Transcrição paralela 15x faster** (50% done)
  - Speedup: 0.4 → 5.9 seg/s
  - Workers: 6 paralelos (auto-detect VRAM)
  - Checkpoint: incremental a cada 10 seg
- ⏳ Build metadata (após transcrição)

**Bugs corrigidos**:
- ✅ Contador reset ao retomar
- ✅ segment_index sequencial (0,1,2...)
- ✅ Data loss (save incremental)
- ✅ WebM orphans

---

## 🔄 EM ANDAMENTO

### Transcrição Paralela (50%)
```
Progresso: [4583/9173] 50.0%
Speed:     5.9 seg/s (15x faster!)  
ETA:       ~13 minutos
Workers:   6 paralelos
VRAM:      5.6GB / 24GB (23%)
```

**Após completar (~13min)**:
1. Executar `build_ljs_dataset.py`
2. Validar metadata CSV
3. Iniciar Sprint 2

---

## ⏸️ PRÓXIMAS AÇÕES

### Sprint 2: Treinamento (60% template)

**Arquivos prontos**:
- ✅ `train_config.yaml` (LoRA, hiperparâmetros)
- ⏸️ `train_xtts.py` (60% - 6 TODOs pendentes)

**TODOs críticos**:
1. `load_pretrained_model()` - Carregar XTTS-v2
2. `create_dataset()` - TTSDataset
3. `create_scheduler()` - Warmup + cosine
4. `train_step()` - Forward pass
5. `validate()` - Métricas
6. Training loop - Integração

**Referência**: `app/engines/xtts_engine.py` (já funciona!)

**Steps**:
```bash
# 1. Instalar deps
pip install TTS peft tensorboard

# 2. Implementar TODOs (usar xtts_engine.py como ref)

# 3. Smoke test
head -100 train/data/MyTTSDataset/metadata_train.csv > test_metadata.csv
python -m train.scripts.train_xtts --config train/config/train_config.yaml --max-steps 10

# 4. Full training (50 epochs)
python -m train.scripts.train_xtts --config train/config/train_config.yaml
```

---

## 📊 MÉTRICAS

### Dataset
- Vídeos: 15 episódios Flow Podcast
- Áudio total: ~30-40h
- Segmentos: 9173 (7-12s avg)
- Transcritos: 4583 (50%)
- Format: 22050Hz mono 16-bit WAV

### Performance
- Transcrição: **15x speedup** (0.4 → 5.9 seg/s)
- VRAM: 23% uso (eficiente)
- Workers: 6 auto-detectados

### Qualidade
- VAD: Alta precision
- Text: pt-BR normalizado (num2words, lowercase)
- OOV handling: Retry com modelo HP

---

## 🎯 ROADMAP

### Hoje (~13min + 3h)
1. ⏳ **Aguardar transcrição** (13min)
2. ⏳ **Build metadata** (5min)
3. ⏳ **Instalar TTS** (10min)
4. ⏳ **Implementar TODOs** (2h)
5. ⏳ **Smoke test** (30min)

### Próximos dias (~8-10h)
6. ⏳ Full training (4-6h)
7. ⏳ API integration (2-3h)
8. ⏳ Testes (2h)

---

## 📁 ARQUIVOS CHAVE

### Configuração
- `train/config/dataset_config.yaml` ✅
- `train/config/train_config.yaml` ✅
- `train/.env.example` ✅
- `train/env_config.py` ✅

### Scripts
- `train/scripts/download_youtube.py` ✅
- `train/scripts/segment_audio.py` ✅
- `train/scripts/transcribe_audio_parallel.py` ✅ (ATUAL)
- `train/scripts/build_ljs_dataset.py` ⏸️
- `train/scripts/train_xtts.py` ⏸️ (60%)

### Dados
- `train/data/raw/*.wav` ✅ (15 vídeos)
- `train/data/processed/wavs/*.wav` ✅ (9173)
- `train/data/processed/transcriptions.json` 🔄 (50%)
- `train/data/MyTTSDataset/metadata_*.csv` ⏳

---

**Ver detalhes completos**: [SPRINTS.md](../SPRINTS.md)
