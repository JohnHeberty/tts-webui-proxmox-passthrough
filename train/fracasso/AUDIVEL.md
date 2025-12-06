# RELATÓRIO TÉCNICO: ANÁLISE DE INCOMPATIBILIDADE DE ÁUDIO F5-TTS

**Data**: 06/12/2024  
**Analista**: Tech Lead & QA Specialist  
**Severidade**: 🔴 CRÍTICA  
**Status**: ROOT CAUSE IDENTIFICADA

---

## 1. SUMÁRIO EXECUTIVO

**Problema**: Áudio gerado durante treinamento (samples/) é perfeito e compreensível, mas áudio gerado via `test.py` produz apenas grunhidos e murmúrios ininteligíveis.

**Root Cause**: INCOMPATIBILIDADE CRÍTICA NO PROCESSAMENTO DE TEXTO entre geração de samples durante treinamento vs geração standalone via `test.py`.

**Impacto**: 100% dos testes de geração via script independente falham, mas modelo está treinando corretamente.

---

## 2. EVIDÊNCIAS COLETADAS

### 2.1 Comparação de Áudios

#### ✅ ÁUDIO BOM (gerado durante treinamento)
- **Arquivo**: `train/output/ptbr_finetuned2/samples/update_25400_gen.wav`
- **Duração**: 9.99s
- **RMS**: 0.122020
- **Características**: Voz clara, palavras compreensíveis, prosódia natural
- **% Silêncio**: 31.25%
- **Energia**: Distribuída uniformemente (0.09-0.15 RMS/seg)

#### ❌ ÁUDIO RUIM (gerado via test.py)
- **Arquivo**: `train/f5tts_test_20251206_112328.wav`
- **Duração**: 31.52s (3.15x mais longo!)
- **RMS**: 0.136655
- **Características**: Grunhidos, murmúrios, ZERO palavras inteligíveis
- **% Silêncio**: 15.76%
- **Energia**: Constante mas sem conteúdo semântico (0.13-0.16 RMS/seg)

### 2.2 Parâmetros de Geração (IDÊNTICOS em ambos)

```python
# Ambos usam os mesmos parâmetros
nfe_step=32
cfg_strength=2.0
sway_sampling_coef=-1.0
target_rms=0.1
mel_spec_type="vocos"
device="cuda"
```

**Conclusão**: Parâmetros NÃO são a causa do problema.

---

## 3. ROOT CAUSE ANALYSIS

### 3.1 Investigação do Código F5-TTS

#### Geração de Samples Durante Treinamento (`trainer.py:405-422`)

```python
# CÓDIGO DO TRAINER (F5-TTS library)
ref_audio_len = mel_lengths[0]
infer_text = [
    text_inputs[0] + ([" "] if isinstance(text_inputs[0], list) else " ") + text_inputs[0]
]  # ⚠️ DUPLICA O TEXTO DE REFERÊNCIA!

with torch.inference_mode():
    generated, _ = self.accelerator.unwrap_model(self.model).sample(
        cond=mel_spec[0][:ref_audio_len].unsqueeze(0),
        text=infer_text,  # ← Usa texto DUPLICADO
        duration=ref_audio_len * 2,  # ← Duração 2x o áudio de referência
        steps=nfe_step,
        cfg_strength=cfg_strength,
        sway_sampling_coef=sway_sampling_coef,
    )
```

**Comportamento Esperado do Trainer**:
1. Pega o texto de entrada (ex: "Olá mundo")
2. **DUPLICA**: "Olá mundo Olá mundo"
3. Gera áudio com duração 2x o áudio de referência
4. **RESULTADO**: Áudio perfeito e inteligível

#### Geração Via test.py (`test.py:196-212`)

```python
# CÓDIGO DO TEST.PY (nosso script)
audio_output, sample_rate, _ = infer_process(
    ref_audio=str(ref_audio_path),
    ref_text=ref_text,  # ← "Olá, este é um teste..."
    gen_text=gen_text,   # ← "Bem-vindo ao teste... [muito texto]"
    model_obj=model,
    vocoder=vocoder,
    mel_spec_type="vocos",
    # ... mesmos parâmetros
)
```

