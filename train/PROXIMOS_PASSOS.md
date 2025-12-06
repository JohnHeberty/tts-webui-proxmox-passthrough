# 🚀 GUIA RÁPIDO - PRÓXIMOS PASSOS

## ✅ O QUE JÁ ESTÁ PRONTO

### 1. Script de Teste que FUNCIONA
```bash
python3 train/teste_ok.py --audio <SEU_AUDIO.wav>
```
- ✅ Testa vocoder e extração de MEL
- ✅ Resultado: PERFEITO
- ⚠️ Limitação: Não gera áudio novo, apenas reconstrói

### 2. Configuração Validada para Novo Treinamento
```bash
# Ver configuração em:
cat train/config_novo_validado.yaml
```
- ✅ Parâmetros testados
- ✅ Vocab correto
- ✅ Checkpoint pre-trained como base

### 3. Script Automatizado de Treinamento
```bash
./train/iniciar_novo_treinamento.sh
```
- ✅ Verifica pré-requisitos
- ✅ Cria backups
- ✅ Inicia treinamento
- ✅ Salva logs

---

## 🎯 OPÇÃO 1: TREINAR NOVO MODELO (RECOMENDADO)

### Passo 1: Verificar Pré-requisitos
```bash
# Verificar dataset
ls -lah train/data/f5_dataset/
wc -l train/data/f5_dataset/metadata.csv

# Verificar vocab
wc -l train/config/vocab.txt

# Verificar VRAM
nvidia-smi

# Verificar espaço em disco
df -h .
```

### Passo 2: Iniciar Treinamento
```bash
# Opção A: Script automatizado (mais fácil)
./train/iniciar_novo_treinamento.sh

# Opção B: Comando manual
python3 -m f5_tts.train.train \
  --config train/config_novo_validado.yaml \
  --data_dir train/data/f5_dataset \
  --output_dir train/output/ptbr_novo_validado \
  --vocab_file train/config/vocab.txt
```

### Passo 3: Monitorar Treinamento
```bash
# Ver logs em tempo real
tail -f train/logs/novo_treinamento_*.log

# Ver tensorboard (se disponível)
tensorboard --logdir train/output/ptbr_novo_validado
```

### Passo 4: Testar Novo Modelo
```bash
# Após alguns checkpoints serem salvos (ex: model_200.pt)
python3 train/infer_como_trainer.py \
  --checkpoint train/output/ptbr_novo_validado/model_200.pt \
  --ref-audio train/output/ptbr_novo_validado/samples/update_200_ref.wav \
  --ref-text "Texto do sample" \
  --output train/teste_novo_modelo.wav

# Validar
python3 train/validar_audio.py train/teste_novo_modelo.wav
```

---

## 🔧 OPÇÃO 2: AJUSTAR MODELO ATUAL

### Investigar Diferenças no Código Fonte

```bash
# Comparar função de geração do trainer vs infer
diff -u \
  <(sed -n '407,430p' /root/.local/lib/python3.11/site-packages/f5_tts/model/trainer.py) \
  <(sed -n '490,520p' /root/.local/lib/python3.11/site-packages/f5_tts/infer/utils_infer.py)

# Verificar se há diferenças em:
# - Preprocessamento de texto
# - Estado do modelo (train/eval mode)
# - Configuração de seeds/determinismo
# - Precisão numérica
```

### Testar Checkpoints Anteriores

```bash
# Listar checkpoints disponíveis
ls -lah train/output/ptbr_finetuned2/*.pt

# Testar cada um
for ckpt in train/output/ptbr_finetuned2/model_*.pt; do
  echo "Testando $ckpt..."
  python3 train/infer_como_trainer.py \
    --checkpoint "$ckpt" \
    --ref-audio train/output/ptbr_finetuned2/samples/update_25400_ref.wav \
    --ref-text "E essa coisa de viagem no tempo do Lock" \
    --output "train/teste_${ckpt##*/}.wav"
  
  python3 train/validar_audio.py "train/teste_${ckpt##*/}.wav"
  echo "---"
done
```

