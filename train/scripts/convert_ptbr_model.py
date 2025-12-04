#!/usr/bin/env python3
"""
Script para converter modelo pt-BR do HuggingFace para formato compatível com F5-TTS

O modelo pt-BR usa estrutura diferente do esperado pelo F5-TTS:
- pt-BR: ema_model (dict direto)
- F5-TTS: ema_model_state_dict (dict)

Este script realiza a conversão necessária.
"""

import torch
import sys
from pathlib import Path
import shutil

def convert_ptbr_checkpoint(input_path: Path, output_path: Path) -> bool:
    """
    Converte checkpoint pt-BR para formato F5-TTS
    
    Transformações:
    1. ema_model -> ema_model_state_dict (adiciona wrapper necessário)
    2. step -> update (renomeia para compatibilidade)
    3. Adiciona campos faltantes: initted, step dentro de ema_model_state_dict
    """
    print(f"🔄 Convertendo modelo pt-BR para F5-TTS...")
    print(f"   Origem: {input_path}")
    print(f"   Destino: {output_path}")
    
    try:
        # Carregar checkpoint original
        print("\n📥 Carregando checkpoint original...")
        checkpoint = torch.load(input_path, map_location='cpu', weights_only=False)
        
        print(f"✅ Checkpoint carregado")
        print(f"   Keys originais: {list(checkpoint.keys())}")
        
        # Criar novo checkpoint com estrutura correta
        converted = {}
        
        # 1. Converter ema_model para ema_model_state_dict
        if "ema_model" in checkpoint:
            print("\n🔧 Convertendo EMA model...")
            
            # F5-TTS espera ema_model_state_dict com campos específicos
            ema_dict = checkpoint["ema_model"]
            
            # Adicionar campos necessários se não existirem
            if "initted" not in ema_dict:
                ema_dict["initted"] = torch.tensor(True)
                print("   ➕ Adicionado campo 'initted'")
            
            if "step" not in ema_dict:
                # Usar step do checkpoint principal ou 0
                step_value = checkpoint.get("step", 200000)
                ema_dict["step"] = torch.tensor(step_value)
                print(f"   ➕ Adicionado campo 'step' = {step_value}")
            
            # Verificar se as keys já têm prefixo "ema_model."
            sample_keys = list(ema_dict.keys())[:5]
            has_prefix = any(k.startswith("ema_model.") for k in sample_keys)
            
            if not has_prefix:
                # Adicionar prefixo "ema_model." a todas as keys do transformer
                print("   🔧 Adicionando prefixo 'ema_model.' às keys...")
                new_ema_dict = {}
                for key, value in ema_dict.items():
                    if key in ["initted", "step", "update"]:
                        # Manter campos de controle sem prefixo
                        new_ema_dict[key] = value
                    else:
                        # Adicionar prefixo às keys do modelo
                        new_ema_dict[f"ema_model.{key}"] = value
                ema_dict = new_ema_dict
                print(f"   ✅ Prefixo adicionado ({len(ema_dict)} keys)")
            
            converted["ema_model_state_dict"] = ema_dict
            print(f"   ✅ EMA convertido ({len(ema_dict)} keys)")
        else:
            print("   ⚠️  Campo 'ema_model' não encontrado!")
            return False
        
        # 2. Copiar model_state_dict se existir
        if "model_state_dict" in checkpoint:
            converted["model_state_dict"] = checkpoint["model_state_dict"]
            print(f"✅ Model state dict copiado ({len(checkpoint['model_state_dict'])} keys)")
        else:
            print("   ℹ️  'model_state_dict' não encontrado (opcional)")
        
        # 3. Copiar optimizer_state_dict
        if "optimizer_state_dict" in checkpoint:
            converted["optimizer_state_dict"] = checkpoint["optimizer_state_dict"]
            print("✅ Optimizer state dict copiado")
        
        # 4. Copiar scheduler_state_dict
        if "scheduler_state_dict" in checkpoint:
            converted["scheduler_state_dict"] = checkpoint["scheduler_state_dict"]
            print("✅ Scheduler state dict copiado")
        
        # 5. Converter step -> update
        if "step" in checkpoint:
            # F5-TTS usa "update" que é step / grad_accumulation_steps
            # Por padrão usamos grad_accumulation_steps = 1 para manter o mesmo valor
            converted["update"] = checkpoint["step"]
            print(f"✅ Campo 'update' definido = {checkpoint['step']}")
        elif "update" in checkpoint:
            converted["update"] = checkpoint["update"]
            print(f"✅ Campo 'update' já existe = {checkpoint['update']}")
        else:
            # Fallback para 0
            converted["update"] = 0
            print("⚠️  Campo 'update' não encontrado, usando 0")
        
        # Salvar checkpoint convertido
        print(f"\n💾 Salvando checkpoint convertido...")
        output_path.parent.mkdir(parents=True, exist_ok=True)
        torch.save(converted, output_path)
        
        file_size_gb = output_path.stat().st_size / (1024**3)
        print(f"✅ Checkpoint convertido salvo!")
        print(f"   Tamanho: {file_size_gb:.2f} GB")
        print(f"   Keys finais: {list(converted.keys())}")
        
        # Verificar estrutura final
        print("\n🔍 Verificação final:")
        sample_ema_keys = list(converted["ema_model_state_dict"].keys())[:5]
        print(f"   EMA keys (primeiras 5): {sample_ema_keys}")
        
        return True
        
    except Exception as e:
        print(f"\n❌ Erro durante conversão: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    # Carregar config do .env
    import sys
    from pathlib import Path as PathLib
    project_root = PathLib(__file__).parent.parent.parent
    sys.path.insert(0, str(project_root))
    from train.utils.env_loader import get_training_config
    config = get_training_config()
    
    # Caminhos usando .env
    ckpts_dir = config.get('f5tts_ckpts_dir', '/root/.local/lib/python3.11/ckpts')
    dataset_name = config.get('train_dataset_name', 'f5_dataset')
    input_path = Path(f"{ckpts_dir}/{dataset_name}/pretrained_model_200000.pt")
    output_path = Path(f"{ckpts_dir}/{dataset_name}/model_200000_converted.pt")
    
    if not input_path.exists():
        print(f"❌ Modelo não encontrado: {input_path}")
        print("\nProcurando em locais alternativos...")
        
        # Tentar localização alternativa (PRETRAIN_MODEL_PATH do .env)
        pretrained_path = config.get('pretrained_model_path')
        if pretrained_path:
            alt_path = project_root / pretrained_path
            if alt_path.exists():
                input_path = alt_path
                output_path = alt_path.parent / "model_200000_converted.pt"
                print(f"✅ Encontrado em: {input_path}")
            else:
                print("❌ Modelo pt-BR não encontrado em nenhum local!")
                return 1
        else:
            print("❌ Modelo pt-BR não encontrado em nenhum local!")
            return 1
    
    # Fazer backup do original
    backup_path = input_path.parent / f"{input_path.stem}_backup.pt"
    if not backup_path.exists():
        print(f"\n📦 Criando backup: {backup_path.name}")
        shutil.copy2(input_path, backup_path)
    
    # Converter
    success = convert_ptbr_checkpoint(input_path, output_path)
    
    if success:
        print("\n" + "="*60)
        print("✅ CONVERSÃO CONCLUÍDA COM SUCESSO!")
        print("="*60)
        print(f"\nAgora você pode usar o modelo convertido:")
        print(f"  {output_path}")
        print("\nPara usar no treinamento, atualize o .env:")
        print(f"  PRETRAIN_MODEL_PATH=ckpts/f5_dataset/model_200000_converted.pt")
        return 0
    else:
        print("\n" + "="*60)
        print("❌ CONVERSÃO FALHOU")
        print("="*60)
        return 1


if __name__ == "__main__":
    sys.exit(main())
