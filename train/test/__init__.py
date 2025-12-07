"""
Testes para Voice Cloning - XTTS-v2

Este pacote contém testes automatizados para validar o pipeline de voice cloning:
- Preparação de áudio
- Transcrição com Whisper
- Clonagem de voz com XTTS-v2
- Métricas de qualidade

Executar todos os testes:
    pytest train/test/ -v

Executar testes específicos:
    pytest train/test/test_pytest.py::TestTranscription -v
    pytest train/test/ -k "transcription" -v

Ver logs detalhados:
    pytest train/test/ -v -s

Ignorar testes lentos:
    pytest train/test/ -v -m "not slow"
"""

__version__ = "1.0.0"
