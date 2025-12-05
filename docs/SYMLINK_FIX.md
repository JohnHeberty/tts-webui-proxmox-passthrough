# Fix: Symlink Quebrado em model_last.pt

## 🐛 Problema

**Erro:** `FileNotFoundError: Custom checkpoint not found: /app/train/output/ptbr_finetuned2/model_last.pt`

**Causa Raiz:**
O arquivo `model_last.pt` era um **symlink quebrado** que apontava para um arquivo fora da estrutura montada do Docker:

```bash
model_last.pt -> ../../../blobs/ddc223bbecf96fd5f759c7b52dd9233fad7b44f31546726af48d2d1642e55f7f
```

O Docker não consegue seguir symlinks que apontam para diretórios não montados, resultando em erro de "arquivo não encontrado" mesmo que o symlink exista.

## ✅ Solução

### Remover Symlink e Criar Arquivo Real

```bash
cd /home/tts-webui-proxmox-passthrough/train/output/ptbr_finetuned2

# Remover symlink quebrado
rm -f model_last.pt

# Criar cópia real do checkpoint válido
cp model_33200.pt model_last.pt

# Verificar
ls -lh *.pt
```

**Resultado:**
```
-rw-r--r-- 1 root root 5.1G Dec  5 15:48 model_33200.pt
-rw-r--r-- 1 root root 5.1G Dec  5 19:38 model_last.pt      ✅ Agora é arquivo real
-rw-r--r-- 1 root root 5.1G Dec  5 18:52 model_last_BK.pt
```

### Reiniciar Container

```bash
docker compose restart celery-worker
```

## 🔍 Como Identificar Symlinks Quebrados

```bash
# Encontrar symlinks quebrados
find /home/tts-webui-proxmox-passthrough/train/output -type l ! -exec test -e {} \; -print

# Ver para onde um symlink aponta
ls -l model_last.pt
readlink -f model_last.pt  # Mostra caminho absoluto (se válido)
```

## 📝 Prevenção

### Para Evitar Symlinks Problemáticos com Docker

1. **Sempre use arquivos reais** para checkpoints montados em volumes Docker
2. **Se precisar usar symlinks**, garanta que o destino esteja dentro do volume montado
3. **Verifique symlinks** antes de montar volumes:
   ```bash
   find . -type l -ls
   ```

### Estrutura de Volumes Docker-Compose

O `docker-compose.yml` monta:
```yaml
volumes:
  - ./train:/app/train  # Training checkpoints and data
```

**✅ Funciona:**
- `/home/.../train/output/ptbr_finetuned2/model_last.pt` (arquivo real)
- `/home/.../train/output/ptbr_finetuned2/model_last.pt -> model_33200.pt` (symlink relativo)

**❌ Não Funciona:**
- `model_last.pt -> ../../../blobs/xxx` (symlink fora do volume)
- `model_last.pt -> /root/.cache/huggingface/xxx` (caminho absoluto não montado)

## 🎯 Configuração de Checkpoint Customizado

### Opção 1: Usar Fine-Tuned (Padrão Atual)

```bash
# .env
F5TTS_CUSTOM_CHECKPOINT=/app/train/output/ptbr_finetuned2/model_last.pt
```

### Opção 2: Usar Modelo Pretrained

```bash
# .env - Comentar ou deixar vazio
F5TTS_CUSTOM_CHECKPOINT=
# Ou
# F5TTS_CUSTOM_CHECKPOINT=/app/train/output/ptbr_finetuned2/model_last.pt
```

Reiniciar:
```bash
docker compose restart celery-worker audio-voice-service
```

### Opção 3: Checkpoint Específico

```bash
# .env - Usar checkpoint específico
F5TTS_CUSTOM_CHECKPOINT=/app/train/output/ptbr_finetuned2/model_33200.pt
```

## 🧪 Verificação

### Dentro do Container

```bash
# Verificar se arquivo existe dentro do container
docker exec audio-voice-celery ls -lh /app/train/output/ptbr_finetuned2/*.pt

# Verificar se é arquivo real (não symlink)
docker exec audio-voice-celery stat /app/train/output/ptbr_finetuned2/model_last.pt
```

### Logs

```bash
# Ver se F5-TTS carregou corretamente
docker compose logs celery-worker | grep -E "F5-TTS|checkpoint|model_last"

# Deve mostrar algo como:
# ✅ Using custom trained checkpoint: /app/train/output/ptbr_finetuned2/model_last.pt
# Loading checkpoint: /app/train/output/ptbr_finetuned2/model_last.pt
# ✅ F5-TTS model and vocoder loaded successfully
```

## 📚 Referências

- **Docker Volumes:** https://docs.docker.com/storage/volumes/
- **Symlinks in Docker:** https://docs.docker.com/storage/bind-mounts/#configure-bind-propagation
- **File Type Detection:** `man stat`, `man readlink`

## 🐛 Troubleshooting

### Erro Persiste Após Correção

1. **Verificar permissões:**
   ```bash
   ls -la train/output/ptbr_finetuned2/model_last.pt
   # Deve ser readable (r--r--r-- ou similar)
   ```

2. **Verificar espaço em disco:**
   ```bash
   df -h /home
   # Precisa ter ~10GB livres para carregar checkpoint
   ```

3. **Verificar integridade do arquivo:**
   ```bash
   # Tamanho deve ser ~5GB
   du -sh train/output/ptbr_finetuned2/model_last.pt
   
   # Testar se é válido (dentro do container)
   docker exec audio-voice-celery python3 -c "import torch; torch.load('/app/train/output/ptbr_finetuned2/model_last.pt', map_location='cpu'); print('✅ Valid')"
   ```

4. **Limpar cache e reiniciar:**
   ```bash
   docker compose down
   docker compose up -d
   ```

## ✅ Resolução

**Status:** ✅ Resolvido em 2025-12-05

**Ação Tomada:**
- Removido symlink quebrado
- Criado arquivo real copiando checkpoint válido
- Container reiniciado e F5-TTS carregando corretamente

**Impacto:**
- F5-TTS agora carrega checkpoint customizado sem erros
- Fallback para XTTS não é mais necessário
- API pode usar modelo fine-tuned

---

**Última Atualização:** 2025-12-05  
**Autor:** Audio Voice Service Team
