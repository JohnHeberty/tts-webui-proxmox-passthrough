# 🐍 Guia de Reset do Ambiente Python (Pós-Remoção F5-TTS)

**Data:** $(date +%Y-%m-%d)  
**Status:** Guia Oficial de Migração

---

## 🎯 Objetivo

Recriar ambiente Python limpo, sem dependências órfãs do F5-TTS, otimizando uso de memória e espaço em disco.

---

## 📋 Contexto

Com a remoção do F5-TTS, as seguintes dependências foram eliminadas:
- `f5-tts==1.1.9`
- `cached-path>=1.6.2`
- `faster-whisper>=1.0.0`
- `vocos==0.1.0`

**Benefícios do reset:**
- ✅ Limpeza de pacotes órfãos
- ✅ Redução de espaço em disco (~2-3GB)
- ✅ Menos conflitos de versão
- ✅ Ambiente mais leve e rápido

---

## 🔧 Opção 1: Manter Conda (Recomendado para GPU)

Conda gerencia melhor dependências CUDA e é ideal para ambientes com GPU.

### Passo a Passo

```bash
# 1. Desativar ambiente atual
conda deactivate

# 2. Listar ambientes disponíveis (para confirmar nome)
conda env list

# 3. Remover ambiente antigo (ajustar nome se necessário)
conda env remove -n tts-webui

# 4. Criar ambiente limpo com Python 3.11
conda create -n tts-webui python=3.11 -y

# 5. Ativar novo ambiente
conda activate tts-webui

# 6. Atualizar pip
pip install --upgrade pip setuptools wheel

# 7. Reinstalar dependências (já sem F5-TTS)
cd /home/tts-webui-proxmox-passthrough
pip install -r requirements.txt

# 8. Verificar CUDA (se GPU disponível)
python -c "import torch; print(f'CUDA disponível: {torch.cuda.is_available()}')"
python -c "import torch; print(f'CUDA versão: {torch.version.cuda}')"
python -c "import torch; print(f'GPUs detectadas: {torch.cuda.device_count()}')"

# 9. Verificar que F5-TTS não está instalado
pip list | grep -E "f5-tts|vocos|faster-whisper"
# Esperado: saída vazia (nenhum resultado)

# 10. Testar XTTS (opcional)
python -c "from TTS.api import TTS; tts = TTS('tts_models/multilingual/multi-dataset/xtts_v2'); print('✅ XTTS OK')"
```

### Configurar Conda no Systemd (Persistência)

Se rodar como serviço systemd, atualizar `ExecStart`:

```ini
# /etc/systemd/system/tts-webui.service
[Service]
ExecStart=/bin/bash -c 'source /opt/conda/etc/profile.d/conda.sh && conda activate tts-webui && cd /home/tts-webui-proxmox-passthrough && uvicorn app.main:app --host 0.0.0.0 --port 8000'
```

Recarregar daemon:
```bash
sudo systemctl daemon-reload
sudo systemctl restart tts-webui
```

---

## 🐍 Opção 2: Migrar para venv (Mais Leve)

venv é nativo do Python e mais leve que Conda (sem overhead de gestão de pacotes).

### Passo a Passo

```bash
# 1. Garantir Python 3.11 instalado
python3.11 --version
# Se não instalado: sudo apt install python3.11 python3.11-venv

# 2. Criar venv no diretório padrão
python3.11 -m venv /opt/tts-webui-venv

# 3. Ativar venv
source /opt/tts-webui-venv/bin/activate

# 4. Atualizar pip
pip install --upgrade pip setuptools wheel

# 5. Instalar PyTorch com CUDA (se GPU disponível)
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118

# 6. Instalar dependências do projeto
cd /home/tts-webui-proxmox-passthrough
pip install -r requirements.txt

# 7. Verificar instalação
pip list | grep -E "coqui-tts|torch|celery|redis"

# 8. Verificar que F5-TTS não está instalado
pip list | grep -E "f5-tts|vocos|faster-whisper"
# Esperado: saída vazia

# 9. Testar XTTS
python -c "from TTS.api import TTS; tts = TTS('tts_models/multilingual/multi-dataset/xtts_v2'); print('✅ XTTS OK')"
```

### Configurar venv no Systemd

```ini
# /etc/systemd/system/tts-webui.service
[Service]
ExecStart=/opt/tts-webui-venv/bin/uvicorn app.main:app --host 0.0.0.0 --port 8000
WorkingDirectory=/home/tts-webui-proxmox-passthrough
```

Recarregar daemon:
```bash
sudo systemctl daemon-reload
sudo systemctl restart tts-webui
```

---

## 🐳 Opção 3: Docker (Isolamento Completo)

Docker garante ambiente 100% reproduzível e isolado.

### Passo a Passo

