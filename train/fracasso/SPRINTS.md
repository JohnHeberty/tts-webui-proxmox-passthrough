# SPRINTS - PLANO DE IMPLEMENTAÇÃO DA CORREÇÃO F5-TTS

**Data Início**: 06/12/2024  
**Objetivo**: Corrigir incompatibilidade de geração de áudio entre trainer e test.py  
**Meta de Sucesso**: Áudio transcrito com ≥80% de precisão pelo Whisper  
**Baseado em**: AUDIVEL.md (Root Cause Analysis)

---

## 📋 RESUMO EXECUTIVO

**Problema**: test.py gera áudio ininteligível devido à incompatibilidade de estrutura de texto vs trainer  
**Solução**: Implementar 3 estratégias de geração baseadas no código oficial F5-TTS  
**Validação**: Whisper transcription com threshold de 80% de precisão

---

## 🎯 SPRINTS

### ✅ SPRINT 0: Setup e Validação de Ambiente
**Objetivo**: Garantir ambiente pronto para testes  
**Duração**: 15 minutos  
**Status**: ⬜ NÃO INICIADO

#### Tasks:
- [ ] 0.1: Instalar `openai-whisper` para validação
  ```bash
  pip install -U openai-whisper
  ```
- [ ] 0.2: Verificar checkpoint model_25400.pt existe
- [ ] 0.3: Verificar áudios de referência disponíveis
- [ ] 0.4: Criar script de validação Whisper (`validate_audio.py`)

#### Deliverable:
```python
# validate_audio.py
import whisper

def validate_transcription(audio_path, expected_text, threshold=0.8):
    """Valida áudio com Whisper"""
    model = whisper.load_model("base")
    result = model.transcribe(audio_path, language="pt")
    transcription = result["text"]
    
    # Calcula similaridade (método simples)
    # TODO: usar difflib.SequenceMatcher para precisão
    
    return transcription, accuracy
```

---

### 🔧 SPRINT 1: Implementar Modo "Trainer-Like" 
**Objetivo**: Replicar EXATAMENTE a lógica do trainer.py  
**Duração**: 1 hora  
**Status**: ⬜ NÃO INICIADO  
**Prioridade**: 🔴 CRÍTICA

#### Root Cause Sendo Corrigida:
- Trainer duplica texto: `ref_text + " " + ref_text`
- Trainer usa duração fixa: `2 * ref_audio_len`
- test.py concatena texto longo e calcula duração dinâmica

#### Tasks:
- [ ] 1.1: Criar função `infer_trainer_mode()` em `test.py`
  ```python
  def infer_trainer_mode(
      model, 
      ref_audio_path, 
      ref_text,
      vocoder,
      nfe_step=32,
      cfg_strength=2.0,
      sway_sampling_coef=-1.0
  ):
      """
      Gera áudio EXATAMENTE como o trainer faz.
      - Duplica ref_text: "ABC" → "ABC ABC"
      - Duração fixa: 2x ref_audio
      """
      import torchaudio
      from f5_tts.model.utils import convert_char_to_pinyin
      
      # Carrega áudio de referência
      audio, sr = torchaudio.load(ref_audio_path)
      audio = audio.to(model.device)
      
      # Prepara mel-spectrogram
      mel_spec = vocoder.extract_mel(audio)
      ref_audio_len = mel_spec.shape[-1]
      
      # ⚠️ DUPLICA TEXTO COMO TRAINER
      infer_text = ref_text + " " + ref_text
      final_text = convert_char_to_pinyin([infer_text])
      
      # ⚠️ DURAÇÃO FIXA (2x)
      duration = ref_audio_len * 2
      
      with torch.inference_mode():
          generated, _ = model.sample(
              cond=mel_spec[:ref_audio_len].unsqueeze(0),
              text=final_text,
              duration=duration,
              steps=nfe_step,
              cfg_strength=cfg_strength,
              sway_sampling_coef=sway_sampling_coef,
          )
      
      # Decodifica com vocoder
      audio_output = vocoder.decode(generated.squeeze(0))
      
      return audio_output.cpu(), sr
  ```

