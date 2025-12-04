# Endpoint Audit - Form() Parameters

**Data:** 2024-12-04  
**Sprint:** SPRINT-06  
**Objetivo:** Identificar e corrigir bugs similares ao Engine Selection Bug

---

## 📊 Sumário Executivo

**Endpoints Auditados:** 2  
**Bugs Encontrados:** 3  
**Severidade:** 🔴 P1 - ALTA (bugs idênticos ao P0 corrigido)

---

## 🔍 Endpoints com Enum em Form()

### ✅ POST /voices/clone

**Status:** ✅ **CORRIGIDO** (SPRINT-01 + SPRINT-04)

**Código Atual:**
```python
tts_engine_str: str = Form('xtts')
# + validate_enum_string(tts_engine_str, TTSEngine, "tts_engine")
```

**Histórico:**
- **Antes:** `tts_engine: TTSEngine = Form(TTSEngine.XTTS)` ❌
- **SPRINT-01:** Mudado para `str` + validação manual ✅
- **SPRINT-04:** Refatorado para usar `validate_enum_string()` ✅

---

### ❌ POST /jobs

**Status:** 🔴 **BUG ENCONTRADO** (3 enums afetados)

**Localização:** `app/main.py` linha 228-248

**Bugs Identificados:**

#### Bug 1: `tts_engine`
```python
# Linha 238 - ❌ BUG IDÊNTICO AO CORRIGIDO
tts_engine: TTSEngine = Form(TTSEngine.XTTS, description="...")
```

**Impacto:**
- Seleção de engine ignorada em jobs de dublagem
- Sempre usa XTTS mesmo se usuário selecionar F5-TTS
- Idêntico ao bug corrigido em `/voices/clone`

**Fix Necessário:**
```python
tts_engine_str: str = Form('xtts', description="...")
# + validação com validate_enum_string()
```

#### Bug 2: `mode`
```python
# Linha 232 - ❌ POSSÍVEL BUG
mode: TTSJobMode = Form(..., description="Modo: dubbing ou dubbing_with_clone")
```

**Impacto:**
- Campo obrigatório (sem default)
- Se FastAPI não converter, vai falhar com erro genérico
- Potencialmente confuso para usuários

**Fix Necessário:**
```python
mode_str: str = Form(..., description="...")
mode = validate_enum_string(mode_str, TTSJobMode, "mode")
```

#### Bug 3: `voice_preset`
```python
# Linha 233 - ❌ POSSÍVEL BUG
voice_preset: Optional[VoicePreset] = Form(VoicePreset.female_generic, description="...")
```

**Impacto:**
- Default pode não funcionar se FastAPI não converter
- Usuário seleciona preset mas sistema pode ignorar
- Similar ao bug de engine selection

**Fix Necessário:**
```python
voice_preset_str: Optional[str] = Form('female_generic', description="...")
if voice_preset_str:
    voice_preset = validate_enum_string(voice_preset_str, VoicePreset, "voice_preset")
```

#### Bug 4: `rvc_f0_method`
```python
# Linha 248 - ❌ POSSÍVEL BUG
rvc_f0_method: RvcF0Method = Form(RvcF0Method.RMVPE, description="...")
```

**Impacto:**
- Método de extração de pitch pode ser ignorado
- RVC pode usar método errado
- Afeta qualidade do voice conversion

**Fix Necessário:**
```python
rvc_f0_method_str: str = Form('rmvpe', description="...")
rvc_f0_method = validate_enum_string(rvc_f0_method_str, RvcF0Method, "rvc_f0_method")
```

---

## 📋 Action Plan

### 🔴 Prioridade 1: Corrigir POST /jobs

**Tarefas:**

1. **Refatorar `tts_engine` parameter**
   - Mudar para `str = Form('xtts')`
   - Adicionar `validate_enum_string()`
   - Adicionar logging
   - Tempo estimado: 10 minutos

2. **Refatorar `mode` parameter**
   - Mudar para `str = Form(...)`
   - Adicionar `validate_enum_string()`
   - Tempo estimado: 10 minutos

