#!/usr/bin/env python3
"""
Verificar estrutura de diretórios do F5-TTS após correções
"""
from pathlib import Path
import sys

def check_structure():
    print("\n🔍 Verificando estrutura de diretórios...\n")
    
    issues = []
    ok_count = 0
    
    # 1. Verificar output directory
    output_dir = Path("/home/tts-webui-proxmox-passthrough/train/output/F5TTS_Base")
    if output_dir.exists():
        print(f"✅ train/output/F5TTS_Base/ existe")
        ok_count += 1
        
        # Verificar checkpoints
        checkpoints = list(output_dir.glob("*.pt"))
        if checkpoints:
            print(f"   ✅ {len(checkpoints)} checkpoint(s) encontrado(s):")
            for ckpt in checkpoints:
                size_gb = ckpt.stat().st_size / (1024**3)
                print(f"      - {ckpt.name} ({size_gb:.1f} GB)")
        else:
            print(f"   ⚠️  Nenhum checkpoint encontrado")
    else:
        print(f"❌ train/output/F5TTS_Base/ NÃO EXISTE")
        issues.append("output_dir_missing")
    
    # 2. Verificar symlink de checkpoints
    f5_ckpt = Path("/root/.local/lib/python3.11/ckpts/f5_dataset")
    if f5_ckpt.exists() and f5_ckpt.is_symlink():
        target = f5_ckpt.resolve()
        if target == output_dir:
            print(f"\n✅ Symlink de checkpoints OK")
            print(f"   /root/.local/lib/python3.11/ckpts/f5_dataset")
            print(f"   → {target}")
            ok_count += 1
        else:
            print(f"\n❌ Symlink aponta para local errado:")
            print(f"   Atual: {target}")
            print(f"   Esperado: {output_dir}")
            issues.append("wrong_symlink_target")
    elif f5_ckpt.exists():
        print(f"\n⚠️  ckpts/f5_dataset existe mas NÃO é symlink")
        print(f"   Isso fará checkpoints serem salvos no local errado!")
        issues.append("not_symlink")
    else:
        print(f"\n❌ Symlink de checkpoints NÃO EXISTE")
        issues.append("symlink_missing")
    
    # 3. Verificar dataset
    data_dir = Path("/home/tts-webui-proxmox-passthrough/train/data/f5_dataset")
    if data_dir.exists():
        wavs = list(data_dir.glob("wavs/*.wav"))
        print(f"\n✅ Dataset OK: {len(wavs)} arquivos .wav")
        ok_count += 1
    else:
        print(f"\n❌ Dataset NÃO ENCONTRADO")
        issues.append("dataset_missing")
    
    # 4. Verificar symlink de data
    data_symlink = Path("/root/.local/lib/python3.11/data")
    if data_symlink.is_symlink():
        target = data_symlink.resolve()
        expected = Path("/home/tts-webui-proxmox-passthrough/train/data")
        if target == expected:
            print(f"✅ Symlink de data OK")
            ok_count += 1
        else:
            print(f"⚠️  Symlink de data aponta para: {target}")
            print(f"   Esperado: {expected}")
    else:
        print(f"⚠️  Symlink de data não encontrado")
    
    # 5. Verificar que scripts/output não existe
    scripts_output = Path("/home/tts-webui-proxmox-passthrough/train/scripts/output")
    if not scripts_output.exists():
        print(f"\n✅ scripts/output/ removido (correto)")
        ok_count += 1
    else:
        print(f"\n⚠️  scripts/output/ ainda existe (deveria ter sido removido)")
        issues.append("scripts_output_exists")
    
    # Resultado
    print(f"\n{'='*70}")
    if not issues:
        print(f"✅ TUDO OK! ({ok_count} verificações passaram)")
        print(f"{'='*70}")
        print(f"\n🚀 Pronto para treinar:")
        print(f"   cd /home/tts-webui-proxmox-passthrough/train")
        print(f"   train")
        return 0
    else:
        print(f"⚠️  {len(issues)} problema(s) encontrado(s)")
        print(f"{'='*70}")
        print(f"\nProblemas:")
        for issue in issues:
            print(f"  - {issue}")
        print(f"\n💡 Execute o script de correção:")
        print(f"   python3 train/scripts/fix_directories.py")
        return 1

if __name__ == "__main__":
    sys.exit(check_structure())
