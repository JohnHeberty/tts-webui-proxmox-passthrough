# Scripts Deprecated

Este diretório contém scripts que foram **substituídos por versões melhores** e não devem mais ser usados no pipeline de produção.

## 📦 Conteúdo

### 1. `prepare_segments.py` ❌ OBSOLETO
**Substituído por:** `prepare_segments_optimized.py`

**Motivo:** Problemas graves de performance
- ❌ Carrega todo o arquivo de áudio na memória (19GB+ RAM para arquivos grandes)
- ❌ Não processa em chunks
- ❌ Causa OOM (Out of Memory) em servidores com pouca RAM

**Use:** `prepare_segments_optimized.py` (5GB RAM, processamento em chunks)

---

### 2. `transcribe_segments.py` ❌ OBSOLETO
**Substituído por:** `transcribe_or_subtitles.py`

**Motivo:** Funcionalidade inferior
- ❌ Usa apenas Whisper (sem aproveitar legendas do YouTube)
- ❌ Não aplica normalização de texto pt-BR
- ❌ Não valida qualidade da transcrição
- ❌ Não retranscreve com modelo melhor se necessário

**Use:** `transcribe_or_subtitles.py` (legendas YouTube + Whisper + validação)

---

### 3. `simple_download.py` ❌ OBSOLETO
**Substituído por:** `download_youtube.py`

**Motivo:** Configuração inadequada
- ❌ Não usa CSV para gerenciar downloads
- ❌ Não suporta filtros de qualidade/formato
- ❌ Baixa em formato errado (não força WAV 24kHz mono)
- ❌ Não organiza arquivos corretamente

**Use:** `download_youtube.py` (CSV + WAV 24kHz mono + organização)

---

### 4. `auto_train.py` ❌ OBSOLETO
**Substituído por:** `run_training.py`

**Motivo:** Desatualizado com API do F5-TTS
- ❌ Usa CLI antiga do F5-TTS que foi deprecada
- ❌ Não usa `finetune_cli` (interface atual)
- ❌ Configuração hardcoded (não usa .env)
- ❌ Não suporta novos parâmetros (early stopping, logging, etc.)

**Use:** `run_training.py` (100% compatível com F5-TTS v1.1.10)

---

## ⚠️ Instruções de Uso

### NÃO USE ESTES SCRIPTS!

Se você encontrar referências a esses scripts em documentação antiga:

1. **Substitua** pelo script equivalente moderno (veja tabela acima)
2. **Reporte** o problema para atualizar a documentação

### Pipeline Correto (2024)

```bash
# 1. Download (CSV-based)
python -m train.scripts.download_youtube

# 2. Segmentação (Memory-optimized)
python -m train.scripts.prepare_segments_optimized

# 3. Transcrição (YouTube + Whisper)
python -m train.scripts.transcribe_or_subtitles

# 4. Metadata
python -m train.scripts.build_metadata_csv

# 5. Dataset F5
python -m train.scripts.prepare_f5_dataset

# 6. Treinamento
python -m train.run_training
```

---

## 🗑️ Por que não foram deletados?

Mantidos aqui por **motivos históricos** e para:
- Referência de implementação antiga
- Comparação de performance (benchmarks)
- Debugging de problemas legacy
- Rollback em caso de emergência (improvável)

**Porém:** Em 99% dos casos, você deve usar os scripts novos.

---

## 📊 Comparação de Performance

| Script | Versão Antiga | Versão Nova | Melhoria |
|--------|--------------|-------------|----------|
| Segmentação | 19GB RAM | 5GB RAM | **74% menos** |
| Transcrição | Só Whisper | YouTube + Whisper | **60% mais rápido** |
| Download | Manual | CSV batch | **Gerenciável** |
| Training | CLI antiga | finetune_cli | **Compatível** |

---

## 📝 Histórico

- **2024-12-04**: Scripts movidos para _deprecated/
- **2024-11**: Criados scripts otimizados
- **2024-10**: Problemas de RAM identificados

---

**Dúvidas?** Consulte `/train/SCRIPTS.md` para classificação completa de todos os scripts.