3. **Refatorar `voice_preset` parameter**
   - Mudar para `Optional[str] = Form('female_generic')`
   - Adicionar validação condicional
   - Tempo estimado: 10 minutos

4. **Refatorar `rvc_f0_method` parameter**
   - Mudar para `str = Form('rmvpe')`
   - Adicionar `validate_enum_string()`
   - Tempo estimado: 10 minutos

**Tempo Total Estimado:** 40 minutos

---

### 🟡 Prioridade 2: Criar Testes

**Tarefas:**

1. **Criar `tests/test_jobs_endpoint.py`**
   - Testar todos os modos (dubbing, dubbing_with_clone)
   - Testar todos os engines (xtts, f5tts)
   - Testar todos os presets
   - Testar RVC parameters
   - Tempo estimado: 1 hora

---

### 🟢 Prioridade 3: Auditoria Completa

**Tarefas:**

1. **Buscar outros Form() + Enum**
   ```bash
   grep -r "Form(.*Enum" app/
   ```

2. **Revisar cada endpoint encontrado**
   - Verificar se usa pattern correto
   - Adicionar testes se necessário

---

## 🧪 Testing Strategy

### Testes Necessários para POST /jobs

```python
# tests/test_jobs_endpoint.py

def test_create_job_with_xtts():
    """Teste: Job com XTTS deve usar XTTS"""
    response = client.post("/jobs", data={
        "text": "Test",
        "source_language": "pt",
        "mode": "dubbing",
        "voice_preset": "female_generic",
        "tts_engine": "xtts"  # ✅ Deve respeitar
    })
    assert response.status_code == 200
    job = response.json()
    assert job["tts_engine"] == "xtts"

def test_create_job_with_f5tts():
    """🔴 CRÍTICO: Job com F5-TTS deve usar F5-TTS"""
    response = client.post("/jobs", data={
        "text": "Test",
        "source_language": "pt",
        "mode": "dubbing",
        "voice_preset": "female_generic",
        "tts_engine": "f5tts"  # ✅ Deve respeitar
    })
    assert response.status_code == 200
    job = response.json()
    assert job["tts_engine"] == "f5tts", "❌ BUG: F5-TTS ignored!"

def test_create_job_invalid_mode():
    """Teste: Modo inválido deve retornar 400"""
    response = client.post("/jobs", data={
        "text": "Test",
        "source_language": "pt",
        "mode": "invalid_mode",  # ❌ Inválido
        "voice_preset": "female_generic"
    })
    assert response.status_code == 400
    assert "mode" in response.json()["detail"].lower()
```

---

## 📊 Resumo

| Endpoint | Parameter | Status | Severidade | ETA Fix |
|----------|-----------|--------|-----------|---------|
| POST /voices/clone | tts_engine | ✅ FIXED | - | - |
| POST /jobs | tts_engine | ❌ BUG | P1 | 10min |
| POST /jobs | mode | ❌ BUG | P1 | 10min |
| POST /jobs | voice_preset | ❌ BUG | P1 | 10min |
| POST /jobs | rvc_f0_method | ❌ BUG | P2 | 10min |

**Total Bugs:** 4  
**Total Fix Time:** ~40 minutos  
**Priority:** P1 (mesmo bug que P0 corrigido)

---

## 🎯 Recomendações

1. **Corrigir POST /jobs imediatamente**
   - Mesma severidade que bug corrigido
   - Afeta funcionalidade principal (dublagem)
   - Fix é simples (mesmo pattern)

2. **Adicionar testes abrangentes**
   - Evitar regressões
   - Garantir cobertura 100%

3. **Considerar linter/static analysis**
   - Detectar `Form(Enum.VALUE)` automaticamente
   - Prevenir bugs futuros

4. **Atualizar code review checklist**
   - Verificar uso de Enums em Form()
   - Exigir validação explícita

---

**📝 Auditoria realizada por:** Senior Dev Team  
**📅 Data:** 2024-12-04  
**Sprint:** SPRINT-06  
**Status:** ⏳ Fixes pendentes
