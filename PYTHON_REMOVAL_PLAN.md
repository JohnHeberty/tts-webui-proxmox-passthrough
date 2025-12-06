# Plano de Remoção de Python Nativo da VM

## ⚠️ ATENÇÃO: Isolamento Docker 100%

Este plano remove Python da VM host, mantendo TUDO dentro dos containers Docker.

---

## 📊 Estado Atual

### Pacotes Python no Sistema (apt)
```
python3                    3.11.2-1+b1
python3-minimal            3.11.2-1+b1
python3-pip                23.0.1+dfsg-1
python3-dev                3.11.2-1+b1
libpython3.11              3.11.2-6+deb12u6
+ 30 pacotes python3-* de sistema
```

### Pacotes Python User-Installed (pip)
```
188 pacotes instalados em /root/.local/lib/python3.11/site-packages/
Incluindo: torch, coqui-tts, celery, redis, fastapi, etc.
Tamanho: ~15GB (estimado)
```

### Dependências de Sistema
```
Nenhum serviço systemd usa Python
Apenas 2 pacotes dependem de python3-minimal (python3, python3)
Seguro remover pacotes user-installed
```

---

## 🎯 Estratégia de Remoção

### FASE 1: Remover Pacotes pip (SEGURO) ✅
**Objetivo**: Limpar /root/.local completamente  
**Impacto**: Zero (tudo está em Docker)  
**Comando**:
```bash
pip freeze --user | xargs pip uninstall -y
rm -rf /root/.local/lib/python3.11/site-packages/*
rm -rf /root/.cache/pip
```

### FASE 2: Manter Python Sistema (RECOMENDADO) ⚠️
**Motivo**: Proxmox pode usar Python para scripts de manutenção  
**Ação**: Manter python3-minimal, python3, python3-apt  
**Resultado**: Python básico do sistema, sem user packages

### FASE 3: Remover Python Completo (OPCIONAL - RISCO ALTO) 🚨
**Motivo**: Isolamento 100% como solicitado  
**Risco**: Pode quebrar ferramentas de sistema (apt-add-repository, etc.)  
**Comando** (NÃO EXECUTAR AINDA):
```bash
apt-get purge -y python3-pip python3-dev python3-setuptools
apt-get autoremove -y
```

---

## 🔧 Comandos Aprovados para Execução

### 1. Limpar Pacotes pip User-Installed
```bash
# Ver lista completa antes de remover
pip list --format=freeze > /tmp/pip-backup.txt

# Remover TODOS os pacotes pip
pip freeze --user 2>/dev/null | xargs -r pip uninstall -y

# Limpar diretórios .local e cache
rm -rf /root/.local/lib/python3.11/site-packages/*
rm -rf /root/.local/lib/python3.11/ckpts
rm -rf /root/.cache/pip
rm -rf /root/.cache/torch
rm -rf /root/.cache/huggingface

# Verificar limpeza
du -sh /root/.local /root/.cache
```

### 2. Verificar Pacotes Remanescentes
```bash
# Apenas pacotes do sistema devem aparecer
dpkg -l | grep python3 | awk '{print $2, $3}'
```

### 3. (OPCIONAL) Remover python3-pip se quiser isolamento total
```bash
apt-get purge -y python3-pip python3-pip-whl
apt-get autoremove -y
```

---

## 📝 Checklist de Validação

Após remoção:

- [ ] `pip list` retorna erro ou lista vazia ✅
- [ ] `/root/.local/lib/python3.11/` está vazio ✅
- [ ] `/root/.cache/` não tem pip/torch/huggingface ✅
- [ ] `du -sh /root/.local` mostra <100MB ✅
- [ ] Docker containers funcionam normalmente ✅
- [ ] `docker compose exec audio-voice-service python --version` retorna Python 3.11 ✅
- [ ] API /health responde HTTP 200 ✅

---

## 🐳 Confirmação de Isolamento Docker

### Antes da Remoção
```bash
# Na VM host (deve falhar após limpeza)
python3 -c "import torch; print(torch.__version__)"

# No container (deve sempre funcionar)
docker compose exec audio-voice-service python -c "import torch; print(torch.__version__)"
```

### Depois da Remoção
```bash
# Host: Erro "No module named 'torch'" ✅ ESPERADO
python3 -c "import torch"

# Container: Funciona normalmente ✅
docker compose exec audio-voice-service python -c "import torch; print('✅ Torch OK no container')"
```

---

## 💾 Espaço a Liberar

```
/root/.local/lib/python3.11/site-packages/  ~12GB
/root/.cache/pip/                            ~1GB
/root/.cache/torch/                          ~1.5GB
/root/.cache/huggingface/                    ~500MB
TOTAL ESTIMADO:                              ~15GB
```

---

## 🚀 Próximos Passos

1. ✅ Build Docker completo (`docker compose build --no-cache`)
2. ⏳ Executar FASE 1 (limpar pip user packages)
3. ⏳ Testar containers (`docker compose up -d`)
4. ⏳ Validar API (`curl http://localhost:8005/health`)
5. ⏳ (Opcional) FASE 3 se quiser remover pip do sistema

---

## 📌 Notas Importantes

- **Volume Mounts**: Código da aplicação em `/app` vem de `./app:/app` (bind mount)
- **Modelos**: `/app/models` monta `./models:/app/models` (acesso direto, sem cópia)
- **Logs**: `./logs:/app/logs` (direto do host)
- **Python no Container**: Instalado via Dockerfile, isolado da VM

**Resultado Final**: VM host sem dependências Python user-installed, tudo roda em Docker.

---

**Data**: 2025-01-XX  
**Status**: Aguardando build Docker completar
