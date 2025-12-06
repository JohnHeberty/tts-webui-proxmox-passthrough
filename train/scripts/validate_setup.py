#!/usr/bin/env python3
"""
Script de validação pré-treinamento
Verifica se tudo está configurado corretamente antes de iniciar o fine-tuning
"""
import os
from pathlib import Path
import sys

from dotenv import load_dotenv


# Add project root to path if needed
project_root = Path(__file__).parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from train.utils.env_loader import get_training_config


def check_emoji(condition, success_msg, fail_msg):
    """Helper para print com emoji"""
    if condition:
        print(f"  ✅ {success_msg}")
        return True
    else:
        print(f"  ❌ {fail_msg}")
        return False


def main():
    print("\n" + "=" * 80)
    print("🔍 VALIDAÇÃO PRÉ-TREINAMENTO F5-TTS")
    print("=" * 80 + "\n")

    # Detectar se está sendo executado de scripts/ ou de train/
    script_path = Path(__file__).resolve()
    if script_path.parent.name == "scripts":
        train_root = script_path.parent.parent
    else:
        train_root = script_path.parent

    project_root = train_root.parent

    print(f"📍 Diretório base: {train_root}\n")

    all_ok = True

    # 1. Verificar .env
    print("📋 1. Arquivo de Configuração (.env)")
    env_file = train_root / ".env"
    all_ok &= check_emoji(
        env_file.exists(), ".env encontrado", ".env não encontrado! Copie de .env.example"
    )

    if env_file.exists():
        load_dotenv(env_file)

        # Verificar variáveis essenciais
        essential_vars = [
            "DATASET_NAME",
            "DATASET_PATH",
            "PRETRAIN_MODEL_PATH",
            "BATCH_SIZE",
            "LEARNING_RATE",
        ]

        for var in essential_vars:
            all_ok &= check_emoji(
                os.getenv(var) is not None, f"{var} configurado", f"{var} não configurado!"
            )

    print()

    # 2. Verificar Dataset
    print("📁 2. Dataset")
    config = get_training_config()
    dataset_path = Path(config.get("dataset_path", train_root / "data" / "f5_dataset"))

    all_ok &= check_emoji(
        dataset_path.exists(),
        f"Diretório encontrado: {dataset_path}",
        f"Diretório não encontrado: {dataset_path}",
    )

    if dataset_path.exists():
        # Metadata
        metadata = dataset_path / "metadata.csv"
        all_ok &= check_emoji(
            metadata.exists(),
            f"metadata.csv encontrado ({metadata.stat().st_size / 1024:.1f} KB)",
            "metadata.csv não encontrado!",
        )

        # Duration
        duration = dataset_path / "duration.json"
        all_ok &= check_emoji(
            duration.exists(), "duration.json encontrado", "duration.json não encontrado!"
        )

        # Vocab
        vocab = dataset_path / "vocab.txt"
        if vocab.exists():
            with open(vocab) as f:
                vocab_size = len(f.readlines())
            all_ok &= check_emoji(True, f"vocab.txt encontrado ({vocab_size} tokens)", "")
        else:
            all_ok &= check_emoji(False, "", "vocab.txt não encontrado!")

        # Wavs
        wavs_dir = dataset_path / "wavs"
        if wavs_dir.exists():
            wav_files = list(wavs_dir.glob("*.wav"))
            all_ok &= check_emoji(
                len(wav_files) > 0,
                f"{len(wav_files)} arquivos .wav encontrados",
                "Nenhum arquivo .wav encontrado!",
            )
        else:
            all_ok &= check_emoji(False, "", "Diretório wavs/ não encontrado!")

    print()

    # 3. Verificar Modelo Pré-treinado
    print("🤖 3. Modelo Pré-treinado")

    pretrain_path = os.getenv(
        "PRETRAIN_MODEL_PATH", "train/pretrained/F5-TTS-pt-br/pt-br/model_200000_fixed.pt"
    )
    if not Path(pretrain_path).is_absolute():
        pretrain_path = project_root / pretrain_path
    else:
        pretrain_path = Path(pretrain_path)

    if pretrain_path.exists():
        size_mb = pretrain_path.stat().st_size / (1024 * 1024)
        all_ok &= check_emoji(
            True, f"Modelo encontrado: {pretrain_path.name} ({size_mb:.1f} MB)", ""
        )

        # Verificar estrutura do modelo
        try:
            import torch

            checkpoint = torch.load(pretrain_path, map_location="cpu", weights_only=False)

            all_ok &= check_emoji(
                "model" in checkpoint or "model_state_dict" in checkpoint,
                "model_state_dict presente",
                "model_state_dict não encontrado!",
            )

            all_ok &= check_emoji(
                "ema_model_state_dict" in checkpoint,
                "EMA presente (recomendado)",
                "EMA não presente (não é crítico)",
            )

            if "iteration" in checkpoint:
                print(f"  ℹ️  Iteração do checkpoint: {checkpoint['iteration']}")
            elif "step" in checkpoint:
                print(f"  ℹ️  Step do checkpoint: {checkpoint['step']}")

        except Exception as e:
            all_ok &= check_emoji(False, "", f"Erro ao carregar modelo: {e}")
    else:
        all_ok &= check_emoji(False, "", f"Modelo não encontrado: {pretrain_path}")
        print("     Execute: python3 -m train.scripts.check_model <caminho_modelo> --fix")

    print()

    # 4. Verificar Dependências
    print("📦 4. Dependências Python")

    dependencies = [
        ("torch", "PyTorch"),
        ("torchaudio", "TorchAudio"),
        ("accelerate", "Accelerate (multi-GPU)"),
        ("f5_tts", "F5-TTS"),
        ("tensorboard", "TensorBoard"),
    ]

    for module, name in dependencies:
        try:
            __import__(module)
            all_ok &= check_emoji(True, f"{name} instalado", "")
        except ImportError:
            all_ok &= check_emoji(False, "", f"{name} não instalado! Execute: pip install {module}")

    print()

    # 5. Verificar GPU
    print("🎮 5. Hardware")

    try:
        import torch

        cuda_available = torch.cuda.is_available()
        all_ok &= check_emoji(
            cuda_available,
            f"CUDA disponível (GPU: {torch.cuda.get_device_name(0) if cuda_available else 'N/A'})",
            "CUDA não disponível! Treinamento será lento na CPU",
        )

        if cuda_available:
            gpu_memory = torch.cuda.get_device_properties(0).total_memory / (1024**3)
            print(f"  ℹ️  VRAM disponível: {gpu_memory:.1f} GB")

            batch_size = int(os.getenv("BATCH_SIZE", 4))
            if gpu_memory < 12 and batch_size > 2:
                print(f"  ⚠️  Recomendação: Reduza BATCH_SIZE para 1 ou 2 (atual: {batch_size})")
    except:
        all_ok &= check_emoji(False, "", "Erro ao verificar GPU")

    print()

    # 6. Verificar Diretórios de Saída
    print("💾 6. Diretórios de Saída")

    output_dir = Path(config.get("output_dir", train_root / "output" / "ptbr_finetuned"))
    output_dir.mkdir(parents=True, exist_ok=True)
    all_ok &= check_emoji(
        output_dir.exists(),
        f"Diretório de output criado: {output_dir.relative_to(project_root)}",
        "",
    )

    runs_dir = Path(config.get("tensorboard_dir", train_root / "runs"))
    runs_dir.mkdir(parents=True, exist_ok=True)
    all_ok &= check_emoji(
        runs_dir.exists(), f"Diretório de logs criado: {runs_dir.relative_to(project_root)}", ""
    )

    print()
    print("=" * 80)

    if all_ok:
        print("✅ VALIDAÇÃO COMPLETA - Sistema pronto para treinamento!")
        print("\nPara iniciar o treinamento:")
        print("  cd /home/tts-webui-proxmox-passthrough")
        print("  python3 -m train.run_training")
    else:
        print("❌ VALIDAÇÃO FALHOU - Corrija os erros acima antes de treinar")
        print("\nConsulte: train/README_QUICKSTART.md para mais informações")

    print("=" * 80 + "\n")

    return 0 if all_ok else 1


if __name__ == "__main__":
    sys.exit(main())
