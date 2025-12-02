# 🚨 SOLUÇÃO RÁPIDA - Execute no HOST Proxmox

## ⚡ Execute estes comandos NO SERVIDOR PROXMOX (não no container!)

### 1️⃣ Conecte-se ao Proxmox via SSH ou Console

```bash
# Conecte-se ao servidor físico Proxmox, não ao container LXC!
ssh root@SEU-IP-PROXMOX
```

### 2️⃣ Carregar módulo nvidia-uvm e criar devices

```bash
# Carregar módulo
modprobe nvidia-uvm

# Criar devices se não existirem
MAJOR=$(grep nvidia-uvm /proc/devices | awk '{print $1}')
if [ -n "$MAJOR" ]; then
  [ ! -e /dev/nvidia-uvm ] && mknod -m 666 /dev/nvidia-uvm c $MAJOR 0
  [ ! -e /dev/nvidia-uvm-tools ] && mknod -m 666 /dev/nvidia-uvm-tools c $MAJOR 1
  chmod 666 /dev/nvidia-uvm /dev/nvidia-uvm-tools
fi

# Verificar
ls -la /dev/nvidia-uvm*
# Deve mostrar:
# crw-rw-rw- 1 root root 508, 0 ... /dev/nvidia-uvm
# crw-rw-rw- 1 root root 508, 1 ... /dev/nvidia-uvm-tools
```

### 3️⃣ Descobrir ID do seu container LXC

```bash
# Listar containers
pct list

# Ou procurar pelo nome
pct list | grep ytaudio  # Ajuste conforme o nome do seu container
```

Anote o **ID** (ex: 100, 101, etc.)

### 4️⃣ Editar configuração do container

Substitua `100` pelo ID do seu container:

```bash
# Parar container
pct stop 100

# Editar configuração
nano /etc/pve/lxc/100.conf
```

**Adicione estas linhas no FINAL do arquivo:**

```conf
# GPU Passthrough - NVIDIA
lxc.cgroup2.devices.allow: c 195:* rwm
lxc.cgroup2.devices.allow: c 508:* rwm
lxc.mount.entry: /dev/nvidia0 dev/nvidia0 none bind,optional,create=file
lxc.mount.entry: /dev/nvidiactl dev/nvidiactl none bind,optional,create=file
lxc.mount.entry: /dev/nvidia-uvm dev/nvidia-uvm none bind,optional,create=file
lxc.mount.entry: /dev/nvidia-uvm-tools dev/nvidia-uvm-tools none bind,optional,create=file
```

**Salvar:** `Ctrl+O`, `Enter`, `Ctrl+X`

### 5️⃣ Iniciar container

```bash
pct start 100
```

### 6️⃣ Entrar no container e testar

```bash
# Entrar no container
pct enter 100

# OU via SSH se tiver configurado
ssh root@IP-DO-CONTAINER

# Verificar devices
ls -la /dev/nvidia*

# Deve mostrar nvidia-uvm agora!
```

### 7️⃣ Reiniciar Docker dentro do container

Agora dentro do container LXC:

```bash
cd /home/tts-webui-proxmox-passthrough
docker compose down
docker compose up -d

# Aguardar alguns segundos
sleep 5

# Verificar logs
docker logs audio-voice-api | grep CUDA
```

**✅ Deve mostrar:** 
```
✅ CUDA disponível: True
🎮 GPU: NVIDIA GeForce RTX 3090
```

---

## 🔄 Persistir configuração no boot

Para que os devices sejam criados automaticamente no boot do Proxmox:

```bash
# No HOST Proxmox
cat > /etc/systemd/system/nvidia-uvm-init.service << 'EOF'
[Unit]
Description=NVIDIA UVM Device Initialization
After=nvidia-persistenced.service

[Service]
Type=oneshot
ExecStart=/sbin/modprobe nvidia-uvm
ExecStart=/bin/bash -c 'MAJOR=$$(grep nvidia-uvm /proc/devices | awk "{print \\$$1}"); [ -n "$$MAJOR" ] && [ ! -e /dev/nvidia-uvm ] && mknod -m 666 /dev/nvidia-uvm c $$MAJOR 0 || true'
ExecStart=/bin/bash -c 'MAJOR=$$(grep nvidia-uvm /proc/devices | awk "{print \\$$1}"); [ -n "$$MAJOR" ] && [ ! -e /dev/nvidia-uvm-tools ] && mknod -m 666 /dev/nvidia-uvm-tools c $$MAJOR 1 || true'
ExecStart=/bin/chmod 666 /dev/nvidia-uvm /dev/nvidia-uvm-tools
RemainAfterExit=yes

[Install]
WantedBy=multi-user.target
EOF

systemctl daemon-reload
systemctl enable nvidia-uvm-init.service
systemctl start nvidia-uvm-init.service
```

---

## 📊 Exemplo Completo

```bash
# ==== NO HOST PROXMOX ====

# 1. Criar devices
modprobe nvidia-uvm
MAJOR=$(grep nvidia-uvm /proc/devices | awk '{print $1}')
mknod -m 666 /dev/nvidia-uvm c $MAJOR 0
mknod -m 666 /dev/nvidia-uvm-tools c $MAJOR 1

# 2. Editar container (substitua 100 pelo seu ID)
pct stop 100
echo "lxc.cgroup2.devices.allow: c 195:* rwm" >> /etc/pve/lxc/100.conf
echo "lxc.cgroup2.devices.allow: c 508:* rwm" >> /etc/pve/lxc/100.conf
echo "lxc.mount.entry: /dev/nvidia0 dev/nvidia0 none bind,optional,create=file" >> /etc/pve/lxc/100.conf
echo "lxc.mount.entry: /dev/nvidiactl dev/nvidiactl none bind,optional,create=file" >> /etc/pve/lxc/100.conf
echo "lxc.mount.entry: /dev/nvidia-uvm dev/nvidia-uvm none bind,optional,create=file" >> /etc/pve/lxc/100.conf
echo "lxc.mount.entry: /dev/nvidia-uvm-tools dev/nvidia-uvm-tools none bind,optional,create=file" >> /etc/pve/lxc/100.conf
pct start 100

# 3. Entrar no container
pct enter 100

# ==== DENTRO DO CONTAINER LXC ====

# 4. Verificar devices
ls -la /dev/nvidia*

# 5. Reiniciar Docker
cd /caminho/do/projeto
docker compose down
docker compose up -d

# 6. Verificar CUDA
docker logs audio-voice-api | grep -i cuda
```

---

## ❓ Troubleshooting

### Major number diferente de 508?

```bash
# No HOST Proxmox
cat /proc/devices | grep nvidia

# Ajustar a linha lxc.cgroup2.devices.allow conforme output
# Se nvidia-uvm for 510, por exemplo:
# lxc.cgroup2.devices.allow: c 510:* rwm
```

### Container não inicia após editar .conf?

```bash
# Verificar erros
pct status 100

# Remover últimas linhas adicionadas
nano /etc/pve/lxc/100.conf
# (remover as linhas lxc.* que você adicionou)

# Tentar iniciar novamente
pct start 100
```

---

## 🎯 Resultado Esperado

Após seguir todos os passos:

✅ `/dev/nvidia-uvm` existe no container LXC  
✅ PyTorch detecta CUDA dentro do Docker  
✅ Logs mostram "CUDA disponível: True"  
✅ Modelos TTS rodam na GPU RTX 3090  

🚀 **Boa sorte!**
