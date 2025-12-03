"""
Download simplificado de áudios do YouTube
"""
import csv
import os
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

try:
    import yt_dlp
except ImportError:
    print("❌ yt-dlp não encontrado. Instale com: pip install yt-dlp")
    sys.exit(1)


def main():
    # Diretórios
    videos_csv = project_root / "train" / "data" / "videos.csv"
    output_dir = project_root / "train" / "data" / "raw"
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Carregar vídeos do CSV (pula linhas de comentário)
    videos = []
    with open(videos_csv, 'r', encoding='utf-8') as f:
        # Pular linhas de comentário
        lines = [line for line in f if line.strip() and not line.strip().startswith('#')]
        
        if not lines:
            print(f"❌ Nenhum vídeo encontrado em {videos_csv}")
            return
        
        # Primeira linha é o cabeçalho
        import io
        csv_content = '\n'.join(lines)
        reader = csv.DictReader(io.StringIO(csv_content))
        
        for row in reader:
            if row.get('youtube_url', '').strip():
                videos.append(row)
    
    print(f"\n📥 Iniciando download de {len(videos)} vídeos...\n")
    
    success = 0
    skipped = 0
    failed = 0
    
    for i, video in enumerate(videos, 1):
        video_id = video['id']
        url = video['youtube_url']
        
        output_filename = f"video_{video_id.zfill(5)}.wav"
        output_path = output_dir / output_filename
        
        # Skip se já existe
        if output_path.exists():
            print(f"[{i}/{len(videos)}] ✓ {output_filename} já existe (pulando)")
            skipped += 1
            continue
        
        # yt-dlp options
        ydl_opts = {
            'format': 'bestaudio/best',
            'outtmpl': str(output_dir / f'temp_{video_id}.%(ext)s'),
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'wav',
                'preferredquality': '0',
            }],
            'postprocessor_args': [
                '-ar', '24000',  # 24kHz
                '-ac', '1',      # mono
            ],
            'quiet': True,
            'no_warnings': True,
        }
        
        try:
            print(f"[{i}/{len(videos)}] ⬇️  Baixando: {url}")
            
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info_dict = ydl.extract_info(url, download=True)
                title = info_dict.get('title', 'Unknown')
                duration = info_dict.get('duration', 0)
                
                # Encontrar arquivo baixado
                temp_files = list(output_dir.glob(f'temp_{video_id}.*'))
                if temp_files:
                    temp_file = temp_files[0]
                    temp_file.rename(output_path)
                    
                    print(f"✅ {output_filename} baixado com sucesso!")
                    print(f"   Título: {title}")
                    print(f"   Duração: {duration:.1f}s\n")
                    success += 1
                else:
                    print(f"❌ Erro: arquivo temporário não encontrado\n")
                    failed += 1
                    
        except Exception as e:
            print(f"❌ Erro ao baixar {url}: {e}\n")
            failed += 1
            continue
    
    print("\n" + "="*60)
    print(f"✅ Sucessos: {success}")
    print(f"⏭️  Pulados: {skipped}")
    print(f"❌ Falhas: {failed}")
    print(f"📁 Arquivos salvos em: {output_dir}")
    print("="*60)


if __name__ == "__main__":
    main()
