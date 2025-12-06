# F5-TTS Training Scripts

Scripts utilitários para o pipeline de treinamento F5-TTS.

## Scripts Disponíveis

### 🏥 `health_check.py` - System Health Check
Verifica ambiente completo de treinamento.

**Uso:**
```bash
python train/scripts/health_check.py
```

**O que verifica:**
- ✅ Versão do Python (3.11+)
- ✅ GPU/CUDA disponível
- ✅ PyTorch instalado e configurado
- ✅ Bibliotecas de áudio (librosa, soundfile)
- ✅ VRAM disponível
- ✅ Disco disponível
- ✅ Estrutura de diretórios
- ✅ Arquivos de configuração

**Saída:**
```
🏥 F5-TTS Training Environment Health Check
==========================================

✅ Python: 3.11.2
✅ PyTorch: 2.5.1+cu121
✅ CUDA: 12.1 available
✅ GPU: NVIDIA RTX 3090 (23.7 GB VRAM)
✅ Audio libs: OK
✅ Disk space: 450 GB free
✅ Config files: OK

🎉 Environment is healthy!
```

---

### 🎙️ `AgentF5TTSChunk.py` - Batch Inference
Processamento em lote de textos para áudio.

**Uso:**
```bash
python train/scripts/AgentF5TTSChunk.py \
    --checkpoint models/f5tts/model_last.pt \
    --vocab train/config/vocab.txt \
    --input texts.txt \
    --output-dir output/
```

**Funcionalidades:**
- Processa múltiplos textos de um arquivo
- Suporta chunking automático de textos longos
- Salva metadados (duração, params)
- Progress bar

---

### 📦 `download_models.py` - Model Downloader
Download de modelos pré-treinados do HuggingFace.

**Uso:**
```bash
python scripts/download_models.py
```

**Modelos baixados:**
- F5-TTS PT-BR (firstpixel/F5-TTS-pt-br)
- Vocos vocoder
- Whisper (para transcrição)

---

### 🎤 `create_default_speaker.py` - Default Voice Profile
Cria perfil de voz padrão para testes.

**Uso:**
```bash
python scripts/create_default_speaker.py \
    --audio reference.wav \
    --text "Transcrição do áudio de referência"
```

---

### 🔧 `create_voice_presets.py` - Voice Presets
Cria presets de qualidade para F5-TTS.

**Uso:**
```bash
python scripts/create_voice_presets.py
```

**Presets criados:**
- `balanced` - Equilíbrio qualidade/velocidade
- `expressive` - Máxima expressividade
- `stable` - Máxima estabilidade

---

### 🔍 Validation Scripts

#### `validate-deps.sh`
Valida dependências instaladas:
```bash
bash scripts/validate-deps.sh
```

#### `validate-gpu.sh`
Valida GPU e CUDA:
```bash
bash scripts/validate-gpu.sh
```

#### `validate-optimization.sh`
Valida otimizações aplicadas:
```bash
bash scripts/validate-optimization.sh
```

---

## Scripts de Dataset

### `prepare_segments_optimized.py`
Prepara dataset com segmentação otimizada.

**Uso:**
```bash
python train/scripts/prepare_segments_optimized.py \
    --input-dir raw_audio/ \
    --output-dir processed/ \
    --config train/config/config.yaml
```

**Pipeline:**
1. Segmenta áudio em chunks
2. Aplica VAD para remover silêncios
3. Normaliza volume (LUFS)
4. Valida duração e qualidade
5. Salva metadados

---

## Exemplos de Uso

### 1. Health Check Antes de Treinar

```bash
# Verificar ambiente
python train/scripts/health_check.py

# Se OK, iniciar treino
python -m train.run_training
```

### 2. Inferência em Lote

```bash
# Criar arquivo com textos
cat > texts.txt << EOF
Primeira frase para sintetizar.
Segunda frase com mais conteúdo.
Terceira frase para testar.
EOF

# Processar em lote
python train/scripts/AgentF5TTSChunk.py \
    --checkpoint models/f5tts/model_last.pt \
    --vocab train/config/vocab.txt \
    --input texts.txt \
    --output-dir output/ \
    --nfe-step 32
```

### 3. Download e Setup

```bash
# 1. Download modelos
python scripts/download_models.py

# 2. Validar ambiente
python train/scripts/health_check.py

# 3. Criar preset padrão
python scripts/create_voice_presets.py
```

---

## Desenvolvimento

### Adicionar Novo Script

1. Criar arquivo em `train/scripts/`:
```python
#!/usr/bin/env python3
"""
Descrição do script
"""
import argparse
import logging

def main():
    parser = argparse.ArgumentParser(description="...")
    parser.add_argument("--input", required=True)
    args = parser.parse_args()
    
    # Lógica do script
    print("✅ Concluído!")

if __name__ == "__main__":
    main()
```

2. Tornar executável:
```bash
chmod +x train/scripts/novo_script.py
```

3. Adicionar ao README

---

## Troubleshooting

### Health Check Falha

**Problema:** GPU não detectada
```bash
❌ CUDA: Not available
```

**Solução:**
```bash
# Verificar instalação CUDA
nvidia-smi

# Reinstalar PyTorch com CUDA
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu121
```

### Batch Inference Lento

**Problema:** Inferência muito lenta

**Solução:**
```bash
# Use service mode (model caching)
python train/scripts/AgentF5TTSChunk.py \
    --use-service \  # Cacheia modelo
    --nfe-step 16    # Reduz steps
```

---

## Referências

- [Health Check Documentation](../docs/INFRASTRUCTURE_SETUP.md)
- [Inference API](../docs/INFERENCE_API.md)
- [Training Guide](../docs/TUTORIAL.md)

---

**Autor:** F5-TTS Training Pipeline  
**Versão:** 1.0  
**Data:** 2025-12-06
