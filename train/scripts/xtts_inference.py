"""
XTTS-v2 Inference Module

Wrapper para inferência com modelo XTTS-v2 fine-tunado.
Suporta carregamento de checkpoints customizados e voice cloning.

Usage:
    # Base model
    inference = XTTSInference()
    audio = inference.synthesize("Olá mundo", language="pt")
    
    # Fine-tuned model
    inference = XTTSInference(checkpoint_path="train/checkpoints/best_model.pt")
    audio = inference.synthesize("Texto custom", speaker_wav="reference.wav")
"""

import torch
import torch.serialization
import numpy as np
from pathlib import Path
from typing import Optional, Union
import logging

# PyTorch 2.6+ safe_globals fix
from TTS.tts.configs.xtts_config import XttsConfig
try:
    from TTS.tts.models.xtts import XttsAudioConfig, XttsArgs
    from TTS.config.shared_configs import BaseDatasetConfig
    torch.serialization.add_safe_globals([XttsConfig, XttsAudioConfig, XttsArgs, BaseDatasetConfig])
except ImportError:
    try:
        from TTS.config.shared_configs import BaseDatasetConfig
        from TTS.tts.models.xtts import XttsArgs
        torch.serialization.add_safe_globals([XttsConfig, XttsArgs, BaseDatasetConfig])
    except ImportError:
        try:
            from TTS.config.shared_configs import BaseDatasetConfig
            torch.serialization.add_safe_globals([XttsConfig, BaseDatasetConfig])
        except ImportError:
            torch.serialization.add_safe_globals([XttsConfig])

logger = logging.getLogger(__name__)


