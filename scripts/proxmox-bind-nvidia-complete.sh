#!/bin/bash
# Execute NO HOST PROXMOX
# Copia bibliotecas e binários NVIDIA para container LXC 134

set -e

CTID=134
HOST_NVIDIA_VERSION="550.163.01"

echo "🎮 Configurando bibliotecas NVIDIA no container LXC $CTID..."

# Verificar se estamos no host Proxmox
if ! command -v pct &> /dev/null; then
    echo "❌ ERRO: Execute este script NO HOST PROXMOX!"
    exit 1
fi

# Verificar driver no host
if ! nvidia-smi &> /dev/null; then
    echo "❌ ERRO: Driver NVIDIA não funciona no host!"
    exit 1
fi

echo "✅ Host Proxmox detectado"
echo "✅ Driver NVIDIA: $(nvidia-smi --query-gpu=driver_version --format=csv,noheader | head -1)"

# Parar container
echo ""
echo "🔄 Parando container $CTID..."
pct stop $CTID

sleep 2

# Configurar bind mounts
CONFIG_FILE="/etc/pve/lxc/${CTID}.conf"
BACKUP_FILE="${CONFIG_FILE}.backup-nvidia-$(date +%Y%m%d-%H%M%S)"

cp "$CONFIG_FILE" "$BACKUP_FILE"
echo "✅ Backup: $BACKUP_FILE"

# Remover bind mounts antigos de NVIDIA
sed -i '/lxc.mount.entry.*nvidia/d' "$CONFIG_FILE"

echo ""
echo "🔧 Adicionando bind mounts de binários e bibliotecas NVIDIA..."

# Adicionar bind mounts essenciais
cat >> "$CONFIG_FILE" << 'EOFCONF'
# NVIDIA Driver Bind Mounts
lxc.mount.entry: /usr/bin/nvidia-smi usr/bin/nvidia-smi none bind,optional,create=file,ro 0 0
lxc.mount.entry: /usr/bin/nvidia-debugdump usr/bin/nvidia-debugdump none bind,optional,create=file,ro 0 0
lxc.mount.entry: /usr/bin/nvidia-persistenced usr/bin/nvidia-persistenced none bind,optional,create=file,ro 0 0
lxc.mount.entry: /usr/lib/x86_64-linux-gnu/libnvidia-ml.so.1 usr/lib/x86_64-linux-gnu/libnvidia-ml.so.1 none bind,optional,create=file,ro 0 0
lxc.mount.entry: /usr/lib/x86_64-linux-gnu/libcuda.so.1 usr/lib/x86_64-linux-gnu/libcuda.so.1 none bind,optional,create=file,ro 0 0
lxc.mount.entry: /usr/lib/x86_64-linux-gnu/libnvcuvid.so.1 usr/lib/x86_64-linux-gnu/libnvcuvid.so.1 none bind,optional,create=file,ro 0 0
lxc.mount.entry: /usr/lib/x86_64-linux-gnu/libnvidia-encode.so.1 usr/lib/x86_64-linux-gnu/libnvidia-encode.so.1 none bind,optional,create=file,ro 0 0
lxc.mount.entry: /dev/nvidia0 dev/nvidia0 none bind,optional,create=file 0 0
lxc.mount.entry: /dev/nvidiactl dev/nvidiactl none bind,optional,create=file 0 0
lxc.mount.entry: /dev/nvidia-uvm dev/nvidia-uvm none bind,optional,create=file 0 0
lxc.mount.entry: /dev/nvidia-uvm-tools dev/nvidia-uvm-tools none bind,optional,create=file 0 0
EOFCONF

echo "✅ Bind mounts adicionados"

# Iniciar container
echo ""
echo "🔄 Iniciando container $CTID..."
pct start $CTID

sleep 5

# Verificar dentro do container
echo ""
echo "🧪 Testando NVIDIA dentro do container..."
echo ""

if pct exec $CTID -- nvidia-smi &> /dev/null; then
    echo "✅ nvidia-smi funciona!"
    pct exec $CTID -- nvidia-smi --query-gpu=name,driver_version --format=csv,noheader
else
    echo "❌ nvidia-smi falhou!"
    echo "   Verificando bibliotecas..."
    pct exec $CTID -- ls -lah /usr/lib/x86_64-linux-gnu/libnvidia-ml.so.1 2>&1 || true
    pct exec $CTID -- ls -lah /usr/lib/x86_64-linux-gnu/libcuda.so.1 2>&1 || true
fi

echo ""
echo "════════════════════════════════════════════════════════════"
echo "✅ CONFIGURAÇÃO CONCLUÍDA!"
echo "════════════════════════════════════════════════════════════"
echo ""
echo "📝 Próximos passos DENTRO DO CONTAINER:"
echo ""
echo "   1. Testar NVIDIA:"
echo "      nvidia-smi"
echo ""
echo "   2. Reiniciar Docker:"
echo "      cd /home/tts-webui-proxmox-passthrough"
echo "      docker compose down"
echo "      docker compose up -d"
echo ""
echo "   3. Verificar CUDA:"
echo "      docker logs audio-voice-api | grep CUDA"
echo ""
