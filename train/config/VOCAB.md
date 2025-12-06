# Vocabulary Management

## Overview

This directory contains the **canonical vocabulary file** (`vocab.txt`) for F5-TTS PT-BR fine-tuning.

**IMPORTANT:** `vocab.txt` is the **single source of truth** for vocabulary across the entire project.

---

## Files

### `vocab.txt`
- **Status:** ✅ Canonical (SOURCE OF TRUTH)
- **Origin:** `firstpixel/F5-TTS-pt-br`
- **SHA256:** `2a05f992e00af9b0bd3800a8d23e78d520dbd705284ed2eedb5f4bd29398fa3c`
- **Size:** 2546 tokens
- **Encoding:** UTF-8
- **Format:** One token per line

**DO NOT MODIFY THIS FILE DIRECTLY!**

If you need to update the vocabulary, follow the proper procedure documented below.

---

## Hash Verification

The vocabulary file integrity is protected by SHA256 hash verification.

### Verify Hash

```bash
# Using train/utils/vocab.py
python3 -m train.utils.vocab hash train/config/vocab.txt

# Expected output:
# SHA256: 2a05f992e00af9b0bd3800a8d23e78d520dbd705284ed2eedb5f4bd29398fa3c

# Or using system tools
sha256sum train/config/vocab.txt
```

---

## Vocabulary Consolidation

The project had **3 copies** of vocab.txt in different locations:

1. ✅ `train/config/vocab.txt` - **Canonical (SOURCE OF TRUTH)**
2. ✅ `train/data/vocab.txt` - Synced copy
3. ✅ `train/data/f5_dataset/vocab.txt` - Synced copy

All copies are now synchronized and validated.

---

## Usage

### Audit All Vocabs

Check all vocab.txt files in the project:

```bash
python3 -m train.utils.vocab audit
```

**Output:**
```
================================================================================
VOCABULARY AUDIT
================================================================================
Found 3 vocab.txt files:

✅ VALID      train/config/vocab.txt
             Hash: 2a05f992e00af9b0bd3800a8d23e78d520dbd705284ed2eedb5f4bd29398fa3c

✅ VALID      train/data/f5_dataset/vocab.txt
             Hash: 2a05f992e00af9b0bd3800a8d23e78d520dbd705284ed2eedb5f4bd29398fa3c

✅ VALID      train/data/vocab.txt
             Hash: 2a05f992e00af9b0bd3800a8d23e78d520dbd705284ed2eedb5f4bd29398fa3c

================================================================================
Summary: 3 valid, 0 invalid
================================================================================
```

### Validate Single Vocab

```bash
python3 -m train.utils.vocab validate train/data/f5_dataset/vocab.txt
```

### Compare Two Vocabs

```bash
python3 -m train.utils.vocab compare train/config/vocab.txt train/data/vocab.txt
```

### Sync Vocab to Canonical

If a vocab file becomes out of sync:

```bash
# Dry run (preview only)
python3 -m train.utils.vocab sync train/data/f5_dataset/vocab.txt --dry-run

# Actually sync
python3 -m train.utils.vocab sync train/data/f5_dataset/vocab.txt
```

### Consolidate All Vocabs

Sync all vocab files in the project to the canonical version:

```bash
# Dry run (preview)
python3 -m train.utils.vocab consolidate --dry-run

# Actually consolidate
python3 -m train.utils.vocab consolidate
```

---

## Python API

### Load Vocabulary

```python
from train.utils.vocab import load_vocab

# Load canonical vocab
vocab = load_vocab("train/config/vocab.txt")
print(f"Vocab size: {len(vocab)}")  # 2546
```

### Validate Vocab

```python
from train.utils.vocab import validate_vocab, CANONICAL_VOCAB_HASH

is_valid, hash_val, info = validate_vocab(
    "train/data/f5_dataset/vocab.txt",
    verbose=True
)

if is_valid:
    print("✅ Vocab is valid!")
else:
    print(f"❌ Hash mismatch: {hash_val} != {CANONICAL_VOCAB_HASH}")
```

### Compute Hash

```python
from train.utils.vocab import compute_vocab_hash

hash_val = compute_vocab_hash("train/config/vocab.txt")
print(f"SHA256: {hash_val}")
```

---

## Why Hash Validation?

### Problem: Vocabulary Inconsistency

The audit revealed vocabulary files with different hashes:

```
train/config/vocab.txt            → 2a05f9... (CANONICAL)
train/data/vocab.txt              → 2a05f9... (OK)
train/data/f5_dataset/vocab.txt   → 4e1739... (DIFFERENT!)
```