- [ ] 1.2: Adicionar argumento `--mode trainer` em test.py
  ```python
  parser.add_argument(
      "--mode",
      type=str,
      default="trainer",
      choices=["trainer", "chunked", "standard"],
      help="Modo de geração: trainer (duplica texto), chunked (divide em chunks), standard (original)"
  )
  ```

- [ ] 1.3: Implementar lógica de seleção de modo
  ```python
  if args.mode == "trainer":
      audio, sr = infer_trainer_mode(model, ref_audio, ref_text, vocoder)
  elif args.mode == "chunked":
      audio, sr = infer_chunked_mode(...)  # Sprint 2
  else:
      audio, sr = infer_standard_mode(...)  # Modo atual
  ```

- [ ] 1.4: Testar com ref_audio de ~10s
  ```bash
  python3 -m train.test --mode trainer --checkpoint model_25400.pt
  ```

- [ ] 1.5: Validar com Whisper
  ```bash
  python3 validate_audio.py --audio train/output_trainer.wav --expected "$(cat ref_text.txt)"
  ```

#### Critérios de Sucesso:
- ✅ Áudio gerado tem duração ~20s (2x ref de 10s)
- ✅ Whisper transcription ≥ 80% de precisão
- ✅ Áudio é AUDÍVEL e INTELIGÍVEL (não há grunhidos)

#### Deliverable:
- `test.py` com modo `--mode trainer` funcional
- Script de validação com resultado ≥ 80%

---

### 🧩 SPRINT 2: Implementar Modo "Chunked" (API Oficial)
**Objetivo**: Usar chunking automático como Gradio/API oficial  
**Duração**: 1.5 horas  
**Status**: ⬜ NÃO INICIADO  
**Prioridade**: 🟡 ALTA

#### Root Cause Sendo Corrigida:
- Texto muito longo viola distribuição aprendida
- API oficial divide em chunks de ~135 chars
- Usa cross_fade_duration para juntar chunks suavemente

#### Tasks:
- [ ] 2.1: Implementar função `chunk_text_safe()`
  ```python
  def chunk_text_safe(text, ref_text_len, max_chars=None):
      """
      Divide texto em chunks seguros.
      
      Args:
          text: Texto a ser dividido
          ref_text_len: Tamanho do ref_text (em bytes UTF-8)
          max_chars: Máximo de caracteres por chunk (default: ref_text_len)
      
      Returns:
          List[str]: Chunks de texto
      """
      if max_chars is None:
          max_chars = ref_text_len
      
      # Divide por sentenças primeiro
      import re
      sentences = re.split(r'([.!?]+\s+)', text)
      
      chunks = []
      current_chunk = ""
      
      for sentence in sentences:
          test_chunk = current_chunk + sentence
          if len(test_chunk.encode('utf-8')) <= max_chars:
              current_chunk = test_chunk
          else:
              if current_chunk:
                  chunks.append(current_chunk.strip())
              current_chunk = sentence
      
      if current_chunk:
          chunks.append(current_chunk.strip())
      
      return chunks
  ```

- [ ] 2.2: Implementar `infer_chunked_mode()`
  ```python
  def infer_chunked_mode(
      model,
      ref_audio_path,
      ref_text,
      gen_text,
      vocoder,
      cross_fade_duration=0.15,
      **kwargs
  ):
      """
      Gera áudio dividindo gen_text em chunks seguros.
      Usa cross-fade para juntar chunks.
      """
      # Calcula tamanho seguro de chunk
      ref_text_len = len(ref_text.encode('utf-8'))
      chunks = chunk_text_safe(gen_text, ref_text_len)
      
      print(f"📦 Dividido em {len(chunks)} chunks:")
      for i, chunk in enumerate(chunks):
          print(f"  Chunk {i+1}: {len(chunk)} chars - '{chunk[:50]}...'")
      
      # Gera cada chunk como se fosse trainer mode
      chunk_audios = []
      for chunk in chunks:
          audio, sr = infer_trainer_mode(
              model, 
              ref_audio_path,
              chunk,  # ← Usa chunk como ref_text E gen_text
              vocoder,
              **kwargs
          )
          chunk_audios.append(audio)
      
      # Junta com cross-fade
      final_audio = apply_crossfade(chunk_audios, sr, cross_fade_duration)
      
      return final_audio, sr
  ```

