"""
Quick Start - Teste Mínimo do Pipeline

Este script executa um teste end-to-end do pipeline de treinamento
com um exemplo mínimo (1 vídeo curto).

Uso:
    python -m train.quickstart

Pré-requisitos:
    - ffmpeg instalado
    - pip install -r train/requirements_train.txt
"""
import subprocess
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


def run_command(cmd: str, description: str):
    """Executa comando e mostra progresso"""
    print(f"\n{'='*80}")
    print(f"⏳ {description}")
    print(f"{'='*80}")
    print(f"Comando: {cmd}\n")
    
    result = subprocess.run(cmd, shell=True)
    
    if result.returncode != 0:
        print(f"\n❌ Erro ao executar: {description}")
        sys.exit(1)
    
    print(f"\n✅ Concluído: {description}")


def main():
    """Main function"""
    print("""
╔══════════════════════════════════════════════════════════════╗
║                                                              ║
║   🎙️  F5-TTS QUICKSTART - TESTE MÍNIMO DO PIPELINE 🎙️      ║
║                                                              ║
╚══════════════════════════════════════════════════════════════╝

Este script vai:
  1. Verificar dependências
  2. Executar pipeline completo com exemplo mínimo
  3. Validar que tudo está funcionando

ATENÇÃO: Este é apenas um TESTE com dados mínimos.
Para treinamento real, adicione vídeos em train/data/videos.csv
""")
    
    input("Pressione ENTER para continuar...")
    
    # Verificar dependências
    print("\n🔍 Verificando dependências...")
    
    try:
        import yt_dlp
        print("  ✓ yt-dlp")
    except ImportError:
        print("  ✗ yt-dlp NÃO ENCONTRADO")
        print("    Instale com: pip install yt-dlp")
        sys.exit(1)
    
    try:
        import whisper
        print("  ✓ openai-whisper")
    except ImportError:
        print("  ✗ openai-whisper NÃO ENCONTRADO")
        print("    Instale com: pip install openai-whisper")
        sys.exit(1)
    
    try:
        from f5_tts.model import CFM
        print("  ✓ f5-tts")
    except ImportError:
        print("  ✗ f5-tts NÃO ENCONTRADO")
        print("    Instale com: pip install f5-tts")
        sys.exit(1)
    
    try:
        subprocess.run(['ffmpeg', '-version'], capture_output=True, check=True)
        print("  ✓ ffmpeg")
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("  ✗ ffmpeg NÃO ENCONTRADO")
        print("    Instale conforme seu SO (apt/brew/choco install ffmpeg)")
        sys.exit(1)
    
    print("\n✅ Todas as dependências OK!")
    
    # Verificar se videos.csv tem vídeos
    videos_csv = project_root / "train" / "data" / "videos.csv"
    
    with open(videos_csv, 'r') as f:
        lines = [l.strip() for l in f.readlines() if l.strip() and not l.startswith('id,')]
    
    if not lines:
        print("\n⚠️  ATENÇÃO: train/data/videos.csv está vazio!")
        print("\nPara teste, você precisa adicionar pelo menos 1 vídeo.")
        print("Exemplo:")
        print("  1,https://www.youtube.com/watch?v=XXXXXXXXXXX,speaker1,neutral,pt-br,train,Teste")
        print("\nAdicione um vídeo e execute novamente.")
        sys.exit(1)
    
    print(f"\n📋 {len(lines)} vídeo(s) encontrado(s) em videos.csv")
    
    # Executar pipeline
    print("\n" + "="*80)
    print("INICIANDO PIPELINE COMPLETO")
    print("="*80)
    
    # 1. Download
    run_command(
        "python -m train.scripts.download_youtube",
        "1/6 - Download de áudio do YouTube"
    )
    
    # 2. Segmentação
    run_command(
        "python -m train.scripts.prepare_segments",
        "2/6 - Segmentação de áudio"
    )
    
    # 3. Transcrição
    run_command(
        "python -m train.scripts.transcribe_or_subtitles",
        "3/6 - Transcrição de áudio"
    )
    
    # 4. Metadata
    run_command(
        "python -m train.scripts.build_metadata_csv",
        "4/6 - Construção do metadata.csv"
    )
    
    # 5. Dataset
    run_command(
        "python -m train.scripts.prepare_f5_dataset",
        "5/6 - Preparação do dataset F5-TTS"
    )
    
    # 6. Mostrar resumo (não treinar de verdade em quickstart)
    print("\n" + "="*80)
    print("✅ PIPELINE COMPLETO EXECUTADO COM SUCESSO!")
    print("="*80)
    print("\nDataset preparado em: train/data/f5_dataset/")
    print("\nPara iniciar o treinamento:")
    print("  python -m train.run_training")
    print("\nOu edite train/config/train_config.yaml primeiro para ajustar hiperparâmetros.")
    print("\n" + "="*80)


if __name__ == "__main__":
    main()