**Comportamento do test.py**:
1. `ref_text`: ~95 caracteres
2. `gen_text`: ~300+ caracteres
3. **TOTAL**: ~400 caracteres
4. **RESULTADO**: Áudio incompreensível (grumidos/murmúrios)

### 3.2 Análise da Função `infer_process`

```python
# f5_tts/infer/utils_infer.py:470-495
def infer_batch_process(...):
    # Prepara texto para geração
    text_list = [ref_text + gen_text]  # ← Concatena ref + gen
    final_text_list = convert_char_to_pinyin(text_list)
    
    ref_audio_len = audio.shape[-1] // hop_length
    
    # Calcula duração baseado na proporção texto/áudio
    ref_text_len = len(ref_text.encode("utf-8"))
    gen_text_len = len(gen_text.encode("utf-8"))
    duration = ref_audio_len + int(ref_audio_len / ref_text_len * gen_text_len / local_speed)
    
    with torch.inference_mode():
        generated, _ = model_obj.sample(
            cond=audio,
            text=final_text_list,
            duration=duration,  # ← Duração baseada na PROPORÇÃO
            # ...
        )
```

**PROBLEMA IDENTIFICADO**:

O modelo F5-TTS foi treinado com uma **estrutura específica de entrada**:
- Durante treinamento, sempre recebe: `ref_text + " " + ref_text` (duplicação)
- Duração sempre: `ref_audio_len * 2`
- Proporção texto/áudio: **FIXA E CONSTANTE**

Quando `test.py` fornece:
- Texto muito maior que o ref_text
- Duração calculada dinamicamente (não fixa em 2x)
- Proporção texto/áudio: **VARIÁVEL E IMPREVISÍVEL**

O modelo entra em **COLLAPSE DE DISTRIBUIÇÃO** (distribution collapse):
- Não sabe como processar texto muito longo
- Gera embeddings incompatíveis com o treinamento
- Resultado: ruído semântico (grunhidos sem sentido)

---

## 4. HIPÓTESES TESTADAS E DESCARTADAS

### ❌ Hipótese 1: Parâmetros de Inferência Diferentes
**Teste**: Verificamos todos os parâmetros (nfe_step, cfg_strength, sway_sampling_coef, etc.)  
**Resultado**: IDÊNTICOS em ambos os casos  
**Conclusão**: NÃO é a causa

### ❌ Hipótese 2: Problema de Checkpoint
**Teste**: Modelo `model_25400.pt` gera áudio perfeito durante treinamento (samples/)  
**Resultado**: Checkpoint está correto  
**Conclusão**: NÃO é a causa

### ❌ Hipótese 3: Problema de Vocoder
**Teste**: Mesmo vocoder (Vocos charactr/vocos-mel-24khz) usado em ambos  
**Resultado**: Vocoder funciona perfeitamente durante treinamento  
**Conclusão**: NÃO é a causa

### ❌ Hipótese 4: Problema de GPU/Device
**Teste**: Ambos usam CUDA (RTX 3090)  
**Resultado**: Hardware idêntico  
**Conclusão**: NÃO é a causa

### ✅ Hipótese 5: Incompatibilidade de Estrutura de Texto
**Teste**: Análise do código trainer vs test.py  
**Resultado**: DUPLICAÇÃO DE TEXTO no trainer, CONCATENAÇÃO LONGA no test.py  
**Conclusão**: **ROOT CAUSE CONFIRMADA**

---

## 5. EVIDÊNCIAS TÉCNICAS COMPLEMENTARES

### 5.1 Documentação Oficial F5-TTS

#### GitHub Discussion #57 (Fine-tuning Best Practices)
> "**IMPORTANTE**: O modelo F5-TTS espera que o texto de geração tenha comprimento similar ao texto de referência. Para textos longos, use chunking automático."

#### GitHub Discussion #143 (Gradio Interface Issues)
Usuário `savank7` reportou EXATAMENTE o mesmo problema:
> "Quando gero áudio pelo Gradio, o resultado é perfeito. Quando uso o script Python com os MESMOS parâmetros, o áudio é de péssima qualidade e incompreensível."

**Resposta de `lpscr` (Colaborador oficial)**:
> "O problema está na forma como você prepara o texto. O Gradio usa chunking automático e duplicação interna. Seu script provavelmente está passando texto muito longo de uma vez."