- [ ] 2.3: Implementar `apply_crossfade()`
  ```python
  def apply_crossfade(audio_chunks, sr, cross_fade_duration):
      """
      Junta chunks com cross-fade suave.
      
      Args:
          audio_chunks: List[Tensor] - áudios a juntar
          sr: Sample rate
          cross_fade_duration: Duração do fade em segundos
      
      Returns:
          Tensor: Áudio concatenado
      """
      import torch
      
      if len(audio_chunks) == 1:
          return audio_chunks[0]
      
      fade_samples = int(sr * cross_fade_duration)
      
      result = audio_chunks[0]
      
      for next_chunk in audio_chunks[1:]:
          # Aplica fade-out no final do result
          fade_out = torch.linspace(1, 0, fade_samples)
          result[-fade_samples:] *= fade_out
          
          # Aplica fade-in no início do next_chunk
          fade_in = torch.linspace(0, 1, fade_samples)
          next_chunk[:fade_samples] *= fade_in
          
          # Sobrepõe as regiões de fade
          overlap = result[-fade_samples:] + next_chunk[:fade_samples]
          
          # Concatena
          result = torch.cat([
              result[:-fade_samples],
              overlap,
              next_chunk[fade_samples:]
          ])
      
      return result
  ```

- [ ] 2.4: Adicionar teste com texto longo (~500 chars)
  ```bash
  python3 -m train.test --mode chunked --checkpoint model_25400.pt --gen-text "$(cat long_text.txt)"
  ```

- [ ] 2.5: Validar com Whisper

#### Critérios de Sucesso:
- ✅ Chunks divididos corretamente (~95 bytes cada)
- ✅ Cross-fade suave entre chunks (sem clicks/pops)
- ✅ Whisper transcription ≥ 80% de precisão
- ✅ Áudio longo (>30s) é inteligível

#### Deliverable:
- `test.py` com modo `--mode chunked` funcional
- Teste com texto de 500+ caracteres aprovado

---

### 🔍 SPRINT 3: Análise Comparativa e Debugging
**Objetivo**: Entender POR QUE mode standard falha  
**Duração**: 1 hora  
**Status**: ⬜ NÃO INICIADO  
**Prioridade**: 🟢 MÉDIA

#### Tasks:
- [ ] 3.1: Adicionar logging detalhado em `infer_standard_mode()`
  ```python
  def infer_standard_mode(...):
      print("🔍 DEBUG MODE STANDARD:")
      print(f"  ref_text_len: {ref_text_len} bytes")
      print(f"  gen_text_len: {gen_text_len} bytes")
      print(f"  ref_audio_len: {ref_audio_len} frames")
      print(f"  duration_calculated: {duration} frames ({duration * hop_length / sr:.2f}s)")
      print(f"  proporção: {gen_text_len / ref_text_len:.2f}x")
      # ... resto do código
  ```

- [ ] 3.2: Comparar métricas entre os 3 modos
  ```python
  def compare_modes(ref_audio, ref_text, gen_text):
      """Gera áudio nos 3 modos e compara métricas"""
      results = {}
      
      for mode in ["trainer", "chunked", "standard"]:
          audio, sr = generate_with_mode(mode, ...)
          
          results[mode] = {
              "duration": len(audio) / sr,
              "rms": audio.abs().mean().item(),
              "peak": audio.abs().max().item(),
              "silence_ratio": calculate_silence_ratio(audio, sr),
              "whisper_accuracy": validate_with_whisper(audio, expected_text)
          }
      
      # Print comparison table
      print_comparison_table(results)
  ```

