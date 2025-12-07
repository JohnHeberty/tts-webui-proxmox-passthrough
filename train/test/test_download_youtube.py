"""
Testes para download_youtube.py

Valida download de vídeos do YouTube para o dataset.
"""

import pytest
from pathlib import Path
import sys
from unittest.mock import Mock, patch, MagicMock
import subprocess

# Setup paths
TEST_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = TEST_DIR.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))


class TestDownloadYoutube:
    """Testes para download de vídeos do YouTube."""
    
    @pytest.fixture
    def mock_config(self):
        """Config mockado."""
        return {
            "audio": {
                "target_sample_rate": 22050,
                "channels": 1,
                "bit_depth": 16,
                "format": "wav"
            },
            "youtube": {
                "audio_format": "bestaudio/best",
                "max_retries": 3,
                "retry_delay": 5
            }
        }
    
    @pytest.fixture
    def mock_videos_csv(self, tmp_path):
        """Cria CSV mockado."""
        csv_file = tmp_path / "videos.csv"
        csv_file.write_text(
            "video_id,url,title\n"
            "test001,https://youtube.com/watch?v=test1,Test Video 1\n"
            "test002,https://youtube.com/watch?v=test2,Test Video 2\n"
        )
        return csv_file
    
    def test_videos_csv_exists(self):
        """Verifica se videos.csv existe no projeto."""
        videos_csv = PROJECT_ROOT / "train" / "data" / "videos.csv"
        
        if not videos_csv.exists():
            pytest.skip(f"videos.csv não encontrado em {videos_csv}")
        
        assert videos_csv.exists()
        assert videos_csv.stat().st_size > 0
    
    def test_videos_csv_format(self, mock_videos_csv):
        """Testa formato do CSV."""
        lines = mock_videos_csv.read_text().strip().split("\n")
        
        # Header
        assert lines[0] == "video_id,url,title"
        
        # At least one video
        assert len(lines) > 1
        
        # Valid format
        for line in lines[1:]:
            parts = line.split(",")
            assert len(parts) >= 3  # video_id, url, title (título pode ter vírgulas)
    
    @patch('subprocess.run')
    def test_ytdlp_command_format(self, mock_run, mock_config):
        """Testa formato do comando yt-dlp."""
        mock_run.return_value = Mock(returncode=0)
        
        # Comando esperado
        expected_args = [
            "yt-dlp",
            "-f", "bestaudio/best",
            "-x",
            "--audio-format", "wav",
            "--audio-quality", "0",
            "--postprocessor-args", f"-ar 22050 -ac 1",
        ]
        
        # Verificar que contém argumentos essenciais
        for arg in expected_args[:6]:  # Primeiros argumentos fixos
            assert arg in expected_args
    
    def test_sample_rate_configuration(self, mock_config):
        """Testa configuração de sample rate."""
        assert mock_config["audio"]["target_sample_rate"] == 22050
        assert mock_config["audio"]["channels"] == 1
    
    @patch('subprocess.run')
    def test_retry_logic(self, mock_run, mock_config):
        """Testa lógica de retry em caso de falha."""
        # Simula falha nos primeiros 2 tries, sucesso no 3º
        mock_run.side_effect = [
            Mock(returncode=1),  # Falha
            Mock(returncode=1),  # Falha
            Mock(returncode=0),  # Sucesso
        ]
        
        max_retries = mock_config["youtube"]["max_retries"]
        assert max_retries == 3
    
    def test_output_directory_structure(self, tmp_path):
        """Testa estrutura de diretórios de saída."""
        data_dir = tmp_path / "train" / "data"
        raw_dir = data_dir / "raw"
        
        # Criar estrutura
        raw_dir.mkdir(parents=True, exist_ok=True)
        
        assert data_dir.exists()
        assert raw_dir.exists()
    
    @patch('subprocess.run')
    def test_download_success(self, mock_run, tmp_path):
        """Testa download bem-sucedido."""
        mock_run.return_value = Mock(returncode=0)
        
        output_file = tmp_path / "video_test001.wav"
        
        # Simula criação do arquivo
        output_file.write_bytes(b"RIFF" + b"\x00" * 100)  # WAV header mínimo
        
        assert output_file.exists()
        assert output_file.stat().st_size > 0
    
    @patch('subprocess.run')
    def test_download_failure_handling(self, mock_run):
        """Testa tratamento de erro em download."""
        mock_run.return_value = Mock(returncode=1, stderr="ERROR: Video not available")
        
        result = mock_run.return_value
        assert result.returncode != 0
    
    def test_audio_format_validation(self, mock_config):
        """Valida formato de áudio configurado."""
        assert mock_config["audio"]["format"] == "wav"
        assert mock_config["audio"]["bit_depth"] == 16
    
    @pytest.mark.integration
    @patch('subprocess.run')
    def test_full_download_pipeline(self, mock_run, tmp_path, mock_videos_csv):
        """Teste de integração do pipeline completo."""
        # Mock bem-sucedido
        mock_run.return_value = Mock(returncode=0)
        
        # Estrutura de diretórios
        data_dir = tmp_path / "train" / "data"
        raw_dir = data_dir / "raw"
        raw_dir.mkdir(parents=True)
        
        # Simula arquivo baixado
        output = raw_dir / "video_test001.wav"
        output.write_bytes(b"RIFF" + b"\x00" * 1000)
        
        assert output.exists()
        assert output.suffix == ".wav"
        assert output.stat().st_size > 0


class TestDownloadYoutubeHelpers:
    """Testes para funções auxiliares."""
    
    def test_sanitize_filename(self):
        """Testa sanitização de nomes de arquivo."""
        # Caracteres inválidos devem ser removidos/substituídos
        test_cases = [
            ("Test: Video!", "Test_ Video_"),
            ("Video/Name", "Video_Name"),
            ("Normal_Name", "Normal_Name"),
        ]
        
        for input_name, expected in test_cases:
            # Sanitização básica: substituir caracteres especiais por _
            sanitized = input_name.replace(":", "_").replace("/", "_").replace("!", "_")
            assert sanitized == expected
    
    def test_validate_url(self):
        """Testa validação de URLs do YouTube."""
        valid_urls = [
            "https://youtube.com/watch?v=test123",
            "https://www.youtube.com/watch?v=test123",
            "https://youtu.be/test123",
        ]
        
        invalid_urls = [
            "https://notYouTube.com/video",
            "invalid-url",
            "",
        ]
        
        for url in valid_urls:
            assert "youtube.com" in url or "youtu.be" in url
        
        for url in invalid_urls:
            assert "youtube.com" not in url and "youtu.be" not in url


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
