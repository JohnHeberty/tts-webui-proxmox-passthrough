#!/usr/bin/env python3
"""
Corrige chaves do modelo pt-BR para compatibilidade com F5-TTS
Remove sufixo _state_dict das chaves principais
"""
import torch
from pathlib import Path

def fix_model_keys(input_path, output_path):
    """Renomeia chaves principais para remover _state_dict"""
    print(f"📥 Carregando: {input_path}")
    checkpoint = torch.load(input_path, map_location='cpu', weights_only=False)
    
    print(f"\n🔑 Chaves originais:")
    for key in checkpoint.keys():
        print(f"  - {key}")
    
    # Criar novo checkpoint com chaves corretas
    new_checkpoint = {}
    
    for key, value in checkpoint.items():
        # Remover _state_dict do final
        if key.endswith('_state_dict'):
            new_key = key.replace('_state_dict', '')
        else:
            new_key = key
        
        # Renomear 'step' para 'iteration'
        if new_key == 'step':
            new_key = 'iteration'
        
        new_checkpoint[new_key] = value
        print(f"  {key} → {new_key}")
    
    print(f"\n💾 Salvando: {output_path}")
    torch.save(new_checkpoint, output_path)
    
    print("\n✅ Modelo corrigido!")
    print(f"\n🔑 Novas chaves:")
    for key in new_checkpoint.keys():
        print(f"  - {key}")

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) < 2:
        print("Uso: python fix_model_keys.py <caminho_modelo_pt>")
        sys.exit(1)
    
    input_model = Path(sys.argv[1])
    
    if not input_model.exists():
        print(f"❌ Arquivo não encontrado: {input_model}")
        sys.exit(1)
    
    # Nome do arquivo de saída
    output_model = input_model.parent / f"{input_model.stem}_fixed_v2.pt"
    
    fix_model_keys(input_model, output_model)
