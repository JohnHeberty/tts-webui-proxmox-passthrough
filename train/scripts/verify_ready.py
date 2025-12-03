#!/usr/bin/env python3
"""
Teste de verificação final antes de iniciar treinamento
Verifica todos os componentes críticos
"""
import sys
from pathlib import Path
import torch

# Cores para terminal
GREEN = '\033[92m'
RED = '\033[91m'
YELLOW = '\033[93m'
BLUE = '\033[94m'
RESET = '\033[0m'

def check(condition, message, error_msg=""):
    """Helper para verificação"""
    if condition:
        print(f"{GREEN}✅{RESET} {message}")
        return True
    else:
        print(f"{RED}❌{RESET} {message}")
        if error_msg:
            print(f"   {error_msg}")
        return False

def main():
    print(f"\n{BLUE}{'='*70}{RESET}")
    print(f"{BLUE}VERIFICAÇÃO PRÉ-TREINAMENTO F5-TTS{RESET}")
    print(f"{BLUE}{'='*70}{RESET}\n")
    
    all_ok = True
    
    # 1. Dataset
    print(f"{YELLOW}📁 Dataset{RESET}")
    dataset_path = Path("/home/tts-webui-proxmox-passthrough/train/data/f5_dataset")
    wavs_dir = dataset_path / "wavs"
    metadata_file = dataset_path / "metadata.csv"
    
    all_ok &= check(dataset_path.exists(), "Diretório dataset existe")
    all_ok &= check(wavs_dir.exists(), "Diretório wavs/ existe")
    all_ok &= check(metadata_file.exists(), "Arquivo metadata.csv existe")
    
    if wavs_dir.exists():
        wav_files = list(wavs_dir.glob("*.wav"))
        all_ok &= check(len(wav_files) > 0, f"Arquivos .wav encontrados: {len(wav_files)}")
    
    # Verificar symlink pinyin
    pinyin_dir = dataset_path.parent / "f5_dataset_pinyin"
    if pinyin_dir.exists():
        is_symlink = pinyin_dir.is_symlink()
        check(is_symlink, "Symlink f5_dataset_pinyin existe")
    else:
        print(f"{YELLOW}⚠️{RESET}  Symlink f5_dataset_pinyin não existe (será criado automaticamente)")
    
    print()
    
    # 2. Checkpoint
    print(f"{YELLOW}💾 Checkpoint{RESET}")
    checkpoint_path = Path("/root/.local/lib/python3.11/ckpts/f5_dataset/model_last.pt")
    
    all_ok &= check(checkpoint_path.exists(), "Checkpoint encontrado")
    
    if checkpoint_path.exists():
        size_gb = checkpoint_path.stat().st_size / (1024**3)
        check(size_gb > 0.1, f"Tamanho do checkpoint: {size_gb:.2f} GB")
        
        # Verificar estrutura
        try:
            print(f"   {BLUE}⏳{RESET} Validando estrutura do checkpoint...")
            ckpt = torch.load(checkpoint_path, map_location='cpu', weights_only=False)
            
            all_ok &= check('ema_model_state_dict' in ckpt, "Campo ema_model_state_dict presente")
            all_ok &= check('model_state_dict' in ckpt, "Campo model_state_dict presente")
            all_ok &= check('update' in ckpt, f"Campo update presente (valor: {ckpt.get('update', 'N/A')})")
            
            # Verificar EMA
            if 'ema_model_state_dict' in ckpt:
                ema = ckpt['ema_model_state_dict']
                has_prefix = any(k.startswith('ema_model.') for k in ema.keys())
                all_ok &= check(has_prefix, "Keys EMA com prefixo correto")
            
            print(f"{GREEN}   ✅ Checkpoint compatível com F5-TTS!{RESET}")
            
        except Exception as e:
            all_ok = False
            print(f"{RED}   ❌ Erro ao carregar checkpoint: {e}{RESET}")
    
    print()
    
    # 3. Configuração
    print(f"{YELLOW}⚙️  Configuração{RESET}")
    env_file = Path("/home/tts-webui-proxmox-passthrough/train/.env")
    
    all_ok &= check(env_file.exists(), "Arquivo .env existe")
    
    if env_file.exists():
        with open(env_file) as f:
            content = f.read()
            all_ok &= check('PRETRAIN_MODEL_PATH=ckpts/f5_dataset/model_last.pt' in content, 
                          "PRETRAIN_MODEL_PATH configurado corretamente")
            all_ok &= check('USE_FINETUNE_FLAG=true' in content,
                          "USE_FINETUNE_FLAG=true")
    
    print()
    
    # 4. GPU
    print(f"{YELLOW}🎮 GPU{RESET}")
    cuda_available = torch.cuda.is_available()
    all_ok &= check(cuda_available, "CUDA disponível")
    
    if cuda_available:
        gpu_name = torch.cuda.get_device_name(0)
        check(True, f"GPU: {gpu_name}")
        
        vram_gb = torch.cuda.get_device_properties(0).total_memory / (1024**3)
        check(vram_gb > 10, f"VRAM: {vram_gb:.1f} GB")
    
    print()
    
    # 5. F5-TTS
    print(f"{YELLOW}📦 F5-TTS{RESET}")
    try:
        import f5_tts
        check(True, "Módulo f5_tts instalado")
        
        from f5_tts.train.finetune_cli import main as finetune_main
        check(True, "finetune_cli importável")
        
    except ImportError as e:
        all_ok = False
        check(False, "F5-TTS não instalado corretamente", str(e))
    
    print()
    
    # Resultado Final
    print(f"{BLUE}{'='*70}{RESET}")
    if all_ok:
        print(f"{GREEN}✅ TODOS OS CHECKS PASSARAM - PRONTO PARA TREINAR!{RESET}")
        print(f"{BLUE}{'='*70}{RESET}\n")
        
        print(f"{GREEN}Para iniciar o treinamento:{RESET}")
        print(f"  cd /home/tts-webui-proxmox-passthrough/train")
        print(f"  train")
        print()
        
        return 0
    else:
        print(f"{RED}❌ ALGUNS CHECKS FALHARAM - CORRIJA OS PROBLEMAS ACIMA{RESET}")
        print(f"{BLUE}{'='*70}{RESET}\n")
        return 1

if __name__ == "__main__":
    sys.exit(main())
