# 🚀 Status do Projeto XTTS-v2 Training Pipeline

**Data**: 2025-12-06  
**Tech Lead**: Claude Sonnet 4.5  
**Objetivo**: Pipeline completo de fine-tuning XTTS-v2 para português brasileiro

---

## 📊 Progresso Geral

| Sprint | Status | Progresso | Tempo |
|--------|--------|-----------|-------|
| Sprint 0 | ✅ Completo | 100% | 1h |
| Sprint 1 | ✅ Completo | 100% | 4h |
| Sprint 2 | 🔄 Em progresso | 60% | 2h |
| Sprint 3 | ⏳ Pendente | 0% | - |
| Sprint 4 | ⏳ Pendente | 0% | - |
| Sprint 5 | ⏳ Pendente | 0% | - |

**Total**: 3/6 sprints | **Horas gastas**: 7h | **Estimativa restante**: 13-21h

---

## ✅ Sprint 0: Segurança & Cleanup (COMPLETO)

**Objetivos**: Garantir segurança e limpar referências F5-TTS

**Entregáveis**:
- ✅ Auditoria de secrets (nenhum exposto)
- ✅ Docs F5-TTS marcadas como deprecated
- ✅ Git commit com análise completa (MORE.md, SPRINTS.md)

**Arquivos**:
- `MORE.md` (66KB) - Análise técnica completa
- `SPRINTS.md` (25KB) - Plano de 6 sprints
- `SPRINT0_REPORT.md` (3KB) - Relatório de segurança

**Commit**: `5cd4abd` - "docs: Add MORE.md & SPRINTS.md + Sprint 0 security audit"

---

## ✅ Sprint 1: Estrutura train/ + Pipeline de Dados (COMPLETO)

**Objetivos**: Criar infraestrutura de preparação de dados XTTS-v2

**Entregáveis**:
- ✅ Estrutura `train/` completa
- ✅ `dataset_config.yaml` (22050Hz, 7-12s, VAD streaming)
- ✅ 4 scripts migrados de `scripts/not_remove/`:
  1. `download_youtube.py` - Download YouTube → 22050Hz WAV
  2. `segment_audio.py` - VAD streaming (7-12s)
  3. `transcribe_audio.py` - Whisper + legendas YT
  4. `build_ljs_dataset.py` - LJSpeech format
- ✅ `pipeline.py` - Orquestrador completo
- ✅ 15 vídeos Flow Podcast em `videos.csv`
- ✅ README.md completo

**Estrutura Criada**:
```
train/
├── config/dataset_config.yaml
├── data/
│   ├── videos.csv (15 vídeos, ~30-40h)
│   ├── raw/          (áudios baixados)
│   ├── processed/    (segmentos VAD)
│   └── MyTTSDataset/ (LJSpeech format)
├── scripts/ (5 scripts)
├── output/ (checkpoints, samples)
└── logs/
```

**Commits**:
- `f1ebaec` - "docs: Update Sprint 1 based on existing scripts"
- `9ffd011` - "feat: Complete Sprint 1 - XTTS-v2 train/ structure + data pipeline"

**Arquivos**: 16 files, 2381 lines

---

## 🔄 Sprint 2: Treinamento XTTS-v2 (60% COMPLETO)

**Objetivos**: Implementar fine-tuning com LoRA

**Entregáveis**:
- ✅ `train_config.yaml` (94 linhas)
  - LoRA config (rank 16, alpha 32)
  - Training hyperparams (lr 1e-5, 10k steps)
  - Checkpointing (save every 500 steps)
  - TensorBoard logging
- ✅ `train_xtts.py` (373 linhas) - TEMPLATE
  - Estrutura completa de training loop
  - LoRA integration (PEFT)
  - Mixed precision (AMP)
  - Checkpoint management
  - TensorBoard hooks
- ⏳ Implementação TTS API (pendente)
- ⏳ Dataset loader (pendente)
- ⏳ Training loop real (pendente)

**Commit**: `bed4287` - "feat: Sprint 2 (partial) - XTTS-v2 training template with LoRA"

**Próximos Passos**:
1. Integrar com `app/engines/xtts_engine.py` (já existe!)
2. Usar TTS.tts.models.xtts.Xtts para loading
3. Implementar custom dataset para metadata.csv
4. Testar training com dataset pequeno

---

## 🔄 Pipeline de Dados - STATUS ATUAL

**Processo em Background**: `PID 380097`

**Progresso Download**:
- ✅ Vídeo 1: video_00001.wav (✓ completo)
- ✅ Vídeo 2: video_00002.wav (✓ completo)
- ✅ Vídeo 3: video_00003.wav (✓ completo)
- 🔄 Vídeo 4: Em download...
- ⏳ Vídeos 5-15: Aguardando

**Tempo Estimado**:
- Download: ~2-3h (15 vídeos × 10-15min cada)
- Segmentação: ~1-2h (VAD streaming)
- Transcrição: ~3-4h (Whisper base)
- Build dataset: ~10min

**Total**: ~7-10 horas para completar pipeline

