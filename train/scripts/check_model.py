#!/usr/bin/env python3
"""
Script para verificar e corrigir modelos .pt do F5-TTS
Resolve problemas comuns com EMA e estrutura de checkpoints
"""
import argparse
from pathlib import Path

import torch


def check_model(model_path):
    """Verifica estrutura do modelo"""
    print(f"\n📁 Verificando: {model_path}")
    print("=" * 80)

    try:
        checkpoint = torch.load(model_path, map_location="cpu")

        print(f"\n🔍 Tipo: {type(checkpoint)}")

        if isinstance(checkpoint, dict):
            print("\n🔑 Chaves disponíveis:")
            for key in checkpoint.keys():
                if isinstance(checkpoint[key], dict):
                    num_params = len(checkpoint[key])
                    print(f"  - {key}: {num_params} items")
                elif isinstance(checkpoint[key], torch.Tensor):
                    print(f"  - {key}: Tensor {tuple(checkpoint[key].shape)}")
                else:
                    print(f"  - {key}: {type(checkpoint[key])}")

            # Verificar modelo principal
            if "model" in checkpoint:
                model_dict = checkpoint["model"]
                total_params = sum(
                    p.numel() for p in model_dict.values() if isinstance(p, torch.Tensor)
                )
                print(f"\n✅ Modelo principal: {total_params / 1e6:.1f}M parâmetros")
            elif "state_dict" in checkpoint:
                model_dict = checkpoint["state_dict"]
                total_params = sum(
                    p.numel() for p in model_dict.values() if isinstance(p, torch.Tensor)
                )
                print(f"\n✅ State dict: {total_params / 1e6:.1f}M parâmetros")
            else:
                # Checkpoint é o próprio state_dict
                total_params = sum(
                    p.numel() for p in checkpoint.values() if isinstance(p, torch.Tensor)
                )
                print(f"\n✅ State dict direto: {total_params / 1e6:.1f}M parâmetros")

            # Verificar EMA
            if "ema_model_state_dict" in checkpoint:
                ema_dict = checkpoint["ema_model_state_dict"]
                ema_params = sum(
                    p.numel() for p in ema_dict.values() if isinstance(p, torch.Tensor)
                )
                print(f"✅ EMA disponível: {ema_params / 1e6:.1f}M parâmetros")
            else:
                print("⚠️  EMA não disponível")

            # Verificar otimizador
            if "optimizer" in checkpoint:
                print("✅ Optimizer state disponível")
            else:
                print("ℹ️  Optimizer state não disponível")

            # Verificar iteração/epoch
            if "iteration" in checkpoint:
                print(f"📊 Iteração: {checkpoint['iteration']}")
            if "epoch" in checkpoint:
                print(f"📊 Epoch: {checkpoint['epoch']}")

        else:
            print("⚠️  Checkpoint não é um dicionário")

        print("\n" + "=" * 80)
        return checkpoint

    except Exception as e:
        print(f"\n❌ Erro ao carregar modelo: {e}")
        import traceback

        traceback.print_exc()
        return None