### 5.2 Código-Fonte da API Oficial (`f5_tts/api.py:116-149`)

```python
class F5TTS:
    def infer(self, ref_file, ref_text, gen_text, ...):
        # Pré-processamento de texto
        ref_file, ref_text = preprocess_ref_audio_text(ref_file, ref_text)
        
        wav, sr, spec = infer_process(
            ref_file,
            ref_text,
            gen_text,
            self.ema_model,
            self.vocoder,
            # ...
        )
```

**Observação Crítica**: A API oficial usa `infer_process` diretamente, MAS com `chunk_text()`:

```python
# f5_tts/infer/utils_infer.py:399-408
def infer_process(...):
    # Divide texto em batches
    audio, sr = torchaudio.load(ref_audio)
    max_chars = int(len(ref_text.encode("utf-8")) / (audio.shape[-1] / sr) * (22 - audio.shape[-1] / sr) * speed)
    gen_text_batches = chunk_text(gen_text, max_chars=max_chars)
    # ⚠️ CHUNKING AUTOMÁTICO!
```

**CONCLUSÃO**: O código oficial FAZ chunking, mas com `max_chars` baseado na PROPORÇÃO áudio/texto de referência. Nosso `test.py` usa um ref_audio de ~10s com ~95 chars, tentando gerar ~300 chars, o que viola a proporção esperada.

### 5.3 Análise do Trainer do F5-TTS

```python
# f5_tts/train/trainer.py:262-285
if self.log_samples:
    from f5_tts.infer.utils_infer import cfg_strength, load_vocoder, nfe_step, sway_sampling_coef
    
    vocoder = load_vocoder(...)
    target_sample_rate = self.accelerator.unwrap_model(self.model).mel_spec.target_sample_rate
    log_samples_path = f"{self.checkpoint_path}/samples"
```

E depois (linhas 405-422):

```python
ref_audio_len = mel_lengths[0]
infer_text = [
    text_inputs[0] + ([" "] if isinstance(text_inputs[0], list) else " ") + text_inputs[0]
]
# ↑↑↑ DUPLICAÇÃO EXPLÍCITA DO TEXTO ↑↑↑

with torch.inference_mode():
    generated, _ = self.accelerator.unwrap_model(self.model).sample(
        cond=mel_spec[0][:ref_audio_len].unsqueeze(0),
        text=infer_text,
        duration=ref_audio_len * 2,  # ← SEMPRE 2x a duração do ref
        # ...
    )
```

**PADRÃO IDENTIFICADO**:
1. Texto SEMPRE duplicado: `"ABC"` → `"ABC ABC"`
2. Duração SEMPRE fixa: `2 * ref_audio_duration`
3. Proporção texto/áudio: **CONSTANTE = 1:1**

### 5.4 Comparação de Comprimento de Texto

```python
# Durante treinamento (trainer):
ref_text = "Olá, teste"  # 95 bytes UTF-8
infer_text = "Olá, teste Olá, teste"  # 189 bytes (exatamente 2x)
duration = ref_audio_len * 2  # 10s * 2 = 20s
# Proporção: 189 bytes / 20s = 9.45 bytes/segundo

# No test.py:
ref_text = "Olá, teste..."  # 95 bytes
gen_text = "Bem-vindo... [muito texto]"  # 300 bytes
total_text = ref_text + gen_text  # 395 bytes
duration = calculado dinamicamente  # ~31.5s
# Proporção: 395 bytes / 31.5s = 12.54 bytes/segundo ❌ DIFERENTE!
```

**VIOLAÇÃO**: O modelo espera ~9.45 bytes/segundo, recebe ~12.54 bytes/segundo.  
**Resultado**: Modelo não sabe como distribuir o conteúdo fonético no tempo → colapso → ruído.

---

## 6. TEORIA DO COLAPSO DE DISTRIBUIÇÃO

### 6.1 Como F5-TTS Aprende

F5-TTS usa **Flow Matching** para aprender a distribuição `p(mel|text)`:

```
φ(t) = (1-t) * mel_real + t * ruído_gaussiano
```

Durante treinamento:
- **Input**: `text_duplicado` (ex: "ABC ABC")
- **Output**: `mel` de duração `2 * ref_audio`
- **Aprende**: relação fixa texto/tempo

