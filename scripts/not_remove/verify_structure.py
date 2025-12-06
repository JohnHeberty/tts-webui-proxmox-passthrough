#!/usr/bin/env python3
"""
Verificar estrutura de diretórios do F5-TTS após correções
"""
from pathlib import Path
import sys


# Carregar config do .env
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))
from train.utils.env_loader import get_training_config


config = get_training_config()


def check_structure():
    print("\n🔍 Verificando estrutura de diretórios...\n")

    issues = []
    ok_count = 0

    # 1. Verificar output directory
    output_dir = project_root / config.get("output_dir", "train/output/ptbr_finetuned")
    output_rel = output_dir.relative_to(project_root)
    if output_dir.exists():
        print(f"✅ {output_rel}/ existe")
        ok_count += 1

        # Verificar checkpoints
        checkpoints = list(output_dir.glob("*.pt"))
        if checkpoints:
            print(f"   ✅ {len(checkpoints)} checkpoint(s) encontrado(s):")
            for ckpt in checkpoints:
                size_gb = ckpt.stat().st_size / (1024**3)
                print(f"      - {ckpt.name} ({size_gb:.1f} GB)")
        else:
            print("   ⚠️  Nenhum checkpoint encontrado")
    else:
        print("❌ train/output/F5TTS_Base/ NÃO EXISTE")
        issues.append("output_dir_missing")

    # 2. Verificar symlink de checkpoints
    ckpts_dir = config.get("f5tts_ckpts_dir", "/root/.local/lib/python3.11/ckpts")
    dataset_name = config.get("train_dataset_name", "f5_dataset")
    f5_ckpt = Path(f"{ckpts_dir}/{dataset_name}")
    if f5_ckpt.exists() and f5_ckpt.is_symlink():
        target = f5_ckpt.resolve()
        if target == output_dir:
            print("\n✅ Symlink de checkpoints OK")
            print(f"   {ckpts_dir}/{dataset_name}")
            print(f"   → {target}")
            ok_count += 1
        else:
            print("\n❌ Symlink aponta para local errado:")
            print(f"   Atual: {target}")
            print(f"   Esperado: {output_dir}")
            issues.append("wrong_symlink_target")
    elif f5_ckpt.exists():
        print("\n⚠️  ckpts/f5_dataset existe mas NÃO é symlink")
        print("   Isso fará checkpoints serem salvos no local errado!")
        issues.append("not_symlink")
    else:
        print("\n❌ Symlink de checkpoints NÃO EXISTE")
        issues.append("symlink_missing")

    # 3. Verificar dataset
    data_dir = project_root / config.get("dataset_path", "train/data/f5_dataset")
    if data_dir.exists():
        wavs = list(data_dir.glob("wavs/*.wav"))
        print(f"\n✅ Dataset OK: {len(wavs)} arquivos .wav")
        ok_count += 1
    else:
        print("\n❌ Dataset NÃO ENCONTRADO")
        issues.append("dataset_missing")

    # 4. Verificar symlink de data
    f5_base_dir = config.get("f5tts_base_dir", "/root/.local/lib/python3.11")
    data_symlink = Path(f"{f5_base_dir}/data")
    if data_symlink.is_symlink():
        target = data_symlink.resolve()
        expected = (
            project_root / config.get("dataset_path", "train/data/f5_dataset").rsplit("/", 1)[0]
        )
        if target == expected:
            print("✅ Symlink de data OK")
            ok_count += 1
        else:
            print(f"⚠️  Symlink de data aponta para: {target}")
            print(f"   Esperado: {expected}")
    else:
        print("⚠️  Symlink de data não encontrado")

    # 5. Verificar que scripts/output não existe
    scripts_output = Path("/home/tts-webui-proxmox-passthrough/train/scripts/output")
    if not scripts_output.exists():
        print("\n✅ scripts/output/ removido (correto)")
        ok_count += 1
    else:
        print("\n⚠️  scripts/output/ ainda existe (deveria ter sido removido)")
        issues.append("scripts_output_exists")

    # Resultado
    print(f"\n{'='*70}")
    if not issues:
        print(f"✅ TUDO OK! ({ok_count} verificações passaram)")
        print(f"{'='*70}")
        print("\n🚀 Pronto para treinar:")
        print("   cd /home/tts-webui-proxmox-passthrough/train")
        print("   train")
        return 0
    else:
        print(f"⚠️  {len(issues)} problema(s) encontrado(s)")
        print(f"{'='*70}")
        print("\nProblemas:")
        for issue in issues:
            print(f"  - {issue}")
        print("\n💡 Execute o script de correção:")
        print("   python3 train/scripts/fix_directories.py")
        return 1


if __name__ == "__main__":
    sys.exit(check_structure())