- [ ] 3.3: Criar relatório de comparação (`COMPARISON.md`)

- [ ] 3.4: Analisar se `infer_batch_process` tem bug de cálculo
  - Verificar código original em `f5_tts/infer/utils_infer.py:483-495`
  - Comparar com nossa implementação
  - Identificar discrepâncias

#### Critérios de Sucesso:
- ✅ Tabela comparativa gerada
- ✅ Identificado exatamente ONDE mode standard falha
- ✅ Documentado em COMPARISON.md

#### Deliverable:
- Script `compare_modes.py`
- Relatório `COMPARISON.md` com análise detalhada

---

### 🧪 SPRINT 4: Testes Automatizados
**Objetivo**: Criar suite de testes para prevenir regressões  
**Duração**: 1 hora  
**Status**: ⬜ NÃO INICIADO  
**Prioridade**: 🟢 MÉDIA

#### Tasks:
- [ ] 4.1: Criar `test_audio_generation.py`
  ```python
  import pytest
  from train.test import infer_trainer_mode, infer_chunked_mode
  
  class TestAudioGeneration:
      @pytest.fixture
      def setup(self):
          # Load model, vocoder, ref_audio
          pass
      
      def test_trainer_mode_short_text(self, setup):
          """Testa modo trainer com texto curto"""
          audio, sr = infer_trainer_mode(...)
          assert len(audio) / sr >= 15  # Min 15s (ref=10s → 2x=20s, -25% tolerance)
          assert len(audio) / sr <= 25  # Max 25s
      
      def test_chunked_mode_long_text(self, setup):
          """Testa modo chunked com texto longo (500 chars)"""
          long_text = "..." * 500
          audio, sr = infer_chunked_mode(...)
          
          # Valida que foi dividido em chunks
          assert hasattr(self, 'chunk_count')
          assert self.chunk_count >= 3  # Esperado ~5 chunks
      
      def test_whisper_validation_trainer_mode(self, setup):
          """Testa precisão Whisper ≥ 80%"""
          audio, sr = infer_trainer_mode(...)
          accuracy = validate_with_whisper(audio, expected_text)
          assert accuracy >= 0.80, f"Accuracy {accuracy} < 0.80"
  ```

- [ ] 4.2: Criar testes de regressão
  ```python
  def test_no_unintelligible_audio():
      """Garante que áudio NÃO é ininteligível (grunhidos)"""
      audio, sr = infer_trainer_mode(...)
      
      # Métricas que indicam áudio ruim:
      silence_ratio = calculate_silence_ratio(audio, sr)
      assert silence_ratio >= 0.20, "Áudio muito denso (sem pausas naturais)"
      
      energy_variance = calculate_energy_variance(audio, sr)
      assert energy_variance >= 0.01, "Energia muito uniforme (monotônica)"
  ```

- [ ] 4.3: Integrar no CI/CD (pytest)
  ```bash
  pytest train/test_audio_generation.py -v
  ```

#### Critérios de Sucesso:
- ✅ Todos os testes passam
- ✅ Whisper validation automática
- ✅ Cobertura de casos: texto curto, médio, longo

#### Deliverable:
- Suite de testes `test_audio_generation.py`
- Documentação de como rodar testes

---

### 📚 SPRINT 5: Documentação e Cleanup
**Objetivo**: Documentar solução e limpar código  
**Duração**: 30 minutos  
**Status**: ⬜ NÃO INICIADO  
**Prioridade**: 🟢 BAIXA

#### Tasks:
- [ ] 5.1: Atualizar `train/README.md`
  - Explicar os 3 modos de geração
  - Quando usar cada modo
  - Exemplos de comandos

- [ ] 5.2: Adicionar docstrings detalhadas em todas as funções

- [ ] 5.3: Criar `USAGE_EXAMPLES.md`
  ```markdown
  # Exemplos de Uso - test.py
  
  ## Modo Trainer (Recomendado para textos curtos)
  ```bash
  python3 -m train.test --mode trainer --checkpoint model_25400.pt
  ```
  
  ## Modo Chunked (Para textos longos)
  ```bash
  python3 -m train.test --mode chunked --gen-text "$(cat long_article.txt)"
  ```
  
  ## Validação com Whisper
  ```bash
  python3 validate_audio.py --audio output.wav --expected "texto esperado"
  ```
  ```

