#!/bin/bash
set -e

# Configurar bibliotecas CUDA compat para compatibilidade com driver
export LD_LIBRARY_PATH="/usr/local/cuda-12.4/compat:${LD_LIBRARY_PATH}"
export CUDA_HOME="/usr/local/cuda-12.4"

# Fix permissions for mounted volumes
echo "Fixing directory permissions..."
chmod 777 /app/temp /app/uploads /app/processed /app/logs 2>/dev/null || true
chown -R appuser:appuser /app/voice_profiles /app/models 2>/dev/null || true

# Switch to appuser and execute command
exec gosu appuser "$@"
