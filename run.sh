#!/bin/bash
# F5-TTS Training Pipeline - Unified Runner
# Usage: ./run.sh

set -e

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}════════════════════════════════════════════════════════════════${NC}"
echo -e "${BLUE}   F5-TTS Training Pipeline - Portuguese Fine-tuning${NC}"
echo -e "${BLUE}════════════════════════════════════════════════════════════════${NC}"
echo ""

# Ensure we're in the project root
cd "$(dirname "$0")"
PROJECT_ROOT=$(pwd)

# Add tensorboard to PATH
export PATH="$HOME/.local/bin:$PATH"

# Check if TensorBoard is already running
if pgrep -f "tensorboard.*train/runs" > /dev/null; then
    echo -e "${GREEN}✓${NC} TensorBoard já está rodando"
else
    echo -e "${BLUE}→${NC} Iniciando TensorBoard em background..."
    mkdir -p train/logs
    nohup tensorboard --logdir=train/runs --host=0.0.0.0 --port=6006 --reload_interval=30 > train/logs/tensorboard.log 2>&1 &
    sleep 2
    
    # Verify TensorBoard started successfully
    if curl -s -o /dev/null -w "%{http_code}" http://localhost:6006 | grep -q "200"; then
        echo -e "${GREEN}✓${NC} TensorBoard disponível em: http://192.168.18.134:6006"
    else
        echo -e "${BLUE}⚠${NC}  TensorBoard iniciado mas ainda carregando..."
    fi
fi

echo ""
echo -e "${BLUE}→${NC} Iniciando treinamento..."
echo ""

# Run training with environment forcing runs/ to stay in train/
cd "$PROJECT_ROOT/train"
export WANDB_DIR="$PROJECT_ROOT/train/runs"
export TENSORBOARD_DIR="$PROJECT_ROOT/train/runs"

python3 run_training.py

echo ""
echo -e "${GREEN}════════════════════════════════════════════════════════════════${NC}"
echo -e "${GREEN}   Treinamento concluído!${NC}"
echo -e "${GREEN}════════════════════════════════════════════════════════════════${NC}"