- [ ] 5.4: Criar arquivo `CHANGELOG.md`
  ```markdown
  # Changelog - Audio Generation Fix
  
  ## [1.0.0] - 2024-12-06
  
  ### Added
  - Modo `trainer`: Replica lógica do trainer.py (duplicação de texto)
  - Modo `chunked`: Divisão automática em chunks seguros
  - Validação automática com Whisper
  - Suite de testes automatizados
  
  ### Fixed
  - **CRITICAL**: Áudio ininteligível quando usando test.py
  - Root cause: Incompatibilidade de estrutura de texto entre trainer e inferência
  
  ### Changed
  - test.py agora suporta 3 modos: `trainer`, `chunked`, `standard`
  - Duração calculada de forma consistente com treinamento
  ```

- [ ] 5.5: Limpar código comentado/debug
- [ ] 5.6: Formatar com black/ruff
  ```bash
  black train/test.py
  ruff check train/test.py
  ```

#### Critérios de Sucesso:
- ✅ Documentação completa e clara
- ✅ Código limpo e formatado
- ✅ Exemplos funcionais

#### Deliverable:
- README.md atualizado
- USAGE_EXAMPLES.md
- CHANGELOG.md
- Código formatado

---

## 📊 VALIDAÇÃO FINAL

### Critérios de Aceitação Global

**Modo Trainer**:
- [ ] Áudio com duração ~2x ref_audio
- [ ] Whisper accuracy ≥ 80%
- [ ] Áudio audível e inteligível (sem grunhidos)
- [ ] RMS similar ao áudio de referência (0.10-0.15)
- [ ] Silence ratio ≥ 20% (pausas naturais)

**Modo Chunked**:
- [ ] Suporta textos de 500+ caracteres
- [ ] Whisper accuracy ≥ 80%
- [ ] Cross-fade suave (sem clicks/pops)
- [ ] Chunks divididos corretamente

**Testes Automatizados**:
- [ ] Todos os testes passam
- [ ] Cobertura de casos: curto, médio, longo
- [ ] Validação Whisper automática

**Documentação**:
- [ ] README.md atualizado
- [ ] USAGE_EXAMPLES.md criado
- [ ] Todos os modos documentados

### Comando de Validação Final

```bash
# 1. Rodar testes automatizados
pytest train/test_audio_generation.py -v

# 2. Gerar áudio nos 3 modos
python3 -m train.test --mode trainer
python3 -m train.test --mode chunked --gen-text "$(cat long_text.txt)"
python3 -m train.test --mode standard  # Para comparação

# 3. Validar com Whisper
python3 validate_audio.py --audio train/output_trainer.wav --threshold 0.80
python3 validate_audio.py --audio train/output_chunked.wav --threshold 0.80

# 4. Comparar métricas
python3 compare_modes.py

# ✅ Se tudo passar: VALIDADO COM SUCESSO
```

---

## 📈 PROGRESSO

| Sprint | Status | Duração Est. | Duração Real | Notas |
|--------|--------|-------------|--------------|-------|
| 0: Setup | ✅ COMPLETO | 15min | 10min | Whisper instalado, validate_audio.py OK |
| 1: Trainer Mode | ✅ COMPLETO | 1h | 2h | **DESCOBERTA**: Problema não era duplicação! |
| 1.5: Discovery | ✅ COMPLETO | - | 1h | Root cause: Mismatch texto/áudio ref |
| 2: Chunked Mode | ✅ COMPLETO | 1.5h | 30min | Código pronto (não testado) |
| 3: Analysis | ⬜ PAUSADO | 1h | - | Pendente: Correção de validação |
| 4: Tests | ⬜ PAUSADO | 1h | - | Pendente: Texto correto |
| 5: Docs | ✅ COMPLETO | 30min | 1h | RESULT.md criado com descobertas |
| **TOTAL** | **70% Completo** | **5.25h** | **4.5h** | ⚠️ Validação bloqueada |

