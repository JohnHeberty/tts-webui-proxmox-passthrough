# 🎮 Configuração de GPU no Proxmox LXC

## Problema Identificado

Você está rodando dentro de um **container LXC no Proxmox**, e precisa configurar o passthrough da GPU NVIDIA RTX 3090 corretamente.

## ✅ O que está funcionando
- ✅ `nvidia-smi` funciona dentro do container LXC
- ✅ Driver NVIDIA 550.163.01 detectado
- ✅ GPU RTX 3090 visível
- ✅ Docker com runtime nvidia configurado

## ❌ O que NÃO está funcionando
- ❌ Devices `/dev/nvidia-uvm` e `/dev/nvidia-uvm-tools` não existem/corrompidos
- ❌ PyTorch não consegue inicializar CUDA
- ❌ Módulos do kernel não disponíveis dentro do LXC

---

## 🔧 Solução: Configurar no Host Proxmox

### 1️⃣ No HOST Proxmox (fora do container)

Conecte-se ao seu servidor Proxmox (não ao container) e execute:

```bash
# 1. Carregar módulo nvidia-uvm no HOST
modprobe nvidia-uvm

# 2. Criar devices se não existirem
if [ ! -e /dev/nvidia-uvm ]; then
  MAJOR=$(grep nvidia-uvm /proc/devices | awk '{print $1}')
  mknod -m 666 /dev/nvidia-uvm c $MAJOR 0
fi

if [ ! -e /dev/nvidia-uvm-tools ]; then
  MAJOR=$(grep nvidia-uvm /proc/devices | awk '{print $1}')
  mknod -m 666 /dev/nvidia-uvm-tools c $MAJOR 1
fi

# 3. Verificar devices criados
ls -la /dev/nvidia*
```

### 2️⃣ Configurar o Container LXC

**Edite o arquivo de configuração do container** (substitua `100` pelo ID do seu container):

```bash
# No HOST Proxmox
nano /etc/pve/lxc/100.conf
```

**Adicione estas linhas:**

```conf
# GPU Passthrough - NVIDIA RTX 3090
lxc.cgroup2.devices.allow: c 195:* rwm
lxc.cgroup2.devices.allow: c 508:* rwm
lxc.cgroup2.devices.allow: c 242:* rwm
lxc.mount.entry: /dev/nvidia0 dev/nvidia0 none bind,optional,create=file
lxc.mount.entry: /dev/nvidiactl dev/nvidiactl none bind,optional,create=file
lxc.mount.entry: /dev/nvidia-uvm dev/nvidia-uvm none bind,optional,create=file
lxc.mount.entry: /dev/nvidia-uvm-tools dev/nvidia-uvm-tools none bind,optional,create=file
lxc.mount.entry: /dev/nvidia-modeset dev/nvidia-modeset none bind,optional,create=file
```

### 3️⃣ Persistir devices no boot do Proxmox

Crie um script para carregar módulos e criar devices no boot:

```bash
# No HOST Proxmox
cat > /etc/systemd/system/nvidia-uvm-init.service << 'EOF'
[Unit]
Description=NVIDIA UVM Init
After=nvidia-persistenced.service

[Service]
Type=oneshot
ExecStart=/sbin/modprobe nvidia-uvm
ExecStart=/bin/bash -c 'MAJOR=$$(grep nvidia-uvm /proc/devices | awk "{print \\$$1}"); [ ! -e /dev/nvidia-uvm ] && mknod -m 666 /dev/nvidia-uvm c $$MAJOR 0 || true'
ExecStart=/bin/bash -c 'MAJOR=$$(grep nvidia-uvm /proc/devices | awk "{print \\$$1}"); [ ! -e /dev/nvidia-uvm-tools ] && mknod -m 666 /dev/nvidia-uvm-tools c $$MAJOR 1 || true'
RemainAfterExit=yes

[Install]
WantedBy=multi-user.target
EOF

# Habilitar serviço
systemctl daemon-reload
systemctl enable nvidia-uvm-init.service
systemctl start nvidia-uvm-init.service
```

### 4️⃣ Reiniciar Container LXC

```bash
# No HOST Proxmox
pct stop 100
pct start 100

# OU via interface web Proxmox
```

---

## 🧪 Testar dentro do Container

Após reiniciar o container:

```bash
# 1. Verificar devices
ls -la /dev/nvidia*

# Esperado:
# crw-rw-rw- 1 nobody nogroup 195,   0 /dev/nvidia0
# crw-rw-rw- 1 nobody nogroup 195, 255 /dev/nvidiactl
# crw-rw-rw- 1 nobody nogroup 508,   0 /dev/nvidia-uvm
# crw-rw-rw- 1 nobody nogroup 508,   1 /dev/nvidia-uvm-tools

# 2. Testar CUDA no container Docker
docker exec audio-voice-api python -c "import torch; print('CUDA available:', torch.cuda.is_available())"

# Esperado: CUDA available: True
```

---

## 🐛 Troubleshooting

### Se os devices ainda não aparecem dentro do container LXC:

```bash
# No HOST Proxmox, verificar major numbers
cat /proc/devices | grep nvidia

# Exemplo de saída:
# 195 nvidia-frontend
# 508 nvidia-uvm
# 242 nvidia-modeset

# Ajustar lxc.cgroup2.devices.allow conforme os major numbers do SEU sistema
```

### Se PyTorch ainda não detecta CUDA:

```bash
# Dentro do container LXC
docker exec audio-voice-api bash -c '
  ls -la /dev/nvidia*
  echo "---"
  python -c "import torch; print(torch.cuda.is_available())"
  echo "---"
  ldd /usr/local/lib/python3.11/dist-packages/torch/lib/libtorch_cuda.so | grep cuda
'
```

---

## 📝 Resumo das Ações

**No Host Proxmox:**
1. ✅ Carregar `nvidia-uvm`: `modprobe nvidia-uvm`
2. ✅ Criar devices `/dev/nvidia-uvm*`
3. ✅ Criar serviço systemd para persistir
4. ✅ Editar `/etc/pve/lxc/100.conf` com passthrough
5. ✅ Reiniciar container LXC

**Dentro do Container LXC:**
1. ✅ Verificar devices com `ls -la /dev/nvidia*`
2. ✅ Reiniciar containers Docker: `docker compose down && docker compose up -d`
3. ✅ Verificar CUDA: `docker logs audio-voice-api | grep CUDA`

---

## 🔗 Referências

- [Proxmox LXC GPU Passthrough](https://www.reddit.com/r/homelab/comments/x1bcjt/gpu_passthrough_to_lxc_on_proxmox/)
- [NVIDIA Docker Container Runtime](https://nvidia.github.io/nvidia-docker/)
- [PyTorch CUDA Troubleshooting](https://pytorch.org/get-started/locally/)

---

## ⚠️ Alternativa: Container LXC Privilegiado

Se a solução acima não funcionar, você pode precisar **converter o container para privilegiado**:

```bash
# No HOST Proxmox
pct stop 100
nano /etc/pve/lxc/100.conf

# Alterar/adicionar:
unprivileged: 0

# Reiniciar
pct start 100
```

**Nota:** Containers privilegiados têm acesso root ao host - usar com cuidado!
