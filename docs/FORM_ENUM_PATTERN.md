# Pattern: FastAPI Form() com Enums

## Problema

FastAPI não converte automaticamente strings para Enums em `Form()` parameters.

### Bug Comum

```python
# ❌ ERRADO - Ignora valor enviado pelo frontend
from fastapi import Form
from enum import Enum

class TTSEngine(Enum):
    XTTS = "xtts"
    F5TTS = "f5tts"

@app.post("/endpoint")
async def endpoint(
    engine: TTSEngine = Form(TTSEngine.XTTS)  # ❌ BUG!
):
    # engine SEMPRE será TTSEngine.XTTS
    # Valor enviado pelo frontend é IGNORADO
    ...
```

**Consequência:** Sistema sempre usa default, independente do valor enviado.

---

## Solução Correta

### Opção 1: Validação Manual (Simples e Recomendada)

```python
from fastapi import Form, HTTPException
from app.utils.form_parsers import validate_enum_string

@app.post("/endpoint")
async def endpoint(
    engine_str: str = Form('xtts')
):
    # Validar e converter
    engine = validate_enum_string(engine_str, TTSEngine, "tts_engine")
    
    # Use engine.value para obter string
    print(f"Engine selecionado: {engine.value}")
    
    # Ou use diretamente o enum
    if engine == TTSEngine.F5TTS:
        ...
```

**Vantagens:**
- ✅ Simples e direto
- ✅ Fácil de entender
- ✅ Validação explícita
- ✅ Case-insensitive por padrão

### Opção 2: Depends() com Parser (Mais Robusto)

```python
from fastapi import Depends
from app.utils.form_parsers import parse_enum_form

@app.post("/endpoint")
async def endpoint(
    engine: TTSEngine = Depends(
        parse_enum_form(TTSEngine, TTSEngine.XTTS, "tts_engine")
    )
):
    # engine já é TTSEngine enum
    # Conversão automática + validação
    print(f"Engine: {engine.value}")
```

**Vantagens:**
- ✅ Mais elegante (dependency injection)
- ✅ Reutilizável
- ✅ Type hints corretos
- ✅ Validação automática

**Desvantagens:**
- ⚠️ Mais complexo para iniciantes
- ⚠️ Requer import adicional

---

## Exemplos Práticos

### Exemplo 1: Clone de Voz (Caso Real)

```python
# app/main.py - Endpoint /voices/clone
from app.utils.form_parsers import validate_enum_string
from app.models import TTSEngine

@app.post("/voices/clone", status_code=202)
async def clone_voice(
    file: UploadFile = File(...),
    name: str = Form(...),
    language: str = Form(...),
    tts_engine_str: str = Form('xtts', description="TTS engine: 'xtts' or 'f5tts'"),
):
    # Validar engine
    tts_engine = validate_enum_string(
        tts_engine_str, 
        TTSEngine, 
        "tts_engine",
        case_sensitive=False  # Aceita "XTTS", "xtts", "XtTs", etc.
    )
    
    # Criar job com engine correto
    job = Job.create_new(
        tts_engine=tts_engine.value,  # Converte para string
        ...
    )
```

### Exemplo 2: Lista de Engines

```python
from app.utils.form_parsers import validate_enum_list

@app.post("/batch-process")
async def batch_process(
    engines_str: list[str] = Form(['xtts'])  # Lista de strings
):
    # Validar todos os engines
    engines = validate_enum_list(
        engines_str,
        TTSEngine,
        "engines",
        allow_duplicates=False  # Remove duplicatas
    )
    
    # Process com múltiplos engines
    for engine in engines:
        print(f"Processing with {engine.value}")
```

### Exemplo 3: Validação Custom

```python
from app.utils.form_parsers import validate_enum_string

@app.post("/custom")
async def custom_endpoint(
    mode_str: str = Form(...)
):
    try:
        mode = validate_enum_string(mode_str, JobMode, "mode")
    except HTTPException as e:
        # Custom error handling
        logger.error(f"Invalid mode: {mode_str}")
        return JSONResponse(
            status_code=400,
            content={"error": "invalid_mode", "details": e.detail}
        )
    
    # Continue processing
    ...
```

---

## Guidelines e Best Practices

### ✅ DO (Fazer)

1. **SEMPRE use validação explícita:**
   ```python
   # ✅ CORRETO
   engine_str: str = Form('xtts')
   engine = validate_enum_string(engine_str, TTSEngine, "tts_engine")
   ```

2. **SEMPRE adicione logging:**
   ```python
   logger.info(f"📥 Request received: engine={engine.value}")
   ```

3. **SEMPRE teste todos os valores do enum:**
   ```python
   # Em seus testes
   for engine_value in ['xtts', 'f5tts']:
       response = client.post("/endpoint", data={"engine": engine_value})
       assert response.status_code == 202
   ```

