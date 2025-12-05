# 🚀 Scripts de Segmentação de Áudio - Guia Rápido

## 📁 Arquivos Disponíveis

| Script | Uso | RAM | Velocidade |
|--------|-----|-----|------------|
| `prepare_segments.py` | ❌ Deprecated | 27 GB | Lento |
| `prepare_segments_optimized.py` | ✅ V2 | 400 MB | Médio |
| **`prepare_segments_v2.py`** | ⭐ **V3 RECOMENDADO** | **185 MB** | **Rápido** |

---

## ⚡ Quick Start

### Processamento Básico (V3)

```bash
# Processamento sequencial (economiza RAM)
python3 -m train.scripts.prepare_segments_v2

# Processamento paralelo (4 cores)
python3 -m train.scripts.prepare_segments_v2 --parallel --workers 4
```

### Comparar Versões

```bash
# Benchmark V2 vs V3
python3 train/scripts/benchmark_segmentation.py

# Comparar resultados
python3 train/scripts/migrate_segmentation.py --compare --validate --report migration_report.md
```

---

## 📊 Quando Usar Cada Versão

### Use V2 (`prepare_segments_optimized.py`) se:
- Arquivo pequeno (<30 minutos)
- RAM disponível > 2GB
- Quer código mais simples

### Use V3 (`prepare_segments_v2.py`) se: ⭐
- Arquivo grande (>1 hora)
- Muitos arquivos para processar
- RAM limitada (<2GB)
- Quer processamento paralelo
- Arquivo maior que RAM disponível

---

## 🛠️ Troubleshooting

### Problema: "Out of Memory"

**V2:**
```yaml
# dataset_config.yaml
segmentation:
  vad_chunk_duration: 15.0  # Reduzir de 30s
```

**V3:**
```bash
# Desabilitar normalização pesada
# Editar dataset_config.yaml:
audio:
  normalize_audio: false
```

### Problema: Muito Lento

```bash
# Use processamento paralelo
python3 -m train.scripts.prepare_segments_v2 --parallel --workers 8

# Ou aumente chunk size (usa mais RAM mas é mais rápido)
# dataset_config.yaml:
# vad_chunk_duration: 60.0
```

### Problema: Segmentos Muito Pequenos

```yaml
# dataset_config.yaml
segmentation:
  min_duration: 5.0        # Aumentar mínimo
  vad_threshold: -35       # Menos sensível (era -40)
  min_silence_duration: 1.0  # Mais silêncio necessário
```

---

## 📖 Documentação Completa

- **Guia de Otimização:** `OPTIMIZATION_GUIDE.md`
- **README do Training:** `../README.md`
- **Config:** `../config/dataset_config.yaml`

---

## 🔬 Validação

```bash
# Validar integridade dos segmentos
python3 train/scripts/migrate_segmentation.py --validate

# Comparar V2 vs V3
python3 train/scripts/migrate_segmentation.py --compare
```

---

## 💡 Dicas

1. **Sempre faça backup** antes de processar arquivos grandes
2. **Teste com 1 arquivo** antes de processar tudo
3. **Use --parallel** apenas se tiver múltiplos CPUs
4. **Monitor RAM** com `htop` durante processamento
5. **Logs** estão em `train/logs/prepare_segments_v2.log`

---

## 📈 Performance Esperada

**Arquivo de 2h @ 48kHz:**

| Métrica | V2 | V3 (1 core) | V3 (4 cores) |
|---------|----|----|--------------|
| RAM | 420 MB | 185 MB | 680 MB |
| Tempo | 6 min | 5 min | 3 min |
| Segmentos | ~1250 | ~1250 | ~1250 |

**50 arquivos de 30 min:**

| Métrica | V2 | V3 (4 cores) |
|---------|----|----|
| RAM | 1.2 GB | 680 MB |
| Tempo | 4.5h | 1.2h |
| Taxa | 11 GB/h | 42 GB/h |
