#!/bin/bash
# Script para remover symlinks F5-TTS FORA do repositório
# EXECUTE COM CUIDADO - Revisar destinos antes de confirmar
# Data: $(date +%Y-%m-%d)

set -euo pipefail

echo "🔍 Procurando symlinks F5-TTS em /root/.local/lib/python3.11/..."
echo ""

# Possíveis locais mencionados em MORE.md e documentação
POSSIBLE_SYMLINKS=(
    "/root/.local/lib/python3.11/ckpts"
    "/root/.local/lib/python3.11/data"
    "/root/.cache/huggingface/hub/models--charactr--vocos-mel-24khz"
    "/root/.cache/huggingface/hub/models--firstpixel--F5-TTS-pt-br"
)

SYMLINKS_FOUND=0
SYMLINKS_REMOVED=0

for symlink in "${POSSIBLE_SYMLINKS[@]}"; do
    if [ -L "$symlink" ]; then
        echo "📌 SYMLINK ENCONTRADO: $symlink"
        ls -la "$symlink"
        ((SYMLINKS_FOUND++))
        read -p "Remover este symlink? (y/N): " confirm
        if [[ "$confirm" == "y" || "$confirm" == "Y" ]]; then
            rm -v "$symlink"
            echo "✅ Removido: $symlink"
            ((SYMLINKS_REMOVED++))
        else
            echo "⏭️ Pulado: $symlink"
        fi
        echo ""
    elif [ -d "$symlink" ]; then
        echo "📁 DIRETÓRIO ENCONTRADO (não é symlink): $symlink"
        echo "   Tamanho: $(du -sh "$symlink" 2>/dev/null || echo 'N/A')"
        ((SYMLINKS_FOUND++))
        read -p "Remover este diretório? (y/N): " confirm
        if [[ "$confirm" == "y" || "$confirm" == "Y" ]]; then
            rm -rfv "$symlink"
            echo "✅ Removido: $symlink"
            ((SYMLINKS_REMOVED++))
        else
            echo "⏭️ Pulado: $symlink"
        fi
        echo ""
    else
        echo "❌ NÃO ENCONTRADO: $symlink"
        echo ""
    fi
done

echo ""
echo "📊 RESUMO:"
echo "   - Locais verificados: ${#POSSIBLE_SYMLINKS[@]}"
echo "   - Symlinks/diretórios encontrados: $SYMLINKS_FOUND"
echo "   - Removidos: $SYMLINKS_REMOVED"
echo ""

if [ $SYMLINKS_FOUND -eq 0 ]; then
    echo "✅ Nenhum symlink F5-TTS encontrado nos locais conhecidos"
else
    echo "🎯 Para procurar manualmente por outros symlinks F5-TTS:"
    echo "   find /root -type l -name '*f5*' 2>/dev/null"
    echo "   find /root -type l -name '*vocos*' 2>/dev/null"
    echo "   find /root -type d -name '*F5-TTS*' 2>/dev/null"
fi

echo ""
echo "✅ Script concluído!"
