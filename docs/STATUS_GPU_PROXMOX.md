# 🎮 Problema GPU no Proxmox LXC + Docker

## 📋 Situação Atual

Você está rodando:
```
Proxmox Host (Servidor Físico)
  └── Container LXC "ytaudio" (Ubuntu)
       └── Docker Containers
            ├── audio-voice-api (TTS Service)
            └── audio-voice-celery (Worker)
```

**GPU:** NVIDIA RTX 3090  
**Driver:** 550.163.01  
**CUDA:** 11.8 (PyTorch) / 12.4 (Driver)

## ❌ Problema

```
CUDA initialization: CUDA unknown error
⚠️  CUDA NÃO DISPONÍVEL!
```

PyTorch não consegue usar a GPU porque **`/dev/nvidia-uvm`** não existe dentro do container LXC.

## ✅ Diagnóstico Completo

| Item | Status | Detalhes |
|------|--------|----------|
| Driver NVIDIA no LXC | ✅ OK | `nvidia-smi` funciona |
| Docker runtime nvidia | ✅ OK | `default-runtime: nvidia` |
| Devices `/dev/nvidia0` | ✅ OK | Existem e têm permissões corretas |
| Devices `/dev/nvidia-uvm*` | ❌ FALTANDO | **Causa do erro!** |
| PyTorch detecta CUDA | ❌ FALHA | Por falta dos devices acima |

## 🛠️ Solução

### Opção 1: 🎯 **RECOMENDADO** - Configurar no Proxmox Host

**Veja:** [`docs/PROXMOX_FIX_RAPIDO.md`](docs/PROXMOX_FIX_RAPIDO.md)

Resumo:
1. Acessar o **servidor Proxmox** (não o container)
2. Executar: `modprobe nvidia-uvm` e criar devices
3. Editar `/etc/pve/lxc/[ID].conf` para fazer passthrough
4. Reiniciar container LXC
5. Reiniciar containers Docker

**Tempo:** ~5 minutos  
**Permanente:** ✅ Sim (com systemd service)

### Opção 2: ⚠️ Workaround Temporário - Rodar em CPU

Se não puder acessar o Proxmox agora, os containers já estão rodando em **fallback CPU**. Funciona, mas é mais lento.

## 📁 Arquivos de Documentação

1. **[docs/PROXMOX_FIX_RAPIDO.md](docs/PROXMOX_FIX_RAPIDO.md)** - Guia passo-a-passo para corrigir AGORA
2. **[docs/PROXMOX_GPU_SETUP.md](docs/PROXMOX_GPU_SETUP.md)** - Documentação completa com troubleshooting
3. **[scripts/init-nvidia-devices.sh](scripts/init-nvidia-devices.sh)** - Script para diagnosticar devices

## 🧪 Como Testar Após Correção

Dentro do container LXC:

```bash
# 1. Verificar devices
ls -la /dev/nvidia-uvm*
# Esperado: crw-rw-rw- 1 root root 508, 0 ... /dev/nvidia-uvm

# 2. Reiniciar Docker
cd /home/tts-webui-proxmox-passthrough
docker compose down && docker compose up -d

# 3. Verificar CUDA
docker logs audio-voice-api | grep CUDA
# Esperado: "✅ CUDA disponível: True"
```

## 🔗 Próximos Passos

1. [ ] Acessar servidor Proxmox
2. [ ] Seguir [`docs/PROXMOX_FIX_RAPIDO.md`](docs/PROXMOX_FIX_RAPIDO.md)
3. [ ] Testar CUDA funcionando
4. [ ] (Opcional) Configurar systemd service para persistir no boot

## 💡 Por que isso acontece?

Containers LXC compartilham o kernel com o host Proxmox, mas não montam automaticamente todos os devices. Os devices `/dev/nvidia-uvm*` são criados dinamicamente quando o módulo `nvidia-uvm` é carregado, mas:

- ❌ O container LXC não pode carregar módulos do kernel
- ❌ O container LXC não herda os devices automaticamente
- ✅ **Solução:** Configurar passthrough manual no arquivo do container

## 📚 Referências

- [Proxmox LXC Documentation](https://pve.proxmox.com/wiki/Linux_Container)
- [NVIDIA Docker Container Runtime](https://github.com/NVIDIA/nvidia-docker)
- [PyTorch CUDA Troubleshooting](https://pytorch.org/get-started/locally/)

---

**Status Atual:** 🟡 Containers rodando em CPU (fallback)  
**Próxima Ação:** Configurar GPU no Proxmox Host