```bash
# 1. Rebuild imagem Docker (já usa requirements.txt atualizado sem F5-TTS)
cd /home/tts-webui-proxmox-passthrough
docker-compose build --no-cache

# 2. Parar containers antigos
docker-compose down

# 3. Remover volumes órfãos (opcional - CUIDADO: perde dados Redis/uploads)
docker volume prune -f

# 4. Rodar containers
docker-compose up -d

# 5. Verificar logs
docker-compose logs -f --tail=100

# 6. Verificar que F5-TTS não está no container
docker-compose exec app pip list | grep -E "f5-tts|vocos|faster-whisper"
# Esperado: saída vazia

# 7. Testar XTTS dentro do container
docker-compose exec app python -c "from TTS.api import TTS; tts = TTS('tts_models/multilingual/multi-dataset/xtts_v2'); print('✅ XTTS OK')"
```

---

## ✅ Verificação Pós-Setup (Todas as Opções)

Execute estes testes independente do método escolhido:

### 1. Verificar Pacotes Removidos

```bash
pip list | grep f5-tts    # deve retornar vazio
pip list | grep vocos     # deve retornar vazio
pip list | grep faster-whisper  # deve retornar vazio
```

### 2. Verificar XTTS Funcional

```bash
python -c "from TTS.api import TTS; tts = TTS('tts_models/multilingual/multi-dataset/xtts_v2'); print('XTTS OK')"
```

### 3. Verificar API

```bash
# Iniciar servidor (se não rodando)
uvicorn app.main:app --host 0.0.0.0 --port 8000 &

# Testar health check
curl http://localhost:8000/health

# Testar criação de job com XTTS
curl -X POST http://localhost:8000/jobs \
  -F "text=Olá mundo" \
  -F "source_language=pt-BR" \
  -F "mode=dubbing" \
  -F "tts_engine=xtts"
# Esperado: HTTP 200 com job_id

# Testar rejeição de F5-TTS
curl -X POST http://localhost:8000/jobs \
  -F "text=teste" \
  -F "source_language=pt-BR" \
  -F "mode=dubbing" \
  -F "tts_engine=f5tts"
# Esperado: HTTP 400 "F5-TTS engine has been removed"
```

### 4. Verificar Quality Profiles

```bash
curl http://localhost:8000/quality-profiles | jq
# Esperado: apenas profiles XTTS (balanced, expressive, stable)
```

---

## 🔧 Troubleshooting

### Erro: "No module named 'f5_tts'"

**Causa:** Ambiente antigo ainda ativo ou imports antigos no código.

**Solução:**
```bash
# Verificar ambiente ativo
which python
pip list | grep f5

# Se f5-tts ainda aparece, recriar ambiente do zero
```

### Erro: CUDA not available

**Causa:** PyTorch instalado sem suporte CUDA ou drivers NVIDIA desatualizados.

**Solução:**
```bash
# Verificar drivers NVIDIA
nvidia-smi

# Reinstalar PyTorch com CUDA
pip uninstall torch torchvision torchaudio
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118

# Verificar
python -c "import torch; print(torch.cuda.is_available())"
```

### Erro: Celery não conecta ao Redis

**Causa:** Redis não rodando ou variáveis de ambiente incorretas.

**Solução:**
```bash
# Verificar Redis
redis-cli ping  # Esperado: PONG

# Verificar .env
cat .env | grep REDIS
# Esperado: REDIS_URL=redis://localhost:6379/5

# Reiniciar Celery
pkill -f celery
celery -A app.celery_tasks worker --loglevel=info
```

### Erro: Import "TTSEngine.F5TTS" não encontrado

**Causa:** Código antigo ainda tentando importar F5-TTS.

**Solução:**
```bash
# Buscar referências órfãs
grep -r "F5TTS" app/ --include="*.py"
grep -r "f5tts" app/ --include="*.py"

# Se encontrar, remover manualmente
```

---

## 📊 Comparação de Métodos

| Método | Espaço em Disco | Performance | Isolamento | Recomendado Para |
|--------|----------------|-------------|------------|------------------|
| **Conda** | ~2GB (ambiente) | Boa | Médio | Desenvolvimento local com GPU |
| **venv** | ~500MB (ambiente) | Ótima | Baixo | Produção em servidor dedicado |
| **Docker** | ~3GB (imagem) | Boa | Alto | Produção multi-servidor/k8s |

---

## 🎯 Checklist Final

- [ ] Ambiente recriado do zero
- [ ] `pip list` não mostra f5-tts, vocos, faster-whisper
- [ ] XTTS funciona (`TTS.api import` sem erros)
- [ ] CUDA disponível (se GPU presente)
- [ ] API responde em `/health`
- [ ] Endpoint `/jobs` aceita `xtts` e rejeita `f5tts`
- [ ] Quality profiles retornam apenas XTTS
- [ ] Celery conecta ao Redis
- [ ] Logs não mostram erros de import

---

## 📞 Suporte

**Problemas comuns:**
- Import errors → Recriar ambiente do zero
- CUDA not available → Verificar drivers NVIDIA + reinstalar PyTorch
- API errors → Verificar logs em `logs/app.log`

**Referências:**
- XTTS: https://github.com/coqui-ai/TTS
- PyTorch CUDA: https://pytorch.org/get-started/locally/
- Celery: https://docs.celeryproject.org/

---

✅ **Ambiente limpo e pronto para produção!**