class XTTSInference:
    """
    XTTS-v2 Inference Engine
    
    Carrega modelo XTTS-v2 (base ou fine-tuned) para síntese de voz.
    """
    
    def __init__(
        self,
        checkpoint_path: Optional[Union[str, Path]] = None,
        device: Optional[str] = None,
        use_deepspeed: bool = False
    ):
        """
        Inicializa engine de inferência.
        
        Args:
            checkpoint_path: Path para checkpoint fine-tuned.
                           Se None, usa modelo base XTTS-v2.
            device: Device PyTorch ('cuda', 'cpu', 'cuda:0', 'auto').
                   Se None ou 'auto', detecta automaticamente.
            use_deepspeed: Habilita DeepSpeed para inferência otimizada.
        """
        self.checkpoint_path = Path(checkpoint_path) if checkpoint_path else None
        self.device = self._setup_device(device)
        self.use_deepspeed = use_deepspeed
        
        logger.info("🎤 Inicializando XTTS Inference Engine...")
        logger.info(f"   Device: {self.device}")
        logger.info(f"   Checkpoint: {self.checkpoint_path or 'Base model'}")
        
        # Carregar modelo
        self.model = self._load_model()
        
        # Configurações default
        self.default_language = "pt"
        self.default_sample_rate = 22050
        
        logger.info("✅ XTTS Inference Engine pronto!")
    
    def _setup_device(self, device: Optional[str]) -> torch.device:
        """Detecta ou valida device PyTorch."""
        if device is None or device == "auto":
            device = "cuda" if torch.cuda.is_available() else "cpu"
        
        device_obj = torch.device(device)
        
        if device_obj.type == "cuda" and not torch.cuda.is_available():
            logger.warning("⚠️  CUDA solicitado mas não disponível. Usando CPU.")
            device_obj = torch.device("cpu")
        
        return device_obj
    
    def _load_model(self):
        """
        Carrega modelo XTTS-v2.
        
        Returns:
            Modelo carregado (TTS.api.TTS ou custom wrapper)
        """
        try:
            from TTS.api import TTS
        except ImportError:
            logger.error("❌ TTS (Coqui) não encontrado. Instale com: pip install TTS")
            raise
        
        # Configurar environment
        import os
        os.environ['COQUI_TOS_AGREED'] = '1'
        
        # Fix PyTorch 2.6 weights_only issue
        import torch.serialization
        try:
            from TTS.tts.configs.xtts_config import XttsConfig
            torch.serialization.add_safe_globals([XttsConfig])
        except Exception as e:
            logger.warning(f"⚠️  Não foi possível adicionar safe_globals: {e}")
        
        if self.checkpoint_path and self.checkpoint_path.exists():
            # Carregar checkpoint fine-tuned
            logger.info(f"📥 Carregando checkpoint: {self.checkpoint_path}")
            
            # OPÇÃO 1: Carregar base model e aplicar checkpoint
            model = TTS(
                "tts_models/multilingual/multi-dataset/xtts_v2",
                gpu=(self.device.type == "cuda"),
                progress_bar=False
            )
            
            # Carregar state_dict do checkpoint
            checkpoint = torch.load(self.checkpoint_path, map_location=self.device)
            
            if 'model_state_dict' in checkpoint:
                # Checkpoint de training (com optimizer, etc)
                state_dict = checkpoint['model_state_dict']
                logger.info(f"   Epoch/Step: {checkpoint.get('global_step', 'N/A')}")
                logger.info(f"   Val Loss: {checkpoint.get('val_loss', 'N/A')}")
            else:
                # Best model (apenas weights)
                state_dict = checkpoint
            
            # Aplicar weights ao modelo
            model.synthesizer.tts_model.load_state_dict(state_dict, strict=False)
            logger.info("✅ Checkpoint carregado com sucesso!")
            
        else:
            # Carregar modelo base
            logger.info("📥 Carregando modelo base XTTS-v2...")
            model = TTS(
                "tts_models/multilingual/multi-dataset/xtts_v2",
                gpu=(self.device.type == "cuda"),
                progress_bar=False
            )
            logger.info("✅ Modelo base carregado!")
        
        return model
    
    def synthesize(
        self,
        text: str,
        language: str = "pt",
        speaker_wav: Optional[Union[str, Path]] = None,
        speed: float = 1.0,
        temperature: float = 0.75,
        length_penalty: float = 1.0,
        repetition_penalty: float = 2.0,
        top_k: int = 50,
        top_p: float = 0.85,
    ) -> np.ndarray:
        """
        Sintetiza áudio a partir de texto.
        
        Args:
            text: Texto para sintetizar
            language: Código de idioma ('pt', 'en', 'es', 'fr', 'de', etc)
            speaker_wav: Path para áudio de referência (voice cloning).
                        Se None, usa voz padrão do modelo.
            speed: Velocidade da fala (0.5-2.0)
            temperature: Criatividade da geração (0.0-1.0)
            length_penalty: Penalidade por comprimento
            repetition_penalty: Penalidade por repetição
            top_k: Top-K sampling
            top_p: Nucleus sampling
        
        Returns:
            Array numpy com áudio (22050 Hz mono)
        
        Example:
            >>> inference = XTTSInference()
            >>> audio = inference.synthesize(
            ...     "Olá, como vai?",
            ...     language="pt",
            ...     speaker_wav="reference.wav"
            ... )
            >>> # Salvar áudio
            >>> import soundfile as sf
            >>> sf.write("output.wav", audio, 22050)
        """
        logger.info(f"🎙️  Sintetizando: '{text[:50]}...'")
        logger.info(f"   Language: {language}")
        logger.info(f"   Speaker: {speaker_wav or 'Default'}")
        
        # Validar inputs
        if not text or not text.strip():
            raise ValueError("Texto vazio não pode ser sintetizado")
        
        if speed < 0.5 or speed > 2.0:
            logger.warning(f"⚠️  Speed {speed} fora do range [0.5-2.0]. Ajustando...")
            speed = max(0.5, min(2.0, speed))
        
        # Converter speaker_wav para string se for Path
        if speaker_wav:
            speaker_wav = str(Path(speaker_wav).resolve())
            if not Path(speaker_wav).exists():
                raise FileNotFoundError(f"Arquivo de speaker não encontrado: {speaker_wav}")
        
        # Gerar áudio
        try:
            if speaker_wav:
                # Voice cloning com speaker reference
                audio = self.model.tts(
                    text=text,
                    language=language,
                    speaker_wav=speaker_wav,
                    speed=speed,
                    temperature=temperature,
                    length_penalty=length_penalty,
                    repetition_penalty=repetition_penalty,
                    top_k=top_k,
                    top_p=top_p,
                )
            else:
                # Voz padrão do modelo
                audio = self.model.tts(
                    text=text,
                    language=language,
                    speed=speed,
                    temperature=temperature,
                    length_penalty=length_penalty,
                    repetition_penalty=repetition_penalty,
                    top_k=top_k,
                    top_p=top_p,
                )
            
            # Converter para numpy array se necessário
            if isinstance(audio, list):
                audio = np.array(audio, dtype=np.float32)
            elif torch.is_tensor(audio):
                audio = audio.cpu().numpy()
            
            logger.info(f"✅ Áudio gerado: {len(audio)/self.default_sample_rate:.2f}s")
            
            return audio
            
        except Exception as e:
            logger.error(f"❌ Erro na síntese: {e}")
            raise
    
    def synthesize_to_file(
        self,
        text: str,
        output_path: Union[str, Path],
        **kwargs
    ) -> Path:
        """
        Sintetiza áudio e salva em arquivo.
        
        Args:
            text: Texto para sintetizar
            output_path: Path do arquivo de saída (.wav)
            **kwargs: Argumentos adicionais para synthesize()
        
        Returns:
            Path do arquivo salvo
        
        Example:
            >>> inference = XTTSInference()
            >>> path = inference.synthesize_to_file(
            ...     "Teste de síntese",
            ...     "output.wav",
            ...     language="pt"
            ... )
        """
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Gerar áudio
        audio = self.synthesize(text, **kwargs)
        
        # Salvar arquivo
        import soundfile as sf
        sf.write(output_path, audio, self.default_sample_rate)
        
        logger.info(f"💾 Áudio salvo: {output_path}")
        
        return output_path
    
    def get_model_info(self) -> dict:
        """
        Retorna informações sobre o modelo carregado.
        
        Returns:
            Dict com informações do modelo
        """
        info = {
            "model_type": "XTTS-v2",
            "checkpoint": str(self.checkpoint_path) if self.checkpoint_path else "Base model",
            "device": str(self.device),
            "sample_rate": self.default_sample_rate,
            "languages": ["pt", "en", "es", "fr", "de", "it", "pl", "tr", "ru", "nl", "cs", "ar", "zh-cn", "ja", "hu", "ko"],
        }
        
        # Adicionar info do checkpoint se disponível
        if self.checkpoint_path and self.checkpoint_path.exists():
            checkpoint = torch.load(self.checkpoint_path, map_location="cpu")
            info["checkpoint_step"] = checkpoint.get("global_step", "N/A")
            info["checkpoint_val_loss"] = checkpoint.get("val_loss", "N/A")
        
        return info


