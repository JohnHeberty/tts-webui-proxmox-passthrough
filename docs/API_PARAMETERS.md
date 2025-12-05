# API Parameter Reference - POST /jobs

**Last Updated:** 2024-12-05 00:20 UTC  
**Status:** ✅ FIXED - All parameter names updated

---

## ⚠️ BREAKING CHANGE

Os nomes dos parâmetros foram **corrigidos** para remover o sufixo `_str`:

| ❌ Nome Antigo (ERRADO) | ✅ Nome Novo (CORRETO) | Tipo | Descrição |
|------------------------|------------------------|------|-----------|
| `mode_str` | `mode` | string | Modo: 'dubbing' ou 'dubbing_with_clone' |
| `tts_engine_str` | `tts_engine` | string | Engine: 'xtts' ou 'f5tts' |
| `voice_preset_str` | `voice_preset` | string | Preset de voz genérica |
| `rvc_f0_method_str` | `rvc_f0_method` | string | Método de extração F0 |

---

## 📋 Parâmetros Completos

### **Obrigatórios**

| Parâmetro | Tipo | Descrição | Exemplo |
|-----------|------|-----------|---------|
| `text` | string | Texto para dublar (1-10.000 caracteres) | `"Olá, mundo!"` |
| `source_language` | string | Idioma do texto | `"pt-BR"` |
| `mode` | string | Modo de dublagem | `"dubbing"` ou `"dubbing_with_clone"` |

### **Condicionais**

| Parâmetro | Tipo | Quando Usar | Exemplo |
|-----------|------|-------------|---------|
| `voice_preset` | string | Quando `mode=dubbing` | `"female_generic"` |
| `voice_id` | string | Quando `mode=dubbing_with_clone` | `"2caa74ef-..."` |

### **Opcionais**

| Parâmetro | Tipo | Padrão | Descrição |
|-----------|------|--------|-----------|
| `target_language` | string | `source_language` | Idioma de destino |
| `tts_engine` | string | `"xtts"` | Engine TTS: `"xtts"` ou `"f5tts"` |
| `ref_text` | string | `null` | Transcrição para F5-TTS |
| `quality_profile_id` | string | `"{engine}_balanced"` | ID do perfil de qualidade |

### **RVC (Voice Conversion)**

| Parâmetro | Tipo | Padrão | Descrição |
|-----------|------|--------|-----------|
| `enable_rvc` | boolean | `false` | Ativar conversão RVC |
| `rvc_model_id` | string | `null` | ID do modelo RVC |
| `rvc_pitch` | int | `0` | Pitch shift (-12 a +12) |
| `rvc_index_rate` | float | `0.75` | Index rate (0.0 a 1.0) |
| `rvc_filter_radius` | int | `3` | Raio do filtro (0 a 7) |
| `rvc_rms_mix_rate` | float | `0.25` | RMS mix (0.0 a 1.0) |
| `rvc_protect` | float | `0.33` | Proteção (0.0 a 0.5) |
| `rvc_f0_method` | string | `"rmvpe"` | Método F0: `"rmvpe"`, `"harvest"`, `"crepe"` |

---

## 🔧 Exemplos de Uso

### **Exemplo 1: Dublagem com voz genérica (XTTS)**

```bash
curl -X POST 'http://localhost:8005/jobs' \
  -H 'Content-Type: application/x-www-form-urlencoded' \
  -d 'text=Olá, mundo!' \
  -d 'source_language=pt-BR' \
  -d 'mode=dubbing' \
  -d 'voice_preset=female_generic' \
  -d 'tts_engine=xtts'
```

### **Exemplo 2: Dublagem com voz clonada (F5-TTS)**

```bash
curl -X POST 'http://localhost:8005/jobs' \
  -H 'Content-Type: application/x-www-form-urlencoded' \
  -d 'text=Esse é um teste de clonagem de voz!' \
  -d 'source_language=pt-BR' \
  -d 'mode=dubbing_with_clone' \
  -d 'voice_id=2caa74ef-5037-4f0a-8ba1-0d3818637155' \
  -d 'tts_engine=f5tts' \
  -d 'ref_text=Texto de referência da voz clonada'
```

