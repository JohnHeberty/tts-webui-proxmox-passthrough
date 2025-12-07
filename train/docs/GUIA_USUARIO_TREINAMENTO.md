# 📚 Guia do Usuário - Treinamento XTTS-v2

**Guia completo para treinar seu próprio modelo de síntese de voz (TTS) personalizado**

Este guia foi criado para que qualquer pessoa, **mesmo sem conhecimento técnico avançado**, consiga treinar um modelo de voz personalizado usando o sistema XTTS-v2.

---

## 📋 Índice

1. [O que você vai conseguir fazer](#o-que-você-vai-conseguir-fazer)
2. [Requisitos do Sistema](#requisitos-do-sistema)
3. [Preparação dos Dados](#preparação-dos-dados)
4. [Configuração do Treinamento](#configuração-do-treinamento)
5. [Executando o Treinamento](#executando-o-treinamento)
6. [Monitorando o Progresso](#monitorando-o-progresso)
7. [Testando Seu Modelo](#testando-seu-modelo)
8. [Solução de Problemas](#solução-de-problemas)
9. [Perguntas Frequentes](#perguntas-frequentes)

---

## 🎯 O que você vai conseguir fazer

Após seguir este guia, você será capaz de:

✅ **Criar um modelo de voz personalizado** que imita qualquer voz que você quiser  
✅ **Gerar áudio sintético** com a voz treinada dizendo qualquer texto  
✅ **Clonar vozes** com apenas alguns minutos de áudio de referência  
✅ **Melhorar a qualidade** do modelo através de ajustes e mais treinamento  

**Exemplo prático**: Você pode treinar um modelo com gravações da sua própria voz e depois fazer esse modelo "ler" livros, artigos ou qualquer texto!

---

## 💻 Requisitos do Sistema

### Hardware Mínimo

| Componente | Mínimo | Recomendado |
|------------|--------|-------------|
| **GPU** | NVIDIA GTX 1080 (8GB VRAM) | NVIDIA RTX 3090 (24GB VRAM) |
| **RAM** | 16 GB | 32 GB ou mais |
| **Armazenamento** | 50 GB livres | 100 GB SSD |
| **CPU** | 4 cores | 8+ cores |

⚠️ **Importante**: Você **PRECISA** de uma placa de vídeo NVIDIA com suporte CUDA. CPUs comuns não conseguirão treinar o modelo em tempo razoável.

### Software Necessário

✅ **Linux** (Ubuntu 20.04+ recomendado) ou **Windows 10/11**  
✅ **Python 3.9 ou 3.10** (não use 3.11+, ainda não é totalmente compatível)  
✅ **CUDA 11.8** (para GPUs NVIDIA)  
✅ **Git** (para clonar o repositório)  

---

## 📁 Preparação dos Dados

### Passo 1: Grave ou Colete Áudios

Você precisa de áudios da voz que deseja clonar. Quanto mais, melhor!

**Requisitos dos áudios:**

- ✅ **Formato**: WAV (preferencial) ou MP3
- ✅ **Qualidade**: 22050 Hz ou superior
- ✅ **Duração**: Entre 5 segundos e 30 segundos por arquivo
- ✅ **Quantidade**: Mínimo 30 minutos, ideal 2-10 horas
- ✅ **Silêncio**: Pouco ruído de fundo
- ✅ **Conteúdo**: Voz clara, sem música ou efeitos

**Dicas para gravação:**

🎤 Grave em ambiente silencioso (sem eco, sem barulho de fundo)  
🎤 Use um microfone decente (não precisa ser profissional)  
🎤 Fale naturalmente, com entonação variada  
🎤 Leia frases completas (não palavras isoladas)  
🎤 Varie o conteúdo (perguntas, afirmações, emoções diferentes)  

### Passo 2: Organize os Arquivos

Crie uma pasta com seus áudios:

```
meus_audios/
├── audio001.wav
├── audio002.wav
├── audio003.wav
└── ...
```

### Passo 3: Prepare o Dataset

O sistema precisa dos áudios em um formato específico. Use o script de preparação:

```bash
# Navegar até a pasta do projeto
cd /home/tts-webui-proxmox-passthrough

# Executar script de preparação
python -m train.scripts.prepare_dataset \
    --input_dir meus_audios/ \
    --output_dir train/data/MyTTSDataset \
    --language pt
```

**O que esse comando faz:**

1. ✅ Converte todos os áudios para o formato correto (WAV 22050 Hz)
2. ✅ Divide automaticamente em treino (90%) e validação (10%)
3. ✅ Cria arquivos de metadados necessários
4. ✅ Verifica qualidade dos áudios

**Resultado esperado:**

```
✅ Dataset preparado com sucesso!

📊 Estatísticas:
   Total de áudios: 250
   Treino: 225 samples (90%)
   Validação: 25 samples (10%)
   Duração total: 2h 15min
   
📁 Arquivos criados:
   train/data/MyTTSDataset/wavs/       (áudios processados)
   train/data/MyTTSDataset/metadata_train.csv
   train/data/MyTTSDataset/metadata_val.csv
```

---

## ⚙️ Configuração do Treinamento

### Passo 1: Editar Arquivo de Configuração

Abra o arquivo de configuração com seu editor preferido:

```bash
nano train/config/train_config.yaml
```

### Passo 2: Ajustar Parâmetros Principais

#### **Para iniciantes** (configuração segura):

```yaml
# Quanto tempo treinar
training:
  num_epochs: 50              # 50 épocas é um bom começo
  learning_rate: 1.0e-5       # Taxa de aprendizado (NÃO MUDE se não souber)
  
# Recursos da GPU
data:
  batch_size: 2               # Use 2 se tem 8-12 GB VRAM
                              # Use 4-6 se tem 24 GB VRAM
                              
# A cada quantas épocas salvar
logging:
  save_every_n_epochs: 5      # Salva checkpoint a cada 5 épocas
  log_every_n_steps: 50       # Log a cada 50 passos
```

#### **Configuração avançada** (usuários experientes):

```yaml
training:
  num_epochs: 100             # Mais épocas = melhor qualidade (demora mais)
  learning_rate: 5.0e-6       # Learning rate menor = mais estável
  use_amp: false              # Mixed precision (pode dar erro em algumas GPUs)
  
data:
  batch_size: 6               # Maior batch = mais rápido (precisa mais VRAM)
  num_workers: 4              # Mais workers = carregamento mais rápido
  
logging:
  save_every_n_epochs: 1      # Salva a cada época (mais checkpoints)
  use_tensorboard: true       # Monitoramento visual (recomendado!)
```

### Tabela de Referência - Batch Size vs VRAM

| VRAM Disponível | Batch Size Recomendado |
|-----------------|------------------------|
| 8 GB | 1-2 |
| 12 GB | 2-4 |
| 16 GB | 4-6 |
| 24 GB | 6-8 |

⚠️ **Se der erro "Out of Memory"**: Diminua o `batch_size` para 1

---

## 🚀 Executando o Treinamento

### Opção 1: Treinamento Completo (Recomendado)

Execute o comando abaixo e deixe o treinamento rodar:

```bash
python -m train.scripts.train_xtts --config train/config/train_config.yaml
```

**Saída esperada:**

```
🚀 Iniciando treinamento XTTS-v2...
   Epochs: 50
   Batch size: 2
   Learning rate: 1e-05
   Device: cuda

📊 Datasets carregados:
   Train: 225 samples
   Val: 25 samples
   Steps per epoch: 112

============================================================
EPOCH 1/50
============================================================

Epoch 1/50 | Step 10/112 | Loss: 0.5641 | Avg: 0.5534 | LR: 1.00e-05
Epoch 1/50 | Step 20/112 | Loss: 0.5421 | Avg: 0.5498 | LR: 1.00e-05
...
```

### Opção 2: Teste Rápido (Smoke Test)

Antes de treinar por horas, teste se tudo está funcionando:

```bash
python -m train.scripts.train_xtts --config train/config/smoke_test.yaml
```

Este teste roda apenas **2 épocas** e termina em ~10 minutos. Se funcionar, seu sistema está pronto!

### Quanto Tempo Demora?

| Dataset | GPU | Épocas | Tempo Estimado |
|---------|-----|--------|----------------|
| 30 min áudio | RTX 3090 | 50 | 2-4 horas |
| 2 horas áudio | RTX 3090 | 50 | 8-12 horas |
| 10 horas áudio | RTX 3090 | 100 | 24-48 horas |
| 30 min áudio | GTX 1080 | 50 | 6-10 horas |

💡 **Dica**: Deixe treinando durante a noite ou quando não estiver usando o computador.

---

## 📊 Monitorando o Progresso

### Opção 1: Logs no Terminal

Acompanhe o progresso direto no terminal:

```
📊 EPOCH 5 COMPLETO
   Train Loss: 0.4123
   Val Loss: 0.3987
   
💾 Checkpoint salvo: checkpoint_epoch_5.pt
📢 Sample: epoch_5_step_560_output.wav + reference.wav
```

**O que significam os números:**

- **Train Loss**: Erro no treino (quanto menor, melhor)
- **Val Loss**: Erro na validação (quanto menor, melhor)
- **🏆 Novo melhor modelo**: Aparece quando o modelo melhora

**Valores típicos:**

- Início: Loss ~0.6-0.8 (normal, modelo ainda aprendendo)
- Após 20 épocas: Loss ~0.3-0.5 (já está ficando bom)
- Após 50 épocas: Loss ~0.2-0.3 (qualidade boa)
- Após 100 épocas: Loss <0.2 (excelente qualidade)

### Opção 2: TensorBoard (Visual)

TensorBoard mostra gráficos bonitos do progresso!

**1. Em outro terminal, execute:**

```bash
tensorboard --logdir train/runs --port 6006
```

**2. Abra no navegador:**

```
http://localhost:6006
```

**O que você verá:**

📈 **Gráfico de Loss**: Curva descendo = modelo melhorando  
📈 **Learning Rate**: Veja como a taxa de aprendizado muda  
📈 **Comparação Treino vs Validação**: Se divergirem muito, pode estar overfitting  

---

## 🎵 Testando Seu Modelo

### Passo 1: Encontre o Melhor Checkpoint

Os checkpoints ficam salvos em:

```
train/output/checkpoints/
├── best_model.pt              ← MELHOR MODELO (use este!)
├── checkpoint_epoch_5.pt
├── checkpoint_epoch_10.pt
└── ...
```

### Passo 2: Teste com Script Automático

Execute o teste de voice cloning:

```bash
python -m train.scripts.test_voice_clone
```

**O que esse script faz:**

1. ✅ Carrega seu modelo treinado (`best_model.pt`)
2. ✅ Pega um áudio de referência
3. ✅ Transcreve o áudio automaticamente (usando Whisper)
4. ✅ Gera novo áudio com a voz clonada
5. ✅ Compara qualidade entre original e clonado
6. ✅ Dá uma nota de 0 a 5 para a qualidade

**Saída esperada:**

```
📝 ETAPA 1: Transcrição do áudio de referência
✅ Transcrição completa:
   "Este é um teste do sistema de síntese de voz."

🎙️  ETAPA 2: Geração de áudio clonado
✅ Áudio clonado gerado: cloned_output.wav

📊 ETAPA 3: Análise de qualidade comparativa
⏱️  Duração:
   Referência: 3.45s
   Clonado: 3.52s
   Diferença: 0.07s (102.0%)

🎵 Similaridade Espectral (MFCC):
   Similaridade: 0.8234 (0-1, maior = mais similar)
   Qualidade: ✅ Excelente

⭐ Score Geral (estimado MOS 0-5):
   ⭐ SCORE FINAL: 4.12/5.0
   Qualidade: ✅ EXCELENTE - Clonagem de alta qualidade
```

### Passo 3: Ouça os Áudios

Os resultados ficam em `train/test/results/`:

```
train/test/results/
├── cloned_output.wav      ← Áudio gerado pelo modelo
├── transcription.txt      ← Texto transcrito
└── test_results.json      ← Métricas detalhadas
```

**Compare você mesmo:**

🎧 Ouça `reference_test.wav` (original)  
🎧 Ouça `cloned_output.wav` (gerado)  

### Passo 4: Teste com Seu Próprio Texto

Crie um script Python simples:

```python
from train.scripts.xtts_inference import XTTSInference

# Carregar modelo treinado
model = XTTSInference(
    checkpoint_path="train/output/checkpoints/best_model.pt"
)

# Gerar áudio com voz clonada
model.synthesize_to_file(
    text="Olá! Este é meu modelo de voz personalizado.",
    output_path="meu_audio.wav",
    language="pt",
    speaker_wav="train/test/audio/reference_test.wav"
)

print("✅ Áudio gerado: meu_audio.wav")
```

Execute:

```bash
python meu_teste.py
```

---

## 🔧 Solução de Problemas

### ❌ Erro: "CUDA Out of Memory"

**Problema**: GPU sem memória suficiente.

**Solução**:

1. Abra `train/config/train_config.yaml`
2. Diminua `batch_size` de 2 para 1
3. Tente novamente

```yaml
data:
  batch_size: 1  # Era 2, agora é 1
```

### ❌ Erro: "No module named 'TTS'"

**Problema**: Biblioteca TTS (Coqui) não instalada.

**Solução**:

```bash
pip install TTS
```

### ❌ Erro: "Whisper not found"

**Problema**: Whisper não instalado (necessário para transcrição).

**Solução**:

```bash
pip install openai-whisper
```

### ❌ Loss não diminui / fica estagnado

**Problema**: Modelo não está aprendendo.

**Possíveis causas e soluções**:

1. **Dataset muito pequeno**: Adicione mais áudios (ideal >1 hora)
2. **Learning rate muito alto**: Diminua para `5.0e-6`
3. **Overfitting**: Adicione mais dados de validação
4. **Áudios ruins**: Verifique qualidade (sem ruído, voz clara)

### ❌ Áudio gerado com qualidade ruim

**Problema**: Modelo gera áudio, mas qualidade é baixa.

**Soluções**:

1. **Treine mais épocas**: Tente 100-200 épocas em vez de 50
2. **Melhore dataset**: 
   - Remova áudios com ruído
   - Adicione mais variedade
   - Garanta que todos estejam no formato correto
3. **Ajuste hyperparâmetros**:
   ```yaml
   training:
     learning_rate: 5.0e-6  # Menor = mais estável
     num_epochs: 100
   ```

### ❌ TensorBoard não abre

**Problema**: Porta 6006 já está em uso.

**Solução**: Use porta diferente:

```bash
tensorboard --logdir train/runs --port 6007
# Abra: http://localhost:6007
```

---

## ❓ Perguntas Frequentes

### 1. Quanto áudio preciso para treinar?

**Resposta**:

- **Mínimo**: 30 minutos (qualidade básica)
- **Bom**: 1-2 horas (qualidade razoável)
- **Excelente**: 5-10 horas (alta qualidade)
- **Profissional**: 20+ horas (qualidade máxima)

### 2. Posso treinar com áudios de podcast/YouTube?

**Resposta**: Sim, mas com cuidados:

✅ **Permitido**: Se você tem direitos sobre o áudio  
⚠️ **Qualidade**: Remova músicas, efeitos sonoros, múltiplas vozes  
⚠️ **Legal**: Respeite direitos autorais (use apenas com permissão)  

### 3. Quanto custa treinar (em energia elétrica)?

**Resposta**: Estimativa aproximada:

- RTX 3090: ~350W
- 10 horas de treino = 3.5 kWh
- Custo: R$ 2-5 (dependendo da tarifa)

### 4. Posso parar o treinamento e continuar depois?

**Resposta**: SIM! O sistema salva checkpoints automaticamente.

Para continuar de onde parou:

```bash
python -m train.scripts.train_xtts \
    --config train/config/train_config.yaml \
    --resume_from train/output/checkpoints/checkpoint_epoch_20.pt
```

### 5. Qual a diferença entre treino e fine-tuning?

**Resposta**:

- **Treino do zero**: Demora semanas, precisa centenas de horas de áudio
- **Fine-tuning** (o que fazemos aqui): Ajusta modelo pré-treinado, demora horas, precisa 30min-10h de áudio

Estamos fazendo **fine-tuning**, que é muito mais rápido e prático!

### 6. O modelo funciona em tempo real?

**Resposta**: Depende da GPU:

- RTX 3090: ~1-2 segundos para gerar 10 segundos de áudio
- RTX 4090: <1 segundo para 10 segundos de áudio
- GTX 1080: ~3-5 segundos para 10 segundos de áudio

**Não é exatamente tempo real**, mas é rápido o suficiente para muitas aplicações!

### 7. Posso usar o modelo comercialmente?

**Resposta**: Depende:

- ✅ **Código**: MIT License (livre para uso comercial)
- ⚠️ **Modelo XTTS-v2**: Verifique licença do Coqui TTS
- ⚠️ **Voz clonada**: Precisa de permissão do dono da voz

**Recomendação**: Consulte um advogado para uso comercial.

### 8. Como melhorar a qualidade do áudio gerado?

**Checklist de qualidade**:

- [ ] Dataset com >2 horas de áudio
- [ ] Áudios sem ruído de fundo
- [ ] Microfone decente (não precisa ser caro)
- [ ] Ambiente silencioso
- [ ] Variedade no conteúdo (não repetir frases)
- [ ] Treinar por 100+ épocas
- [ ] Val Loss <0.25
- [ ] Usar `best_model.pt` (não checkpoints intermediários)

### 9. Posso treinar múltiplas vozes no mesmo modelo?

**Resposta**: NÃO recomendado. Treine um modelo separado para cada voz.

Se misturar vozes:
- ❌ Qualidade cai
- ❌ Modelo fica confuso
- ❌ Difícil controlar qual voz será usada

### 10. O que fazer se meu computador travar durante o treino?

**Resposta**:

1. ✅ **Não se preocupe**: Checkpoints são salvos automaticamente
2. ✅ **Reinicie** e continue de onde parou (veja pergunta 4)
3. ✅ **Prevenção futura**:
   - Monitore temperatura da GPU
   - Use batch_size menor
   - Feche outros programas pesados

---

## 📖 Recursos Adicionais

### Documentação Técnica

- 📄 [XTTS-v2 Paper](https://arxiv.org/abs/2406.04904)
- 📄 [Coqui TTS Docs](https://docs.coqui.ai/)
- 📄 [TensorBoard Guide](https://www.tensorflow.org/tensorboard)

### Comunidade

- 💬 Discord: [Coqui Community](https://discord.gg/coqui)
- 🐙 GitHub: [XTTS Issues](https://github.com/coqui-ai/TTS/issues)

### Tutoriais em Vídeo

- 🎥 "Voice Cloning with XTTS" - YouTube
- 🎥 "TensorBoard for Beginners" - YouTube
- 🎥 "Audio Preprocessing Tutorial" - YouTube

---

## 🎓 Conclusão

Parabéns! 🎉 Agora você sabe como:

✅ Preparar um dataset de áudio  
✅ Configurar e executar o treinamento  
✅ Monitorar o progresso com TensorBoard  
✅ Testar e usar seu modelo personalizado  
✅ Resolver problemas comuns  

**Próximos passos**:

1. 🚀 Treine seu primeiro modelo com 1-2 horas de áudio
2. 🎧 Teste a qualidade e compare com o original
3. 🔧 Ajuste parâmetros para melhorar resultados
4. 📈 Aumente o dataset para melhor qualidade
5. 🎯 Use seu modelo em produção!

**Precisa de ajuda?**

- 📧 Abra uma issue no GitHub
- 💬 Pergunte na comunidade Discord
- 📚 Consulte a documentação técnica

**Boa sorte com seu treinamento!** 🚀🎤

---

*Última atualização: Dezembro 2024*  
*Versão do guia: 1.0*  
*Compatível com: XTTS-v2, Python 3.9-3.10, CUDA 11.8*