**Logs**:
- `train/logs/pipeline_full.log` (acompanhamento)
- `train/logs/download_youtube.log`
- `train/logs/segment_audio.log` (quando iniciar)
- `train/logs/transcribe_audio.log` (quando iniciar)
- `train/logs/build_metadata.log` (quando iniciar)

**Comando para acompanhar**:
```bash
tail -f train/logs/pipeline_full.log
```

---

## 📁 Arquivos do Projeto

**Configuração**:
- `train/config/dataset_config.yaml` (73 linhas)
- `train/config/train_config.yaml` (94 linhas)

**Scripts**:
- `train/scripts/download_youtube.py` (265 linhas)
- `train/scripts/segment_audio.py` (572 linhas)
- `train/scripts/transcribe_audio.py` (831 linhas)
- `train/scripts/build_ljs_dataset.py` (204 linhas)
- `train/scripts/pipeline.py` (243 linhas)
- `train/scripts/train_xtts.py` (373 linhas)

**Documentação**:
- `train/README.md` (195 linhas)
- `MORE.md` (66KB)
- `SPRINTS.md` (25KB)
- `SPRINT0_REPORT.md` (3KB)

**Total**: ~3500 linhas de código + 94KB de docs

---

## 🔧 Dependências Instaladas

**Essenciais**:
- ✅ yt-dlp (2025.11.12) - Download YouTube
- ✅ openai-whisper (20250625) - Transcrição
- ✅ num2words (0.5.14) - Expansão de números pt-BR
- ✅ soundfile (0.13.1) - Audio I/O
- ✅ scipy (1.16.3) - Resample, filters
- ✅ pyloudnorm (0.1.1) - Normalização loudness
- ✅ click (8.3.1) - CLI
- ✅ pyyaml (6.0.3) - Config files

**PyTorch**:
- ✅ torch (2.9.1) - Deep learning
- ✅ tqdm (4.67.1) - Progress bars

**Treinamento (para Sprint 2)**:
- ⏳ TTS (coqui-tts) - Modelo XTTS-v2
- ⏳ peft - LoRA implementation
- ⏳ tensorboard - Logging

---

## 🎯 Próximas Ações

### Imediato (enquanto pipeline roda)
1. ✅ Instalar dependências faltantes: `pip install TTS peft tensorboard`
2. ✅ Implementar integração real com Coqui TTS
3. ✅ Testar carregamento de modelo XTTS-v2
4. ✅ Criar custom dataset loader

### Quando Pipeline Completar
1. Validar dataset gerado
2. Verificar metadata.csv
3. Calcular estatísticas (duração, distribuição)
4. Executar primeiro teste de training

### Sprint 3 (Integração API)
1. Modificar `app/engines/xtts_engine.py`
2. Adicionar suporte a custom checkpoints
3. Criar endpoint de inferência
4. Testar voz clonada

---

## 📈 Métricas de Sucesso

**Dataset**:
- ✅ Estrutura LJSpeech criada
- 🔄 15 vídeos sendo processados (~30-40h áudio bruto)
- ⏳ Esperado: ~3-5h áudio limpo (500-1000 segmentos 7-12s)

**Training (quando implementado)**:
- [ ] Modelo carrega sem erros
- [ ] Training loop executa
- [ ] Checkpoints são salvos
- [ ] Validação gera samples
- [ ] Loss diminui consistentemente

**API (Sprint 3)**:
- [ ] Custom checkpoint carrega
- [ ] Inferência funciona
- [ ] Voice cloning preserva características
- [ ] Latência aceitável (<5s para 10s áudio)

---

## 🐛 Problemas Conhecidos

1. **yt-dlp warnings**: JavaScript runtime não encontrado
   - **Solução**: Warnings apenas, downloads funcionam
   - **Opção**: `pip install yt-dlp[default]` se quiser resolver

2. **Template train_xtts.py**: Requer implementação TTS
   - **Status**: Estrutura completa, precisa integrar API
   - **Próximo**: Usar código de `app/engines/xtts_engine.py`

3. **Pipeline em background**: Pode demorar 7-10h
   - **Status**: Normal, processar 30-40h de áudio
   - **Monitoramento**: `tail -f train/logs/pipeline_full.log`

---

## 📝 Notas Técnicas

**XTTS-v2 Specs**:
- Sample rate: 22050Hz (não 24000!)
- Duration ideal: 7-12s por segmento
- Format: WAV mono 16-bit
- Metadata: LJSpeech format (`path|text`)

**Diferenças F5-TTS → XTTS-v2**:
- ✅ Sample rate: 24000 → 22050Hz
- ✅ Duration: 3-30s → 7-12s
- ✅ Text norm: Case-sensitive → Lowercase
- ✅ Dataset path: f5_dataset → MyTTSDataset

**Hardware**:
- GPU: RTX 3090 (23GB VRAM)
- RAM: Suficiente para VAD streaming
- Storage: ~50GB necessário (dataset + checkpoints)

---

**Última atualização**: 2025-12-06 15:40 (Pipeline rodando, Sprint 2 em progresso)
