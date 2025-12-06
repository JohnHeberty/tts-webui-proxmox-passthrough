#!/bin/bash
# Cleanup script para remover checkpoints duplicados/desnecessários

OUTPUT_DIR="/home/tts-webui-proxmox-passthrough/train/output/ptbr_finetuned2"

echo "=================================================="
echo "🧹 F5-TTS Checkpoint Cleanup"
echo "=================================================="
echo ""

cd "$OUTPUT_DIR" || exit 1

echo "📊 Estado ANTES da limpeza:"
ls -lh *.pt 2>/dev/null | awk '{printf "  %s  %s\n", $9, $5}'
echo ""

# Remover checkpoints com prefixo pretrained_ (criados pela lib F5-TTS)
echo "🗑️  Removendo checkpoints com prefixo 'pretrained_'..."
removed_count=0
freed_space=0

for file in pretrained_model_*.pt; do
    if [ -f "$file" ]; then
        size=$(stat -f%z "$file" 2>/dev/null || stat -c%s "$file" 2>/dev/null)
        size_gb=$(echo "scale=2; $size / 1024 / 1024 / 1024" | bc)
        
        echo "   Removendo: $file ($size_gb GB)"
        rm -f "$file"
        rm -f "${file%.pt}.metadata.json"  # Remover metadata também
        
        removed_count=$((removed_count + 1))
        freed_space=$(echo "$freed_space + $size_gb" | bc)
    fi
done

echo ""
if [ $removed_count -gt 0 ]; then
    echo "✅ Removidos $removed_count arquivo(s)"
    echo "✅ Espaço liberado: ${freed_space} GB"
else
    echo "ℹ️  Nenhum arquivo com prefixo 'pretrained_' encontrado"
fi

echo ""
echo "📊 Estado DEPOIS da limpeza:"
ls -lh *.pt 2>/dev/null | awk '{printf "  %s  %s\n", $9, $5}'

echo ""
echo "=================================================="
echo "✅ Limpeza concluída!"
echo "=================================================="