def fix_model(checkpoint, output_path, add_ema=False):
    """Corrige estrutura do modelo"""
    print("\n🔧 Corrigindo modelo...")

    try:
        # Extrair state_dict principal
        if "model" in checkpoint:
            model_state = checkpoint["model"]
        elif "model_state_dict" in checkpoint:
            model_state = checkpoint["model_state_dict"]
        elif "state_dict" in checkpoint:
            model_state = checkpoint["state_dict"]
        elif isinstance(checkpoint, dict) and any(
            k.startswith("model.") or k.startswith("transformer.") for k in checkpoint.keys()
        ):
            model_state = checkpoint
        else:
            print("❌ Não foi possível identificar state_dict")
            print("   Chaves disponíveis:", list(checkpoint.keys()))
            return False

        # Criar nova estrutura
        new_checkpoint = {
            "model": model_state,
            "iteration": checkpoint.get("iteration", checkpoint.get("step", 0)),
        }

        # Copiar EMA se existir
        if "ema_model_state_dict" in checkpoint:
            new_checkpoint["ema_model_state_dict"] = checkpoint["ema_model_state_dict"]
            print("✅ EMA copiado do checkpoint original")
        elif add_ema:
            # Criar EMA como cópia do modelo (não ideal, mas funciona)
            new_checkpoint["ema_model_state_dict"] = model_state.copy()
            print("⚠️  EMA criado como cópia do modelo (não é ideal)")

        # Copiar optimizer se existir
        if "optimizer" in checkpoint:
            new_checkpoint["optimizer"] = checkpoint["optimizer"]
        elif "optimizer_state_dict" in checkpoint:
            new_checkpoint["optimizer"] = checkpoint["optimizer_state_dict"]

        # Copiar scheduler se existir
        if "scheduler" in checkpoint:
            new_checkpoint["scheduler"] = checkpoint["scheduler"]
        elif "scheduler_state_dict" in checkpoint:
            new_checkpoint["scheduler"] = checkpoint["scheduler_state_dict"]

        # Salvar
        torch.save(new_checkpoint, output_path)
        print(f"✅ Modelo corrigido salvo em: {output_path}")

        # Verificar arquivo salvo
        print("\n🔍 Verificando arquivo salvo...")
        check_model(output_path)

        return True

    except Exception as e:
        print(f"❌ Erro ao corrigir modelo: {e}")
        import traceback

        traceback.print_exc()
        return False


def convert_to_safetensors(checkpoint, output_path):
    """Converte para SafeTensors (mais seguro)"""
    print("\n🔧 Convertendo para SafeTensors...")

    try:
        from safetensors.torch import save_file

        # Extrair state_dict
        if "model" in checkpoint:
            model_state = checkpoint["model"]
        elif "state_dict" in checkpoint:
            model_state = checkpoint["state_dict"]
        else:
            model_state = checkpoint

        # Salvar
        save_file(model_state, output_path)
        print(f"✅ Modelo salvo como SafeTensors: {output_path}")

        return True

    except ImportError:
        print("❌ safetensors não instalado. Instale com: pip install safetensors")
        return False
    except Exception as e:
        print(f"❌ Erro ao converter: {e}")
        import traceback

        traceback.print_exc()
        return False


def main():
    parser = argparse.ArgumentParser(description="Verificar e corrigir modelos F5-TTS .pt")
    parser.add_argument("model_path", type=str, help="Caminho do modelo .pt")
    parser.add_argument("--fix", action="store_true", help="Corrigir estrutura do modelo")
    parser.add_argument("--add-ema", action="store_true", help="Adicionar EMA se não existir")
    parser.add_argument("--output", type=str, help="Caminho de saída (padrão: {model}_fixed.pt)")
    parser.add_argument("--safetensors", action="store_true", help="Converter para SafeTensors")

    args = parser.parse_args()

    model_path = Path(args.model_path)

    if not model_path.exists():
        print(f"❌ Arquivo não encontrado: {model_path}")
        return

    # Verificar modelo
    checkpoint = check_model(model_path)

    if checkpoint is None:
        return

    # Corrigir se solicitado
    if args.fix:
        if not args.output:
            output_path = model_path.parent / f"{model_path.stem}_fixed.pt"
        else:
            output_path = Path(args.output)

        success = fix_model(checkpoint, output_path, add_ema=args.add_ema)

        if success and args.safetensors:
            st_path = output_path.with_suffix(".safetensors")
            convert_to_safetensors(checkpoint, st_path)

    elif args.safetensors:
        if not args.output:
            output_path = model_path.with_suffix(".safetensors")
        else:
            output_path = Path(args.output)

        convert_to_safetensors(checkpoint, output_path)


if __name__ == "__main__":
    main()