---

## 🆘 OPÇÃO 3: WORKAROUND TEMPORÁRIO

Se geração nova não funcionar, usar reconstrução:

### Processo:
1. Grave áudio com a voz desejada
2. Use `teste_ok.py` para processar com vocoder
3. Resultado: Áudio com qualidade melhorada

```bash
# Exemplo
python3 train/teste_ok.py \
  --audio meu_audio_gravado.wav \
  --output meu_audio_processado.wav
```

**Limitação**: Não gera texto novo, apenas melhora áudio existente.

---

## 📊 MONITORAMENTO DO TREINAMENTO

### Arquivos Importantes:

```
train/output/ptbr_novo_validado/
├── model_200.pt          # Checkpoint update 200
├── model_400.pt          # Checkpoint update 400
├── ...
├── model_last.pt         # Último checkpoint
└── samples/
    ├── update_200_gen.wav   # Sample gerado
    ├── update_200_ref.wav   # Sample de referência
    └── ...

train/logs/
├── novo_treinamento_YYYYMMDD_HHMMSS.log  # Log completo
└── tensorboard/                           # Métricas (se habilitado)
```

### Validar Samples Durante Treinamento:

```bash
# A cada checkpoint salvo, validar o sample gerado
python3 train/validar_audio.py \
  train/output/ptbr_novo_validado/samples/update_200_gen.wav

# Comparar com inferência
python3 train/infer_como_trainer.py \
  --checkpoint train/output/ptbr_novo_validado/model_200.pt \
  --ref-audio train/output/ptbr_novo_validado/samples/update_200_ref.wav \
  --ref-text "<TEXTO_DO_SAMPLE>" \
  --output train/teste_update_200.wav

python3 train/validar_audio.py train/teste_update_200.wav
```

---

## ⚡ COMANDOS RÁPIDOS

```bash
# Testar pipeline que FUNCIONA
python3 train/teste_ok.py \
  --audio train/output/ptbr_finetuned2/samples/update_25400_gen.wav

# Iniciar novo treinamento
./train/iniciar_novo_treinamento.sh

# Verificar VRAM durante treinamento
watch -n 1 nvidia-smi

# Ver últimas linhas do log
tail -f train/logs/novo_treinamento_*.log

# Parar treinamento (se necessário)
# Ctrl+C no terminal do treinamento
# O último checkpoint será salvo automaticamente
```

---

## 📞 QUANDO PEDIR AJUDA

Se após treinar novo modelo o problema persistir:

1. **Coletar informações**:
```bash
# Versão da biblioteca
pip show f5-tts

# Listar checkpoints gerados
ls -lah train/output/ptbr_novo_validado/*.pt

# Copiar últimas 50 linhas do log
tail -50 train/logs/novo_treinamento_*.log > train/debug_log.txt
```

2. **Informações a reportar**:
   - Versão do F5-TTS
   - Configuração usada (config_novo_validado.yaml)
   - Logs de erro
   - Resultado dos testes de validação
   - Comparação samples do trainer vs inferência

---

## ✨ EXPECTATIVA DE RESULTADO

### Cenário Ideal:
- ✅ Novo modelo treina sem erros
- ✅ Samples do trainer são inteligíveis
- ✅ Inferência via `infer_como_trainer.py` também funciona
- ✅ Similaridade > 80%

### Cenário Realista:
- ✅ Samples do trainer funcionam
- ⚠️ Inferência pode ainda ter problemas
- 🔧 Necessário ajustar parâmetros ou código

### Cenário Pessimista:
- ❌ Problema persiste mesmo com novo modelo
- 🐛 Confirma bug na biblioteca F5-TTS
- 💡 Usar workaround (reconstrução apenas)

---

**Última atualização**: 06/12/2024 14:00
