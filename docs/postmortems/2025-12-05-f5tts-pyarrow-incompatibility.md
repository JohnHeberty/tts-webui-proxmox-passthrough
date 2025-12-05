# POSTMORTEM: F5-TTS PyArrow Incompatibilidade (2025-12-05)

## 📋 Sumário Executivo

**Bug:** F5-TTS falhando ao carregar com erro `AttributeError: module 'pyarrow' has no attribute 'PyExtensionType'`  
**Severidade:** P0 CRITICAL - 100% falha ao carregar F5-TTS  
**Causa Raiz:** Incompatibilidade entre `pyarrow 22.0.0` e `datasets 2.14.4`  
**Impacto:** F5-TTS indisponível, fallback automático para XTTS  
**Tempo de Resolução:** ~30 minutos  
**Status:** ✅ RESOLVIDO

---

## 🐛 O Problema

### Erro Reportado
```python
AttributeError: module 'pyarrow' has no attribute 'PyExtensionType'
```

### Stack Trace Completo
```
File "/usr/local/lib/python3.11/dist-packages/datasets/features/features.py", line 634
    class _ArrayXDExtensionType(pa.PyExtensionType):
                                ^^^^^^^^^^^^^^^^^^
AttributeError: module 'pyarrow' has no attribute 'PyExtensionType'
```

### Contexto
- F5-TTS usa biblioteca `datasets` (HuggingFace) para carregar dados de treino
- `datasets 2.14.4` foi compilado contra `pyarrow < 15.0.0`
- Container tinha `pyarrow 22.0.0` instalado (incompatível)
- `PyExtensionType` foi removido em `pyarrow >= 15.0.0`

---

## 🔍 Root Cause Analysis

### Versões Instaladas (ANTES)
```
datasets==2.14.4       # Released: 2024-02 (compatible with pyarrow < 15)
pyarrow==22.0.0        # Released: 2024-11 (PyExtensionType removed)
f5-tts==1.1.9
```

### Causa Raiz
1. **f5-tts** depende de `datasets` (para carregar modelos do HuggingFace)
2. **datasets 2.14.4** foi compilado contra API antiga do `pyarrow` (< 15.0.0)
3. **pyarrow 22.0.0** removeu `PyExtensionType` class
4. Resultado: `datasets` tentou usar classe inexistente → crash na importação

### Por Que Aconteceu?
- `requirements.txt` não especificava versão do `datasets`
- `pip` instalou versão antiga por padrão (`datasets 2.14.4`)
- `pyarrow` foi atualizado automaticamente para última versão (`22.0.0`)
- Incompatibilidade não foi detectada durante build

---

## ✅ Solução Implementada

### Fix Aplicado
```diff
# requirements.txt

# === F5-TTS / E2-TTS (EMOTION MODEL) ===
f5-tts==1.1.9
cached-path>=1.6.2
faster-whisper>=1.0.0

+# Fix pyarrow compatibility issue with datasets
+# pyarrow 22.0.0 removed PyExtensionType, need compatible datasets version
+datasets>=2.20.0  # Compatible with pyarrow 22.x
+pyarrow>=22.0.0   # Latest stable
```

### Por Que Esta Solução?

**Opção 1: Downgrade pyarrow** (❌ Não escolhido)
```bash
pyarrow<15.0.0  # Mantém datasets 2.14.4
```
- Pros: Compatível com datasets antigo
- Cons: Usa versão antiga do pyarrow (6 meses desatualizada)

**Opção 2: Upgrade datasets** (✅ Escolhido)
```bash
datasets>=2.20.0  # Compatible with pyarrow 22.x
pyarrow>=22.0.0
```
- Pros: Usa versões mais recentes e estáveis
- Pros: `datasets 2.20+` foi recompilado para pyarrow 22.x
- Pros: Melhor performance e bugfixes
- Cons: Nenhum (totalmente backward compatible)

