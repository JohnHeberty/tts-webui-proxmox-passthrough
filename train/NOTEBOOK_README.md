# 🎙️ F5-TTS Test Notebook - Guia Completo

## 📋 Visão Geral

Este notebook permite testar o modelo F5-TTS fine-tuned **diretamente**, sem necessidade de API, containers Docker ou qualquer infraestrutura adicional. É ideal para:

- ✅ Testar rapidamente o modelo treinado
- ✅ Experimentar com diferentes parâmetros
- ✅ Comparar qualidade com samples do treinamento
- ✅ Gerar áudios para demonstração
- ✅ Debugar problemas de qualidade

## 🚀 Quick Start

### 1. Ativar Ambiente Virtual

```bash
cd /home/tts-webui-proxmox-passthrough/train
python3 -m venv venv
source venv/bin/activate
```

### 2. Instalar Dependências

```bash
pip install f5-tts torch torchaudio soundfile numpy matplotlib librosa jupyter ipython
pip install num2words  # Para conversão de números
pip install pydub      # Para exportar MP3 (opcional)
```

### 3. Iniciar Jupyter

```bash
jupyter notebook notebook.ipynb
```

Ou usar VS Code com extensão Jupyter (já configurada).

## 📚 Estrutura do Notebook

### Seção 1-2: Setup Inicial
- Imports e verificação de GPU
- Configuração de paths e device

### Seção 3: Carregar Modelo
- Load do checkpoint fine-tuned (`model_last.pt`)
- Load do vocoder Vocos
- Verificação de parâmetros

### Seção 4-5: Preparar Dados
- Seleção de áudio de referência
- Definição de textos (ref_text + gen_text)

### Seção 6-7: Geração
- **Geração de áudio com parâmetros otimizados**
- Salvamento em WAV
- Player de áudio integrado

### Seção 8: Visualização
- Waveform
- Spectrogram
- Mel Spectrogram

### Seção 9-10: Análise
- Métricas de qualidade (RMS, SNR, clipping, etc)
- Comparação com samples do treinamento

### Seção 11: Testes Experimentais
- Diferentes configurações de parâmetros
- Comparação de qualidade vs velocidade

### Seção 12-13: Extras
- Exportação para MP3
- Resumo e próximos passos

## ⚙️ Parâmetros Principais

### nfe_step (Number of Function Evaluations)

Controla o número de steps da diffusion. Mais steps = melhor qualidade, mas mais lento.

```python
nfe_step=16   # 🚀 FAST - RTF ~0.7x (rápido)
nfe_step=32   # ⭐ BALANCED - RTF ~1.5x (recomendado - match treinamento)
nfe_step=48   # 💎 HIGH QUALITY - RTF ~2.2x
nfe_step=64   # 👑 ULTRA QUALITY - RTF ~3.0x (diminishing returns)
```

### cfg_strength (Classifier-Free Guidance)

Controla quanto o modelo segue a referência vs gera livremente.

```python
cfg_strength=1.5   # Mais criativo, menos fiel à referência
cfg_strength=2.0   # ⭐ Padrão (match treinamento)
cfg_strength=2.5   # Mais fiel à referência, menos variação
```

### sway_sampling_coef

Controle de variação/randomness na geração.

```python
sway_sampling_coef=-1.0   # ⭐ AUTO (recomendado - match treinamento)
sway_sampling_coef=0.0    # Sem variação
sway_sampling_coef=0.3    # ❌ NÃO USAR! Causa artefatos
```

**⚠️ IMPORTANTE:** Sempre use `sway_sampling_coef=-1.0` (auto). Valores positivos causam artefatos de áudio!

## 🎯 Casos de Uso

### Caso 1: Teste Rápido de Qualidade

```python
# Use parâmetros padrão (match com treinamento)
nfe_step=32
cfg_strength=2.0
sway_sampling_coef=-1.0
```

Resultado esperado: **Qualidade idêntica aos samples do treinamento**

### Caso 2: Produção em Massa (Velocidade)

```python
# Sacrifica um pouco de qualidade por velocidade
nfe_step=16
cfg_strength=1.5
sway_sampling_coef=-1.0
```

Resultado esperado: **RTF ~0.7x (70% do tempo real), qualidade BOA**

### Caso 3: Máxima Qualidade (Demo/Apresentação)

```python
# Qualidade premium para demonstrações
nfe_step=64
cfg_strength=2.5
sway_sampling_coef=-1.0
```

Resultado esperado: **RTF ~3.0x, qualidade EXCELENTE**

## 📊 Interpretando Métricas

### RMS (Root Mean Square)

Mede o volume médio do áudio.

- **Ideal:** 0.05 - 0.3
- **< 0.05:** Áudio muito baixo
- **> 0.3:** Áudio muito alto (risco de clipping)