4. **SEMPRE documente valores aceitos:**
   ```python
   engine: str = Form(
       'xtts',
       description="TTS engine: 'xtts' (default, stable) or 'f5tts' (experimental)"
   )
   ```

### ❌ DON'T (Não Fazer)

1. **NUNCA use Enum diretamente em Form():**
   ```python
   # ❌ ERRADO - Ignora input do usuário
   engine: TTSEngine = Form(TTSEngine.XTTS)
   ```

2. **NUNCA assuma que string é válida:**
   ```python
   # ❌ ERRADO - Pode crashar
   engine_str: str = Form('xtts')
   engine = TTSEngine(engine_str)  # ValueError se inválido
   ```

3. **NUNCA use validação case-sensitive sem motivo:**
   ```python
   # ❌ ERRADO - UX ruim
   if engine_str not in ['xtts', 'f5tts']:  # Só aceita lowercase
       raise HTTPException(...)
   
   # ✅ CORRETO - Case-insensitive
   validate_enum_string(engine_str, TTSEngine, "engine", case_sensitive=False)
   ```

4. **NUNCA esqueça de converter enum→string ao salvar:**
   ```python
   # ❌ ERRADO - Pode causar serialization errors
   job.tts_engine = engine  # TTSEngine enum
   
   # ✅ CORRETO
   job.tts_engine = engine.value  # String 'xtts' ou 'f5tts'
   ```

---

## Testing Checklist

Ao usar Enums em endpoints, sempre teste:

- [ ] ✅ Valor válido (lowercase): `'xtts'`
- [ ] ✅ Valor válido (uppercase): `'XTTS'`
- [ ] ✅ Valor válido (mixed case): `'XtTs'`
- [ ] ✅ Valor inválido: `'invalid_engine'` → 400
- [ ] ✅ Valor vazio: `''` → 400 ou default
- [ ] ✅ Valor None: `null` → 400 ou default
- [ ] ✅ Default funciona quando omitido
- [ ] ✅ Logging mostra valor recebido
- [ ] ✅ Job/DB salva valor correto

---

## Troubleshooting

### Problema: "ValueError: 'XTTS' is not a valid TTSEngine"

**Causa:** Tentou converter string com case diferente.

**Solução:**
```python
# Usar case_sensitive=False
validate_enum_string(value, TTSEngine, "engine", case_sensitive=False)
```

### Problema: "Engine sempre usa default"

**Causa:** Usando `Form(Enum.VALUE)` diretamente.

**Solução:**
```python
# Mudar de:
engine: TTSEngine = Form(TTSEngine.XTTS)

# Para:
engine_str: str = Form('xtts')
engine = validate_enum_string(engine_str, TTSEngine, "engine")
```

### Problema: "HTTPException not caught by FastAPI"

**Causa:** HTTPException levantada fora de endpoint.

**Solução:**
```python
# validate_enum_string() já levanta HTTPException
# FastAPI vai capturar automaticamente
# Não precisa try/except
```

---

## Migration Guide

### Passo 1: Identificar endpoints problemáticos

```bash
# Procurar por Form() com Enum
grep -r "Form(.*Enum" app/
```

### Passo 2: Refatorar um por vez

```python
# ANTES
from app.models import TTSEngine

@app.post("/endpoint")
async def endpoint(
    engine: TTSEngine = Form(TTSEngine.XTTS)
):
    ...

# DEPOIS
from app.utils.form_parsers import validate_enum_string

@app.post("/endpoint")
async def endpoint(
    engine_str: str = Form('xtts')
):
    engine = validate_enum_string(engine_str, TTSEngine, "tts_engine")
    # Resto do código igual (usar engine.value onde necessário)
    ...
```

### Passo 3: Adicionar testes

```python
# tests/test_endpoint.py
def test_endpoint_with_valid_engine():
    response = client.post("/endpoint", data={"engine": "xtts"})
    assert response.status_code == 200

def test_endpoint_with_invalid_engine():
    response = client.post("/endpoint", data={"engine": "invalid"})
    assert response.status_code == 400
    assert "tts_engine" in response.json()["detail"]
```

### Passo 4: Deploy e monitorar

```bash
# Deploy
docker-compose restart service

# Monitorar logs
docker-compose logs -f service | grep -i "engine\|error"
```

---

## Referências

- **Bug Original:** `RESULT.md` - Engine Selection Bug
- **Sprint Implementation:** `SPRINTS.md` - SPRINT-04
- **Código:** `app/utils/form_parsers.py`
- **Testes:** `tests/test_clone_voice_engine_selection.py`

---

**📝 Criado em:** 2024-12-04  
**🔄 Última atualização:** 2024-12-04  
**✅ Status:** Padrão recomendado para todos os endpoints
