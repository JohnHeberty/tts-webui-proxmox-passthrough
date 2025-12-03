#!/usr/bin/env python3
"""
VSCode Terminal Launcher
Abre um novo terminal no VSCode para monitoramento (TensorBoard, etc)
"""
import sys
import json
import subprocess
from pathlib import Path


def open_vscode_terminal(command: str, name: str = "Monitor") -> bool:
    """
    Abre um novo terminal no VSCode e executa comando
    
    Args:
        command: Comando a executar
        name: Nome do terminal
    """
    try:
        # Método 1: Usar code CLI
        # Nota: Isso pode não funcionar em todos os ambientes
        # VSCode precisa ter CLI instalado (code command)
        
        # Criar script temporário
        script_path = Path("/tmp/vscode_terminal_script.sh")
        with open(script_path, 'w') as f:
            f.write(f"#!/bin/bash\n")
            f.write(f"# Terminal: {name}\n")
            f.write(f"{command}\n")
            f.write(f"# Manter terminal aberto\n")
            f.write(f"exec bash\n")
        
        script_path.chmod(0o755)
        
        # Tentar abrir terminal via code
        try:
            # VSCode integrated terminal via CLI
            result = subprocess.run(
                ['code', '--new-window', str(script_path)],
                capture_output=True,
                timeout=2
            )
            if result.returncode == 0:
                print(f"✅ Terminal '{name}' aberto no VSCode")
                return True
        except (subprocess.TimeoutExpired, FileNotFoundError):
            pass
        
        # Método 2: Usar gnome-terminal ou terminal padrão
        terminals = [
            ['gnome-terminal', '--', 'bash', str(script_path)],
            ['xterm', '-e', 'bash', str(script_path)],
            ['konsole', '-e', 'bash', str(script_path)],
        ]
        
        for term_cmd in terminals:
            try:
                subprocess.Popen(term_cmd, start_new_session=True)
                print(f"✅ Terminal '{name}' aberto: {term_cmd[0]}")
                return True
            except FileNotFoundError:
                continue
        
        # Método 3: Fallback - tmux/screen se disponível
        try:
            subprocess.run(['tmux', 'new-window', '-n', name, command], check=True)
            print(f"✅ Terminal '{name}' aberto no tmux")
            return True
        except (FileNotFoundError, subprocess.CalledProcessError):
            pass
        
        print(f"⚠️  Não foi possível abrir terminal automaticamente")
        print(f"Execute manualmente: {command}")
        return False
        
    except Exception as e:
        print(f"❌ Erro ao abrir terminal: {e}")
        return False


def launch_tensorboard(logdir: str, port: int = 6006):
    """Lança TensorBoard em novo terminal"""
    command = f"cd {logdir} && tensorboard --logdir . --port {port} --bind_all"
    return open_vscode_terminal(command, "TensorBoard")


def launch_monitoring():
    """Lança script de monitoramento"""
    command = "watch -n 1 nvidia-smi"
    return open_vscode_terminal(command, "GPU Monitor")


if __name__ == '__main__':
    import argparse
    
    parser = argparse.ArgumentParser(description="Abrir terminal VSCode")
    parser.add_argument('--tensorboard', action='store_true', help="Abrir TensorBoard")
    parser.add_argument('--gpu-monitor', action='store_true', help="Monitorar GPU")
    parser.add_argument('--command', type=str, help="Comando customizado")
    parser.add_argument('--name', type=str, default="Terminal", help="Nome do terminal")
    
    args = parser.parse_args()
    
    if args.tensorboard:
        logdir = Path(__file__).parent.parent / "runs"
        launch_tensorboard(str(logdir))
    elif args.gpu_monitor:
        launch_monitoring()
    elif args.command:
        open_vscode_terminal(args.command, args.name)
    else:
        print("Use --tensorboard, --gpu-monitor ou --command 'seu_comando'")
