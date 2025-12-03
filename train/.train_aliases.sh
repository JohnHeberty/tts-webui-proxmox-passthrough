#!/bin/bash
# Comandos Úteis para Fine-tuning F5-TTS

# ============================================================================
# VALIDAÇÃO E VERIFICAÇÃO
# ============================================================================

# Validar setup completo
alias validate-train='cd /home/tts-webui-proxmox-passthrough/train && python3 scripts/validate_setup.py'

# Verificar modelo .pt
alias check-model='cd /home/tts-webui-proxmox-passthrough/train && python3 scripts/check_model.py'

# Ver configuração atual
alias show-config='cd /home/tts-webui-proxmox-passthrough/train && cat .env'

# ============================================================================
# TREINAMENTO
# ============================================================================

# Iniciar treinamento
alias start-train='cd /home/tts-webui-proxmox-passthrough && python3 -m train.run_training'

# Continuar treinamento (resume automático)
alias resume-train='cd /home/tts-webui-proxmox-passthrough && python3 -m train.run_training'

# ============================================================================
# MONITORAMENTO
# ============================================================================

# Iniciar TensorBoard
alias tensorboard-train='cd /home/tts-webui-proxmox-passthrough/train && tensorboard --logdir runs --port 6006'

# Ver logs em tempo real
alias tail-logs='cd /home/tts-webui-proxmox-passthrough/train && tail -f logs/*.log'

# Ver GPU usage
alias gpu-watch='watch -n 1 nvidia-smi'

# ============================================================================
# CHECKPOINTS
# ============================================================================

# Listar checkpoints
alias list-ckpts='cd /home/tts-webui-proxmox-passthrough/train && ls -lh output/ptbr_finetuned/*.pt'

# Ver último checkpoint
alias last-ckpt='cd /home/tts-webui-proxmox-passthrough/train && ls -lht output/ptbr_finetuned/*.pt | head -1'

# Verificar checkpoint específico
# Uso: check-ckpt output/ptbr_finetuned/model_1000.pt
alias check-ckpt='cd /home/tts-webui-proxmox-passthrough/train && python3 scripts/check_model.py'

# ============================================================================
# DATASET
# ============================================================================

# Ver estatísticas do dataset
alias dataset-stats='cd /home/tts-webui-proxmox-passthrough/train && python3 -c "
import json
from pathlib import Path
data_dir = Path(\"data/f5_dataset\")
with open(data_dir / \"duration.json\") as f:
    durations = json.load(f)[\"duration\"]
print(f\"Total samples: {len(durations)}\")
print(f\"Total duration: {sum(durations)/3600:.2f} hours\")
print(f\"Min: {min(durations):.1f}s, Max: {max(durations):.1f}s\")
print(f\"Mean: {sum(durations)/len(durations):.1f}s\")
"'

# Contar arquivos wav
alias count-wavs='cd /home/tts-webui-proxmox-passthrough/train && find data/f5_dataset/wavs -name "*.wav" | wc -l'

# ============================================================================
# MANUTENÇÃO
# ============================================================================

# Limpar checkpoints antigos (manter últimos 5)
alias clean-ckpts='cd /home/tts-webui-proxmox-passthrough/train && ls -t output/ptbr_finetuned/model_*.pt | tail -n +6 | xargs rm -f'

# Limpar logs antigos
alias clean-logs='cd /home/tts-webui-proxmox-passthrough/train && find runs -name "events.out.*" -mtime +7 -delete'

# Backup de checkpoint
# Uso: backup-ckpt model_10000.pt
backup-ckpt() {
    cd /home/tts-webui-proxmox-passthrough/train
    cp "output/ptbr_finetuned/$1" "output/ptbr_finetuned/$1.backup.$(date +%Y%m%d_%H%M%S)"
}

# ============================================================================
# TROUBLESHOOTING
# ============================================================================

# Verificar CUDA
alias check-cuda='python3 -c "import torch; print(f\"CUDA: {torch.cuda.is_available()}\"); print(f\"GPU: {torch.cuda.get_device_name(0) if torch.cuda.is_available() else None}\")"'

# Verificar VRAM disponível
alias check-vram='nvidia-smi --query-gpu=memory.used,memory.free,memory.total --format=csv'

# Matar processos do treinamento
alias kill-train='pkill -f "train.run_training"'

# Matar TensorBoard
alias kill-tensorboard='pkill -f "tensorboard"'

# ============================================================================
# INFORMAÇÕES
# ============================================================================

# Mostrar help
alias train-help='cat /home/tts-webui-proxmox-passthrough/train/README_QUICKSTART.md'

# Mostrar mudanças
alias train-changes='cat /home/tts-webui-proxmox-passthrough/train/CHANGES.md'

# Mostrar documentação completa
alias train-docs='cat /home/tts-webui-proxmox-passthrough/train/docs/FINETUNING.md | less'

# ============================================================================
# EXEMPLOS DE USO
# ============================================================================

echo "✅ Aliases de fine-tuning carregados!"
echo ""
echo "Comandos disponíveis:"
echo "  validate-train     - Validar setup"
echo "  start-train        - Iniciar treinamento"
echo "  tensorboard-train  - Abrir TensorBoard"
echo "  list-ckpts         - Listar checkpoints"
echo "  dataset-stats      - Estatísticas do dataset"
echo "  gpu-watch          - Monitorar GPU"
echo ""
echo "Para ver todos: grep '^alias' ~/.train_aliases.sh"
