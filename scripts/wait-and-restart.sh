#!/bin/bash
# Script para aguardar build e reiniciar containers

echo "⏳ Aguardando build finalizar..."

# Aguarda o processo de build terminar
while pgrep -f "docker compose build" > /dev/null; do
    sleep 5
    echo -n "."
done

echo ""
echo "✅ Build finalizado!"

# Verifica se houve erro no build
if [ -f /tmp/docker-build.log ]; then
    if grep -qi "error" /tmp/docker-build.log; then
        echo "❌ Build com erros. Verifique /tmp/docker-build.log"
        exit 1
    fi
fi

echo "🔄 Reiniciando containers..."
cd /home/tts-webui-proxmox-passthrough
docker compose down
docker compose up -d

echo "✅ Containers reiniciados com sucesso!"
echo ""
echo "📊 Status dos containers:"
docker compose ps

echo ""
echo "📋 Para ver logs em tempo real:"
echo "   docker compose logs -f audio-voice-celery"