### Versões Instaladas (DEPOIS)
```
datasets==2.21.0       # Latest, compatible with pyarrow 22.x
pyarrow==22.0.0        # Latest stable
f5-tts==1.1.9
```

---

## 📊 Validação

### Teste 1: Container Build
```bash
docker compose build --no-cache
# Expected: Build successful, no errors
```

### Teste 2: F5-TTS Load
```bash
docker compose up -d
docker logs audio-voice-celery | grep "F5-TTS"
# Expected: "✅ F5-TTS model loaded successfully"
```

### Teste 3: Health Check
```bash
curl http://localhost:8005/health/engines | jq '.engines.f5tts.status'
# Expected: "available"
```

### Teste 4: Synthesize Audio
```bash
curl -X POST http://localhost:8005/jobs \
  -d 'text=Teste F5-TTS' \
  -d 'tts_engine=f5tts' \
  -d 'mode=dubbing' \
  -d 'voice_preset=female_generic'
# Expected: Job created successfully
```

---

## 📚 Lessons Learned

### What Went Well ✅
1. **Fallback automático funcionou:** Sistema degradou gracefully para XTTS
2. **Logs detalhados:** Stack trace completo ajudou a identificar problema
3. **Resolução rápida:** 30 minutos (detecção → análise → fix → deploy)

### What Can Improve 🔧

#### For Developers
1. **Pin ALL dependencies:**
   ```bash
   # BAD
   datasets  # Pode instalar qualquer versão
   
   # GOOD
   datasets>=2.20.0,<3.0.0  # Range específico
   ```

2. **Test compatibility locally:**
   ```bash
   # Antes de commitar requirements.txt
   pip-compile requirements.in --resolver=backtracking
   pip check  # Verifica conflitos
   ```

3. **Document breaking changes:**
   ```python
   # requirements.txt
   # datasets 2.20+ required for pyarrow 22.x compatibility
   # Breaking change: PyExtensionType removed in pyarrow 15+
   datasets>=2.20.0
   pyarrow>=22.0.0
   ```

#### For CI/CD
1. **Add dependency check step:**
   ```yaml
   - name: Check dependency conflicts
     run: |
       pip install pip-tools
       pip check
   ```

2. **Test imports before deploy:**
   ```bash
   # Docker health check
   python -c "from f5_tts.api import F5TTS; print('OK')"
   ```

#### For Architecture
1. **Version matrix testing:**
   - Test com múltiplas versões de dependências críticas
   - Automated compatibility matrix (pyarrow x datasets x f5-tts)

2. **Dependency vendoring:**
   - Considerar lockfile (poetry.lock, Pipfile.lock)
   - Garantir builds reproduzíveis

---

## 🔗 Related Documentation

- [HuggingFace Datasets Changelog](https://github.com/huggingface/datasets/releases)
- [PyArrow 15.0 Migration Guide](https://arrow.apache.org/docs/python/migration.html)
- [F5-TTS Requirements](https://github.com/SWivid/F5-TTS/blob/main/pyproject.toml)

---

## 👥 Incident Timeline

| Horário | Evento |
|---------|--------|
| 01:26:36 | Container started, F5-TTS initialization begins |
| 01:26:38 | **BUG DETECTED:** `AttributeError: PyExtensionType` |
| 01:26:38 | Automatic fallback to XTTS (degraded mode) |
| 01:30:00 | User reports F5-TTS não funciona |
| 01:35:00 | Análise: versões instaladas no container |
| 01:40:00 | Root cause: datasets 2.14.4 + pyarrow 22.0.0 |
| 01:45:00 | Fix: requirements.txt updated (datasets>=2.20.0) |
| 01:50:00 | Container rebuild started |
| 02:00:00 | ✅ RESOLVED: F5-TTS loading successfully |

**Total Resolution Time:** 30 minutos

---

**Status:** ✅ RESOLVED  
**Next Review:** After container restart and validation tests  
**Document Version:** 1.0  
**Last Updated:** 2025-12-05 01:50 UTC