**Impact:**
- Model trained with one vocab but inferred with another = **errors**
- Unknown words (OOV) during inference
- Degraded audio quality
- Checkpoint incompatibility

### Solution: Hash-Based Validation

1. **Single Source of Truth:** `train/config/vocab.txt`
2. **Hash Verification:** SHA256 checksum ensures integrity
3. **Automated Sync:** `train/utils/vocab.py` keeps copies in sync
4. **CI/CD Integration:** Pre-commit hooks can validate hashes

---

## Updating Vocabulary

### When to Update

Only update vocabulary if:

1. Adding support for new language
2. Adding special tokens
3. Fixing encoding issues

**WARNING:** Updating vocabulary invalidates all existing checkpoints!

### Update Procedure

1. **Backup current vocab:**
   ```bash
   cp train/config/vocab.txt train/config/vocab.txt.backup
   ```

2. **Update canonical vocab:**
   ```bash
   # Edit train/config/vocab.txt
   vim train/config/vocab.txt
   ```

3. **Compute new hash:**
   ```bash
   python3 -m train.utils.vocab hash train/config/vocab.txt
   ```

4. **Update hash constant:**
   Edit `train/utils/vocab.py`:
   ```python
   CANONICAL_VOCAB_HASH = "new_hash_here"
   ```

5. **Sync all copies:**
   ```bash
   python3 -m train.utils.vocab consolidate
   ```

6. **Update config:**
   Edit `train/config/base_config.yaml`:
   ```yaml
   paths:
     vocab_file: "train/config/vocab.txt"
   ```

7. **Retrain model:**
   All existing checkpoints are now **incompatible**!

---

## Integration with Config System

The unified config system (Sprint 1, Task 2) references the canonical vocab:

```yaml
# train/config/base_config.yaml
paths:
  vocab_file: "train/config/vocab.txt"  # SOURCE OF TRUTH
```

**Access in code:**

```python
from train.config.loader import load_config

config = load_config()
vocab_path = config.paths.vocab_file  # "train/config/vocab.txt"
```

---

## CI/CD Integration

### Pre-Commit Hook

```bash
#!/bin/bash
# .git/hooks/pre-commit

echo "🔍 Validating vocabulary consistency..."
python3 -m train.utils.vocab audit --root train

if [ $? -ne 0 ]; then
    echo "❌ Vocab validation failed! Run: python3 -m train.utils.vocab consolidate"
    exit 1
fi

echo "✅ Vocab validation passed"
```

### GitHub Actions

```yaml
name: Vocab Validation

on: [push, pull_request]

jobs:
  validate-vocab:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Validate Vocabulary
        run: python3 -m train.utils.vocab audit --root train
```

---

## Troubleshooting

### Hash Mismatch

**Problem:**
```
❌ train/data/f5_dataset/vocab.txt
   Computed: 4e173934be56...
   Expected: 2a05f992e00a...
```

**Solution:**
```bash
python3 -m train.utils.vocab sync train/data/f5_dataset/vocab.txt
```

### Multiple Invalid Vocabs

**Problem:**
```
Summary: 1 valid, 2 invalid
```

**Solution:**
```bash
# Consolidate all at once
python3 -m train.utils.vocab consolidate
```

### Canonical Vocab Missing

**Problem:**
```
❌ Canonical vocab not found: train/config/vocab.txt
```

**Solution:**
1. Restore from backup or git
2. Download from `firstpixel/F5-TTS-pt-br`
3. Sync from another valid copy

---

## Best Practices

1. **Never edit vocab.txt directly in dataset directories**
2. **Always use canonical vocab as source**
3. **Run `audit` before training**
4. **Run `consolidate` after dataset preparation**
5. **Validate hashes in CI/CD**
6. **Document vocab changes in CHANGELOG**

---

## Sprint 1 Status

- ✅ **S1-T3:** Consolidate vocabulary with hash validation
  - Created `train/utils/vocab.py` (hash validation utilities)
  - Documented canonical vocab (`train/config/vocab.txt`)
  - Synced all vocab copies
  - Verified integrity (3/3 vocabs valid)
  - Created this documentation

---

## See Also

- `train/utils/vocab.py` - Vocabulary utilities
- `train/config/base_config.yaml` - Unified config (vocab_file path)
- `train/config/loader.py` - Config loader
- `MORE.md` - Problem P2 (Vocabulário Duplicado)
- `SPRINTS_PLAN.md` - Sprint 1, Task 3
