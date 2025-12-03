# 🎯 F5-TTS Fine-tuning - Guia Rápido

## ✅ Configuração Concluída

O projeto de treinamento foi configurado com as seguintes correções:

### 1. Dataset
- ✅ Removido symlink `f5_dataset_pinyin`
- ✅ Configurado para usar `train/data/f5_dataset` diretamente

### 2. Modelo Pré-treinado PT-BR
- ✅ Modelo baixado: `train/pretrained/F5-TTS-pt-br/pt-br/model_200000.pt`
- ✅ Modelo corrigido: `model_200000_fixed.pt` (estrutura compatível com F5-TTS)
- ✅ EMA verificado e funcionando (337.1M parâmetros)
- ✅ Configurado no `.env`

### 3. Scripts Úteis
- ✅ `scripts/check_model.py` - Verifica e corrige modelos .pt
- ✅ Documentação em `docs/FINETUNING.md`

## 🚀 Como Usar

### Passo 1: Preparar Dataset

Certifique-se de que seu dataset está em `train/data/f5_dataset/`:

```
f5_dataset/
├── metadata.csv       # formato: audio_path|text
├── duration.json      # {"duration": [1.5, 2.3, ...]}
├── vocab.txt          # um token por linha
└── wavs/              # arquivos .wav em 24kHz
```

### Passo 2: Ajustar Hiperparâmetros (Opcional)

Edite `train/.env` conforme sua GPU:

```bash
# Para GPU com pouca VRAM (< 12GB)
BATCH_SIZE=1
GRAD_ACCUMULATION_STEPS=8
LEARNING_RATE=5e-5

# Para GPU com VRAM média (12-24GB)
BATCH_SIZE=4
GRAD_ACCUMULATION_STEPS=4
LEARNING_RATE=1e-4

# Para GPU com alta VRAM (> 24GB)
BATCH_SIZE=8
GRAD_ACCUMULATION_STEPS=2
LEARNING_RATE=7.5e-5
```

### Passo 3: Iniciar Treinamento

```bash
cd /home/tts-webui-proxmox-passthrough
python3 -m train.run_training
```

O treinamento irá:
1. ✅ Carregar modelo pré-treinado PT-BR com EMA
2. ✅ Continuar fine-tuning a partir de 200k iterações
3. ✅ Salvar checkpoints em `train/output/ptbr_finetuned/`
4. ✅ Gerar samples de áudio a cada 250 updates
5. ✅ Logar métricas no TensorBoard em `train/runs/`

### Passo 4: Monitorar Progresso

Em outro terminal:

```bash
cd /home/tts-webui-proxmox-passthrough/train
tensorboard --logdir runs --port 6006
```

Acesse: http://localhost:6006

## 📊 Estrutura de Arquivos

```
train/
├── .env                          # Configurações (EDITÁVEL)
├── run_training.py              # Script principal
├── data/
│   └── f5_dataset/              # Seu dataset (OBRIGATÓRIO)
├── pretrained/
│   └── F5-TTS-pt-br/
│       └── pt-br/
│           ├── model_200000.pt         # Original
│           └── model_200000_fixed.pt   # Corrigido (USADO)
├── output/
│   └── ptbr_finetuned/          # Checkpoints gerados
│       ├── model_last.pt        # Último checkpoint
│       ├── model_1000.pt        # Checkpoints salvos
│       └── samples/             # Áudios gerados
├── runs/                         # TensorBoard logs
├── scripts/
│   └── check_model.py           # Verificar/corrigir modelos
└── docs/
    └── FINETUNING.md            # Documentação detalhada
```

## 🔧 Troubleshooting

### Erro de EMA

Se encontrar erro relacionado a EMA:

```bash
cd train
python3 scripts/check_model.py pretrained/F5-TTS-pt-br/pt-br/model_200000.pt --fix
```

### Verificar Modelo

```bash
cd train
python3 scripts/check_model.py pretrained/F5-TTS-pt-br/pt-br/model_200000_fixed.pt
```

### Out of Memory

Reduza BATCH_SIZE no `.env`:

```bash
BATCH_SIZE=1  # ou 2
GRAD_ACCUMULATION_STEPS=8  # aumentar para compensar
```

### Dataset Não Encontrado

Verifique se existe:
- `train/data/f5_dataset/metadata.csv`
- `train/data/f5_dataset/wavs/` com arquivos .wav
- `train/data/f5_dataset/vocab.txt`

## 📚 Documentação Completa

Para detalhes sobre fine-tuning, EMA, hiperparâmetros e boas práticas, veja:

- **Guia completo**: `train/docs/FINETUNING.md`
- **F5-TTS oficial**: https://github.com/SWivid/F5-TTS/tree/main/src/f5_tts/train
- **Discussion #57**: https://github.com/SWivid/F5-TTS/discussions/57

## ⚡ Quick Start (TL;DR)

```bash
# 1. Certifique-se de que o dataset está em train/data/f5_dataset
# 2. Ajuste BATCH_SIZE em train/.env se necessário
# 3. Execute:
cd /home/tts-webui-proxmox-passthrough
python3 -m train.run_training

# 4. Em outro terminal, monitore:
cd train
tensorboard --logdir runs --port 6006
```

## 🎯 Resultados Esperados

- **Primeiras 1k iterações**: Modelo aprende características básicas do dataset
- **1k - 10k iterações**: Melhora na pronúncia e naturalidade
- **10k - 50k iterações**: Fine-tuning refinado, resultados estáveis
- **50k+ iterações**: Risco de overfitting se dataset for pequeno

**Dica**: Use Early Stopping para evitar overfitting (configurado em `.env`)

## 📞 Suporte

Para problemas específicos, consulte:
1. `train/docs/FINETUNING.md` (troubleshooting avançado)
2. Logs do TensorBoard
3. Issues no GitHub do F5-TTS

---

**Status**: ✅ Pronto para treinar!
