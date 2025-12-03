#!/bin/bash
# Instalador do comando 'train'
# Cria symlink global para fácil acesso

set -e

TRAIN_ROOT="/home/tts-webui-proxmox-passthrough/train"
TRAIN_CMD="$TRAIN_ROOT/train"
INSTALL_DIR="/usr/local/bin"

echo "=================================================="
echo "🚀 Instalador do F5-TTS Auto-Trainer"
echo "=================================================="
echo ""

# Verificar se existe
if [ ! -f "$TRAIN_CMD" ]; then
    echo "❌ Erro: $TRAIN_CMD não encontrado"
    exit 1
fi

# Verificar permissões
if [ ! -x "$TRAIN_CMD" ]; then
    echo "⚠️  Tornando executável..."
    chmod +x "$TRAIN_CMD"
fi

# Criar symlink
echo "📦 Criando symlink em $INSTALL_DIR/train..."

if [ -L "$INSTALL_DIR/train" ] || [ -f "$INSTALL_DIR/train" ]; then
    echo "⚠️  Removendo instalação anterior..."
    sudo rm -f "$INSTALL_DIR/train"
fi

sudo ln -s "$TRAIN_CMD" "$INSTALL_DIR/train"

echo "✅ Comando 'train' instalado com sucesso!"
echo ""
echo "=================================================="
echo "📋 Uso:"
echo "=================================================="
echo ""
echo "  train                  # Executar pipeline completo"
echo "  train --validate-only  # Apenas validar setup"
echo "  train --tensorboard    # Abrir TensorBoard"
echo "  train --monitor        # Monitorar GPU"
echo "  train --help           # Ajuda completa"
echo ""
echo "=================================================="
echo "✅ Instalação concluída!"
echo "=================================================="