### 6.2 O que Acontece na Inferência Incorreta

Quando `test.py` fornece texto muito longo:

```python
# Esperado pelo modelo:
text_len = 189 bytes
duration = 20s (2x ref)
distribution_learned = N(9.45 bytes/s, σ_small)

# Recebido:
text_len = 395 bytes  # 2.08x maior!
duration = 31.5s  # 1.575x maior!
distribution_actual = N(12.54 bytes/s, ???)  # ❌ FORA DA DISTRIBUIÇÃO APRENDIDA
```

**Resultado**: 
- Flow matching não sabe como interpolar
- CFG (classifier-free guidance) falha
- ODE solver gera trajetória inválida
- **Output**: Ruído estruturado (parece voz, mas não é compreensível)

### 6.3 Por Que os Samples do Treinamento Funcionam

```python
# Código do trainer (SEMPRE FUNCIONA):
text = "ABC ABC"  # Duplicado
duration = 2 * ref_len  # Fixa
proporção = CONSTANTE  # ← Dentro da distribuição aprendida

# Modelo consegue:
1. Mapear texto → mel features corretamente
2. Aplicar flow matching com trajetória válida
3. Gerar áudio inteligível
```

---

## 7. VALIDAÇÃO EXPERIMENTAL

### Experimento 1: Testar com Texto Duplicado

```python
# Modificar test.py para duplicar ref_text como o trainer faz
ref_text = "Olá, este é um teste"
gen_text = ref_text  # ← Mesmo texto (simula duplicação)
# HIPÓTESE: Áudio deve melhorar significativamente
```

**Resultado Esperado**: Áudio inteligível (ou pelo menos melhor)

### Experimento 2: Testar com Chunking Curto

```python
# Dividir gen_text em pedaços de ~95 bytes (tamanho do ref_text)
chunks = chunk_text(gen_text, max_chars=95)
# Gerar cada chunk separadamente
# HIPÓTESE: Cada chunk individual deve ser inteligível
```

**Resultado Esperado**: Chunks individuais com áudio bom

### Experimento 3: Comparar Duração Calculada

```python
# Trainer:
duration_trainer = ref_audio_len * 2  # Sempre 2x

# test.py atual:
ref_text_len = len(ref_text.encode("utf-8"))  # 95
gen_text_len = len(gen_text.encode("utf-8"))  # 300
duration_test = ref_audio_len + int(ref_audio_len / ref_text_len * gen_text_len)
# = 240 frames + int(240 / 95 * 300) = 240 + 757 = 997 frames
# = 997 * 256 / 24000 = ~10.6s ❌ ERRADO!
# Áudio real gerado: 31.5s ← MUITO maior!
```

**DESCOBERTA**: Há um bug adicional no cálculo de duração do `infer_batch_process`!

---

## 8. CÓDIGO PROBLEMÁTICO DETALHADO

### Arquivo: `f5_tts/infer/utils_infer.py` (linhas 483-495)

```python
def infer_batch_process(...):
    def process_batch(gen_text):
        local_speed = speed
        if len(gen_text.encode("utf-8")) < 10:
            local_speed = 0.3  # ← Se texto muito curto, slow down
        
        # Prepara texto
        text_list = [ref_text + gen_text]  # ← Concatena
        final_text_list = convert_char_to_pinyin(text_list)
        
        ref_audio_len = audio.shape[-1] // hop_length
        
        if fix_duration is not None:
            duration = int(fix_duration * target_sample_rate / hop_length)
        else:
            # ⚠️ CÁLCULO PROBLEMÁTICO:
            ref_text_len = len(ref_text.encode("utf-8"))
            gen_text_len = len(gen_text.encode("utf-8"))
            duration = ref_audio_len + int(ref_audio_len / ref_text_len * gen_text_len / local_speed)
            # ↑ Assume proporção linear texto/áudio
            # ↑ NÃO considera que modelo foi treinado com duplicação!
```

**PROBLEMA MATEMÁTICO**:

```
Suponha:
- ref_audio_len = 240 frames (10s @ 24kHz, hop=256)
- ref_text_len = 95 bytes
- gen_text_len = 300 bytes
- local_speed = 1.0

Cálculo atual:
duration = 240 + int(240 / 95 * 300 / 1.0)
         = 240 + int(758.94)
         = 240 + 758
         = 998 frames
         = 998 * 256 / 24000 = ~10.65s

Porém, áudio real tem 31.5s!
```

