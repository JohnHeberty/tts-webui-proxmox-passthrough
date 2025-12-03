# 🚀 Guia Rápido - Pipeline F5-TTS

**Comandos na ordem para treinar um modelo do zero**

---

## ⚡ Execução Completa (Copy-Paste)

```bash
# Ir para o diretório
cd /home/tts-webui-proxmox-passthrough

# 1. Download (15 min)
python3 -m train.scripts.simple_download

# 2. Segmentação (8 min, <500MB RAM)
python3 -m train.scripts.prepare_segments_optimized

# 3. Transcrição Base (2-4h)
python3 -m train.scripts.transcribe_segments

# 4. Normalização (<1 min)
python3 -m train.scripts.normalize_transcriptions

# 5. Validação + Re-processamento (30 min)
python3 -m train.scripts.validate_and_reprocess

# 6. Metadata (<1 min)
python3 -m train.scripts.build_metadata_csv

# 7. Dataset F5-TTS (<1 min)
python3 -m train.scripts.prepare_f5_dataset

# 8. Treinamento (2-4h)
python3 -m train.run_training
```

**Tempo Total:** ~6-10 horas (depende da GPU e quantidade de dados)

---

## 📊 Verificar Progresso

```bash
# Ver quantos áudios baixados
ls train/data/raw/*.wav | wc -l

# Ver quantos segmentos
ls train/data/processed/wavs/*.wav | wc -l

# Ver quantas transcrições
wc -l train/data/processed/transcriptions.json

# Ver metadata
head train/data/processed/metadata.csv

# Ver logs
tail -f train/logs/transcribe.log
```

---

## 🔧 Troubleshooting Rápido

### RAM muito alta durante segmentação?
```bash
# Use o script otimizado
python3 -m train.scripts.prepare_segments_optimized
```

### Transcrição com erros?
```bash
# Re-validar e re-processar
python3 -m train.scripts.validate_and_reprocess
```

### Números e % não normalizados?
```bash
# Normalizar texto
python3 -m train.scripts.normalize_transcriptions
```

### GPU out of memory no treinamento?
```yaml
# Editar train/config/train_config.yaml
training:
  batch_size_per_gpu: 2  # reduzir de 4
  gradient_accumulation_steps: 8  # aumentar de 4
```

---

## 📁 Arquivos Importantes

| Arquivo | Descrição |
|---------|-----------|
| `train/data/videos.csv` | Lista de vídeos (EDITAR AQUI) |
| `train/config/dataset_config.yaml` | Config de processamento |
| `train/config/train_config.yaml` | Config de treinamento |
| `train/data/processed/transcriptions.json` | Transcrições finais |
| `train/data/processed/metadata.csv` | Dataset final |
| `train/output/checkpoints/final/` | Modelo treinado |

---

## ✅ Checklist

- [ ] Editei `train/data/videos.csv` com URLs
- [ ] Instalei dependências: `pip install -r train/requirements_train.txt`
- [ ] ffmpeg instalado: `ffmpeg -version`
- [ ] Download concluído: `ls train/data/raw/*.wav`
- [ ] Segmentação concluída: `ls train/data/processed/wavs/*.wav`
- [ ] Transcrição concluída: `wc -l train/data/processed/transcriptions.json`
- [ ] Normalização concluída: grep `"normalized": true` na primeira linha
- [ ] Validação concluída: ~90%+ transcrições válidas
- [ ] Metadata gerado: `train/data/processed/metadata.csv` existe
- [ ] Dataset gerado: `train/output/dataset/train.arrow` existe
- [ ] Treinamento iniciado: ver `train/logs/training.log`

---

**Tempo estimado total:** 6-10 horas (automático, não requer supervisão)

**Dica:** Execute em uma sessão tmux/screen para manter rodando em background!

```bash
# Criar sessão
tmux new -s f5tts

# Executar pipeline
python3 -m train.scripts.simple_download && \
python3 -m train.scripts.prepare_segments_optimized && \
python3 -m train.scripts.transcribe_segments && \
python3 -m train.scripts.normalize_transcriptions && \
echo "s" | python3 -m train.scripts.validate_and_reprocess && \
python3 -m train.scripts.build_metadata_csv && \
python3 -m train.scripts.prepare_f5_dataset && \
python3 -m train.run_training

# Destacar: Ctrl+B, D
# Voltar: tmux attach -t f5tts
```