### Clipping

Samples que atingem o limite digital (±1.0).

- **Ideal:** < 0.1%
- **> 1%:** Distorção audível

### SNR (Signal-to-Noise Ratio)

Relação sinal/ruído em dB.

- **Excelente:** > 30 dB
- **Bom:** 20-30 dB
- **Ruim:** < 20 dB

### Spectral Centroid

"Brilho" do áudio (frequência média ponderada).

- **Voz natural:** 500-3000 Hz
- **Muito baixo (<500):** Voz abafada
- **Muito alto (>3000):** Voz metálica

## 🐛 Troubleshooting

### Problema: Áudio com artefatos/glitches

**Causa:** `sway_sampling_coef` com valor positivo

**Solução:**
```python
sway_sampling_coef=-1.0  # Sempre usar -1.0 (auto)
```

### Problema: Voz não parece com a referência

**Causas possíveis:**
1. `ref_text` não é a transcrição exata do áudio
2. Áudio de referência muito curto (<5s) ou muito longo (>30s)
3. Áudio de referência com muito ruído

**Soluções:**
```python
# 1. Transcreva EXATAMENTE o que está no áudio de referência
ref_text = "texto exato do áudio"

# 2. Use áudio de 10-30 segundos
# Verifique: duration = len(audio) / sr

# 3. Use áudio limpo (sem ruído de fundo)
```

### Problema: Geração muito lenta

**Causa:** `nfe_step` muito alto ou GPU não sendo usada

**Soluções:**
```python
# 1. Reduzir nfe_step
nfe_step=16  # Mais rápido

# 2. Verificar se GPU está sendo usada
print(f"Device: {device}")  # Deve mostrar 'cuda'
print(f"CUDA available: {torch.cuda.is_available()}")

# 3. Se GPU não disponível, considere usar CPU com nfe_step=16
```

### Problema: Out of Memory (CUDA)

**Causa:** VRAM insuficiente

**Soluções:**
```python
# 1. Reduzir batch (já é 1 no notebook)

# 2. Usar CPU
device = "cpu"

# 3. Limpar cache entre gerações
torch.cuda.empty_cache()
```

## 📁 Estrutura de Arquivos

```
train/
├── notebook.ipynb           # ⭐ Este notebook
├── NOTEBOOK_README.md       # 📚 Esta documentação
├── test_output/             # 📁 Áudios gerados pelo notebook
│   ├── f5tts_test_*.wav
│   ├── spectrogram_*.png
│   └── test_*.wav
├── output/
│   └── ptbr_finetuned2/
│       ├── model_last.pt    # 🎯 Checkpoint usado
│       ├── model_33200.pt
│       └── samples/         # 🔊 Samples do treinamento
│           ├── update_33200_gen.wav
│           └── update_33200_ref.wav
└── venv/                    # 🐍 Virtual environment
```

## 🎓 Conceitos Importantes

### Flow Matching Diffusion

F5-TTS usa **Flow Matching**, uma técnica de diffusion mais eficiente que modelos tradicionais como Stable Diffusion.

- **Vantagem:** Melhor qualidade com menos steps
- **Trade-off:** Mais lento que modelos autoregressivos (como XTTS)

### Zero-Shot Voice Cloning

O modelo consegue clonar qualquer voz com apenas 3-30 segundos de áudio de referência.

- **Sem fine-tuning adicional:** Apenas carrega o checkpoint
- **Qualidade:** Depende da qualidade e duração do áudio de referência

### Fine-Tuning para PT-BR

O modelo foi fine-tuned especificamente para português brasileiro:

- **Melhora:** Prosódia natural, entonação, ritmo
- **Dataset:** Áudios de qualidade em PT-BR
- **Resultado:** Fala mais natural que modelo base multilingual

## 📚 Referências

- **Paper:** [F5-TTS: A Fairerseq Fair-Speech Text-to-Speech Model](https://arxiv.org/abs/2410.06885)
- **Documentação Interna:**
  - `docs/F5TTS_QUALITY_FIX.md` - Parâmetros e qualidade
  - `app/quality_profiles.py` - Profiles pré-configurados
  - `docs/SYMLINK_FIX.md` - Troubleshooting de checkpoints

## 🤝 Contribuindo

Para melhorar este notebook:

1. Adicione novos exemplos de uso
2. Documente casos de edge
3. Adicione visualizações interessantes
4. Compartilhe descobertas sobre parâmetros

## ⚖️ Licença

Este notebook é parte do projeto `tts-webui-proxmox-passthrough`.

F5-TTS: Licença do projeto original (verificar repositório oficial).

---

**Última Atualização:** 2025-12-05  
**Versão:** 1.0  
**Autor:** Audio Voice Service Team