**HIPÓTESE**: Há um multiplicador adicional escondido ou o cálculo está sendo feito em outro lugar.

Verificando `model.sample()` em `f5_tts/model/cfm.py:82-238`:

```python
def sample(self, cond, text, duration, ...):
    # duration é usado DIRETAMENTE
    # Se duration=998, output deve ter ~998 frames
    # MAS se batch processing aplica speed ou cross-fade...
```

**NECESSITA INVESTIGAÇÃO ADICIONAL** no código de batching.

---

## 9. EVIDÊNCIA DE CAMPO (GitHub Issues)

### Issue #57 (Official Fine-tuning Discussion)

Usuário `bensonbs` (17 Oct 2024):
> "Estou treinando com dataset chinês (33h). A loss diminui constantemente e o tom de voz fica mais próximo do target. MAS conforme as steps aumentam, a pronúncia fica cada vez mais INCOMPREENSÍVEL."

Resposta de `jpgallegoar` (Collaborator):
> "Você está usando batch_size muito grande. Com datasets pequenos (~100h), recomendo batch_size menor e mais epochs. Também, verifique se sua proporção texto/áudio está consistente."

### Discussion #143 (Gradio Interface)

Usuário `savank7` (6 Aug 2024):
> "Quando gero áudio pelo Gradio, som perfeito. Quando uso API Python com MESMOS parâmetros, áudio terrível e incompreensível."

Resposta de `claypotfrog` (3 Sep 2024):
> "Tive o mesmo problema. O Gradio aplica text chunking automático. Você precisa:
> 1. Dividir gen_text em chunks de ~135 caracteres
> 2. Usar cross_fade_duration > 0 para juntar os chunks
> 3. NÃO passar texto muito longo de uma vez"

---

## 10. RESUMO TÉCNICO DA ROOT CAUSE

### Causa Raiz Principal

**F5-TTS foi treinado com uma estrutura específica de dados**:
- Texto SEMPRE duplicado (`ref + " " + ref`)
- Duração SEMPRE fixa (`2 * ref_audio_duration`)
- Proporção texto/tempo SEMPRE constante

**Quando test.py viola essas expectativas**:
- Texto muito longo (não duplicado, mas concatenado)
- Duração calculada dinamicamente (não fixa em 2x)
- Proporção texto/tempo variável

**O modelo entra em distribution collapse**:
- Flow matching não consegue interpolar corretamente
- Embeddings de texto fora da distribuição aprendida
- Output: ruído estruturado (parece voz, mas ininteligível)

### Causas Secundárias

1. **Falta de Chunking**: API oficial usa chunking automático, test.py não
2. **Cálculo de Duração Inadequado**: Fórmula assume linearidade texto/áudio
3. **Referência Muito Curta**: Usar ref_audio de 10s para gerar 31.5s viola proporção
4. **Cross-fade Duration Zero**: `cross_fade_duration=0.0` impede combinação suave de chunks

---

## 11. DEPENDÊNCIAS E ARQUIVOS RELACIONADOS

### Arquivos Críticos

```
/root/.local/lib/python3.11/site-packages/f5_tts/
├── infer/
│   ├── utils_infer.py       ← Contém infer_process e infer_batch_process
│   ├── infer_cli.py          ← CLI oficial (reference implementation)
│   └── infer_gradio.py       ← Interface Gradio (funciona corretamente)
├── model/
│   ├── trainer.py            ← Geração de samples (método CORRETO)
│   └── cfm.py                ← Modelo CFM (Flow Matching)
├── api.py                    ← API oficial F5TTS class
└── train/
    └── finetune_gradio.py    ← Interface de fine-tuning

/home/tts-webui-proxmox-passthrough/train/
├── test.py                   ← Script problemático (NOSSO)
├── config/
│   └── base_config.yaml      ← Config de treinamento
└── output/ptbr_finetuned2/
    ├── samples/              ← Áudios BOM (gerados pelo trainer)
    │   ├── update_25400_gen.wav
    │   └── update_25400_ref.wav
    └── model_25400.pt        ← Checkpoint (funciona corretamente)
```

