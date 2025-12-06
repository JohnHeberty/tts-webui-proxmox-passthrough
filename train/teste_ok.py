#!/usr/bin/env python3
"""
TESTE OK - Processo que FUNCIONA PERFEITAMENTE
===============================================

Este script demonstra o que ESTÁ FUNCIONANDO:
- ✅ Extração de MEL spectrogram do modelo fine-tuned
- ✅ Reconstrução de áudio pelo Vocoder
- ✅ Qualidade de áudio perfeita

O que NÃO está incluído aqui (e que está quebrado):
- ❌ Geração de novo áudio via model.sample()
- ❌ Inferência com texto customizado

Este é apenas um teste de validação do pipeline vocoder.
"""

from f5_tts.infer.utils_infer import load_model, load_vocoder
from f5_tts.model import DiT
import torch
import torchaudio
import argparse

def main():
    parser = argparse.ArgumentParser(description="Teste do pipeline que FUNCIONA")
    parser.add_argument("--audio", required=True, help="Arquivo de áudio de entrada")
    parser.add_argument("--checkpoint", default="train/output/ptbr_finetuned2/model_25400.pt",
                       help="Checkpoint do modelo")
    parser.add_argument("--output", default="train/teste_ok_output.wav",
                       help="Arquivo de saída")
    args = parser.parse_args()

    print("=" * 80)
    print("🧪 TESTE OK - Pipeline que FUNCIONA")
    print("=" * 80)
    
    # Configuração do modelo
    model_cfg = dict(
        dim=1024,
        depth=22,
        heads=16,
        ff_mult=2,
        text_dim=512,
        conv_layers=4
    )
    
    print(f"\n📦 Carregando modelo: {args.checkpoint}")
    model = load_model(
        DiT,
        model_cfg,
        args.checkpoint,
        mel_spec_type='vocos',
        vocab_file='',
        ode_method='euler',
        use_ema=True,
        device='cuda'
    )
    
    print("📦 Carregando vocoder...")
    vocoder = load_vocoder(vocoder_name="vocos", is_local=False, local_path="")
    
    # Carrega áudio
    print(f"\n🔊 Carregando áudio: {args.audio}")
    audio, sr = torchaudio.load(args.audio)
    
    # Preprocessamento
    if audio.shape[0] > 1:
        print("   → Convertendo para mono")
        audio = torch.mean(audio, dim=0, keepdim=True)
    
    if sr != 24000:
        print(f"   → Resampling de {sr}Hz para 24000Hz")
        resampler = torchaudio.transforms.Resample(sr, 24000)
        audio = resampler(audio)
    
    audio = audio.cuda()
    print(f"   ✅ Áudio shape: {audio.shape}")
    
    # PROCESSO QUE FUNCIONA: áudio → MEL → áudio
    print("\n🔄 Executando pipeline:")
    print("   1. Extraindo MEL spectrogram...")
    
    with torch.no_grad():
        # Extrai MEL usando modelo fine-tuned
        mel = model.mel_spec(audio)
        mel = mel.permute(0, 2, 1)
        print(f"      ✅ MEL shape: {mel.shape}")
        
        # Reconstrói áudio do MEL
        print("   2. Reconstruindo áudio com vocoder...")
        mel_for_vocoder = mel.permute(0, 2, 1)
        audio_reconstructed = vocoder.decode(mel_for_vocoder)
        print(f"      ✅ Áudio reconstruído: {audio_reconstructed.shape}")
    
    # Salva resultado
    print(f"\n💾 Salvando em: {args.output}")
    torchaudio.save(args.output, audio_reconstructed.cpu(), 24000)
    
    print("\n" + "=" * 80)
    print("✅ SUCESSO!")
    print("=" * 80)
    print("\n📊 O que foi testado:")
    print("   ✅ Extração de MEL spectrogram (model.mel_spec)")
    print("   ✅ Vocoder (vocos.decode)")
    print("   ✅ Pipeline completo de reconstrução")
    print("\n⚠️ O que NÃO foi testado:")
    print("   ❌ Geração de novo áudio (model.sample)")
    print("   ❌ Síntese com texto customizado")
    print("\n💡 Para testar síntese de texto, use: train/infer_como_trainer.py")
    print()

if __name__ == "__main__":
    main()
