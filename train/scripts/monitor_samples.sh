#!/bin/bash
# Monitor training samples generation

SAMPLES_DIR="/home/tts-webui-proxmox-passthrough/train/output/ptbr_finetuned2/samples"

echo "=================================================="
echo "🎵 F5-TTS Training Samples Monitor"
echo "=================================================="
echo ""
echo "📁 Samples directory: $SAMPLES_DIR"
echo ""

while true; do
    clear
    echo "=================================================="
    echo "🎵 F5-TTS Training Samples Monitor"
    echo "=================================================="
    date
    echo ""
    
    # Count samples
    gen_count=$(ls -1 "$SAMPLES_DIR"/update_*_gen.wav 2>/dev/null | wc -l)
    ref_count=$(ls -1 "$SAMPLES_DIR"/update_*_ref.wav 2>/dev/null | wc -l)
    
    echo "📊 Samples count:"
    echo "   Generated: $gen_count"
    echo "   Reference: $ref_count"
    echo ""
    
    if [ $gen_count -gt 0 ]; then
        echo "📝 Latest samples:"
        ls -lht "$SAMPLES_DIR"/*.wav | head -10
        echo ""
        
        # Show latest update number
        latest_gen=$(ls -t "$SAMPLES_DIR"/update_*_gen.wav 2>/dev/null | head -1)
        if [ -n "$latest_gen" ]; then
            update_num=$(basename "$latest_gen" | sed 's/update_\([0-9]*\)_gen.wav/\1/')
            echo "🎯 Latest update: $update_num"
            echo ""
            
            # Estimate time
            total_size=$(du -sh "$SAMPLES_DIR" | cut -f1)
            echo "💾 Total size: $total_size"
        fi
    else
        echo "⏳ Waiting for first samples to be generated..."
        echo "   (Expected after ~200 updates, approximately 7 minutes)"
    fi
    
    echo ""
    echo "=================================================="
    echo "Press Ctrl+C to stop monitoring"
    echo "Refreshing in 30 seconds..."
    sleep 30
done
