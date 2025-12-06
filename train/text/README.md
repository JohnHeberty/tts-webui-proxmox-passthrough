# F5-TTS Text Processing Modules

Módulos de processamento de texto para o pipeline de treinamento F5-TTS.

## Módulos Disponíveis

### 📝 `normalizer.py` - Text Normalization
Normalização de texto para síntese de voz.

**Principais funções:**
- `TextNormalizer(config)` - Classe principal de normalização
- `normalize(text)` - Normaliza texto completo
- `convert_numbers_to_words(text)` - Converte números para extenso
- `clean_text(text)` - Remove caracteres especiais

**Características:**
- ✅ Converte números para extenso (PT-BR)
- ✅ Normaliza pontuação
- ✅ Remove caracteres especiais
- ✅ Lowercase opcional
- ✅ Replacements customizáveis

**Exemplo:**
```python
from train.text import TextNormalizer

normalizer = TextNormalizer(config={
    "lowercase": True,
    "convert_numbers_to_words": True,
    "numbers_lang": "pt_BR",
    "remove_special_chars": True,
})

text = "Olá! Tenho 25 anos e 100 reais."
normalized = normalizer.normalize(text)
# Output: "olá tenho vinte e cinco anos e cem reais"
```

---

### 🔤 `vocab.py` - Vocabulary Management
Gerenciamento de vocabulário e caracteres permitidos.

**Principais funções:**
- `load_vocab(path)` - Carrega vocabulário de arquivo
- `build_vocab(texts)` - Constrói vocabulário de textos
- `validate_vocab(vocab)` - Valida vocabulário
- `compute_vocab_hash(vocab)` - Hash para verificar mudanças

**Exemplo:**
```python
from train.utils.vocab import load_vocab, validate_vocab

# Carregar vocabulário
vocab = load_vocab("train/config/vocab.txt")

# Validar
info = validate_vocab(vocab, verbose=True)
print(f"Vocab size: {info.size}, unique chars: {info.unique_chars}")
```

---

### 🔍 `qa.py` - Text Quality Assurance
Quality checks para textos do dataset.

**Principais funções:**
- `check_text_quality(text, config)` - Verifica qualidade do texto
- `detect_oov_ratio(text, vocab)` - Detecta caracteres fora do vocab
- `check_speech_rate(text, duration)` - Valida taxa de fala
- `filter_poor_quality(texts)` - Filtra textos de baixa qualidade

**Checks realizados:**
- ✅ Comprimento mínimo/máximo
- ✅ Caracteres out-of-vocabulary (OOV)
- ✅ Taxa de fala (chars/segundo)
- ✅ Presença de música/ruído markers
- ✅ Proporção de palavras válidas

**Exemplo:**
```python
from train.text.qa import check_text_quality

result = check_text_quality(
    text="Este é um texto de exemplo.",
    duration=2.5,
    vocab=vocab,
    config={
        "min_text_length": 10,
        "max_text_length": 500,
        "min_speech_rate": 5.0,
        "max_speech_rate": 25.0,
    }
)

if result.is_valid:
    print("✅ Texto válido")
else:
    print(f"❌ Problemas: {result.issues}")
```

---

## Pipeline Completo

Exemplo de pipeline de processamento de texto:

```python
from train.text import TextNormalizer
from train.text.qa import check_text_quality
from train.utils.vocab import load_vocab

# 1. Carregar vocab
vocab = load_vocab("train/config/vocab.txt")

# 2. Criar normalizer
normalizer = TextNormalizer(config={
    "lowercase": True,
    "convert_numbers_to_words": True,
    "numbers_lang": "pt_BR",
    "remove_special_chars": True,
    "allowed_chars": vocab,
})

# 3. Normalizar texto
raw_text = "Olá! Tenho 25 anos."
text = normalizer.normalize(raw_text)

# 4. Validar qualidade
qa_result = check_text_quality(
    text=text,
    duration=2.0,
    vocab=vocab,
    config={
        "min_text_length": 10,
        "max_text_length": 500,
        "oov_ratio_threshold": 0.1,
    }
)

if qa_result.is_valid:
    print(f"✅ Texto processado: {text}")
else:
    print(f"❌ Texto rejeitado: {qa_result.issues}")
```

---

## Configuração Recomendada

### Para Português Brasileiro

```python
text_config = {
    # Normalização
    "lowercase": True,
    "convert_numbers_to_words": True,
    "numbers_lang": "pt_BR",
    "normalize_punctuation": True,
    "remove_special_chars": True,
    
    # Caracteres permitidos (PT-BR)
    "allowed_chars": (
        "abcdefghijklmnopqrstuvwxyz"
        "áàâãéêíóôõúç"
        "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
        "ÁÀÂÃÉÊÍÓÔÕÚÇ"
        "0123456789 .,!?;:-'\"()"
    ),
    
    # Replacements
    "replacements": {
        "...": ".",
        "!!": "!",
        "??": "?",
        "  ": " ",
    },
    
    # Quality filters
    "min_text_length": 10,
    "max_text_length": 500,
    "min_word_count": 2,
    "oov_ratio_threshold": 0.1,
    "min_speech_rate": 5.0,
    "max_speech_rate": 25.0,
    
    # Cleanup
    "remove_lines_with": [
        "[música]",
        "[aplausos]",
        "[risos]",
        "♪",
    ],
}
```

---

## Conversão de Números

O módulo converte números para extenso em português:

```python
from train.text import TextNormalizer

normalizer = TextNormalizer({"convert_numbers_to_words": True})

examples = [
    "25" → "vinte e cinco",
    "100" → "cem",
    "1000" → "mil",
    "2023" → "dois mil e vinte e três",
    "3.14" → "três ponto quatorze",
    "50%" → "cinquenta por cento",
]
```

---

## Quality Checks

### Detecção de OOV (Out-of-Vocabulary)

```python
from train.text.qa import detect_oov_ratio

text = "Café com açúcar @ 10h!"
oov_ratio, oov_chars = detect_oov_ratio(text, vocab)

if oov_ratio > 0.1:  # > 10% OOV
    print(f"⚠️ High OOV ratio: {oov_ratio:.1%}")
    print(f"   Unknown chars: {oov_chars}")
```

### Taxa de Fala

```python
from train.text.qa import check_speech_rate

text = "Este é um texto de exemplo com várias palavras."
duration = 2.5  # segundos
chars_per_sec = len(text) / duration

if 5.0 <= chars_per_sec <= 25.0:
    print("✅ Speech rate OK")
else:
    print(f"❌ Abnormal speech rate: {chars_per_sec:.1f} chars/s")
```

---

## Testes

Para testar os módulos de texto:

```bash
pytest tests/train/text/ -v
```

---

## Dependências

```bash
pip install num2words unidecode
```

---

## Referências

- **num2words**: Conversão de números para extenso
- **Text Normalization**: [Speech Synthesis Best Practices](https://arxiv.org/abs/1711.00350)

---

**Autor:** F5-TTS Training Pipeline  
**Versão:** 1.0  
**Data:** 2025-12-06