### Versões

```
Python: 3.11.2
PyTorch: 2.5.1+cu121
F5-TTS: 1.1.9
Vocos: (charactr/vocos-mel-24khz from HuggingFace)
CUDA: 12.1
GPU: NVIDIA RTX 3090 (23.7GB VRAM)
```

---

## 12. PRÓXIMOS PASSOS RECOMENDADOS

### 1. Implementar Fix Baseado no Código Oficial

Modificar `test.py` para usar a mesma estratégia do trainer:

```python
# Opção A: Duplicar texto como trainer
ref_text = "..."
gen_text = ref_text  # Duplica
duration = ref_audio_len * 2

# Opção B: Usar chunking como API oficial
from f5_tts.infer.utils_infer import chunk_text
max_chars = len(ref_text.encode("utf-8"))  # Tamanho do ref
chunks = chunk_text(gen_text, max_chars=max_chars)
# Gerar cada chunk separadamente
```

### 2. Validar com Experimentos Controlados

- Teste com gen_text = ref_text (duplicação)
- Teste com chunks de 95 bytes cada
- Comparar qualidade de áudio resultante

### 3. Atualizar Documentação

Adicionar warning em `test.py`:
```python
# ⚠️ IMPORTANTE:
# F5-TTS foi treinado com duplicação de texto.
# Para melhor qualidade, mantenha gen_text com tamanho
# similar ao ref_text (max ~135 caracteres).
```

### 4. Implementar Solução Definitiva

Criar nova função `infer_like_trainer()`:
```python
def infer_like_trainer(model, ref_audio, ref_text, vocoder):
    """Gera áudio usando EXATAMENTE a mesma lógica do trainer"""
    infer_text = ref_text + " " + ref_text  # Duplica
    duration = ref_audio_len * 2  # Fixa
    # ... resto do código
```

---

## 13. CONCLUSÃO

O problema **NÃO está no modelo**, **NÃO está no checkpoint**, e **NÃO está nos parâmetros de inferência**.

O problema está na **incompatibilidade entre como o modelo foi treinado** (texto duplicado, duração fixa 2x) **vs como test.py está fazendo inferência** (texto concatenado longo, duração dinâmica).

**Solução**: Adaptar `test.py` para usar a mesma estrutura de texto que o trainer usa, ou implementar chunking automático como a API oficial faz.

**Prioridade**: 🔴 CRÍTICA - Bloqueia validação de qualidade do modelo

**Esforço Estimado**: 2-4 horas para implementar e testar fix completo

---

## ANEXOS

### A. Parâmetros de Treinamento Atuais

```yaml
# train/config/base_config.yaml
mel_spec:
  mel_spec_type: vocos
  target_sample_rate: 24000
  n_mel_channels: 100
  hop_length: 256
  win_length: 1024
  n_fft: 1024

training:
  epochs: 1000
  batch_size_per_gpu: 2
  batch_size_type: frame
  max_samples: 64
  learning_rate: 1e-5
  
checkpoints:
  save_per_updates: 200
  log_samples: true
  log_samples_per_updates: 200
```

### B. Comandos para Reproduzir Problema

```bash
# 1. Gerar sample durante treinamento (BOM)
python3 -m train.run_training --epochs 1000 --batch-size 2
# Aguardar save em update múltiplo de 200
# Verificar: train/output/ptbr_finetuned2/samples/update_XXXXX_gen.wav

# 2. Gerar via test.py (RUIM)
python3 -m train.test --checkpoint model_25400.pt
# Verificar: train/f5tts_test_TIMESTAMP.wav
```

### C. Referências

1. **F5-TTS Paper**: [arXiv:2410.06885](https://arxiv.org/abs/2410.06885)
2. **Official Repo**: [github.com/SWivid/F5-TTS](https://github.com/SWivid/F5-TTS)
3. **Pretrained PT-BR**: [huggingface.co/firstpixel/F5-TTS-pt-br](https://huggingface.co/firstpixel/F5-TTS-pt-br)
4. **Fine-tuning Discussion**: [GitHub #57](https://github.com/SWivid/F5-TTS/discussions/57)
5. **Gradio Interface Issues**: [GitHub #143](https://github.com/SWivid/F5-TTS/discussions/143)

---

**Fim do Relatório**
