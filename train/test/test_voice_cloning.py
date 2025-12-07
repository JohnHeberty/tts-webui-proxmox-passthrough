"""
Teste de Voice Cloning - Validação Completa

PIPELINE CORRETO:
1. Pega áudio original (reference_test.wav)
2. Transcreve com Whisper → salva transcription.txt em results/
3. Clona voz do áudio original + gera novo áudio com a transcrição → salva cloned_output.wav
4. Transcreve o áudio gerado com Whisper → valida se falou a mesma frase

VALIDAÇÃO:
- Se transcrição original == transcrição do áudio gerado → PASSOU
- Áudio gerado deve ter voz clonada + mesmo conteúdo do texto original

Executar:
    pytest train/test/test_voice_cloning.py -v -s
"""

import pytest
from pathlib import Path
import soundfile as sf
import numpy as np
import json
import sys
from difflib import SequenceMatcher

# Setup paths
TEST_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = TEST_DIR.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

# Diretórios
AUDIO_DIR = TEST_DIR / "audio"
RESULTS_DIR = TEST_DIR / "results"
REFERENCE_AUDIO = AUDIO_DIR / "reference_test.wav"


def similarity_ratio(text1: str, text2: str) -> float:
    """Calcula similaridade entre dois textos (0-1)."""
    return SequenceMatcher(None, text1.lower().strip(), text2.lower().strip()).ratio()