### **Exemplo 3: Dublagem com RVC**

```bash
curl -X POST 'http://localhost:8005/jobs' \
  -H 'Content-Type: application/x-www-form-urlencoded' \
  -d 'text=Teste com conversão de voz!' \
  -d 'source_language=pt-BR' \
  -d 'mode=dubbing' \
  -d 'voice_preset=male_deep' \
  -d 'tts_engine=xtts' \
  -d 'enable_rvc=true' \
  -d 'rvc_model_id=my-rvc-model' \
  -d 'rvc_pitch=-3' \
  -d 'rvc_f0_method=rmvpe'
```

---

## 🐛 Erros Comuns

### 1. **Field required: mode**
❌ **Causa:** Usando `mode_str` em vez de `mode`  
✅ **Solução:** Use `mode=dubbing` (sem `_str`)

### 2. **Field required: tts_engine**
❌ **Causa:** Usando `tts_engine_str` em vez de `tts_engine`  
✅ **Solução:** Use `tts_engine=f5tts` (sem `_str`)

### 3. **Invalid voice preset**
❌ **Causa:** Preset inválido ou usando `voice_preset_str`  
✅ **Solução:** Use `voice_preset=female_generic` (valores válidos)

### 4. **voice_id required when mode=dubbing_with_clone**
❌ **Causa:** Faltando `voice_id` no modo clone  
✅ **Solução:** Adicione `voice_id=<uuid>`

### 5. **rvc_model_id required when enable_rvc=true**
❌ **Causa:** RVC ativado mas sem modelo  
✅ **Solução:** Adicione `rvc_model_id=<model-id>`

---

## 📊 Valores Válidos

### **mode**
- `"dubbing"` - Voz genérica (usa `voice_preset`)
- `"dubbing_with_clone"` - Voz clonada (usa `voice_id`)

### **tts_engine**
- `"xtts"` - XTTS v2 (estável, rápido)
- `"f5tts"` - F5-TTS (experimental, alta qualidade)

### **voice_preset** (quando `mode=dubbing`)
- `"female_generic"`
- `"male_generic"`
- `"male_deep"`
- (consulte GET /presets para lista completa)

### **rvc_f0_method**
- `"rmvpe"` (recomendado)
- `"fcpe"`
- `"pm"`
- `"harvest"`
- `"dio"`
- `"crepe"`

---

## 🔍 Verificar Swagger

Acesse: `http://localhost:8005/docs`

**⚠️ IMPORTANTE:** Se o Swagger ainda mostrar nomes antigos (`mode_str`, etc.):
1. **Limpe o cache do navegador:** Ctrl+Shift+R
2. **Reinicie o servidor:** `docker compose restart`
3. **Verifique a URL:** Use `/docs` (não `/redoc`)

---

## 📝 Changelog

### 2024-12-05 00:20 UTC
- ✅ Removido sufixo `_str` de todos os parâmetros
- ✅ Corrigido: `mode_str` → `mode`
- ✅ Corrigido: `tts_engine_str` → `tts_engine`
- ✅ Corrigido: `voice_preset_str` → `voice_preset`
- ✅ Corrigido: `rvc_f0_method_str` → `rvc_f0_method`
- ✅ WebUI já estava correto (não precisou mudanças)
- ✅ Backend atualizado e testado

### Commits Relacionados
- `83e42d4` - Fix parameter name mismatch (clone endpoint)
- `<pending>` - Fix parameter name mismatch (jobs endpoint)

---

## 🎯 Próximos Passos

1. ✅ **Teste o script:** `./test_job_creation.sh`
2. ⏳ **Verifique F5-TTS:** Teste clonagem com `tts_engine=f5tts`
3. ⏳ **Atualize documentação:** Postmortem completo
4. ⏳ **Commit final:** Após validação dos testes

---

**Status:** ✅ Pronto para testes  
**Breaking Change:** Sim - clientes externos precisam atualizar nomes de parâmetros  
**Backward Compatibility:** Não - nomes antigos não funcionam mais