# Singleton global para reutilização
_global_inference = None


def get_inference_engine(
    checkpoint_path: Optional[Union[str, Path]] = None,
    force_reload: bool = False
) -> XTTSInference:
    """
    Retorna instância singleton do inference engine.
    
    Args:
        checkpoint_path: Path para checkpoint (None = base model)
        force_reload: Força recarregar modelo mesmo se já existir
    
    Returns:
        XTTSInference instance
    
    Example:
        >>> # Usar em FastAPI
        >>> from train.scripts.xtts_inference import get_inference_engine
        >>> 
        >>> @app.get("/synthesize")
        >>> async def synthesize(text: str):
        >>>     engine = get_inference_engine()
        >>>     audio = engine.synthesize(text)
        >>>     return audio
    """
    global _global_inference
    
    if _global_inference is None or force_reload:
        _global_inference = XTTSInference(checkpoint_path=checkpoint_path)
    
    return _global_inference


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="XTTS Inference CLI")
    parser.add_argument("--checkpoint", type=str, default=None, help="Path to fine-tuned checkpoint")
    parser.add_argument("--text", type=str, required=True, help="Text to synthesize")
    parser.add_argument("--speaker", type=str, default=None, help="Reference speaker WAV file")
    parser.add_argument("--output", type=str, required=True, help="Output WAV file path")
    parser.add_argument("--language", type=str, default="pt", help="Language code (default: pt)")
    parser.add_argument("--temperature", type=float, default=0.7, help="Sampling temperature")
    parser.add_argument("--speed", type=float, default=1.0, help="Speech speed")
    
    args = parser.parse_args()
    
    # Setup logging
    logging.basicConfig(level=logging.INFO)
    
    # Initialize inference engine
    inference = XTTSInference(checkpoint_path=args.checkpoint)
    
    # Synthesize
    inference.synthesize_to_file(
        text=args.text,
        output_path=args.output,
        speaker_wav=args.speaker,
        language=args.language,
        temperature=args.temperature,
        speed=args.speed
    )
    
    print(f"✅ Audio saved to: {args.output}")