class TestVoiceCloning:
    """Teste completo de voice cloning com validação Whisper."""
    
    @pytest.fixture(scope="class")
    def setup_environment(self):
        """Setup inicial."""
        # Criar diretório de resultados
        RESULTS_DIR.mkdir(parents=True, exist_ok=True)
        
        # Aplicar patch PyTorch 2.6
        import torch
        original_load = torch.load
        
        def patched_load(*args, **kwargs):
            if 'weights_only' not in kwargs:
                kwargs['weights_only'] = False
            return original_load(*args, **kwargs)
        
        torch.load = patched_load
        
        # ToS Coqui
        import os
        os.environ['COQUI_TOS_AGREED'] = '1'
        
        yield
    
    def test_1_audio_original_exists(self):
        """Verifica se áudio original existe."""
        assert REFERENCE_AUDIO.exists(), f"Áudio não encontrado: {REFERENCE_AUDIO}"
        
        # Validar formato
        data, sr = sf.read(REFERENCE_AUDIO)
        assert len(data) > 0, "Áudio vazio"
        assert sr > 0, "Sample rate inválido"
        
        print(f"\n✅ Áudio original: {len(data)/sr:.2f}s @ {sr}Hz")
    
    def test_2_transcribe_original(self, setup_environment):
        """Passo 1: Transcreve áudio original com Whisper."""
        import whisper
        
        print(f"\n🎤 Transcrevendo áudio original...")
        
        # Carregar modelo Whisper
        model = whisper.load_model("base")
        
        # Transcrever
        result = model.transcribe(str(REFERENCE_AUDIO), language="pt", fp16=False)
        transcription = result["text"].strip()
        
        assert transcription, "Transcrição vazia"
        assert len(transcription) > 10, "Transcrição muito curta"
        
        # Salvar transcrição original
        trans_file = RESULTS_DIR / "transcription_original.txt"
        trans_file.write_text(transcription, encoding="utf-8")
        
        print(f"✅ Transcrição original salva: {trans_file}")
        print(f"📝 Texto: {transcription[:100]}...")
    
    def test_3_clone_voice_and_generate(self, setup_environment):
        """Passo 2: Clona voz e gera novo áudio com a transcrição."""
        from TTS.api import TTS
        
        # Ler transcrição original
        trans_file = RESULTS_DIR / "transcription_original.txt"
        assert trans_file.exists(), "Transcrição original não encontrada"
        
        transcription = trans_file.read_text(encoding="utf-8").strip()
        
        print(f"\n🎵 Clonando voz e gerando áudio...")
        print(f"📝 Texto para gerar: {transcription[:100]}...")
        
        # Carregar modelo XTTS
        tts = TTS(model_name="tts_models/multilingual/multi-dataset/xtts_v2")
        tts.to("cpu")  # CPU evita erro cuFFT
        
        # Gerar áudio clonado
        output_path = RESULTS_DIR / "cloned_output.wav"
        
        wav = tts.tts(
            text=transcription,
            speaker_wav=str(REFERENCE_AUDIO),
            language="pt"
        )
        
        # Converter para numpy se necessário
        if isinstance(wav, list):
            wav = np.array(wav, dtype=np.float32)
        
        # Salvar áudio gerado
        sf.write(output_path, wav, 22050)
        
        # Validar áudio gerado
        assert output_path.exists(), "Áudio clonado não foi salvo"
        
        data, sr = sf.read(output_path)
        assert len(data) > 0, "Áudio clonado está vazio"
        assert sr == 22050, f"Sample rate incorreto: {sr}"
        
        # Verificar se há som (não é silêncio)
        rms = np.sqrt(np.mean(data**2))
        assert rms > 0.001, f"Áudio parece estar em silêncio (RMS={rms})"
        
        print(f"✅ Áudio clonado salvo: {output_path}")
        print(f"📊 Duração: {len(data)/sr:.2f}s, RMS: {rms:.4f}")
    
    def test_4_transcribe_generated(self, setup_environment):
        """Passo 3: Transcreve áudio gerado e valida."""
        import whisper
        
        # Verificar se áudio gerado existe
        cloned_path = RESULTS_DIR / "cloned_output.wav"
        assert cloned_path.exists(), "Áudio clonado não encontrado"
        
        print(f"\n🎤 Transcrevendo áudio gerado...")
        
        # Carregar modelo Whisper
        model = whisper.load_model("base")
        
        # Transcrever áudio gerado
        result = model.transcribe(str(cloned_path), language="pt", fp16=False)
        generated_transcription = result["text"].strip()
        
        assert generated_transcription, "Transcrição do áudio gerado vazia"
        
        # Salvar transcrição gerada
        trans_generated_file = RESULTS_DIR / "transcription_generated.txt"
        trans_generated_file.write_text(generated_transcription, encoding="utf-8")
        
        print(f"✅ Transcrição gerada salva: {trans_generated_file}")
        print(f"📝 Texto: {generated_transcription[:100]}...")
    
    def test_5_validate_voice_cloning(self):
        """Passo 4: Valida se modelo falou corretamente."""
        # Ler transcrições
        trans_original = (RESULTS_DIR / "transcription_original.txt").read_text(encoding="utf-8").strip()
        trans_generated = (RESULTS_DIR / "transcription_generated.txt").read_text(encoding="utf-8").strip()
        
        print(f"\n🔍 VALIDAÇÃO FINAL")
        print(f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
        print(f"📝 Texto Original:")
        print(f"   {trans_original}")
        print(f"\n📝 Texto Gerado (Whisper no áudio clonado):")
        print(f"   {trans_generated}")
        
        # Calcular similaridade
        similarity = similarity_ratio(trans_original, trans_generated)
        
        print(f"\n📊 Similaridade: {similarity*100:.2f}%")
        print(f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
        
        # Salvar resultado final
        result = {
            "reference_audio": str(REFERENCE_AUDIO.name),
            "cloned_audio": "cloned_output.wav",
            "transcription_original": trans_original,
            "transcription_generated": trans_generated,
            "similarity": similarity,
            "test_passed": similarity >= 0.80,  # 80% mínimo
            "validation": {
                "method": "Whisper ASR comparison",
                "threshold": 0.80,
                "result": "PASSED" if similarity >= 0.80 else "FAILED"
            }
        }
        
        result_file = RESULTS_DIR / "voice_cloning_validation.json"
        with open(result_file, "w", encoding="utf-8") as f:
            json.dump(result, f, indent=2, ensure_ascii=False)
        
        print(f"\n💾 Resultado salvo: {result_file}")
        
        # Assertar validação
        assert similarity >= 0.80, (
            f"❌ FALHOU: Similaridade {similarity*100:.2f}% < 80%\n"
            f"   Original: {trans_original}\n"
            f"   Gerado:   {trans_generated}"
        )
        
        print(f"\n✅ TESTE PASSOU! Modelo reproduziu {similarity*100:.2f}% do texto original")
    
    def test_6_audio_quality_metrics(self):
        """Métricas adicionais de qualidade do áudio."""
        try:
            import librosa
            from scipy.spatial.distance import cosine
        except ImportError:
            pytest.skip("librosa/scipy não instalados")
        
        # Ler áudios
        ref_data, ref_sr = sf.read(REFERENCE_AUDIO)
        cloned_data, cloned_sr = sf.read(RESULTS_DIR / "cloned_output.wav")
        
        # Resamplear referência se necessário
        if ref_sr != cloned_sr:
            ref_data = librosa.resample(ref_data, orig_sr=ref_sr, target_sr=cloned_sr)
            ref_sr = cloned_sr
        
        # Limitar ao menor comprimento
        min_len = min(len(ref_data), len(cloned_data))
        ref_data = ref_data[:min_len]
        cloned_data = cloned_data[:min_len]
        
        # Calcular MFCC
        ref_mfcc = librosa.feature.mfcc(y=ref_data, sr=ref_sr, n_mfcc=13)
        cloned_mfcc = librosa.feature.mfcc(y=cloned_data, sr=cloned_sr, n_mfcc=13)
        
        # Similaridade MFCC
        mfcc_similarity = 1 - cosine(ref_mfcc.mean(axis=1), cloned_mfcc.mean(axis=1))
        
        print(f"\n📊 MÉTRICAS DE QUALIDADE")
        print(f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
        print(f"🎵 MFCC Similarity: {mfcc_similarity*100:.2f}%")
        print(f"⏱️  Duração Original: {len(ref_data)/ref_sr:.2f}s")
        print(f"⏱️  Duração Clonada:  {len(cloned_data)/cloned_sr:.2f}s")
        print(f"📈 RMS Original: {np.sqrt(np.mean(ref_data**2)):.4f}")
        print(f"📈 RMS Clonado:  {np.sqrt(np.mean(cloned_data**2)):.4f}")
        
        # Atualizar resultado
        result_file = RESULTS_DIR / "voice_cloning_validation.json"
        with open(result_file) as f:
            result = json.load(f)
        
        result["audio_metrics"] = {
            "mfcc_similarity": mfcc_similarity,
            "duration_original": len(ref_data)/ref_sr,
            "duration_cloned": len(cloned_data)/cloned_sr,
            "rms_original": float(np.sqrt(np.mean(ref_data**2))),
            "rms_cloned": float(np.sqrt(np.mean(cloned_data**2)))
        }
        
        with open(result_file, "w", encoding="utf-8") as f:
            json.dump(result, f, indent=2, ensure_ascii=False)
        
        assert mfcc_similarity > 0.5, f"MFCC similarity muito baixa: {mfcc_similarity}"
        
        print(f"✅ Métricas de qualidade validadas")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