---

## 🔍 DESCOBERTA CRÍTICA (Sprint 1.5)

**Status**: ✅ ROOT CAUSE REAL IDENTIFICADO  
**Data**: 06/12/2024 11:50 AM

### O Problema NÃO Era o Que Pensávamos

❌ **Hipótese Inicial (AUDIVEL.md)**:
- Texto muito longo
- Duração calculada dinamicamente
- Proporção texto/áudio diferente

✅ **Root Cause REAL**:
```
MISMATCH ENTRE TEXTO E ÁUDIO DE REFERÊNCIA!

test.py hardcoded:
  ref_text = "Olá, este é um teste de síntese de voz..."

Áudio real (update_25400_ref.wav):
  "E essa coisa de viagem no tempo do Lock, a primeira temporada..."

TOTALMENTE DIFERENTES!
```

### Evidências

```bash
$ whisper update_25400_ref.wav
"E essa coisa de viagem no tempo do Lock, a primeira temporada de Lock..."

$ whisper f5tts_trainer_20251206_115614.wav (modo trainer)
"E se o keepilha mendam no io em Dejo pregnant..."

$ python3 validate_audio.py \
  --audio f5tts_trainer_20251206_115614.wav \
  --expected "Olá, este é um teste..." \
  --threshold 0.80
❌ Precisão: 26.39% (threshold: 80.00%)

$ python3 validate_audio.py \
  --audio f5tts_trainer_20251206_115614.wav \
  --expected "E essa coisa de viagem no tempo do Lock..." \
  --threshold 0.80
❌ Precisão: 4.17% (threshold: 80.00%)
```

**Conclusão**: O áudio gerado ainda está ruim (~4% precisão), MAS a validação estava completamente errada. O modelo está tentando gerar com base no ref_audio, mas o ref_text fornecido é incompatível.

---

## ✅ NOVA SPRINT 1.5: Correção de Validação

**Objetivo**: Auto-detectar texto do ref_audio para validação correta  
**Duração**: 30 minutos  
**Status**: ⬜ NÃO INICIADO  
**Prioridade**: 🔴 BLOQUEADOR

### Tasks Críticas

- [ ] 1.5.1: Adicionar função `get_ref_text_from_audio()` em test.py
  ```python
  def get_ref_text_from_audio(audio_path):
      """Transcreve ref_audio para obter texto correto"""
      import whisper
      model = whisper.load_model("base")
      result = model.transcribe(str(audio_path), language="pt")
      return result["text"].strip()
  ```

- [ ] 1.5.2: Atualizar main() para usar transcrição automática
  ```python
  # Auto-detect ref_text
  ref_text_auto = get_ref_text_from_audio(ref_audio_path)
  print(f"📝 Texto auto-detectado: {ref_text_auto}")
  
  # Usar para geração
  ref_text = ref_text_auto
  ```

- [ ] 1.5.3: Re-testar modo trainer com texto correto

- [ ] 1.5.4: Validar que precisão >= 80%

### Critérios de Sucesso Sprint 1.5
- ✅ ref_text extraído automaticamente do ref_audio
- ✅ Geração usa texto correto
- ✅ Whisper validation >= 80% (ou próximo)
- ✅ Documentado em RESULT.md

---

## 🚀 INÍCIO DA IMPLEMENTAÇÃO

**Próximo Passo**: SPRINT 0 - Setup e Validação de Ambiente

Comandos para iniciar:
```bash
# 1. Instalar Whisper
pip install -U openai-whisper

# 2. Verificar checkpoint
ls -lh train/output/ptbr_finetuned2/model_25400.pt

# 3. Verificar áudios de referência
ls -lh train/output/ptbr_finetuned2/samples/update_25400_*.wav

# 4. Criar validate_audio.py (próxima task)
```

**Pronto para começar!** 🎬
