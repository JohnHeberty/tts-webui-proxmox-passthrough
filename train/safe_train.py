#!/usr/bin/env python3
"""
Wrapper de segurança para treinamento F5-TTS com proteções de memória
"""
import os
from pathlib import Path
import subprocess
import sys

import psutil


# Limites de segurança
MAX_RAM_PERCENT = 80  # Não usar mais de 80% da RAM
MIN_FREE_RAM_GB = 2  # Manter pelo menos 2GB livre


def check_memory_safety():
    """Verifica se há memória suficiente para treinar"""
    mem = psutil.virtual_memory()

    total_gb = mem.total / (1024**3)
    available_gb = mem.available / (1024**3)
    used_percent = mem.percent

    print("📊 Memória do Sistema:")
    print(f"   Total: {total_gb:.1f} GB")
    print(f"   Disponível: {available_gb:.1f} GB")
    print(f"   Em uso: {used_percent:.1f}%")
    print()

    if available_gb < MIN_FREE_RAM_GB:
        print("❌ ERRO: Memória insuficiente!")
        print(f"   Necessário: Pelo menos {MIN_FREE_RAM_GB} GB livres")
        print(f"   Disponível: {available_gb:.1f} GB")
        return False

    if used_percent > MAX_RAM_PERCENT:
        print(f"⚠️  AVISO: Sistema já está usando {used_percent:.1f}% da RAM")
        print("   Recomendado: Libere memória antes de treinar")
        response = input("   Continuar mesmo assim? (s/N): ")
        if response.lower() != "s":
            return False

    print("✅ Memória OK para treinamento")
    print()
    return True


def monitor_and_kill_if_needed(process):
    """Monitor de segurança que mata o processo se usar muita RAM"""
    import time

    try:
        while process.poll() is None:
            mem = psutil.virtual_memory()

            # Se RAM livre cair abaixo do mínimo, matar processo
            if mem.available / (1024**3) < MIN_FREE_RAM_GB:
                print()
                print("🚨 ALERTA: RAM CRÍTICA!")
                print(f"   Memória livre: {mem.available / (1024**3):.1f} GB")
                print("   Abortando treinamento para proteger o sistema...")
                print()

                process.terminate()
                time.sleep(2)
                if process.poll() is None:
                    process.kill()

                return False

            time.sleep(5)

        return True

    except KeyboardInterrupt:
        process.terminate()
        return False


def main():
    """Executa treinamento com proteções de memória"""

    # Verificar memória antes de começar
    if not check_memory_safety():
        print("❌ Treinamento abortado por falta de memória")
        sys.exit(1)

    # Configurar limite de memória do processo (se suportado)
    try:
        import resource

        # Limitar RAM virtual a 90% da RAM total
        mem_limit = int(psutil.virtual_memory().total * 0.9)
        resource.setrlimit(resource.RLIMIT_AS, (mem_limit, mem_limit))
        print(f"✅ Limite de memória configurado: {mem_limit / (1024**3):.1f} GB")
        print()
    except:
        print("⚠️  Não foi possível configurar limite de memória")
        print()

    # Configurar variáveis de ambiente para otimizar memória
    os.environ["PYTORCH_CUDA_ALLOC_CONF"] = "max_split_size_mb=512"
    os.environ["OMP_NUM_THREADS"] = "2"
    os.environ["MKL_NUM_THREADS"] = "2"

    print("🚀 Iniciando treinamento com monitoramento de memória...")
    print()

    # Executar run_training.py
    script_dir = Path(__file__).parent
    run_training = script_dir / "run_training.py"

    try:
        process = subprocess.Popen([sys.executable, str(run_training)], cwd=str(script_dir.parent))

        # Monitorar memória durante execução
        success = monitor_and_kill_if_needed(process)

        if success:
            print()
            print("✅ Treinamento concluído com sucesso!")
            sys.exit(0)
        else:
            print()
            print("❌ Treinamento interrompido")
            sys.exit(1)

    except KeyboardInterrupt:
        print()
        print("⚠️  Interrompido pelo usuário")
        sys.exit(0)


if __name__ == "__main__":
    main()
